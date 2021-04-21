from __future__ import unicode_literals

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from .signals import attachments_attached
from .utils import JSONField, get_context_key, get_default_path, get_storage, import_class, sizeof_fmt, Centos7ClamdUnixSocket
from .exceptions import VirusFoundException, InvalidExtensionException, InvalidFileTypeException, FileSizeException

import os
import magic
import mimetypes
import ntpath


FIELD_TYPE_CHOICES = (
    ('string', 'Text'),
    ('text', 'Large Text'),
    ('integer', 'Integer'),
    ('decimal', 'Decimal'),
    ('boolean', 'Boolean'),
    ('date', 'Date'),
    ('email', 'Email Address'),
    ('choice', 'Choice'),
    ('model', 'Model')
)


class AttachmentManager (models.Manager):

    def attach_raw(self, f, obj, user=None, context='', storage=None, path=None, data=None, filename=None):
        if filename is None:
            filename = ntpath.basename(f.name)
        if storage is None:
            storage = get_storage()
        if path is None:
            ct = ContentType.objects.get_for_model(obj)
            path = '%s/%s/%s/%s/%s' % (ct.app_label, ct.model, obj.pk, context, filename)
        new_path = storage.save(path, f)
        return self.create(
            file_path=new_path,
            file_name=filename,
            file_size=f.size,
            user=user,
            context=context,
            data=data,
            content_object=obj
        )


class Attachment (models.Model):
    file_path = models.TextField(unique=True)
    file_name = models.CharField(max_length=200)
    file_size = models.IntegerField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='attachments', null=True, blank=True, on_delete=models.SET_NULL)
    context = models.CharField(max_length=200, blank=True, db_index=True)
    date_created = models.DateTimeField(default=timezone.now, editable=False)

    # User-defined data, stored as JSON in a text field.
    data = JSONField(null=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    objects = AttachmentManager()

    def __str__(self):
        return self.file_name

    def delete(self, **kwargs):
        try:
            get_storage().delete(self.file_path)
        except Exception:
            pass
        super(Attachment, self).delete(**kwargs)

    def get_absolute_url(self):
        show_filenames = getattr(settings, 'ATTACHMENT_URL_FILENAMES', True)
        return reverse('attachment-download', kwargs={
            'attach_id': self.pk,
            'filename': self.file_name if show_filenames else '',
        })

    def get_edit_property_url(self):
        return reverse('edit-attachment-properties', kwargs={
            'attach_id': self.pk,
        })

    def get_view_property_url(self):
        return reverse('view-attachment-properties', kwargs={
            'attach_id': self.pk,
        })

    @property
    def querydata(self):
        from django.utils.datastructures import MultiValueDict
        return MultiValueDict(self.data or {})

    def extract_data(self, request):
        data = {}
        if request and request.POST:
            prefix = 'attachment-%d-' % self.pk
            for key in request.POST:
                if key.startswith(prefix):
                    data[key[len(prefix):]] = request.POST.getlist(key)
        return data

    def get_properties(self):
        return Property.objects.filter(content_type=self.content_type)

    def get_field(self, prop):
        """
            Added for use in bootstrap's template tag render_value. Returns tuple of property label and value
        """
        if prop.data_type == 'model' and prop.slug in self.data:
            return prop.label, prop.model_queryset().get(pk=self.data.get(prop.slug, [])[0])
        else:
            return prop.label, self.data.get(prop.slug, [])


class Property (models.Model):
    label = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, help_text='Must be alphanumeric, with no spaces.')
    data_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)
    choices = models.TextField(blank=True, help_text='Lookup choices for a ChoiceField, one per line.')
    model = models.CharField(max_length=200, blank=True, help_text='The path to the lookup model for a ModelChoiceField.')
    content_type = models.ManyToManyField(ContentType, related_name='attachment_properties', blank=True)
    required = models.BooleanField(default=True)
    is_editable = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'properties'

    def __str__(self):
        return self.label

    @property
    def choice_list(self):
        return [ch.strip() for ch in self.choices.split('\n') if ch.strip()]

    def model_queryset(self, **kwargs):
        ModelClass = import_class(self.model)
        # Lookup models can provide an @classmethod 'field_model_queryset' to have control over what queryset is used
        if hasattr(ModelClass, 'field_model_queryset'):
            try:
                qs = getattr(ModelClass, 'field_model_queryset')(**kwargs)
            except:
                qs = getattr(ModelClass, 'field_model_queryset')()
        else:
            qs = ModelClass.objects.all()
        return qs


class Session (models.Model):
    uuid = models.CharField(max_length=32, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='attachment_sessions', null=True, blank=True, on_delete=models.SET_NULL)
    template = models.CharField(max_length=200, default='attachments/list.html')
    context = models.CharField(max_length=200, blank=True)
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
    date_created = models.DateTimeField(default=timezone.now, editable=False)
    allowed_file_extensions = models.TextField(help_text='Whitespace-separated file extensions that are allowed for upload.', blank=True)
    allowed_file_types = models.TextField(help_text='White list of file types that are allowed for upload, separated by new line. Used as a fallback if file mimetype is not known.', blank=True)

    # User-defined data, stored as JSON in a text field.
    data = JSONField(null=True)

    # Stash the request object when calling attachments.session()
    _request = None

    def __str__(self):
        return self.uuid

    def delete(self, **kwargs):
        for upload in self.uploads.all():
            upload.delete()
        super(Session, self).delete(**kwargs)

    def get_absolute_url(self):
        return reverse('attach', kwargs={
            'session_id': self.uuid,
        })

    def extract_data(self):
        data = {}
        if self._request and self._request.POST:
            for upload in self.uploads.all():
                prefix = 'upload-%d-' % upload.pk
                for key in self._request.POST:
                    if key.startswith(prefix):
                        data[key] = self._request.POST.getlist(key)
        return data

    def set_data(self, extract_data=None, save=True):
        self.data = extract_data(self) if extract_data else self.extract_data()
        if save:
            self.save()

    def hidden_input(self):
        return mark_safe('<input type="hidden" name="%s" value="%s" />' % (get_context_key(self.context), self.uuid))

    def attach(self, obj, storage=None, path=None, data=None, send_signal=True):
        attached = []
        if storage is None:
            storage = get_storage()
        if path is None:
            path = get_default_path
        for upload in self.uploads.all():
            with open(upload.file_path, 'rb') as fp:
                new_path = storage.save(path(upload, obj), File(fp))
                att_data = data(upload) if data else upload.extract_data(self._request)
                attached.append(Attachment.objects.create(
                    file_path=new_path,
                    file_name=upload.file_name,
                    file_size=upload.file_size,
                    user=self.user,
                    context=self.context,
                    data=att_data,
                    content_object=obj
                ))
        if send_signal:
            # Send a signal that attachments were attached. Pass what attachments were attached and to what object.
            attachments_attached.send(sender=self, obj=obj, attachments=attached)
        return attached

    def is_valid(self):
        if not self.content_type:
            return True
        from .forms import PropertyForm
        valids = []
        for upload in self.uploads.all():
            property_form = PropertyForm(self._request.POST, instance=upload, editable_only=False)
            valids.append(property_form.is_valid())
        # Commit the property data to the database
        self.set_data()
        is_valid = all(valids)
        self.bind_form_on_refresh = not is_valid
        return is_valid

    @property
    def upload_forms(self):
        from .forms import PropertyForm
        for upload in self.uploads.all():
            kwargs = {'instance': upload, 'editable_only': False, }
            is_bound = (self._request is not None and (self._request.method == 'POST' or self._request.GET.get('bind-form-data', False)))
            if is_bound:
                kwargs['data'] = PropertyForm.get_form_data_from_session_data(self.data)
            property_form = PropertyForm(**kwargs)   
            if self.data:
                property_key_prefix = 'upload-{}-'.format(upload.pk)
                for key in self.data:
                    # If the property_key_prefix exists in self.data, then we validate the form to show form errors
                    if key.startswith(property_key_prefix):
                        property_form.is_valid()
            yield upload, property_form

    def validate_upload(self, upload):
        '''
        This function validates the given upload by checking:
           1) The file extension is valid
           2) The file type (format) is valid
           3) The file is under the maximum size limit
           4) The file is free of viruses
        These checks can be customized, including turning them on/off completely.
        '''

        # Checking if file extension is within allowed extension list
        if self.allowed_file_extensions:
            allowed_exts = self.allowed_file_extensions.lower().split()
            allowed_exts = [x if x.startswith('.') else '.{}'.format(x) for x in allowed_exts]
            # Allow sites to override the default mime types for certain file extensions
            # xslx files for example can often have the incorrect mime type if created outside excel 
            mime_types_overrides = getattr(settings, 'ATTACHMENTS_MIME_TYPE_OVERRIDES', {})
            filename, ext = os.path.splitext(upload.file_name)
            if ext.lower() not in allowed_exts:
                raise InvalidExtensionException("{} - Error: Unsupported file format. Supported file formats are: {}".format(
                    upload.file_name, ', '.join(allowed_exts)))

            # Checking whether file contents comply with the allowed file extensions (if the file has data).
            # This ensures that file types not allowed are rejected even if they are renamed.
            if upload.file_size != 0:
                file_mime = magic.from_file(upload.file_path, mime=True)
 
                if (set(mimetypes.guess_all_extensions(file_mime)).isdisjoint(set(allowed_exts)) and 
                    file_mime not in mime_types_overrides.get(ext, [])):
                    # In case our check for extensions didn't pass we check if the file type (not mimetype)
                    # is white-listed. If so, we can allow the file to be uploaded.
                    allowed_types = self.allowed_file_types.split('\n')
                    file_type = magic.from_file(upload.file_path, mime=False)
                    if file_type not in allowed_types:
                        raise InvalidFileTypeException("{} - Error: The extension for this file is valid, but the content is not. Please verify the file content has been updated and save it again before attempting upload.".format(
                            upload.file_name))

        # Verify the upload is not over the allowable limit
        # Defaults to 50Mb (in binary byte size)
        max_file_size = getattr(settings, 'ATTACHMENTS_MAX_FILE_SIZE_BYTES', 52428800)
        # max_file_size can be None (which means any size is allowed)
        if max_file_size and upload.file_size > max_file_size:
            raise FileSizeException("File is too large to be uploaded, file cannot be greater than {}".format(sizeof_fmt(max_file_size)))

        if getattr(settings, 'ATTACHMENTS_CLAMD', False):
            # We should explore moving this import in the future
            import pyclamd
            clamd_network_settings = getattr(settings, 'ATTACHMENTS_CLAMD_NETWORK_SETTINGS', {})
            # If network settings are provided we use them to establish a socket connection
            if clamd_network_settings:
                # ClamdNetworkSocket accepts 'host', 'port', and 'timeout' as keys in ATTACHMENTS_CLAMD_NETWORK_SETTINGS
                cd = pyclamd.ClamdNetworkSocket(**clamd_network_settings)
            else:
                cd = Centos7ClamdUnixSocket(filename=getattr(settings, 'ATTACHMENTS_CLAMD_UNIX_SOCKET_LOCATION', None))
            virus = cd.scan_file(upload.file_path)
            if virus is not None:
                raise VirusFoundException('**WARNING** virus: "{}" found in the file: "{}", could not upload!'.format(virus[upload.file_path][1], upload.file_name))


class Upload (models.Model):
    session = models.ForeignKey(Session, related_name='uploads', on_delete=models.CASCADE)
    file_path = models.TextField(unique=True)
    file_name = models.CharField(max_length=200)
    file_size = models.IntegerField()
    date_created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.file_name

    def delete(self, **kwargs):
        try:
            os.remove(self.file_path)
        except Exception:
            pass
        super(Upload, self).delete(**kwargs)

    def extract_data(self, request):
        data = {}
        if request and request.POST:
            prefix = 'upload-%d-' % self.pk
            for key in request.POST:
                if key.startswith(prefix):
                    data[key[len(prefix):]] = request.POST.getlist(key)
        return data

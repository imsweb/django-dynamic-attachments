from django.db import models
from django.core.urlresolvers import reverse
from django.core.files import File
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.conf import settings
from .utils import get_context_key, get_storage, get_default_path, JSONField
import os

FIELD_TYPE_CHOICES = (
    ('string', 'Text'),
    ('text', 'Large Text'),
    ('integer', 'Integer'),
    ('decimal', 'Decimal'),
    ('boolean', 'Boolean'),
    ('date', 'Date'),
    ('lookup', 'Lookup (Dropdown)'),
    ('radio', 'Lookup (Radio)'),
    ('multi', 'Multi-Value Lookup (Checkboxes)'),
    ('multilist', 'Multi-Value Lookup (Multi-Select)'),
    ('email', 'Email Address'),
)

class Attachment (models.Model):
    file_path = models.TextField(unique=True)
    file_name = models.CharField(max_length=200)
    file_size = models.IntegerField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='attachments')
    context = models.CharField(max_length=200, blank=True, db_index=True)
    date_created = models.DateTimeField(default=timezone.now, editable=False)

    # User-defined data, stored as JSON in a text field.
    data = JSONField(null=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    def __unicode__(self):
        return self.file_name

    def delete(self, **kwargs):
        try:
            get_storage().delete(self.file_path)
        except:
            pass
        super(Attachment, self).delete(**kwargs)

    def get_absolute_url(self):
        # TODO: setting to include filename in URL?
        return reverse('attachment-download', kwargs={
            'attach_id': self.pk,
            'filename': self.file_name,
        })

    def get_property_url(self):
        return reverse('show-attachment-properties', kwargs={
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

class Property (models.Model):
    label = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, help_text='Must be alphanumeric, with no spaces.')
    data_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)
    content_type = models.ManyToManyField(ContentType, related_name='attachment_properties', blank=True)

    class Meta:
        verbose_name_plural = 'properties'

    def __unicode__(self):
        return self.label

class Session (models.Model):
    uuid = models.CharField(max_length=32, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='attachment_sessions')
    template = models.CharField(max_length=200, default='attachments/list.html')
    context = models.CharField(max_length=200, blank=True)
    date_created = models.DateTimeField(default=timezone.now, editable=False)

    # Stash the request object when calling attachments.session()
    _request = None

    def __unicode__(self):
        return self.uuid

    def delete(self, **kwargs):
        for upload in self.uploads.all():
            upload.delete()
        super(Session, self).delete(**kwargs)

    def get_absolute_url(self):
        return reverse('attach', kwargs={
            'session_id': self.uuid,
        })

    def hidden_input(self):
        return mark_safe('<input type="hidden" name="%s" value="%s" />' % (get_context_key(self.context), self.uuid))

    def attach(self, obj, storage=None, path=None, data=None):
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
        return attached

class Upload (models.Model):
    session = models.ForeignKey(Session, related_name='uploads')
    file_path = models.TextField(unique=True)
    file_name = models.CharField(max_length=200)
    file_size = models.IntegerField()
    date_created = models.DateTimeField(default=timezone.now)

    def __unicode__(self):
        return self.file_name

    def delete(self, **kwargs):
        try:
            os.remove(self.file_path)
        except:
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

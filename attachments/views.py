from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.move import file_move_safe
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import ContextMixin
import magic

from .exceptions import FileSizeException, InvalidExtensionException, InvalidFileTypeException, VirusFoundException
from .forms import PropertyForm
from .models import Attachment, Session, Upload
from .signals import file_download, file_uploaded, virus_detected
from .utils import Centos7ClamdUnixSocket, ajax_only, get_storage, sizeof_fmt, url_filename, user_has_access, get_template_path

from datetime import datetime
from io import BytesIO
from pathlib import Path
from wsgiref.util import FileWrapper
from zipfile import ZipFile
import json
import logging
import mimetypes
import os
import re
import tempfile

logger = logging.getLogger(__name__)
template_path = get_template_path()

decorators = [ajax_only, csrf_exempt]


@method_decorator(decorators, name='dispatch')
class AttachView(ContextMixin, View):
    http_method_names = ['get', 'post']

    def validate_max_length(self):
        max_lengh = Upload._meta.get_field('file_name').max_length
        if len(self.file.name) > max_lengh:
            raise ValidationError(
                f'An error occurred attaching file to the session. The filename cannot exceed {max_lengh} characters.'
            )

    def sanitize_file_name(self):
        sanitized_chars = r'[<>()\';&"%/\\`]'
        sanitized_name = re.sub(sanitized_chars, '', self.file.name)
        self.file.name = sanitized_name 
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.session = get_object_or_404(Session, uuid=kwargs['session_id'])
        self.session._request = request
        self.file = request.FILES.get('attachment')

        if self.file:
            self.sanitize_file_name()
            self.validate_max_length()

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['session'] = self.session
        return render(request, self.session.template, context)

    def create_tmp_file(self):
        # Copy the Django attachment (which may be a file or in memory) over to a temp file.
        temp_dir = getattr(settings, 'ATTACHMENT_TEMP_DIR', None)
        if temp_dir and not os.path.exists(temp_dir):
            mode = settings.FILE_UPLOAD_DIRECTORY_PERMISSIONS or 0o777
            os.makedirs(temp_dir, mode=mode)
        fd, path = tempfile.mkstemp(dir=temp_dir)
        with os.fdopen(fd, 'wb') as fp:
            for chunk in self.file.chunks():
                fp.write(chunk)

        # Set the desired permissions based on Django's FILE_UPLOAD_PERMISSIONS setting
        if settings.FILE_UPLOAD_PERMISSIONS:
            os.chmod(path, settings.FILE_UPLOAD_PERMISSIONS)

        return path

    def create_upload(self, path):
        return Upload.objects.create(
            file_path=path, file_name=self.file.name, file_size=self.file.size, session=self.session
        )

    def validate_extension(self, path):
        """
        This function validates the given file by checking:
           1) The file extension is valid
           2) The file type (format) is valid
        """
        # Checking if file extension is within allowed extension list
        if self.session.allowed_file_extensions:
            allowed_exts = self.session.allowed_file_extensions.lower().split()
            allowed_exts = [x if x.startswith('.') else f'.{x}' for x in allowed_exts]
            # Allow sites to override the default mime types for certain file extensions
            # xslx files for example can often have the incorrect mime type if created outside excel
            mime_types_overrides = getattr(settings, 'ATTACHMENTS_MIME_TYPE_OVERRIDES', {})
            filename, ext = os.path.splitext(self.file.name)
            if ext.lower() not in allowed_exts:
                allowed_exts = ', '.join(allowed_exts)
                raise InvalidExtensionException(
                    f"{self.file.name} - Error: Unsupported file format. Supported file formats are: {allowed_exts}"
                )

            # Checking whether file contents comply with the allowed file extensions (if the file has data).
            # This ensures that file types not allowed are rejected even if they are renamed.
            if self.file.size != 0:
                file_bytes = list(self.file.chunks())[0]
                file_mime = magic.from_buffer(file_bytes, mime=True)

                if set(mimetypes.guess_all_extensions(file_mime)).isdisjoint(
                    set(allowed_exts)
                ) and file_mime not in mime_types_overrides.get(ext, []):
                    # In case our check for extensions didn't pass we check if the file type (not mimetype)
                    # is white-listed. If so, we can allow the file to be uploaded.
                    allowed_types = self.session.allowed_file_types.split('\n')
                    file_type = magic.from_buffer(file_bytes, mime=False)
                    if file_type not in allowed_types:
                        raise InvalidFileTypeException(
                            f"{ self.file.name } - Error: The extension for this file is valid, but the content is not. Please verify the file content has been updated and save it again before attempting upload."
                        )

    def validate_max_size(self):
        """
        This function validates the file is under the maximum size limit
        """

        # Verify the upload is not over the allowable limit
        # Defaults to 50Mb (in binary byte size)
        max_file_size = getattr(settings, 'ATTACHMENTS_MAX_FILE_SIZE_BYTES', 52428800)
        # max_file_size can be None (which means any size is allowed)
        if max_file_size and self.file.size > max_file_size:
            raise FileSizeException(
                f"File is too large to be uploaded, file cannot be greater than { sizeof_fmt(max_file_size) }"
            )

    def scan_clamd(self, path):
        """
        This function validates the file is free of viruses (if CLAMD is configured)
        """

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
            virus = cd.scan_file(path)
            if virus is not None:
                raise VirusFoundException(
                    f'**WARNING** virus: "{virus[path][1]}" found in the file: "{self.file.name}", could not upload!'
                )

    def set_session_data(self):
        # Update the data for this session (includes all form data for the attachments)
        for key, value in self.request.POST.items():
            if self.session.data:
                self.session.data.update({key: value})
            else:
                self.session.data = {key: value}
        self.session.save()

    def handle_virus_found(self, upload, ex):
        user = getattr(self.request, 'user', "Unknown user")
        filename = upload.file_name
        # If ATTACHMENTS_QUARANTINE_PATH is set, move the offending file to the quarantine, otherwise delete
        attachments_quarantine_path = getattr(settings, 'ATTACHMENTS_QUARANTINE_PATH', None)
        if attachments_quarantine_path:
            quarantine_path = os.path.join(attachments_quarantine_path, os.path.basename(upload.file_path))
            file_move_safe(os.path.basename(upload.file_path), quarantine_path)
            quarantine_msg = f'File has been quarantined here: {quarantine_path}'
        else:
            os.remove(upload.file_path)
            quarantine_path = None
            quarantine_msg = 'File has been removed from the system'

        error_msg = force_str(ex)
        time_of_upload = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"{error_msg} - Uploaded by {user} at {time_of_upload}. {quarantine_msg}."
        logger.exception(log_message)

        virus_detected.send(
            sender=upload,
            user=user,
            filename=filename,
            exception=ex,
            time_of_upload=time_of_upload,
            quarantine_path=quarantine_path,
        )

        return JsonResponse({'ok': False, 'error': error_msg}, content_type=self.content_type)

    def handle_file_upload(self, request, *args, **kwargs):
        try:
            path = self.create_tmp_file()

            self.validate_extension(path)
            self.validate_max_size()
            self.scan_clamd(path)

            upload = self.create_upload(path)
            self.set_session_data()

            # Keeping the sender as 'self.file' for backwards compatibility
            file_uploaded.send(sender=self.file, request=request, session=self.session)
            return JsonResponse(
                {'ok': True, 'file_name': upload.file_name, 'file_size': upload.file_size},
                content_type=self.content_type,
            )

        # These errors have helpful messages, so we return them
        except (InvalidExtensionException, InvalidFileTypeException, FileSizeException) as ex:
            return JsonResponse({'ok': False, 'error': force_str(ex)}, content_type=self.content_type)
        except VirusFoundException as ex:
            return self.handle_virus_found(upload, ex)
        except ValidationError as ex:
            return JsonResponse({'ok': False, 'error': force_str(ex.message)}, content_type=self.content_type)
        except Exception:
            logger.exception(f'Error attaching file to session {self.kwargs["session_id"]}')
            # Since this is a catch all we need to return a generic error (in case a more sensitive error occurred)
            return JsonResponse(
                {'ok': False, 'error': 'An error occurred attaching file to the session.'},
                content_type=self.content_type,
            )

    @property
    def file_is_zipped(self):
        """Return True if self.file is a zip archive."""
        return Path(self.file.name).suffix.lower() == ".zip"

    def post(self, request, *args, **kwargs):
        # Old versions of IE doing iframe uploads would present a Save dialog on JSON responses.
        content_types = {'IFrame': 'text/plain'}
        self.content_type = content_types.get(request.POST.get('X-Requested-With'), 'application/json')
        # we have a zip file, and we're unpacking it
        if self.session.unpack_zip_files and self.file_is_zipped:
            zipped_file = self.file
            errors = []
            success_dicts = []
            with ZipFile(self.file, "r") as zf:
                files = [
                    SimpleUploadedFile(name=fileinfo.filename, content=BytesIO(zf.read(fileinfo.filename)).getbuffer())
                    for fileinfo in zf.infolist() if not fileinfo.is_dir()
                ]
            # zip file is empty - return JsonResponse immediately
            if not files:
                return JsonResponse(
                    {"ok": False, "error": f"{zipped_file.name} is empty."},
                    content_type=self.content_type,
                )
            for self.file in files:
                # zip file contains another zip file - add an error
                if self.file_is_zipped:
                    errors.append(f"{self.file.name} - Error: nested zip files are not supported.")
                else:
                    json_content = json.loads(self.handle_file_upload(request, *args, **kwargs).content)
                    # add an error if there is one
                    if error := json_content.get("error", None):
                        errors.append(error)
                    # we only return success_dicts if all files are error-free, so skip if we already have errors
                    elif not errors:
                        success_dicts.append(json_content)
            # some zip file contents returned errors
            if errors:
                return JsonResponse(
                    {
                        "ok": False,
                        "error": f"Error(s) in {zipped_file.name}:<br /><br />{'<br />'.join(errors)}",
                    },
                    content_type=self.content_type,
                )
            # all zip file contents were error-free
            else:
                return JsonResponse(
                    {
                        "ok": True,
                        "file_name": zipped_file.name,
                        "file_size": zipped_file.size,
                        "files": success_dicts,
                    },
                    content_type=self.content_type,
                )
        # not a zip file, or zip files aren't being unpacked
        return self.handle_file_upload(request, *args, **kwargs)


@csrf_exempt
@ajax_only
def attach(request, session_id):
    view_func = apps.get_app_config('attachments').get_attach_view().as_view()
    return view_func(request, session_id=session_id)


@csrf_exempt
@ajax_only
def delete_upload(request, session_id, upload_id):
    lookup_query = Q(session__uuid=session_id, pk=upload_id)
    if not request.user.has_perm('attachments.delete_upload'):
        lookup_query &= Q(session__user=request.user)
    upload = get_object_or_404(Upload, lookup_query)
    file_name = upload.file_name
    try:
        upload.delete()
        return JsonResponse({'ok': True})
    except Exception as ex:
        logger.exception('Error deleting upload (pk=%s, file_name=%s) from session %s', upload_id, file_name, session_id)
        return JsonResponse({'ok': False, 'error': force_str(ex)})


def download(request, attach_id, filename=None):
    attachment = get_object_or_404(Attachment, pk=attach_id)
    if not user_has_access(request, attachment):
        raise Http404()
    # Fire the download signal, in case receivers want to raise an Http404, or log downloads.
    file_download.send(sender=attachment, request=request)
    storage = get_storage()
    content_type = mimetypes.guess_type(attachment.file_name, strict=False)[0]
    if getattr(settings, 'ATTACHMENTS_USE_XSENDFILE', False):
        response = HttpResponse(content_type=content_type)
        response['X-Sendfile'] = storage.path(attachment.file_path)
    else:
        response = StreamingHttpResponse(FileWrapper(storage.open(attachment.file_path)), content_type=content_type)
    try:
        # Not all storage backends support getting filesize.

        response['Content-Length'] = storage.size(attachment.file_path)
    except NotImplementedError:
        pass
    if getattr(settings, 'ATTACHMENT_ALWAYS_DOWNLOAD', False) or not filename:
        filename = url_filename(filename or attachment.file_name)
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    return response


@ajax_only
def update_attachment(request, attach_id):
    attachment = get_object_or_404(Attachment, pk=attach_id)
    if not user_has_access(request, attachment):
        raise Http404()
    if request.method == 'POST':
        try:
            property_form = PropertyForm(request.POST, instance=attachment)
            if property_form.is_valid():
                attachment.data = attachment.extract_data(request)
                attachment.save()
                return JsonResponse({'ok': True})
            else:
                return JsonResponse({
                    'ok': False,
                    'form_html': loader.render_to_string(f'{template_path}form.html', {'form': property_form}),
                })
        except Exception as ex:
            logger.exception('Error updating attachment (pk=%s, file_name=%s)', attach_id, attachment.file_name)
            return JsonResponse({'ok': False, 'error': force_str(ex)})
    raise Http404()


def edit_attachment_properties(request, attach_id):
    attachment = get_object_or_404(Attachment, pk=attach_id)
    if not user_has_access(request, attachment):
        raise Http404()
    return render(request, 'attachments/edit_properties.html', {
        'att': attachment,
        'form': PropertyForm(instance=attachment),
    })


def view_attachment_properties(request, attach_id):
    attachment = get_object_or_404(Attachment, pk=attach_id)
    if not user_has_access(request, attachment):
        raise Http404()
    return render(request,   f'{template_path}view_properties.html', {
        'att': attachment,
    })

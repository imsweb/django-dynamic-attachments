from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse, StreamingHttpResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.utils.encoding import force_text
from django.views.decorators.csrf import csrf_exempt

from .forms import PropertyForm
from .models import Attachment, Session, Upload
from .signals import file_download, file_uploaded, virus_detected
from .utils import get_storage, url_filename, user_has_access
from .exceptions import VirusFoundException, InvalidExtensionException, InvalidFileTypeException, FileSizeException

from datetime import datetime
from wsgiref.util import FileWrapper
import logging
import mimetypes
import os
import tempfile


logger = logging.getLogger(__name__)


@csrf_exempt
def attach(request, session_id):
    session = get_object_or_404(Session, uuid=session_id)
    session._request = request
    if request.method == 'POST':
        # Old versions of IE doing iframe uploads would present a Save dialog on JSON responses.
        content_type = 'text/plain' if request.POST.get('X-Requested-With', '') == 'IFrame' else 'application/json'
        try:
            f = request.FILES['attachment']
            max_lengh = Upload._meta.get_field('file_name').max_length
            if len(f.name) > max_lengh:
                raise ValidationError('An error occurred attaching file to the session. The filename cannot exceed {} characters.'.format(max_lengh))
            # Copy the Django attachment (which may be a file or in memory) over to a temp file.
            temp_dir = getattr(settings, 'ATTACHMENT_TEMP_DIR', None)
            if temp_dir is not None and not os.path.exists(temp_dir):
                if settings.FILE_UPLOAD_DIRECTORY_PERMISSIONS:
                    os.makedirs(temp_dir, mode=settings.FILE_UPLOAD_DIRECTORY_PERMISSIONS)
                else:
                    os.makedirs(temp_dir)
            fd, path = tempfile.mkstemp(dir=temp_dir)
            with os.fdopen(fd, 'wb') as fp:
                for chunk in f.chunks():
                    fp.write(chunk)

            # Set the desired permissions based on Django's FILE_UPLOAD_PERMISSIONS setting
            if settings.FILE_UPLOAD_PERMISSIONS:
                os.chmod(path, settings.FILE_UPLOAD_PERMISSIONS)

            upload = Upload(file_path=path, file_name=f.name, file_size=f.size, session=session)
            # Validate the upload before we move further
            # This will throw an error if the upload is invalid
            session.validate_upload(upload)
            upload.save()

            # Update the data for this session (includes all form data for the attachments)
            for key, value in request.POST.items():
                if session.data:
                    session.data.update({key: value})
                else:
                    session.data = {key: value}
            session.save()

            # Keeping the sender as 'f' for backwards compatibility
            file_uploaded.send(sender=f, request=request, session=session)
            return JsonResponse({'ok': True, 'file_name': upload.file_name, 'file_size': upload.file_size}, content_type=content_type)

        # These errors have helpful messages, so we return them
        except (InvalidExtensionException, InvalidFileTypeException, FileSizeException) as ex:
            return JsonResponse({'ok': False, 'error': force_text(ex)}, content_type=content_type)
        except VirusFoundException as ex:
            user = getattr(request, 'user', "Unknown user")
            filename = upload.file_name
            time_of_upload = datetime.now()
            #if ATTACHMENTS_QUARANTINE_PATH is set, move the offending file to the quarantine, otherwise delete
            attachments_quarantine_path = getattr(settings, 'ATTACHMENTS_QUARANTINE_PATH', None)
            if attachments_quarantine_path:
                quarantine_path = os.path.join(attachments_quarantine_path, os.path.basename(upload.file_path))
                os.rename(upload.file_path, quarantine_path)
                quarantine_msg = 'File has been quarantined here: {}'.format(quarantine_path)
            else:
                os.remove(upload.file_path)
                quarantine_path = None
                quarantine_msg = 'File has been removed from the system'

            error_msg = force_text(ex)
            log_message = "{} - Uploaded by {} at {}. {}.".format(error_msg,
                                                                  user,
                                                                  time_of_upload.strftime('%Y-%m-%d %H:%M:%S'), 
                                                                  quarantine_msg)
            logger.exception(log_message)

            virus_detected.send(sender=upload, 
                                user=user, 
                                filename=filename, 
                                exception=ex, 
                                time_of_upload=time_of_upload, 
                                quarantine_path=quarantine_path)
            return JsonResponse({'ok': False, 'error': force_text(ex)}, content_type=content_type)
        except ValidationError as ex:
            return JsonResponse({'ok': False, 'error': force_text(ex.message)}, content_type=content_type)
        except Exception as ex:
            logger.exception('Error attaching file to session {}'.format(session_id))
            # Since this is a catch all we need to return a generic error (in case a more sensitive error occurred)
            return JsonResponse({'ok': False, 'error': 'An error occurred attaching file to the session.'}, content_type=content_type)
    else:
        return render(request, session.template, {
            'session': session,
        })


@csrf_exempt
def delete_upload(request, session_id, upload_id):
    session = get_object_or_404(Session, uuid=session_id)
    upload = get_object_or_404(session.uploads, pk=upload_id)
    file_name = upload.file_name
    try:
        upload.delete()
        return JsonResponse({'ok': True})
    except Exception as ex:
        logger.exception('Error deleting upload (pk=%s, file_name=%s) from session %s', upload_id, file_name, session_id)
        return JsonResponse({'ok': False, 'error': force_text(ex)})


def download(request, attach_id, filename=None):
    attachment = get_object_or_404(Attachment, pk=attach_id)
    if not user_has_access(request, attachment):
        raise Http404()
    # Fire the download signal, in case receivers want to raise an Http404, or log downloads.
    file_download.send(sender=attachment, request=request)
    storage = get_storage()
    content_type = mimetypes.guess_type(attachment.file_name, strict=False)[0]
    if getattr(settings, 'ATTACHMENTS_USE_XSENDFILE', False):
        response = HttpResponse(FileWrapper(storage.open(attachment.file_path)), content_type=content_type)
        response['X-Sendfile'] = attachment.file_path
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


def update_attachment(request, attach_id):
    attachment = get_object_or_404(Attachment, pk=attach_id)
    if not user_has_access(request, attachment):
        raise Http404()
    if request.is_ajax() and request.method == 'POST':
        try:
            property_form = PropertyForm(request.POST, instance=attachment)
            if property_form.is_valid():
                attachment.data = attachment.extract_data(request)
                attachment.save()
                return JsonResponse({'ok': True})
            else:
                return JsonResponse({
                    'ok': False,
                    'form_html': loader.render_to_string('attachments/form.html', {'form': property_form}),
                })
        except Exception as ex:
            logger.exception('Error updating attachment (pk=%s, file_name=%s)', attach_id, attachment.file_name)
            return JsonResponse({'ok': False, 'error': force_text(ex)})
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
    return render(request, 'attachments/view_properties.html', {
        'att': attachment,
    })

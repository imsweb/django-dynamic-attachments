from django.conf import settings
from django.http import Http404, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.utils.encoding import force_text
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail


from attachments.exceptions import VirusFoundException

from .forms import PropertyForm
from .models import Attachment, Session
from .signals import file_download, file_uploaded
from .utils import get_storage, url_filename, user_has_access, sizeof_fmt
from .exceptions import VirusFoundException, FileSizeException, FileTypeException

from wsgiref.util import FileWrapper
import logging
import mimetypes
import os
import tempfile
import datetime
from django.conf.global_settings import DEFAULT_FROM_EMAIL



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
            max_file_size = getattr(settings, 'ATTACHMENTS_MAXIMUM_FILE_SIZE', False)
            if max_file_size and f.size > max_file_size:
                raise FileSizeException("File is too large to be uploaded, file cannot be greater than %s" % sizeof_fmt(max_file_size))
            allowed_file_types = getattr(settings, 'ATTACHMENTS_ALLOWED_FILE_TYPES', False)
            if allowed_file_types and f.content_type not in allowed_file_types and f.content_type.split('/') not in allowed_file_types:
                raise FileTypeException("You cannot upload this file type")
            # Copy the Django attachment (which may be a file or in memory) over to a temp file.
            temp_dir = getattr(settings, 'ATTACHMENT_TEMP_DIR', None)
            if temp_dir is not None and not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            fd, path = tempfile.mkstemp(dir=temp_dir)
            with os.fdopen(fd, 'wb') as fp:
                for chunk in f.chunks():
                    fp.write(chunk)
            # After attached file is placed in a temporary file and ATTACHMENTS_CLAMD is active scan it for viruses:
            if getattr(settings, 'ATTACHMENTS_CLAMD', False):
                import pyclamd
                cd = pyclamd.ClamdUnixSocket()
                virus = cd.scan_file(path)
                if virus is not None:
                    #if ATTACHMENTS_QUARANTINE_PATH is set, move the offending file to the quarantine, otherwise delete
                    if getattr(settings, 'ATTACHMENTS_QUARANTINE_PATH', False):
                        quarantine_path = os.path.join(getattr(settings, 'ATTACHMENTS_QUARANTINE_PATH'), os.path.basename(path))
                        os.rename(path, quarantine_path)
                    else:
                        os.remove(path)
                    raise VirusFoundException('**WARNING** virus %s found in the file %s, could not upload!' % (virus[path][1], f.name))
            session.uploads.create(file_path=path, file_name=f.name, file_size=f.size)
            for key, value in request.POST.items():
                if session.data:
                    session.data.update({key: value})
                else:
                    session.data = {key: value}
            session.save()
            return JsonResponse({'ok': True, 'file_name': f.name, 'file_size': f.size}, content_type=content_type)
        except FileSizeException, ex:
            return JsonResponse({'ok': False, 'error': unicode(ex)}, content_type=content_type)
        except FileTypeException, ex:
            return JsonResponse({'ok': False, 'error': unicode(ex)}, content_type=content_type)
        except VirusFoundException as ex:
            user = getattr(request, 'user', None)
            log_message = loader.render_to_string('attachments/virus_email.txt', 
                                                  {'user': user,
                                                   'filename' : f.name,
                                                   'virus_signature' : virus[path][1],
                                                   })
            logger.exception(log_message)
            #if ATTACHMENTS_VIRUS_EMAIL is set to a list/tuple of email addresses to send to it will send email alert
            if getattr(settings, 'ATTACHMENTS_VIRUS_EMAIL', False):
                #send email to email list
                email_list = getattr(settings, 'ATTACHMENTS_VIRUS_EMAIL')
                subject = loader.render_to_string('attachments/virus_subject.txt', {'user': user })
                send_mail(subject, log_message, settings.DEFAULT_FROM_EMAIL, email_list)
        except Exception as ex:
            logger.exception('Error attaching file to session %s', session_id)
            return JsonResponse({'ok': False, 'error': force_text(ex)}, content_type=content_type)
    else:
        file_uploaded.send(sender=f, request=request, session=session)
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

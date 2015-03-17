from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, StreamingHttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from .models import Session, Attachment
from .forms import PropertyForm
from .utils import get_storage, url_filename
from .signals import file_uploaded
from wsgiref.util import FileWrapper
import mimetypes
import tempfile
import logging
import os

logger = logging.getLogger(__name__)

@csrf_exempt
def attach(request, session_id):
    session = Session.objects.get(uuid=session_id)
    if request.method == 'POST':
        try:
            f = request.FILES['attachment']
            file_uploaded.send(sender=f)
            # Copy the Django attachment (which may be a file or in memory) over to a temp file.
            fd, path = tempfile.mkstemp()
            with os.fdopen(fd, 'wb') as fp:
                for chunk in f.chunks():
                    fp.write(chunk)
            session.uploads.create(file_path=path, file_name=f.name, file_size=f.size)
            return JsonResponse({'ok': True, 'file_name': f.name, 'file_size': f.size})
        except Exception, ex:
            logger.exception('Error attaching file to session %s', session_id)
            return JsonResponse({'ok': False, 'error': unicode(ex)})
    else:
        try:
            app_label, model = request.GET['contentType'].split('.', 1)
            content_type = ContentType.objects.get(app_label=app_label, model=model)
        except:
            content_type = None
        return render(request, session.template, {
            'session': session,
            'content_type': content_type,
        })

@csrf_exempt
def delete_upload(request, session_id, upload_id):
    session = Session.objects.get(uuid=session_id)
    upload = get_object_or_404(session.uploads, pk=upload_id)
    file_name = upload.file_name
    try:
        upload.delete()
        return JsonResponse({'ok': True})
    except Exception, ex:
        logger.exception('Error deleting upload (pk=%s, file_name=%s) from session %s', upload_id, file_name, session_id)
        return JsonResponse({'ok': False, 'error': unicode(ex)})

# TODO: permission checking
def download(request, attach_id, filename=None):
    attachment = get_object_or_404(Attachment, pk=attach_id)
    storage = get_storage()
    content_type = mimetypes.guess_type(attachment.file_name, strict=False)[0]
    response = StreamingHttpResponse(FileWrapper(storage.open(attachment.file_path)), content_type=content_type)
    try:
        # Not all storage backends support getting filesize.
        response['Content-Length'] = storage.size(attachment.file_path)
    except:
        pass
    if filename is None:
        filename = url_filename(attachment.file_name)
        response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response

def update_attachment(request, attach_id):
    attachment = get_object_or_404(Attachment, pk=attach_id)
    if request.is_ajax() and request.method == 'POST':
        try:
            property_form = PropertyForm(request.POST, instance=attachment)
            if property_form.is_valid():
                attachment.data = attachment.extract_data(request)
                attachment.save()
                return JsonResponse({'ok': True})
            else:
                raise Exception('Error updating attachment properties.')
        except Exception, ex:
            logger.exception('Error updating attachment (pk=%s, file_name=%s)', attach_id, attachment.file_name)
            return JsonResponse({'ok': False, 'error': unicode(ex)})
    raise Http404()

def show_attachment_properties(request, attach_id):
    attachment = get_object_or_404(Attachment, pk=attach_id)
    return render(request, 'attachments/properties.html', {
        'att': attachment,
    })

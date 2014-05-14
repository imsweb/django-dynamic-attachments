from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render, get_object_or_404
from .models import Session, Attachment
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
        return render(request, session.template, {
            'session': session,
        })

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

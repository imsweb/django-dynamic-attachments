from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import get_storage_class
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.db import models
import json
import urllib
import uuid
import importlib


def get_context_key(context):
    if context:
        return 'attachments-%s' % context
    return 'attachments'

def session(request, template='attachments/list.html', context='', user=None, content_type=None, allowed_file_types=None):
    from .models import Session
    try:
        key = get_context_key(context)
        s = Session.objects.get(uuid=request.POST[key])
        s._request = request
        return s
    except:
        if user is None:
            user = request.user if hasattr(request, 'user') and request.user and request.user.is_authenticated else None
        if content_type and not isinstance(content_type, ContentType):
            content_type = ContentType.objects.get_for_model(content_type)
        if allowed_file_types is None:
            allowed_file_types = getattr(settings, 'ATTACHMENTS_ALLOWED_FILE_TYPES', '')
        for _i in range(5):
            try:
                s = Session.objects.create(user=user, uuid=uuid.uuid4().hex, template=template, context=context, content_type=content_type, allowed_file_types=allowed_file_types)
                s._request = request
                return s
            except:
                pass
        raise Exception('Could not create a unique attachment session')

def get_storage():
    cls, kwargs = getattr(settings, 'ATTACHMENT_STORAGE', (settings.DEFAULT_FILE_STORAGE, {}))
    return get_storage_class(cls)(**kwargs)

def get_default_path(upload, obj):
    ct = ContentType.objects.get_for_model(obj)
    return '%s/%s/%s/%s/%s' % (ct.app_label, ct.model, obj.pk, upload.session.context, upload.file_name)

def url_filename(filename):
    # If the filename is not US-ASCII, we need to urlencode it.
    try:
        return filename.encode('us-ascii')
    except:
        return urllib.quote(filename.encode('utf-8'), safe='/ ')

def user_has_access(request, attachment):
    # Check to see if this attachments model instance has a can_download, otherwise fall back
    # to checking request.user.is_authenticated by default.
    obj = attachment.content_object
    auth = request.user.is_authenticated
    if hasattr(obj, 'can_download'):
        auth = obj.can_download(request, attachment)
        if isinstance(auth, HttpResponse):
            return auth
    return auth

class JSONField (models.TextField):

    def to_python(self, value):
        if value == '':
            return None
        if isinstance(value, basestring):
            return json.loads(value)
        return value

    def from_db_value(self, value, expression, connection, context):
        return None if value is None else self.to_python(value)

    def get_prep_value(self, value):
        if value == '':
            return None
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value, cls=DjangoJSONEncoder)
        return super(JSONField, self).get_prep_value(value)

    def value_to_string(self, obj):
        return self.get_prep_value(self._get_val_from_obj(obj))

#    def deconstruct(self):
#        name, _mod, args, kwargs = super(JSONField, self).deconstruct()
#        return name, 'attachments.utils.JSONField', args, kwargs

def import_class(fq_name):
    module_name, class_name = fq_name.rsplit('.', 1)
    mod = importlib.import_module(module_name)
    return getattr(mod, class_name)

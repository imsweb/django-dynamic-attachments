from django.urls import re_path

from . import views


urlpatterns = [
    re_path(r'^download/(?P<attach_id>[^/]+)/(?P<filename>.*)$', views.download, name='attachment-download'),
    re_path(r'^(?P<session_id>[^/]+)/$', views.attach, name='attach'),
    re_path(r'^delete/upload/(?P<session_id>[^/]+)/(?P<upload_id>[^/]+)/$', views.delete_upload, name='delete-upload'),
    re_path(r'^update/(?P<attach_id>[^/]+)/$', views.update_attachment, name='update-attachment'),
    re_path(r'^properties/edit/(?P<attach_id>[^/]+)/$', views.edit_attachment_properties, name='edit-attachment-properties'),
    re_path(r'^properties/view/(?P<attach_id>[^/]+)/$', views.view_attachment_properties, name='view-attachment-properties')
]

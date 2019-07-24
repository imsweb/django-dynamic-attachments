from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^download/(?P<attach_id>[^/]+)/(?P<filename>.*)$', views.download, name='attachment-download'),
    url(r'^(?P<session_id>[^/]+)/$', views.attach, name='attach'),
    url(r'^delete/upload/(?P<session_id>[^/]+)/(?P<upload_id>[^/]+)/$', views.delete_upload, name='delete-upload'),
    url(r'^update/(?P<attach_id>[^/]+)/$', views.update_attachment, name='update-attachment'),
    url(r'^properties/edit/(?P<attach_id>[^/]+)/$', views.edit_attachment_properties, name='edit-attachment-properties'),
    url(r'^properties/view/(?P<attach_id>[^/]+)/$', views.view_attachment_properties, name='view-attachment-properties')
]

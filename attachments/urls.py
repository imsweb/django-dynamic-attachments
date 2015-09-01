from django.conf.urls import patterns, url

urlpatterns = patterns('attachments.views',
    url(r'^download/(?P<attach_id>[^/]+)/(?P<filename>.*)$', 'download', name='attachment-download'),
    url(r'^(?P<session_id>[^/]+)/$', 'attach', name='attach'),
    url(r'^delete/upload/(?P<session_id>[^/]+)/(?P<upload_id>[^/]+)/$', 'delete_upload', name='delete-upload'),
    url(r'^update/(?P<attach_id>[^/]+)/$', 'update_attachment', name='update-attachment'),
    url(r'^properties/(?P<attach_id>[^/]+)/$', 'show_attachment_properties', name='show-attachment-properties'),
)

from django.conf.urls import patterns, url

urlpatterns = patterns('attachments.views',
    url(r'^download/(?P<attach_id>[^/]+)/(?P<filename>.*)$', 'download', name='attachment-download'),
    url(r'^(?P<session_id>[^/]+)/$', 'attach', name='attach'),
)

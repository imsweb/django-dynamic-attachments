from django.conf.urls import include, url


urlpatterns = [
    url(r'attachments/', include('attachments.urls')),
]

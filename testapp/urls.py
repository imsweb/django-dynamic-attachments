from django.urls import include, path


urlpatterns = [
    path(r'attachments/', include('attachments.urls')),
]

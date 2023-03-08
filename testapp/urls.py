from django.urls import include, re_path


urlpatterns = [
    re_path(r'attachments/', include('attachments.urls')),
]

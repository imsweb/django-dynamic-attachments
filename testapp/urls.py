from django.urls import include, path


urlpatterns = [
    path('attachments/', include('attachments.urls')),
]

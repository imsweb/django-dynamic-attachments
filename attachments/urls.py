from django.urls import path, re_path

from . import views


urlpatterns = [
    re_path(r'^download/(?P<attach_id>\d+)/(?P<filename>.*)$', views.download, name='attachment-download'),
    path('<str:session_id>/', views.attach, name='attach'),
    path('delete/upload/<str:session_id>/<int:upload_id>/', views.delete_upload, name='delete-upload'),
    path('update/<int:attach_id>/', views.update_attachment, name='update-attachment'),
    path('properties/edit/<int:attach_id>/', views.edit_attachment_properties, name='edit-attachment-properties'),
    path('properties/view/<int:attach_id>/', views.view_attachment_properties, name='view-attachment-properties')
]

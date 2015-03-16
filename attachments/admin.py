from django.contrib import admin
from .models import Attachment, Property, Session, Upload

class AttachmentAdmin (admin.ModelAdmin):
    list_display = ('file_path', 'file_name', 'file_size', 'date_created')
    readonly_fields = ('data',)
    
class PropertyAdmin (admin.ModelAdmin):
    pass

class UploadInline (admin.TabularInline):
    model = Upload

class SessionAdmin (admin.ModelAdmin):
    list_display = ('uuid', 'user', 'template', 'context', 'date_created')
    inlines = (UploadInline,)

admin.site.register(Attachment, AttachmentAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(Property, PropertyAdmin)

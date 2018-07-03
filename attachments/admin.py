from django import forms
from django.contrib import admin

from .models import Attachment, Property, Session, Upload
from .utils import import_class


class AttachmentAdmin (admin.ModelAdmin):
    list_display = ('file_path', 'file_name', 'file_size', 'content_type', 'context', 'date_created')
    readonly_fields = ('data',)


class PropertyForm (forms.ModelForm):

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model:
            try:
                import_class(model)
            except ImportError:
                raise forms.ValidationError("Improper path to lookup model.")
        return self.cleaned_data['model']


class PropertyAdmin (admin.ModelAdmin):
    form = PropertyForm
    list_display = ('label', 'slug', 'data_type', 'choices', 'model', 'required')
    prepopulated_fields = {'slug': ('label',)}
    filter_horizontal = ('content_type',)


class UploadInline (admin.TabularInline):
    model = Upload
    extra = 0


class SessionAdmin (admin.ModelAdmin):
    list_display = ('uuid', 'user', 'template', 'context', 'date_created')
    inlines = (UploadInline,)


admin.site.register(Attachment, AttachmentAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(Property, PropertyAdmin)

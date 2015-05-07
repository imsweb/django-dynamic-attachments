from django import forms
from bootstrap import widgets
from .models import Property, Upload, Attachment

PROPERTY_FIELD_CLASSES = {
    'date': forms.DateField,
    'boolean': forms.NullBooleanField,
    'integer': forms.IntegerField,
    'decimal': forms.DecimalField,
    'email': forms.EmailField,
}

PROPERTY_WIDGET_CLASSES = {
    'text': widgets.Textarea,
    'date': widgets.DateInput,
    'radio': forms.RadioSelect,
    'boolean': forms.CheckboxInput,
}

class PropertyForm (forms.Form):

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance')
        content_type = kwargs.pop('content_type', None)
        if isinstance(instance, Attachment) and not content_type:
            content_type = instance.content_type

        super(PropertyForm, self).__init__(*args, **kwargs)

        for prop in Property.objects.filter(content_type=content_type):
            if isinstance(instance, Upload):
                self.fields["upload-%s-%s" % (instance.pk, prop.slug)] = self.formfield(prop)
            elif isinstance(instance, Attachment):
                self.fields["attachment-%s-%s" % (instance.pk, prop.slug)] = self.formfield(prop)
                self.fields["attachment-%s-%s" % (instance.pk, prop.slug)].initial = ','.join(instance.data.get(prop.slug, []))

    def formfield(self, prop, field_class=None, **kwargs):
        if field_class is None:
            field_class = PROPERTY_FIELD_CLASSES.get(prop.data_type, forms.CharField)
        defaults = {
            'label': prop.label,
            'widget': PROPERTY_WIDGET_CLASSES.get(prop.data_type, widgets.TextInput),
        }
        if prop.data_type == 'date':
            # TODO: add a property for date display format?
            defaults['widget'] = defaults['widget'](format='%m/%d/%Y')
        defaults.update(kwargs)
        field = field_class(**defaults)
        return field

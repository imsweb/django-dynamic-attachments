from django import forms

from django.db.models import Q
from .models import Attachment, Property, Upload


PROPERTY_FIELD_CLASSES = {
    'date': forms.DateField,
    'boolean': forms.NullBooleanField,
    'integer': forms.IntegerField,
    'decimal': forms.DecimalField,
    'email': forms.EmailField,
    'choice': forms.ChoiceField,
    'model': forms.ModelChoiceField
}

PROPERTY_WIDGET_CLASSES = {
    'text': forms.Textarea,
    'date': forms.DateInput,
    'choice': forms.Select,
    'model': forms.Select,
    'radio': forms.RadioSelect,
    'boolean': forms.CheckboxInput,
}

DEFAULT_FORM_CLASS = forms.CharField
DEFAULT_WIDGET_CLASS = forms.TextInput

try:
    # XXX: get rid of this
    from bootstrap import widgets
    PROPERTY_WIDGET_CLASSES['text'] = widgets.Textarea
    PROPERTY_WIDGET_CLASSES['date'] = widgets.DateInput
    DEFAULT_WIDGET_CLASS = widgets.TextInput
except ImportError:
    pass


class PropertyForm (forms.Form):

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance')
        editable_only = kwargs.pop('editable_only', True)

        content_type = None
        if isinstance(instance, Attachment):
            content_type = instance.content_type
        elif isinstance(instance, Upload):
            content_type = instance.session.content_type

        super(PropertyForm, self).__init__(*args, **kwargs)

        query = Q(content_type=content_type)
        if editable_only:
            query = Q(query, is_editable=True)

        for prop in Property.objects.filter(query):
            if isinstance(instance, Upload):
                field_key = 'upload-%d-%s' % (instance.pk, prop.slug)
                self.fields[field_key] = self.formfield(prop,
                                                        initial=instance.session.data.get(field_key, None) if instance.session.data else None)
            elif isinstance(instance, Attachment):
                field_key = 'attachment-%d-%s' % (instance.pk, prop.slug)
                self.fields[field_key] = self.formfield(prop, initial=','.join(instance.data.get(prop.slug, []) if instance.data else []))

    def formfield(self, prop, field_class=None, **kwargs):
        if field_class is None:
            field_class = PROPERTY_FIELD_CLASSES.get(prop.data_type, DEFAULT_FORM_CLASS)
        defaults = {
            'label': prop.label,
            'required': prop.required,
            'widget': PROPERTY_WIDGET_CLASSES.get(prop.data_type, DEFAULT_WIDGET_CLASS),
        }
        if prop.data_type == 'date':
            # TODO: add a property for date display format?
            defaults['widget'] = defaults['widget'](format='%m/%d/%Y')
        elif prop.data_type == 'choice':
            choices = [(ch, ch) for ch in prop.choice_list]
            defaults['choices'] = choices
        elif prop.data_type == 'model':
            defaults['queryset'] = prop.model_queryset
            if defaults.get('required', False):
                defaults['empty_label'] = None
        elif prop.data_type == 'boolean':
            kwargs['initial'] = kwargs.get('initial', False) in (True, 'true')
        defaults.update(kwargs)
        field = field_class(**defaults)
        return field

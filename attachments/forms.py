from .models import Property, Upload, Attachment
from bootstrap import widgets
from django import forms

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
    'text': widgets.Textarea,
    'date': widgets.DateInput,
    'choice': forms.Select,
    'model': forms.Select,
    'radio': forms.RadioSelect,
    'boolean': forms.CheckboxInput,
}

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

        qs = Property.objects.filter(content_type=content_type)
        if editable_only:
            qs = qs.filter(is_editable=True)

        for prop in qs:
            if isinstance(instance, Upload):
                field_key = 'upload-%d-%s' % (instance.pk, prop.slug)
                self.fields[field_key] = self.formfield(prop, 
                                                        initial=instance.session.data.get(field_key, None) if instance.session.data else None)
            elif isinstance(instance, Attachment):
                field_key = 'attachment-%d-%s' % (instance.pk, prop.slug)
                self.fields[field_key] = self.formfield(prop, initial=','.join(instance.data.get(prop.slug, []) if instance.data else []))

    def formfield(self, prop, field_class=None, **kwargs):
        if field_class is None:
            field_class = PROPERTY_FIELD_CLASSES.get(prop.data_type, forms.CharField)
        defaults = {
            'label': prop.label,
            'required': prop.required,
            'widget': PROPERTY_WIDGET_CLASSES.get(prop.data_type, widgets.TextInput),
        }

        # If initial values were deserialized from Session.data, they will be
        # lists containing only one item, which is the value we want in the field.
        # This will need to be updated if widgets that can support multiple selections
        # are added.
        initial_value = kwargs.get('initial')
        if isinstance(initial_value, (list, tuple)) and len(initial_value) > 0:
            kwargs['initial'] = initial_value[0]

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
            kwargs['initial'] = kwargs.get('initial', False) in (True, 'true', 'on')
        defaults.update(kwargs)
        field = field_class(**defaults)
        return field

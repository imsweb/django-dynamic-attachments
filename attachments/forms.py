from django import forms

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

        qs = Property.objects.filter(content_type=content_type)
        if editable_only:
            qs = qs.filter(is_editable=True)

        is_upload = isinstance(instance, Upload)
        is_attachment = isinstance(instance, Attachment)
        form_data = kwargs.pop('data', self.get_form_data_from_session_data(instance.session.data) if is_upload else {}) 
        for prop in qs:
            if is_upload:
                field_key = 'upload-%d-%s' % (instance.pk, prop.slug)
                initial_data = form_data.get(field_key, None) if form_data else None
                self.fields[field_key] = self.formfield(prop, initial=initial_data, data=form_data, **kwargs)
            elif is_attachment:
                field_key = 'attachment-%d-%s' % (instance.pk, prop.slug)
                self.fields[field_key] = self.formfield(prop, initial=','.join(instance.data.get(prop.slug, []) if instance.data else []))

    def formfield(self, prop, field_class=None, data=None, **kwargs):
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
            defaults['queryset'] = prop.model_queryset(data=data)
            if defaults.get('required', False):
                defaults['empty_label'] = None
        elif prop.data_type == 'boolean':
            kwargs['initial'] = kwargs.get('initial', False) in (True, 'true', 'on')
        defaults.update(kwargs)
        field = field_class(**defaults)
        return field
    
    @staticmethod
    def get_form_data_from_session_data(session_data):
        """
        This handles converting session.data to a data object that the property form can use for initialization.
        Deserialized session data will be lists containing only one item, which is the value we want in the field.
        Note: This will need to be updated if widgets that can support multiple selections are added.
        """
        form_data = {}
        if session_data is not None:
            for key, val in session_data.items():
                if isinstance(val, (list, tuple)) and len(val) > 0:
                    form_val = val[0]
                else:
                    form_val = val
                form_data[key] = form_val
        return form_data 

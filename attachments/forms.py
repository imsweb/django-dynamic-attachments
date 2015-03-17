from django import forms
from bootstrap import widgets
from .models import Property, Upload, Attachment

PROPERTY_FIELD_CLASSES = {
    'date': forms.DateField,
    'lookup': forms.ChoiceField,
    'radio': forms.ChoiceField,
    'multi': forms.MultipleChoiceField,
    'multilist': forms.MultipleChoiceField,
    'boolean': forms.NullBooleanField,
    'integer': forms.IntegerField,
    'decimal': forms.DecimalField,
    'email': forms.EmailField,
}

PROPERTY_WIDGET_CLASSES = {
    'text': widgets.Textarea,
    'date': widgets.DateInput,
    'lookup': widgets.Select,
    'radio': forms.RadioSelect,
    'multi': forms.CheckboxSelectMultiple,
    'multilist': widgets.SelectMultiple,
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
        elif prop.data_type in ('lookup', 'radio', 'multi', 'multilist'):
            choices = [(ch, ch) for ch in prop.choice_list]
            if prop.data_type == 'lookup':
                choices.insert(0, ('', ''))
            elif prop.data_type == 'multilist':
                # TODO: add a property for size?
                defaults['widget'] = defaults['widget'](attrs={'size':min(len(choices) + 1, 10)})
            defaults['choices'] = choices
        defaults.update(kwargs)
        field = field_class(**defaults)
        return field

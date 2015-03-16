from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
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
    
    class Meta:
        fields = ()

    def __init__(self, *args, **kwargs):
        self.content_type = kwargs.pop('content_type')
        self.att_instance =  kwargs.pop('att_instance')
       
        properties = Property.objects.filter(content_type__model=self.content_type)
        super(PropertyForm, self).__init__(*args, **kwargs)
        
        for property in properties:
            if isinstance(self.att_instance, Upload):
                self.fields["upload-%s-%s" % (self.att_instance.pk, property.slug)] = self.formfield(property)
            elif isinstance(self.att_instance, Attachment):
                self.fields["attachment-%s-%s" % (self.att_instance.pk, property.slug)] = self.formfield(property)
                self.fields["attachment-%s-%s" % (self.att_instance.pk, property.slug)].initial = ','.join(self.att_instance.data.get(property.slug, []))
    
    def formfield(self, property, field_class=None, **kwargs):
        if field_class is None:
            field_class = PROPERTY_FIELD_CLASSES.get(property.data_type, forms.CharField)
        defaults = {
            'label': property.label,
            'widget': PROPERTY_WIDGET_CLASSES.get(property.data_type, widgets.TextInput),
        }
        if property.data_type == 'date':
            # TODO: add a property for date display format?
            defaults['widget'] = defaults['widget'](format='%m/%d/%Y')
        elif property.data_type in ('lookup', 'radio', 'multi', 'multilist'):
            choices = [(ch, ch) for ch in property.choice_list]
            if property.data_type == 'lookup':
                choices.insert(0, ('', ''))
            elif property.data_type == 'multilist':
                # TODO: add a property for size?
                defaults['widget'] = defaults['widget'](attrs={'size':min(len(choices) + 1, 10)})
            defaults['choices'] = choices
        defaults.update(kwargs)
        field = field_class(**defaults)
        return field
    
    
    
    
    
from django import template
from django.contrib.contenttypes.models import ContentType
from ..forms import PropertyForm
from ..models import Property

register = template.Library()

@register.filter
def get_attachment_properties_form(content_type, att_instance):
    kwargs = {'content_type': content_type, 'att_instance': att_instance}
    property_form = PropertyForm(**kwargs)
            
    return property_form


@register.filter
def get_content_type(obj):
    return ContentType.objects.get_for_model(obj)

@register.filter
def has_attachment_properties(content_type):
    properties = Property.objects.filter(content_type__model=content_type)
            
    return True if properties else False
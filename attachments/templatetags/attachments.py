from django import template
from django.contrib.contenttypes.models import ContentType
from ..forms import PropertyForm
from ..models import Property

register = template.Library()

@register.filter
def has_attachment_properties(obj):
    ct = ContentType.objects.get_for_model(obj)
    return Property.objects.filter(content_type=ct).exists()

@register.filter
def attachment_properties_form(obj, content_type=None):
    return PropertyForm(instance=obj, content_type=content_type)

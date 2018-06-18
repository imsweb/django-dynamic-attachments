from django import template
from django.contrib.contenttypes.models import ContentType

from ..forms import PropertyForm
from ..models import Property


register = template.Library()


@register.filter
def has_attachment_properties(content_type):
    if not isinstance(content_type, ContentType):
        content_type = ContentType.objects.get_for_model(content_type)
    return Property.objects.filter(content_type=content_type).exists()


@register.filter
def attachment_properties_form(obj, content_type=None):
    return PropertyForm(instance=obj, content_type=content_type)

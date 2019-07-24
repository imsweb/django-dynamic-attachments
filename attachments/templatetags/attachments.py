from django import template
from django.contrib.contenttypes.models import ContentType

from ..forms import PropertyForm
from ..models import Property


register = template.Library()


@register.filter
def has_attachment_properties(content_type, editable_only=False):
    if not isinstance(content_type, ContentType):
        content_type = ContentType.objects.get_for_model(content_type)
    qs = Property.objects.filter(content_type=content_type)
    if editable_only:
        qs = qs.filter(is_editable=True)
    return qs.exists()


@register.filter
def attachment_properties_form(obj, editable_only=True):
    return PropertyForm(instance=obj, editable_only=editable_only)

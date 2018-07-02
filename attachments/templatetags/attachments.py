from django import template
from django.conf import settings
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
def has_edditable_attachment_properties(content_type, excluded_slugs=""):
    if not isinstance(content_type, ContentType):
        content_type = ContentType.objects.get_for_model(content_type)
    excluded_slugs = excluded_slugs.split(",") if excluded_slugs else getattr(settings, "ATTACHMENTS_EDIT_EXCLUDE_PROPERTY_SLUGS", [])
    return Property.objects.exclude(slug__in=excluded_slugs).filter(content_type=content_type).exists()


@register.filter
def attachment_properties_form(obj):
    return PropertyForm(instance=obj)


@register.simple_tag
def attachment_properties_form(obj, excluded_slugs=""):
    excluded_slugs = excluded_slugs.split(",") if excluded_slugs else getattr(settings, "ATTACHMENTS_EDIT_EXCLUDE_PROPERTY_SLUGS", [])
    return PropertyForm(instance=obj, excluded_slugs=excluded_slugs)

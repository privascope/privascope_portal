from django import template
from django.conf import settings
import markdown2

register = template.Library()

@register.filter
def markdown(text):
    return markdown2.markdown(text, extras=settings.MARKDOWN_EXTRAS)

from django import template

register = template.Library()

def key(d, key_name):
    try:
        value = d[key_name]
    except:
        from django.conf import settings

        value = settings.TEMPLATE_STRING_IF_INVALID

    return value

register.filter('key', key)
from django import template


register = template.Library()


@register.filter
def getattr(obj, attr_name):
    """Return attribute value or call if callable"""
    try:
        val = getattr(obj, attr_name)
    except Exception:
        return ''
    if callable(val):
        try:
            return val()
        except Exception:
            return val
    return val

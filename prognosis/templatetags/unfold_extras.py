from django import template


register = template.Library()


@register.filter
def getattr(obj, attr_name, default=''):
	if obj is None:
		return default
	try:
		val = getattr(obj, attr_name)
	except Exception:
		return default

	if callable(val):
		try:
			return val()
		except Exception:
			return default
	return val

from .models import Company
from rest_framework import permissions


class IsInCompany(permissions.BasePermission):
	"""
	Разрешает доступ только если пользователь привязан к компании объекта.
	"""
	def has_object_permission(self, request, view, obj):
		# obj должен иметь поле company или быть связан с Company
		if hasattr(obj, "company"):
			company = obj.company
		elif hasattr(obj, "company_id"):
			company = Company.active.get(id=obj.company_id)
		else:
			return False

		# use resolved company (works for both object and company_id cases)
		return company.user_roles.filter(user=request.user).exists()

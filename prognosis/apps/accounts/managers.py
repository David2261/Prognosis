from django.db import models


class ActiveCompanyManager(models.Manager):
	def get_queryset(self):
		return super().get_queryset().filter(is_active=True)

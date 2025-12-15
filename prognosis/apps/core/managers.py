from django.db import models


class ActiveScenarioManager(models.Manager):
	def get_queryset(self):
		return super().get_queryset().filter(is_active=True)


class OpenPeriodManager(models.Manager):
	def get_queryset(self):
		return super().get_queryset().filter(is_closed=False)

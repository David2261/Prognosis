from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from core.models import CompanyRelatedModel

User = get_user_model()


class ImportTask(CompanyRelatedModel):
	"""
	Задача импорта — одна на файл
	"""
	STATUS_CHOICES = [
		("pending", _("Ожидает")),
		("processing", _("Обработка")),
		("completed", _("Завершено")),
		("failed", _("Ошибка")),
	]

	slug = models.SlugField(max_length=255, blank=True)
	file = models.FileField(_("Файл"), upload_to="imports/%Y/%m/%d/")
	file_type = models.CharField(
		_("Тип файла"),
		max_length=10,
		choices=[("excel", "Excel"), ("csv", "CSV")])
	status = models.CharField(
		_("Статус"),
		max_length=20,
		choices=STATUS_CHOICES,
		default="pending")
	scenario = models.ForeignKey(
		"core.Scenario",
		on_delete=models.PROTECT,
		verbose_name=_("Сценарий"))
	rows_total = models.PositiveIntegerField(_("Всего строк"), default=0)
	rows_processed = models.PositiveIntegerField(_("Обработано"), default=0)
	rows_success = models.PositiveIntegerField(_("Успешно"), default=0)
	rows_failed = models.PositiveIntegerField(_("Ошибок"), default=0)
	error_log = models.TextField(_("Лог ошибок"), blank=True)
	started_at = models.DateTimeField(_("Начало"), null=True, blank=True)
	finished_at = models.DateTimeField(_("Завершение"), null=True, blank=True)
	created_by = models.ForeignKey(
		User,
		on_delete=models.SET_NULL,
		null=True,
		verbose_name=_("Создал"))

	class Meta:
		verbose_name = _("Задача импорта")
		verbose_name_plural = _("Задачи импорта")
		ordering = ["-created_at"]
		unique_together = ("company", "slug")
		indexes = [
			models.Index(fields=["company", "slug"]),
		]

	def __str__(self):
		return f"Импорт {self.file.name} — {self.get_status_display()}"

	def _generate_unique_slug(self):
		from django.utils.text import slugify
		base_name = self.file.name if self.file else "import"
		base = slugify(base_name.rsplit('/', 1)[-1]) or "import"
		slug = base
		count = 1
		while ImportTask.objects.filter(
			company=self.company,
			slug=slug
		).exclude(pk=getattr(self, 'pk', None)).exists():
			slug = f"{base}-{count}"
			count += 1
		return slug

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = self._generate_unique_slug()
		super().save(*args, **kwargs)

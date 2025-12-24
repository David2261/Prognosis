from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from core.models import CompanyRelatedModel
from core.models import Scenario, TimePeriod


class ReportTemplate(CompanyRelatedModel):
	"""
	Шаблон отчёта (P&L, Cash Flow, Balance и т.д.)
	"""
	name = models.CharField(_("Название"), max_length=255)
	slug = models.SlugField(
		_("Slug"),
		max_length=120,
		unique=False,
		allow_unicode=True,
		blank=True
	)
	code = models.CharField(_("Код шаблона"), max_length=50, unique=True)
	description = models.TextField(_("Описание"), blank=True)
	report_type = models.CharField(
		_("Тип отчёта"),
		max_length=50,
		choices=[
			("pnl", _("P&L / Отчёт о прибылях и убытках")),
			("balance", _("Баланс")),
			("cashflow", _("Cash Flow")),
			("plan_fact", _("План-Факт анализ")),
			("custom", _("Пользовательский")),
		]
	)
	config = models.JSONField(_("Конфигурация"), default=dict)
	is_public = models.BooleanField(_("Публичный"), default=False)
	created_by = models.ForeignKey(
		"authentication.User",
		null=True,
		on_delete=models.SET_NULL)

	class Meta:
		verbose_name = _("Шаблон отчёта")
		verbose_name_plural = _("Шаблоны отчётов")
		unique_together = ("company", "code")

	def save(self, *args, **kwargs):
		if not self.slug:
			base_slug = slugify(self.name, allow_unicode=True)
			self.slug = base_slug
			# Простейший способ избежать коллизий (можно улучшить)
			counter = 1
			while ReportTemplate.objects.filter(
				company=self.company, slug=self.slug
			).exclude(pk=self.pk).exists():
				self.slug = f"{base_slug}-{counter}"
				counter += 1
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.name} ({self.get_report_type_display()})"


class GeneratedReport(CompanyRelatedModel):
	"""
	Сгенерированный отчёт (один экземпляр)
	"""
	template = models.ForeignKey(ReportTemplate, on_delete=models.PROTECT)
	name = models.CharField(_("Название отчёта"), max_length=255)
	scenario = models.ForeignKey(
		Scenario,
		on_delete=models.PROTECT,
		null=True,
		blank=True)
	start_period = models.ForeignKey(
		TimePeriod,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="report_starts")
	end_period = models.ForeignKey(
		TimePeriod,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="report_ends")
	generated_file = models.FileField(
		_("Файл отчёта"),
		upload_to="reports/%Y/%m/%d/",
		null=True,
		blank=True)
	status = models.CharField(
		_("Статус"),
		max_length=20,
		choices=[
			("pending", "Ожидает"),
			("generating", "Генерируется"),
			("ready", "Готов"),
			("failed", "Ошибка")],
		default="pending"
	)
	error_message = models.TextField(blank=True)
	created_by = models.ForeignKey(
		"authentication.User",
		null=True,
		on_delete=models.SET_NULL)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = _("Сгенерированный отчёт")
		verbose_name_plural = _("Сгенерированные отчёты")
		ordering = ["-created_at"]

	def __str__(self):
		return self.name

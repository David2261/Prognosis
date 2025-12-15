from django.db import models
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify


class TimeStampedModel(models.Model):
	"""
	Абстрактная базовая модель с датами создания и обновления.
	Используется во всех моделях проекта.
	"""
	created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
	updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

	class Meta:
		abstract = True


class CompanyRelatedModel(TimeStampedModel):
	"""
	Абстрактная модель с привязкой к компании (тенанту).
	Все основные сущности (сценарии, периоды, фин. данные) наследуют от неё.
	"""
	company = models.ForeignKey(
		"accounts.Company",
		on_delete=models.CASCADE,
		verbose_name=_("Компания"),
		related_name="%(app_label)s_%(class)s_set"
	)

	class Meta:
		abstract = True
		indexes = [
			models.Index(fields=["company"]),
		]


class TimePeriod(CompanyRelatedModel):
	"""
	Период времени: год, квартал, месяц.
	Используется для всех финансовых данных (факт, план, прогноз).
	"""
	year = models.PositiveIntegerField(
		_("Год"),
		validators=[MinValueValidator(2000), MaxValueValidator(2100)]
	)
	quarter = models.PositiveSmallIntegerField(
		_("Квартал"),
		null=True,
		blank=True,
		validators=[MinValueValidator(1), MaxValueValidator(4)]
	)
	month = models.PositiveSmallIntegerField(
		_("Месяц"),
		null=True,
		blank=True,
		validators=[MinValueValidator(1), MaxValueValidator(12)]
	)
	is_closed = models.BooleanField(
		_("Период закрыт"),
		default=False,
		help_text=_("Запрет на редактирование данных после закрытия периода")
	)

	class Meta:
		verbose_name = _("Период")
		verbose_name_plural = _("Периоды")
		unique_together = ("company", "year", "quarter", "month")
		ordering = ["-year", "-quarter", "-month"]
		indexes = [
			models.Index(fields=["company", "year", "quarter", "month"]),
			models.Index(fields=["is_closed"]),
		]

	def __str__(self) -> str:
		if self.month:
			return f"{self.year}-{self.month:02d} ({self.company})"
		if self.quarter:
			return f"{self.year}-Q{self.quarter} ({self.company})"
		return f"{self.year} ({self.company})"

	def clean(self):
		# Валидация: если месяц указан — квартал тоже должен быть, и наоборот
		if self.month and not self.quarter:
			raise ValidationError(_("Если указан месяц, должен быть указан квартал"))
		if self.quarter and self.month:
			expected_quarter = (self.month - 1) // 3 + 1
			if self.quarter != expected_quarter:
				raise ValidationError(_("Квартал не соответствует месяцу"))


class Scenario(CompanyRelatedModel):
	"""
	Сценарий: Бюджет 2025, Факт, Прогноз Март 2025, Оптимистичный и т.д.
	"""
	SCENARIO_TYPES = [
		("actual", _("Факт")),
		("budget", _("Бюджет")),
		("forecast", _("Прогноз")),
		("adjustment", _("Корректировка")),
		("plan", _("План")),
	]

	name = models.CharField(
		_("Название"),
		max_length=255,
		help_text=_("Бюджет 2025, Rolling Forecast Dec'25 и т.д."))
	slug = models.SlugField(max_length=255, blank=True)
	type = models.CharField(
		_("Тип сценария"),
		max_length=20,
		choices=SCENARIO_TYPES)
	version = models.PositiveIntegerField(_("Версия"), default=1)
	is_active = models.BooleanField(_("Активен"), default=True)
	base_scenario = models.ForeignKey(
		"self",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		verbose_name=_("Базируется на"),
		help_text=_("Для корректировок и новых версий")
	)
	start_period = models.ForeignKey(
		TimePeriod,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="scenario_starts",
		verbose_name=_("Начальный период")
	)
	end_period = models.ForeignKey(
		TimePeriod,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="scenario_ends",
		verbose_name=_("Конечный период")
	)

	class Meta:
		verbose_name = _("Сценарий")
		verbose_name_plural = _("Сценарии")
		unique_together = ("company", "name", "version")
		# Ensure slug unique per company
		indexes = [
			models.Index(fields=["company", "slug"]),
		]
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["company", "type", "is_active"]),
		]

	def __str__(self) -> str:
		return f"{self.name} v{self.version} ({self.get_type_display()})"

	def _generate_unique_slug(self):
		base = slugify(self.name) or "scenario"
		slug = base
		count = 1
		while Scenario.objects.filter(
			company=self.company,
			slug=slug).exclude(pk=getattr(self, 'pk', None)).exists():
			slug = f"{base}-{count}"
			count += 1
		return slug

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = self._generate_unique_slug()
		super().save(*args, **kwargs)

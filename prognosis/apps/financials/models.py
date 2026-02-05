from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

from core.models import CompanyRelatedModel, TimePeriod
from dimensions.models import BudgetArticle, CostCenter, Project
from accounts.models import Company
from .mixins import ScenarioPeriodMixin, DimensionMixin, BaseReportMapping


class FinancialLine(CompanyRelatedModel, ScenarioPeriodMixin, DimensionMixin):
	"""
	Основная детальная строка финансовых данных.
	Одна строка — одна сумма по уникальной комбинации измерений + период + сценарий.
	"""
	amount = models.DecimalField(
		_("Сумма"),
		max_digits=19,
		decimal_places=2,
		help_text=_("В основной валюте компании")
	)

	comment = models.TextField(_("Комментарий"), blank=True)
	source = models.CharField(
		_("Источник"),
		max_length=100,
		blank=True,
		help_text=_("Ручной ввод, Excel, ERP, интеграция и т.д.")
	)
	slug = models.SlugField(
		_("Slug"),
		max_length=255,
		unique=True,
		blank=True,
		help_text=_("Уникальный идентификатор для URL")
	)

	class Meta:
		verbose_name = _("Строка финансовых данных")
		verbose_name_plural = _("Строки финансовых данных")
		constraints = [
			models.UniqueConstraint(
				fields=[
					"company", "scenario", "period", "article",
					"cost_center", "department", "project", "account"
				],
				name="unique_financial_line",
				nulls_distinct=True,
			)
		]
		indexes = [
			models.Index(fields=["company", "scenario", "period"]),
			models.Index(fields=["company", "article"]),
			models.Index(fields=["company", "cost_center"]),
			models.Index(fields=["company", "project"]),
			models.Index(fields=["company", "department"]),
		]
		ordering = ["-period__year", "-period__month", "article__code"]

	def __str__(self):
		return f"{self.scenario} | {self.period} | {self.article} | {self.amount}"
	
	def save(self, *args, **kwargs):
		if not self.slug:
			base_slug = slugify(f"{self.company.slug}-{self.scenario.slug}-{self.period}-{self.article.code}")
			slug = base_slug
			i = 1
			while FinancialLine.objects.filter(slug=slug).exclude(pk=self.pk).exists():
				slug = f"{base_slug}-{i}"
				i += 1
			self.slug = slug
		super().save(*args, **kwargs)


class FinancialAggregate(CompanyRelatedModel, ScenarioPeriodMixin):
	"""
	Материализованные (кэшированные) агрегаты для ускорения отчётности и дашбордов.
	Заполняется периодически через Celery или signals.
	"""

	article = models.ForeignKey(
		BudgetArticle,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		verbose_name=_("Статья (или группа)")
	)
	section = models.CharField(
		_("Раздел отчёта"),
		max_length=50,
		blank=True,
		help_text=_("NON_CURRENT_ASSETS, REVENUE, OPEX и т.д.")
	)
	cost_center = models.ForeignKey(CostCenter, null=True, blank=True, on_delete=models.SET_NULL)
	project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL)

	amount = models.DecimalField(_("Сумма"), max_digits=19, decimal_places=2)

	class Meta:
		verbose_name = _("Агрегат финансовых данных")
		verbose_name_plural = _("Агрегаты финансовых данных")
		indexes = [
			models.Index(fields=["company", "scenario", "period", "section"]),
			models.Index(fields=["company", "scenario", "period", "article"]),
		]


class ConsolidationRule(models.Model):
	"""
	Справочник правил элиминации внутригрупповых оборотов.
	Фактические суммы рассчитываются динамически в сервисе консолидации.
	"""
	ELIMINATION_METHODS = [
		("FULL", _("Полная элиминация")),
		("PROPORTIONAL", _("Пропорциональная (по доле владения)")),
		("REVENUE_EXPENSE", _("Только доходы/расходы")),
		("BALANCE_ONLY", _("Только балансовые статьи")),
	]

	article = models.ForeignKey(
		BudgetArticle,
		on_delete=models.PROTECT,
		verbose_name=_("Статья бюджета")
	)
	company_from = models.ForeignKey(
		Company,
		null=True,
		blank=True,
		related_name="elimination_rules_out",
		on_delete=models.PROTECT,
		verbose_name=_("Компания-продавец")
	)
	company_to = models.ForeignKey(
		Company,
		null=True,
		blank=True,
		related_name="elimination_rules_in",
		on_delete=models.PROTECT,
		verbose_name=_("Компания-покупатель")
	)
	method = models.CharField(
		_("Метод элиминации"),
		max_length=20,
		choices=ELIMINATION_METHODS,
		default="FULL"
	)
	is_active = models.BooleanField(_("Активно"), default=True)
	description = models.TextField(_("Описание правила"), blank=True)

	class Meta:
		verbose_name = _("Правило консолидационной элиминации")
		verbose_name_plural = _("Правила консолидационной элиминации")
		unique_together = [("article", "company_from", "company_to")]

	def __str__(self):
		return f"Элиминация {self.article} ({self.get_method_display()})"


class CurrencyRate(models.Model):
	"""Исторические курсы валют"""
	date = models.DateField(_("Дата"))
	base_currency = models.CharField(_("Базовая валюта"), max_length=3)
	target_currency = models.CharField(_("Целевая валюта"), max_length=3)
	rate = models.DecimalField(_("Курс"), max_digits=12, decimal_places=6)
	source = models.CharField(_("Источник"), max_length=50, blank=True, default="")

	class Meta:
		verbose_name = _("Курс валюты")
		verbose_name_plural = _("Курсы валют")
		unique_together = ("date", "base_currency", "target_currency", "source")
		ordering = ["-date"]
		indexes = [
			models.Index(fields=["date", "base_currency", "target_currency"]),
		]

	def __str__(self):
		return f"{self.base_currency}/{self.target_currency} = {self.rate} ({self.date})"


class MetricDefinition(models.Model):
	"""Справочник определений ключевых метрик и формул их расчёта"""
	code = models.CharField(_("Код метрики"), max_length=50, unique=True)
	name = models.CharField(_("Наименование"), max_length=255)
	description = models.TextField(_("Описание"), blank=True)

	formula = models.TextField(
		_("Формула"),
		help_text=_("Например: SUM(REVENUE) - SUM(COGS) или сложные выражения")
	)
	formula_type = models.CharField(
		_("Тип формулы"),
		max_length=20,
		choices=[
			("SIMPLE", _("Простая арифметика")),
			("RATIO", _("Коэффициент")),
			("CUSTOM", _("Пользовательская логика")),
		],
		default="SIMPLE"
	)
	unit = models.CharField(_("Единица измерения"), max_length=20, blank=True)
	is_active = models.BooleanField(_("Активна"), default=True)

	class Meta:
		verbose_name = _("Определение метрики")
		verbose_name_plural = _("Определения метрик")
		ordering = ["code"]

	def __str__(self):
		return f"{self.code} — {self.name}"


class MetricValue(CompanyRelatedModel, ScenarioPeriodMixin):
	"""Материализованное значение рассчитанной метрики"""
	definition = models.ForeignKey(
		MetricDefinition,
		on_delete=models.PROTECT,
		related_name="values"
	)

	value = models.DecimalField(_("Значение"), max_digits=19, decimal_places=4)
	calculation_details = models.JSONField(
		_("Детали расчёта"),
		blank=True,
		null=True
	)
	calculated_at = models.DateTimeField(_("Рассчитано"), auto_now_add=True)
	calculated_by = models.ForeignKey(
		"authentication.User",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		verbose_name=_("Рассчитал")
	)

	class Meta:
		verbose_name = _("Значение метрики")
		verbose_name_plural = _("Значения метрик")
		unique_together = ("company", "definition", "scenario", "period")
		indexes = [
			models.Index(fields=["company", "scenario", "period"]),
			models.Index(fields=["definition"]),
		]

	def __str__(self):
		return f"{self.definition.code} = {self.value} ({self.scenario}, {self.period})"


class FinancialLock(CompanyRelatedModel):
	"""Блокировка редактирования данных по периодам/сценариям"""
	scenario = models.ForeignKey(
		"core.Scenario",
		null=True,
		blank=True,
		on_delete=models.PROTECT
	)
	period_from = models.ForeignKey(
		TimePeriod,
		related_name="locks_from",
		on_delete=models.PROTECT
	)
	period_to = models.ForeignKey(
		TimePeriod,
		related_name="locks_to",
		on_delete=models.PROTECT
	)
	locked_by = models.ForeignKey(
		"authentication.User",
		null=True,
		on_delete=models.SET_NULL
	)
	locked_at = models.DateTimeField(auto_now_add=True)
	reason = models.TextField(_("Причина"), blank=True)

	class Meta:
		verbose_name = _("Блокировка периода")
		verbose_name_plural = _("Блокировки периодов")


class BalanceSheetMapping(BaseReportMapping):
	"""Маппинг статей бюджета на строки бухгалтерского баланса по ФСБУ 4/2023"""
	line_code = models.CharField(_("Код строки"), max_length=20, blank=True)
	section = models.CharField(
		_("Раздел"),
		max_length=50,
		choices=[
			("NON_CURRENT_ASSETS", _("Внеоборотные активы")),
			("CURRENT_ASSETS", _("Оборотные активы")),
			("EQUITY", _("Капитал")),
			("LONG_TERM_LIABILITIES", _("Долгосрочные обязательства")),
			("SHORT_TERM_LIABILITIES", _("Краткосрочные обязательства")),
		]
	)

	class Meta:
		verbose_name = _("Маппинг строки баланса")
		verbose_name_plural = _("Маппинги баланса")
		ordering = ["section", "order"]
		unique_together = [("article", "line_name")]

	def __str__(self):
		return f"{self.article} → {self.line_name}"


class ProfitLossMapping(BaseReportMapping):
	"""Маппинг на строки отчёта о финансовых результатах (P&L)"""
	class Meta:
		verbose_name = _("Маппинг строки P&L")
		verbose_name_plural = _("Маппинги P&L")
		ordering = ["order"]

	def __str__(self):
		return f"{self.article} → {self.line_name}"


class CashFlowMapping(BaseReportMapping):
	"""Маппинг на строки отчёта о движении денежных средств"""
	section = models.CharField(
		_("Раздел"),
		max_length=50,
		choices=[
			("OPERATING", _("Операционная деятельность")),
			("INVESTING", _("Инвестиционная деятельность")),
			("FINANCING", _("Финансовая деятельность")),
		]
	)
	method = models.CharField(
		_("Метод"),
		max_length=20,
		choices=[("DIRECT", _("Прямой")), ("INDIRECT", _("Косвенный"))],
		default="DIRECT"
	)

	class Meta:
		verbose_name = _("Маппинг строки ДДС")
		verbose_name_plural = _("Маппинги ДДС")
		ordering = ["section", "order"]

	def __str__(self):
		return f"{self.article} → {self.section} — {self.line_name or self.get_method_display()}"

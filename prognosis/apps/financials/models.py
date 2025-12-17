from django.db import models
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from core.models import CompanyRelatedModel
from dimensions.models import (
	BudgetArticle, CostCenter,
	Department, Project, ChartOfAccounts
)


class FinancialLine(CompanyRelatedModel):
	"""
	Основная строка финансовых данных: факт, план, бюджет, корректировка.
	Одна строка — одна сумма по комбинации измерений + период + сценарий.
	"""
	scenario = models.ForeignKey(
		"core.Scenario",
		on_delete=models.PROTECT,
		verbose_name=_("Сценарий"),
		related_name="financial_lines"
	)
	period = models.ForeignKey(
		"core.TimePeriod",
		on_delete=models.PROTECT,
		verbose_name=_("Период"),
		related_name="financial_lines"
	)

	# Основные измерения (dimensions)
	article = models.ForeignKey(
		BudgetArticle,
		on_delete=models.PROTECT,
		verbose_name=_("Статья бюджета"),
		related_name="financial_lines"
	)
	cost_center = models.ForeignKey(
		CostCenter,
		null=True,
		blank=True,
		on_delete=models.PROTECT,
		verbose_name=_("ЦФО")
	)
	department = models.ForeignKey(
		Department,
		null=True,
		blank=True,
		on_delete=models.PROTECT,
		verbose_name=_("Подразделение")
	)
	project = models.ForeignKey(
		Project,
		null=True,
		blank=True,
		on_delete=models.PROTECT,
		verbose_name=_("Проект")
	)
	account = models.ForeignKey(
		ChartOfAccounts,
		null=True,
		blank=True,
		on_delete=models.PROTECT,
		verbose_name=_("Счет плана счетов")
	)

	# Суммы (можно расширить: quantity, price и т.д.)
	amount = models.DecimalField(
		_("Сумма"),
		max_digits=19,
		decimal_places=2,
		help_text=_("В основной валюте компании")
	)

	# Дополнительно
	comment = models.TextField(_("Комментарий"), blank=True)
	source = models.CharField(
		_("Источник"),
		max_length=100,
		blank=True,
		help_text=_("Ручной ввод, Excel, ERP и т.д.)"))

	class Meta:
		verbose_name = _("Строка финансовых данных")
		verbose_name_plural = _("Финансовые данные")
		ordering = ["-period__year", "-period__month", "article__code"]
		indexes = [
			models.Index(fields=["company", "scenario", "period"]),
			models.Index(fields=["company", "article"]),
			models.Index(fields=["company", "cost_center"]),
			models.Index(fields=["company", "project"]),
			models.Index(fields=["company", "department"]),
		]
		constraints = [
			models.UniqueConstraint(
				fields=[
					"company",
					"scenario",
					"period",
					"article",
					"cost_center",
					"department",
					"project",
					"account"],
				name="unique_financial_line_with_nulls",
				nulls_distinct=True,
			)
		]

	def save(self, *args, **kwargs):
		if self.pk is None:  # только при создании
			if FinancialLine.objects.filter(
				company=self.company,
				scenario=self.scenario,
				period=self.period,
				article=self.article,
				cost_center=self.cost_center,
				department=self.department,
				project=self.project,
				account=self.account,
			).exists():
				raise ValidationError("Такая комбинация финансовых данных уже существует")
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.scenario} | {self.period} | {self.article} | {self.amount}"

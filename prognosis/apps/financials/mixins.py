from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimePeriod, Scenario
from dimensions.models import BudgetArticle, ChartOfAccounts, CostCenter, Department, Project


class ScenarioPeriodMixin(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.PROTECT)
    period = models.ForeignKey(TimePeriod, on_delete=models.PROTECT)

    class Meta:
        abstract = True


class DimensionMixin(models.Model):
    article = models.ForeignKey(
        BudgetArticle,
        on_delete=models.PROTECT,
        verbose_name=_("Статья бюджета")
    )
    cost_center = models.ForeignKey(CostCenter, null=True, blank=True, on_delete=models.PROTECT)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.PROTECT)
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.PROTECT)
    account = models.ForeignKey(ChartOfAccounts, null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        abstract = True


class BaseReportMapping(models.Model):
    article = models.ForeignKey(BudgetArticle, on_delete=models.CASCADE)
    line_name = models.CharField(_("Строка"), max_length=255)
    order = models.PositiveIntegerField(_("Порядок"), default=0)
    sign = models.IntegerField(_("Знак"), choices=[(1, "+"), (-1, "-")], default=1)

    class Meta:
        abstract = True

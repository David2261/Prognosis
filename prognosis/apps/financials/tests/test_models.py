# financials/tests/test_models.py
import pytest
from decimal import Decimal
from django.db import IntegrityError

from accounts.models import Company
from authentication.models import User
from core.models import Scenario, TimePeriod
from dimensions.models import BudgetArticle, CostCenter, Department, Project, ChartOfAccounts
from financials.models import (
	FinancialLine,
	FinancialAggregate,
	ConsolidationRule,
	CurrencyRate,
	MetricDefinition,
	MetricValue,
	FinancialLock,
	BalanceSheetMapping,
	ProfitLossMapping,
	CashFlowMapping,
)


@pytest.fixture
def company():
	return Company.objects.create(name="Test Company", inn="1234567890")


@pytest.fixture
def user():
	return User.objects.create_user(email="test@example.com", password="pass")


@pytest.fixture
def scenario(company):
	return Scenario.objects.create(
		company=company,
		name="Budget 2025",
		type="budget",
		version=1
	)


@pytest.fixture
def period(company):
	return TimePeriod.objects.create(company=company, year=2025, month=1)


@pytest.fixture
def budget_article(company):
	return BudgetArticle.add_root(company=company, code="REV001", name="Выручка")


@pytest.fixture
def cost_center(company):
	return CostCenter.objects.create(company=company, code="CC01", name="Sales")


@pytest.fixture
def department(company):
	return Department.add_root(company=company, code="DEP01", name="Sales Dept")


@pytest.fixture
def project(company):
	return Project.objects.create(company=company, code="PRJ01", name="Launch")


@pytest.fixture
def chart_account(company):
	return ChartOfAccounts.objects.create(company=company, code="4080", name="Расчёты с покупателями")


# === FinancialLine ===
@pytest.mark.django_db
def test_financialline_creation(company, scenario, period, budget_article):
	line = FinancialLine.objects.create(
		company=company,
		scenario=scenario,
		period=period,
		article=budget_article,
		amount=Decimal("1000.00")
	)
	assert line.pk is not None
	assert line.amount == Decimal("1000.00")
	assert line.company == company


@pytest.mark.django_db
def test_financialline_slug_generation(company, scenario, period, budget_article):
	line1 = FinancialLine.objects.create(
		company=company,
		scenario=scenario,
		period=period,
		article=budget_article,
		amount=Decimal("100.00")
	)

	assert line1.slug
	assert isinstance(line1.slug, str)

	slug_lower = line1.slug.lower()
	assert company.slug.lower() in slug_lower
	assert scenario.slug.lower() in slug_lower
	assert str(period.year) in slug_lower
	assert f"{period.month:02d}" in slug_lower
	assert budget_article.code.lower() in slug_lower

	line2 = FinancialLine.objects.create(
		company=company,
		scenario=scenario,
		period=period,
		article=budget_article,
		amount=Decimal("200.00")
	)

	assert line2.slug != line1.slug
	assert line2.slug.startswith(line1.slug)
	assert line2.slug.endswith("-1") or "-1" in line2.slug.split("-")[-1]


@pytest.mark.django_db
def test_financialline_with_dimensions(
	company, scenario, period, budget_article,
	cost_center, department, project, chart_account
):
	line = FinancialLine.objects.create(
		company=company,
		scenario=scenario,
		period=period,
		article=budget_article,
		cost_center=cost_center,
		department=department,
		project=project,
		account=chart_account,
		amount=Decimal("500.00")
	)
	assert line.cost_center == cost_center
	assert line.department == department
	assert line.project == project
	assert line.account == chart_account
	assert line.company == company


# === FinancialAggregate ===
@pytest.mark.django_db
def test_financialaggregate_creation(company, scenario, period, budget_article):
	agg = FinancialAggregate.objects.create(
		company=company,
		scenario=scenario,
		period=period,
		article=budget_article,
		section="REVENUE",
		amount=Decimal("10000.00")
	)
	assert agg.section == "REVENUE"
	assert agg.amount == Decimal("10000.00")
	assert agg.company == company


# === ConsolidationRule ===
@pytest.mark.django_db
def test_consolidationrule_creation(company, budget_article):
	other_company = Company.objects.create(name="Subsidiary")
	rule = ConsolidationRule.objects.create(
		article=budget_article,
		company_from=company,
		company_to=other_company,
		method="FULL"
	)
	assert rule.method == "FULL"
	assert rule.is_active is True


@pytest.mark.django_db
def test_consolidationrule_unique_together(company, budget_article):
	other_company = Company.objects.create(name="Sub2")
	ConsolidationRule.objects.create(
		article=budget_article,
		company_from=company,
		company_to=other_company,
		method="FULL"
	)

	with pytest.raises(IntegrityError):
		ConsolidationRule.objects.create(
			article=budget_article,
			company_from=company,
			company_to=other_company,
			method="PROPORTIONAL"
		)


# === CurrencyRate ===
@pytest.mark.django_db
def test_currencyrate_creation():
	rate = CurrencyRate.objects.create(
		date="2025-01-01",
		base_currency="USD",
		target_currency="RUB",
		rate=Decimal("95.50"),
		source="CBR"
	)
	assert rate.rate == Decimal("95.50")


@pytest.mark.django_db
def test_currencyrate_unique_together():
	CurrencyRate.objects.create(
		date="2025-01-01",
		base_currency="EUR",
		target_currency="RUB",
		rate=Decimal("100.00"),
		source="ECB"
	)

	with pytest.raises(IntegrityError):
		CurrencyRate.objects.create(
			date="2025-01-01",
			base_currency="EUR",
			target_currency="RUB",
			rate=Decimal("101.00"),
			source="ECB"
		)


# === MetricDefinition & MetricValue ===
@pytest.mark.django_db
def test_metric_definition_creation():
	definition = MetricDefinition.objects.create(
		code="EBITDA",
		name="EBITDA",
		formula="SUM(OP_PROFIT) + SUM(DEPRECIATION)",
		formula_type="SIMPLE"
	)
	assert definition.code == "EBITDA"
	assert definition.is_active is True


@pytest.mark.django_db
def test_metric_value_creation(company, scenario, period):
	definition = MetricDefinition.objects.create(
		code="GROSS_MARGIN",
		name="Валовая маржа",
		formula="REVENUE - COGS"
	)
	value = MetricValue.objects.create(
		company=company,
		definition=definition,
		scenario=scenario,
		period=period,
		value=Decimal("42.5")
	)
	assert value.value == Decimal("42.5")
	assert value.definition == definition
	assert value.company == company


@pytest.mark.django_db
def test_metric_value_unique_together(company, scenario, period):
	definition = MetricDefinition.objects.create(code="ROE", name="ROE")
	MetricValue.objects.create(
		company=company,
		definition=definition,
		scenario=scenario,
		period=period,
		value=Decimal("15.0")
	)

	with pytest.raises(IntegrityError):
		MetricValue.objects.create(
			company=company,
			definition=definition,
			scenario=scenario,
			period=period,
			value=Decimal("16.0")
		)


# === FinancialLock ===
@pytest.mark.django_db
def test_financiallock_creation(company, scenario, period, user):
	other_period = TimePeriod.objects.create(company=company, year=2025, month=12)
	lock = FinancialLock.objects.create(
		company=company,
		scenario=scenario,
		period_from=period,
		period_to=other_period,
		locked_by=user,
		reason="Closed for audit"
	)
	assert lock.reason == "Closed for audit"
	assert lock.locked_by == user
	assert lock.company == company


# === BalanceSheetMapping ===
@pytest.mark.django_db
def test_balance_sheet_mapping(company, budget_article):
	mapping = BalanceSheetMapping.objects.create(
		article=budget_article,
		line_code="1200",
		line_name="Дебиторская задолженность",
		section="CURRENT_ASSETS",
		order=10,
		sign=1
	)
	assert mapping.section == "CURRENT_ASSETS"
	assert mapping.get_section_display() == "Оборотные активы"


# === ProfitLossMapping ===
@pytest.mark.django_db
def test_profit_loss_mapping(budget_article):
	mapping = ProfitLossMapping.objects.create(
		article=budget_article,
		line_name="Выручка",
		order=1,
		sign=1
	)
	assert mapping.line_name == "Выручка"


# === CashFlowMapping ===
@pytest.mark.django_db
def test_cash_flow_mapping(budget_article):
	mapping = CashFlowMapping.objects.create(
		article=budget_article,
		section="OPERATING",
		line_name="Поступления от продаж",
		method="DIRECT",
		order=5,
		sign=1
	)
	assert mapping.section == "OPERATING"
	assert mapping.get_section_display() == "Операционная деятельность"

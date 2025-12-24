import pytest
from decimal import Decimal

from reports.data import get_financial_data_for_report
from financials.models import FinancialLine
from core.models import TimePeriod, Scenario
from accounts.models import Company
from dimensions.models import BudgetArticle


@pytest.mark.django_db
class TestGetFinancialDataForReport:
	"""Тесты для функции get_financial_data_for_report"""

	@pytest.fixture
	def company(self):
		return Company.objects.create(name="Тестовая Компания")

	@pytest.fixture
	def template_pnl(self, company):
		from reports.models import ReportTemplate
		return ReportTemplate.objects.create(
			company=company,
			name="P&L",
			code="PNL-TEST",
			report_type="pnl",
		)

	@pytest.fixture
	def template_plan_fact(self, company):
		from reports.models import ReportTemplate
		return ReportTemplate.objects.create(
			company=company,
			name="План-Факт",
			code="PLAN-FACT",
			report_type="plan_fact",
		)

	@pytest.fixture
	def period_dec(self, company):
		return TimePeriod.objects.create(
			company=company,
			year=2025,
			month=12,
		)

	@pytest.fixture
	def scenario_fact(self, company, period_dec):
		return Scenario.objects.create(
			company=company,
			name="Факт декабрь 2025",
			type="actual",
			start_period=period_dec,
			end_period=period_dec,
		)

	@pytest.fixture
	def scenario_budget(self, company, period_dec):
		return Scenario.objects.create(
			company=company,
			name="Бюджет 2025",
			type="budget",
			start_period=period_dec,
			end_period=period_dec,
		)

	@pytest.fixture
	def articles(self, company):
		return {
			"revenue": BudgetArticle.add_root(
				company=company,
				code="4000",
				name="Выручка"
			),
			"cost": BudgetArticle.add_root(
				company=company,
				code="5000",
				name="Себестоимость"
			),
		}

	@pytest.fixture
	def financial_lines(self, company, period_dec, scenario_fact, scenario_budget, articles):
		FinancialLine.objects.bulk_create([
			FinancialLine(
				company=company,
				period=period_dec,
				scenario=scenario_fact,
				article=articles["revenue"],
				amount=Decimal("1200000.00"),
			),
			FinancialLine(
				company=company,
				period=period_dec,
				scenario=scenario_budget,
				article=articles["revenue"],
				amount=Decimal("1000000.00"),
			),
			FinancialLine(
				company=company,
				period=period_dec,
				scenario=scenario_fact,
				article=articles["cost"],
				amount=Decimal("-750000.00"),
			),
			FinancialLine(
				company=company,
				period=period_dec,
				scenario=scenario_budget,
				article=articles["cost"],
				amount=Decimal("-650000.00"),
			),
		])

	def test_basic_plan_fact_comparison(
		self, company, template_plan_fact, period_dec, financial_lines
	):
		result = get_financial_data_for_report(
			company=company,
			template=template_plan_fact,
			start_period=period_dec,
			end_period=period_dec,
		)

		assert len(result) == 2

		revenue = next(item for item in result if item["article_code"] == "4000")
		cost = next(item for item in result if item["article_code"] == "5000")

		assert revenue["fact"] == 1200000.0
		assert revenue["plan"] == 1000000.0
		assert revenue["deviation"] == 200000.0
		assert pytest.approx(revenue["deviation_percent"], 0.01) == 20.0

		assert cost["fact"] == -750000.0
		assert cost["plan"] == -650000.0
		assert cost["deviation"] == -100000.0
		assert pytest.approx(cost["deviation_percent"], 0.01) == -15.38

	def test_filter_by_scenario(self, company, template_plan_fact, period_dec, scenario_fact, financial_lines):
		result = get_financial_data_for_report(
			company=company,
			template=template_plan_fact,
			scenario=scenario_fact,
			start_period=period_dec,
		)

		assert len(result) == 2
		for item in result:
			assert item["fact"] != 0.0
			assert item["plan"] == 0.0  # только факт

	def test_no_data_returns_empty_list(self, company, template_pnl, period_dec):
		result = get_financial_data_for_report(
			company=company,
			template=template_pnl,
			start_period=period_dec,
		)
		assert result == []

	def test_include_dimensions(self, company, template_plan_fact, period_dec, financial_lines):
		# Предполагаем, что у FinancialLine есть поля cost_center, department, project
		# Если их нет — тест нужно адаптировать
		result = get_financial_data_for_report(
			company=company,
			template=template_plan_fact,
			start_period=period_dec,
			include_dimensions=True,
		)

		for item in result:
			assert "cost_center" in item
			assert "department" in item
			assert "project" in item

	def test_pnl_template_returns_data_without_warning(self, company, template_pnl, period_dec, financial_lines):
		result = get_financial_data_for_report(
			company=company,
			template=template_pnl,
			start_period=period_dec,
		)

		assert not any("warning" in item for item in result)

	def test_balance_template_returns_warning(self, company, period_dec):
		from reports.models import ReportTemplate
		balance_template = ReportTemplate.objects.create(
			company=company,
			name="Баланс",
			code="BAL-TEST",
			report_type="balance",
		)

		result = get_financial_data_for_report(
			company=company,
			template=balance_template,
			start_period=period_dec,
		)

		assert len(result) == 1
		assert "warning" in result[0]
		assert "Баланс пока не реализован" in result[0]["warning"]

	def test_zero_plan_does_not_divide_by_zero(self, company, template_plan_fact, period_dec):
		# Создаём статью отдельно
		special_article = BudgetArticle.add_root(
			company=company,
			code="9999",
			name="Особая статья",
			article_type="other"
		)

		# Создаём сценарий "факт"
		scenario_fact = Scenario.objects.create(
			company=company,
			name="Только факт",
			type="actual",
		)

		# Добавляем строку только с фактом
		FinancialLine.objects.create(
			company=company,
			period=period_dec,
			scenario=scenario_fact,
			article=special_article,
			amount=Decimal("50000.00"),
		)

		result = get_financial_data_for_report(
			company=company,
			template=template_plan_fact,
			start_period=period_dec,
		)

		special = next((r for r in result if r["article_code"] == "9999"), None)
		assert special is not None
		assert special["plan"] == 0.0
		assert special["deviation_percent"] == 0.0

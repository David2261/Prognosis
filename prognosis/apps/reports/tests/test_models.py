import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils.text import slugify
from django.contrib.auth import get_user_model

from reports.models import ReportTemplate, GeneratedReport
from core.models import TimePeriod, Scenario
from accounts.models import Company

User = get_user_model()


@pytest.mark.django_db
class TestReportTemplate:
	"""Тесты для модели ReportTemplate"""

	@pytest.fixture
	def company(self):
		return Company.objects.create(name="Тестовая Компания ООО")

	def test_create_minimal_template(self, company):
		template = ReportTemplate.objects.create(
			company=company,
			name="Отчёт о прибылях и убытках",
			code="PNL-2025",
			report_type="pnl",
		)
		assert template.pk is not None
		assert template.slug == slugify("Отчёт о прибылях и убытках", allow_unicode=True)

	def test_slug_autogeneration_and_uniqueness_within_company(self, company):
		t1 = ReportTemplate.objects.create(
			company=company,
			name="Финансовый анализ",
			code="FA-001",
			report_type="custom",
		)
		assert t1.slug == "финансовый-анализ"

		t2 = ReportTemplate.objects.create(
			company=company,
			name="Финансовый анализ",
			code="FA-002",
			report_type="custom",
		)
		assert t2.slug.startswith("финансовый-анализ-")
		assert t2.slug != t1.slug

	def test_unique_together_company_and_code(self, company):
		ReportTemplate.objects.create(
			company=company,
			name="Баланс",
			code="BAL-2025",
			report_type="balance",
		)

		with pytest.raises(IntegrityError):
			ReportTemplate.objects.create(
				company=company,
				name="Баланс копия",
				code="BAL-2025",
				report_type="balance",
			)

	def test_code_must_be_unique_across_all_companies(self, company):
		ReportTemplate.objects.create(
			company=company,
			name="Универсальный шаблон",
			code="UNIVERSAL-TEMPLATE",
			report_type="custom",
		)

		another_company = Company.objects.create(name="Другая Компания")

		with pytest.raises(IntegrityError):
			ReportTemplate.objects.create(
				company=another_company,
				name="Тот же код",
				code="UNIVERSAL-TEMPLATE",
				report_type="custom",
			)

	def test_invalid_report_type(self, company):
		template = ReportTemplate(
			company=company,
			name="Неверный тип",
			code="WRONG",
			report_type="something_wrong",
		)
		with pytest.raises(ValidationError):
			template.full_clean()

	@pytest.mark.parametrize("report_type", ["pnl", "balance", "cashflow", "plan_fact", "custom"])
	def test_all_valid_report_types(self, company, report_type):
		template = ReportTemplate.objects.create(
			company=company,
			name=f"Тест {report_type}",
			code=f"TEST-{report_type.upper()}",
			report_type=report_type,
		)
		assert template.get_report_type_display()

	def test_str_representation(self, company):
		template = ReportTemplate.objects.create(
			company=company,
			name="Cash Flow 2025",
			code="CF-2025",
			report_type="cashflow",
		)
		str_value = str(template)
		assert "Cash Flow" in str_value or "Cashflow" in str_value
		assert "2025" in str_value


@pytest.mark.django_db
class TestGeneratedReport:
	"""Тесты для модели GeneratedReport"""

	@pytest.fixture
	def company(self):
		return Company.objects.create(name="Компания для тестов отчётов")

	@pytest.fixture
	def template(self, company):
		return ReportTemplate.objects.create(
			company=company,
			name="Стандартный шаблон P&L",
			code="STD-PNL-2025",
			report_type="pnl",
		)

	@pytest.fixture
	def time_period(self, company):
		return TimePeriod.objects.create(
			company=company,
			year=2025,
			month=12,
		)

	@pytest.fixture
	def scenario(self, company, time_period):
		return Scenario.objects.create(
			company=company,
			name="Бюджет 2025",
			type="budget",
			start_period=time_period,
			end_period=time_period,
		)

	def test_create_minimal_report(self, template):
		report = GeneratedReport.objects.create(
			company=template.company,
			template=template,
			name="P&L Декабрь 2025",
		)
		assert report.pk is not None
		assert report.status == "pending"
		assert report.scenario is None
		assert report.start_period is None
		assert report.end_period is None

	def test_full_filled_report(self, template, scenario, time_period):
		report = GeneratedReport.objects.create(
			company=template.company,
			template=template,
			name="Полный отчёт",
			scenario=scenario,
			start_period=time_period,
			end_period=time_period,
			status="generating",
		)
		assert report.scenario == scenario
		assert report.start_period == time_period
		assert report.end_period == time_period
		assert report.status == "generating"

	def test_invalid_status(self):
		report = GeneratedReport(status="invalid_status")
		with pytest.raises(ValidationError):
			report.full_clean()

	@pytest.mark.parametrize("status", ["pending", "generating", "ready", "failed"])
	def test_valid_statuses(self, status, template):
		user = User.objects.create_user(email='test@example.com', password='testpass123')
		report = GeneratedReport(
			company=template.company,
			template=template,
			name=f"Отчёт со статусом {status}",
			status=status,
			created_by=user,
		)
		report.full_clean()

	def test_ordering_newest_first(self, template):
		r1 = GeneratedReport.objects.create(
			company=template.company,
			template=template,
			name="Старый отчёт",
		)
		r2 = GeneratedReport.objects.create(
			company=template.company,
			template=template,
			name="Новый отчёт",
		)
		reports = GeneratedReport.objects.all()
		assert list(reports)[:2] == [r2, r1]

	def test_str_representation(self, template):
		report = GeneratedReport.objects.create(
			company=template.company,
			template=template,
			name="Отчёт за 4 квартал 2025",
		)
		assert str(report) == "Отчёт за 4 квартал 2025"

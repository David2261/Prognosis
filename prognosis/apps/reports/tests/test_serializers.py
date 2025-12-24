import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from reports.models import ReportTemplate, GeneratedReport
from reports.serializers import ReportTemplateSerializer, GeneratedReportSerializer
from core.models import Scenario, TimePeriod

User = get_user_model()


@pytest.mark.django_db
class TestReportTemplateSerializer:
	@pytest.fixture
	def company(self):
		from accounts.models import Company
		return Company.objects.create(name="Test Company")

	@pytest.fixture
	def user(self):
		return User.objects.create_user(email='test@example.com', password='testpass123')

	def test_serialize_full_fields(self, company, user):
		template = ReportTemplate.objects.create(
			company=company,
			name="Отчёт о движении денежных средств",
			code="CASHFLOW-2025",
			report_type="cashflow",
			description="Ежемесячный cash flow",
			is_public=True,
			created_by=user,
			config={"some": "config"},
		)

		serializer = ReportTemplateSerializer(template)
		data = serializer.data

		assert data["id"] == template.id
		assert data["name"] == "Отчёт о движении денежных средств"
		assert data["code"] == "CASHFLOW-2025"
		assert data["report_type"] == "cashflow"
		assert data["description"] == "Ежемесячный cash flow"
		assert data["is_public"] is True
		assert data["config"] == {"some": "config"}
		assert data["slug"]
		assert data["company"] == company.id
		assert data["created_by"] == user.id
		assert "created_at" in data
		assert "updated_at" in data

	def test_create_with_minimal_data(self, company, user):
		data = {
			"name": "План-Факт",
			"code": "PLANFACT-01",
			"report_type": "plan_fact",
			"company": company.id,
		}

		serializer = ReportTemplateSerializer(data=data, context={"request": APIRequestFactory().get("/")})
		assert serializer.is_valid(), serializer.errors

		instance = serializer.save(created_by=user)
		assert instance.name == "План-Факт"
		assert instance.code == "PLANFACT-01"
		assert instance.report_type == "plan_fact"
		assert instance.slug is not None

	def test_slug_generated_on_create(self, company, user):
		data = {
			"name": "Отчёт о прибылях",
			"code": "PNL-TEST",
			"report_type": "pnl",
			"company": company.id,
		}

		serializer = ReportTemplateSerializer(data=data)
		serializer.is_valid(raise_exception=True)
		instance = serializer.save(created_by=user)

		assert instance.slug == "отчёт-о-прибылях"


@pytest.mark.django_db
class TestGeneratedReportSerializer:
	@pytest.fixture
	def company(self):
		from accounts.models import Company
		return Company.objects.create(name="Test Company")

	@pytest.fixture
	def user(self):
		return User.objects.create_user(email='test@example.com', password='testpass123')

	@pytest.fixture
	def template(self, company, user):
		return ReportTemplate.objects.create(
			company=company,
			name="P&L Monthly",
			code="PNL-MONTHLY",
			report_type="pnl",
			created_by=user
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

	def test_serialize_with_related_names(self, company, template, user):
		report = GeneratedReport.objects.create(
			company=company,
			template=template,
			name="P&L за июнь 2025",
			status="ready",
			created_by=user,
			scenario=None,
		)

		serializer = GeneratedReportSerializer(report)
		data = serializer.data

		assert data["id"] == report.id
		assert data["name"] == "P&L за июнь 2025"
		assert data["template"] == template.id
		assert data["template_name"] == "P&L Monthly"
		assert data["status"] == "ready"
		assert data["company"] == company.id
		assert data["created_by"] == user.id
		assert "created_at" in data
		assert "updated_at" in data
		assert data["scenario_name"] is None
		assert data["generated_file"] is None
		assert data["error_message"] == ""

	def test_read_only_fields_are_not_accepted_on_create(self, company, template, user):
		data = {
			"name": "Тестовый отчёт",
			"template": template.id,
			"status": "ready",
			"generated_file": "somefile.pdf",
			"error_message": "Ошибка",
			"company": company.id,
		}

		serializer = GeneratedReportSerializer(data=data)
		assert serializer.is_valid(), serializer.errors

		instance = serializer.save(created_by=user)

		assert instance.status == "pending"
		assert instance.generated_file.name is None
		assert instance.error_message == ""

	def test_scenario_name_when_present(self, company, template, user):
		from core.models import Scenario
		scenario = Scenario.objects.create(
			company=company,
			name="Бюджет 2025",
			type="budget",
		)

		report = GeneratedReport.objects.create(
			company=company,
			template=template,
			name="Бюджетный P&L",
			scenario=scenario,
			created_by=user,
		)

		serializer = GeneratedReportSerializer(report)
		assert serializer.data["scenario_name"] == "Бюджет 2025"

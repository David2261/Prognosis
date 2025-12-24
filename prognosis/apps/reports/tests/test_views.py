import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import Company
from core.models import Scenario, TimePeriod
from reports.models import ReportTemplate, GeneratedReport

User = get_user_model()


@pytest.mark.django_db
class TestReportTemplateViews:
	@pytest.fixture
	def company(self):
		return Company.objects.create(name="Test Company")

	@pytest.fixture
	def user(self, company):
		user = User.objects.create_user(email='test@example.com', password='testpass123')
		company.user_roles.create(user=user, role="admin")
		return user

	@pytest.fixture
	def auth_client(self, user):
		client = APIClient()
		client.force_authenticate(user=user)
		return client

	@pytest.fixture
	def template(self, company, user):
		return ReportTemplate.objects.create(
			company=company,
			name="P&L Monthly",
			code="PNL-MONTHLY",
			report_type="pnl",
			slug="pnl-monthly",
			created_by=user
		)

	def test_list_templates_returns_only_user_company(
		self, auth_client, template
	):
		url = reverse("reports:template-list-create")
		response = auth_client.get(url)

		assert response.status_code == 200
		assert len(response.data) == 1
		assert response.data[0]["name"] == "P&L Monthly"

	def test_create_template_sets_company_and_created_by(
		self, auth_client, user, company
	):
		url = reverse("reports:template-list-create")
		data = {
			"name": "Cash Flow",
			"code": "CF-TEST",
			"report_type": "cashflow",
			"description": "",
			"is_public": False,
			"company": company.id,
			"config": {}
		}

		response = auth_client.post(url, data, format="json")

		assert response.status_code == 201, response.json()

		template = ReportTemplate.objects.get(code="CF-TEST")
		assert template.created_by == user


@pytest.mark.django_db
class TestReportTemplateDetailView:
	@pytest.fixture
	def company(self):
		return Company.objects.create(name="Test Company")

	@pytest.fixture
	def user(self, company):
		user = User.objects.create_user(email='test@example.com', password='testpass123')
		company.user_roles.create(user=user, role="admin")
		return user

	@pytest.fixture
	def auth_client(self, user):
		client = APIClient()
		client.force_authenticate(user=user)
		return client

	@pytest.fixture
	def template(self, company, user):
		return ReportTemplate.objects.create(
			company=company,
			name="P&L Monthly",
			code="PNL-MONTHLY",
			report_type="pnl",
			slug="pnl-monthly",
			created_by=user
		)

	def test_get_template_detail(self, auth_client, template):
		url = reverse("reports:template-detail", args=[template.slug])
		response = auth_client.get(url)

		assert response.status_code == 200
		assert response.data["name"] == template.name

	def test_update_template(self, auth_client, template, company):
		url = reverse("reports:template-detail", args=[template.slug])
		response = auth_client.put(url, {
			"name": "Updated name",
			"code": template.code,
			"report_type": template.report_type,
			"company": company.id,
		})

		assert response.status_code == 200, response.json()
		template.refresh_from_db()
		assert template.name == "Updated name"


@pytest.mark.django_db
class TestGenerateReportView:
	@pytest.fixture
	def company(self):
		return Company.objects.create(name="Test Company")

	@pytest.fixture
	def user(self, company):
		user = User.objects.create_user(email='test@example.com', password='testpass123')
		company.user_roles.create(user=user, role="admin")
		return user

	@pytest.fixture
	def auth_client(self, user):
		client = APIClient()
		client.force_authenticate(user=user)
		return client

	@pytest.fixture
	def template(self, company, user):
		return ReportTemplate.objects.create(
			company=company,
			name="P&L Monthly",
			code="PNL-MONTHLY",
			report_type="pnl",
			slug="pnl-monthly",
			created_by=user
		)

	@pytest.fixture
	def period(self, company):
		return TimePeriod.objects.create(company=company, year=2025, month=6)

	@pytest.fixture
	def mocker(mocker):
		return mocker

	@pytest.fixture
	def scenario(self, company, period):
		return Scenario.objects.create(
			company=company,
			name="Факт июнь 2025",
			type="actual",
			start_period=period,
			end_period=period,
		)

	def test_generate_report_creates_pending_report(
		self, auth_client, template, scenario, period, mocker
	):
		# mocker.patch("reports.tasks.generate_report_task.delay")

		url = reverse("reports:generate-report")
		payload = {
			"slug": template.slug,
			"scenario_id": scenario.id,
			"start_period_id": period.id,
			"end_period_id": period.id,
			"name": "Мой отчёт P&L за июнь"
		}

		response = auth_client.post(url, payload, format="json")

		assert response.status_code == status.HTTP_202_ACCEPTED

		report = GeneratedReport.objects.get(template=template)
		assert report.status == "pending"
		assert report.name == "Мой отчёт P&L за июнь"

	def test_generate_report_without_slug_returns_400(
		self, auth_client
	):
		url = reverse("reports:generate-report")
		response = auth_client.post(url, {})

		assert response.status_code == 400
		assert "slug" in response.data["error"]

	def test_generate_report_duplicate_returns_409(
		self, auth_client, template, scenario, period, user
	):
		GeneratedReport.objects.create(
			company=template.company,
			template=template,
			scenario=scenario,
			start_period=period,
			end_period=period,
			status="pending",
			created_by=user,
		)

		url = reverse("reports:generate-report")
		response = auth_client.post(url, {
			"slug": template.slug,
			"scenario_id": scenario.id,
			"start_period_id": period.id,
			"end_period_id": period.id,
		})

		assert response.status_code == 409
		assert "уже генерируется" in response.data["warning"]

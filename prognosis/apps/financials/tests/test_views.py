# financials/tests/test_views.py
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Company
from core.models import Scenario, TimePeriod
from dimensions.models import BudgetArticle
from financials.models import FinancialLine

User = get_user_model()


@pytest.fixture
def api_client():
	return APIClient()


@pytest.fixture
def user_with_company():
	user = User.objects.create_user(email="finuser@example.com", password="testpass123")
	company = Company.objects.create(name="FinCo", inn="1234567890")
	company.user_roles.create(user=user, role="admin")
	return user, company


@pytest.fixture
def authenticated_client(api_client, user_with_company):
	user, _ = user_with_company
	api_client.force_authenticate(user=user)
	return api_client, user, user.company_roles.first().company


@pytest.mark.django_db
class TestFinancialLineAPI:
	def test_create_list_and_filters(self, authenticated_client):
		client, user, company = authenticated_client

		s1 = Scenario.objects.create(company=company, name="Budget 2026", type="budget")
		s2 = Scenario.objects.create(company=company, name="Actuals 2025", type="actual")
		p1 = TimePeriod.objects.create(company=company, year=2025, month=1)
		p2 = TimePeriod.objects.create(company=company, year=2025, month=2)
		a1 = BudgetArticle.add_root(company=company, code="RA", name="Revenue A")
		a2 = BudgetArticle.add_root(company=company, code="EX", name="Expense")

		create_url = reverse("financials:financialline-list-create")

		response = client.post(
			create_url,
			{
				"scenario": s1.slug,
				"period": p1.pk,
				"article": a1.slug,
				"amount": "1000.00",
			},
			format="json",
		)
		assert response.status_code == status.HTTP_201_CREATED
		assert Decimal(response.data["amount"]) == Decimal("1000.00")

		response = client.post(
			create_url,
			{
				"scenario": s2.slug,
				"period": p2.pk,
				"article": a2.slug,
				"amount": "2000.00",
			},
			format="json",
		)
		assert response.status_code == status.HTTP_201_CREATED

		response = client.get(create_url)
		assert response.status_code == status.HTTP_200_OK
		assert len(response.data) == 2

		response = client.get(create_url, {"scenario": s1.slug})
		assert response.status_code == status.HTTP_200_OK
		assert len(response.data) == 1
		assert response.data[0]["scenario"] == s1.slug

		response = client.get(create_url, {"period": "2025-02"})
		assert response.status_code == status.HTTP_200_OK
		assert len(response.data) == 1
		assert response.data[0]["period"] == p2.pk

		response = client.get(create_url, {"article": a1.slug})
		assert response.status_code == status.HTTP_200_OK
		assert len(response.data) == 1

		response = client.get(create_url, {"scenario": s2.slug, "period": "2025-02"})
		assert len(response.data) == 1

	def test_detail_update_delete(self, authenticated_client):
		client, user, company = authenticated_client

		s = Scenario.objects.create(company=company, name="Test Scenario", type="budget")
		p = TimePeriod.objects.create(company=company, year=2025, month=3)
		a = BudgetArticle.add_root(company=company, code="TEST", name="Test Article")

		fl = FinancialLine.objects.create(
			company=company,
			scenario=s,
			period=p,
			article=a,
			amount=Decimal("500.00"),
			comment="Initial"
		)

		detail_url = reverse("financials:financialline-detail", kwargs={"slug": fl.slug})

		response = client.get(detail_url)
		assert response.status_code == status.HTTP_200_OK
		assert response.data["amount"] == "500.00"
		assert response.data["slug"] == fl.slug

		update_data = {
			"scenario": s.slug,
			"period": p.pk,
			"article": a.slug,
			"amount": "999.99",
			"comment": "Updated via PUT"
		}
		response = client.put(detail_url, update_data, format="json")
		assert response.status_code == status.HTTP_200_OK
		assert response.data["amount"] == "999.99"
		assert response.data["comment"] == "Updated via PUT"

		# PATCH (частичное)
		response = client.patch(detail_url, {"amount": "1234.56"}, format="json")
		assert response.status_code == status.HTTP_200_OK
		assert response.data["amount"] == "1234.56"

		response = client.delete(detail_url)
		assert response.status_code == status.HTTP_204_NO_CONTENT
		assert not FinancialLine.objects.filter(slug=fl.slug).exists()

	def test_unique_constraint_via_api(self, authenticated_client):
		client, _, company = authenticated_client

		s = Scenario.objects.create(company=company, name="Duplicate Test", type="budget")
		p = TimePeriod.objects.create(company=company, year=2025, month=4)
		a = BudgetArticle.add_root(company=company, code="DUP", name="Duplicate Article")

		create_url = reverse("financials:financialline-list-create")
		data = {
			"scenario": s.slug,
			"period": p.pk,
			"article": a.slug,
			"amount": "100.00"
		}

		response = client.post(create_url, data, format="json")
		assert response.status_code == status.HTTP_201_CREATED

		response = client.post(create_url, data, format="json")
		assert response.status_code == status.HTTP_400_BAD_REQUEST
		assert "UNIQUE constraint failed" in str(response.data) or "уже существует" in str(response.data)

	def test_permission_denied_other_company(self, api_client, user_with_company):
		user, company = user_with_company
		api_client.force_authenticate(user=user)

		other_company = Company.objects.create(name="Other Co")
		other_scenario = Scenario.objects.create(company=other_company, name="Other", type="budget")
		other_period = TimePeriod.objects.create(company=other_company, year=2025, month=1)
		other_article = BudgetArticle.add_root(company=other_company, code="X", name="X")

		fl = FinancialLine.objects.create(
			company=other_company,
			scenario=other_scenario,
			period=other_period,
			article=other_article,
			amount=Decimal("999.00")
		)

		detail_url = reverse("financials:financialline-detail", kwargs={"slug": fl.slug})

		response = api_client.get(detail_url)
		assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN]

		list_url = reverse("financials:financialline-list-create")
		response = api_client.get(list_url)
		assert response.status_code == status.HTTP_200_OK
		assert len(response.data) == 0

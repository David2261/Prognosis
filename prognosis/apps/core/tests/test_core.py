from django.forms import ValidationError
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from core.models import Scenario, TimePeriod
from core.views import ScenarioDetailView
from accounts.models import Company

User = get_user_model()


@pytest.mark.django_db
class TestScenarioModel:
	def test_slug_generated_and_unique_within_company(self):
		company = Company.objects.create(name='CompA')
		s1 = Scenario.objects.create(name='Budget 2025', type='budget', company=company, version=1)
		s2 = Scenario.objects.create(name='Budget 2025', type='budget', company=company, version=2)
		assert s1.slug != ''
		assert s2.slug != ''
		assert s1.slug != s2.slug

	def test_unique_name_version_per_company(self):
		company = Company.objects.create(name='CompUnique')
		Scenario.objects.create(name='S', type='plan', version=1, company=company)
		with pytest.raises(Exception):
			Scenario.objects.create(name='S', type='plan', version=1, company=company)


@pytest.mark.django_db
class TestScenarioViews:
	def test_get_scenario_by_slug(self):
		user = User.objects.create_user(email='test@example.com', password='pass')
		company = Company.objects.create(name='CompB')
		company.user_roles.create(user=user, role='admin')
		s = Scenario.objects.create(name='Forecast', type='forecast', company=company)

		factory = APIRequestFactory()
		request = factory.get(f'/v1/scenarios/{s.slug}/')
		force_authenticate(request, user=user)
		view = ScenarioDetailView.as_view()
		response = view(request, slug=s.slug)
		assert response.status_code == 200
		assert response.data['slug'] == s.slug


@pytest.mark.django_db
class TestTimePeriodModel:
	def test_month_without_quarter_auto_fills_quarter(self):
		company = Company.objects.create(name='CP')
		tp = TimePeriod(company=company, year=2025, month=3)
		tp.full_clean()
		tp.save()
		assert tp.quarter == 1  # март → Q1

	def test_month_with_correct_quarter_passes(self):
		company = Company.objects.create(name='CP')
		tp = TimePeriod(company=company, year=2025, month=6, quarter=2)
		tp.full_clean()
		tp.save()
		assert tp.quarter == 2

	def test_month_with_incorrect_quarter_raises(self):
		company = Company.objects.create(name='CP')
		tp = TimePeriod(company=company, year=2025, month=3, quarter=2)
		with pytest.raises(ValidationError) as exc_info:
			tp.full_clean()
			tp.save()
		assert 'Квартал не соответствует указанному месяцу' in str(exc_info.value)

	def test_quarter_without_month_passes(self):
		company = Company.objects.create(name='CP')
		tp = TimePeriod(company=company, year=2025, quarter=3)
		tp.full_clean()
		tp.save()
		assert tp.month is None

	def test_only_year_passes(self):
		company = Company.objects.create(name='CP')
		tp = TimePeriod(company=company, year=2025)
		tp.full_clean()
		tp.save()
		assert tp.quarter is None
		assert tp.month is None

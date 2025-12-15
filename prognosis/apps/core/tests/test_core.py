import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.core.models import Scenario, TimePeriod
from apps.core.views import ScenarioDetailView
from apps.accounts.models import Company

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
    def test_month_without_quarter_raises(self):
        company = Company.objects.create(name='CP')
        tp = TimePeriod(company=company, year=2025, month=3)
        with pytest.raises(Exception):
            tp.full_clean()

    def test_quarter_month_mismatch_raises(self):
        company = Company.objects.create(name='CP2')
        tp = TimePeriod(company=company, year=2025, month=2, quarter=2)
        with pytest.raises(Exception):
            tp.full_clean()

    def test_timeperiod_list_view(self):
        user = User.objects.create_user(email='tpuser@example.com', password='pass')
        company = Company.objects.create(name='TPComp')
        company.user_roles.create(user=user, role='admin')
        TimePeriod.objects.create(company=company, year=2025, month=1, quarter=1)

        factory = APIRequestFactory()
        request = factory.get('/v1/time-periods/')
        force_authenticate(request, user=user)
        from apps.core.views import TimePeriodListView
        view = TimePeriodListView.as_view()
        response = view(request)
        assert response.status_code == 200
        assert isinstance(response.data, list)

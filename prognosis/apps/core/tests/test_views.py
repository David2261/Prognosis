import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.core.models import Scenario, TimePeriod
from apps.core.views import ScenarioListCreateView, ScenarioDetailView, TimePeriodListView
from apps.accounts.models import Company

User = get_user_model()


@pytest.mark.django_db
class TestScenarioViews:
    def test_list_and_active_filter(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        c = Company.objects.create(name='Comp1')
        c.user_roles.create(user=user, role='admin')
        Scenario.objects.create(name='A', type='budget', company=c, is_active=True)
        Scenario.objects.create(name='B', type='budget', company=c, is_active=False)

        factory = APIRequestFactory()
        request = factory.get('/v1/scenarios/')
        force_authenticate(request, user=user)
        view = ScenarioListCreateView.as_view()
        response = view(request)
        assert response.status_code == 200
        assert isinstance(response.data, list)

        # active filter
        request = factory.get('/v1/scenarios/?active=true')
        force_authenticate(request, user=user)
        response = view(request)
        assert all(item['is_active'] for item in response.data)

    def test_get_scenario_by_slug(self):
        user = User.objects.create_user(email='test2@example.com', password='pass')
        c = Company.objects.create(name='CompB')
        c.user_roles.create(user=user, role='admin')
        s = Scenario.objects.create(name='Forecast', type='forecast', company=c)

        factory = APIRequestFactory()
        request = factory.get(f'/v1/scenarios/{s.slug}/')
        force_authenticate(request, user=user)
        view = ScenarioDetailView.as_view()
        response = view(request, slug=s.slug)
        assert response.status_code == 200
        assert response.data['slug'] == s.slug


@pytest.mark.django_db
class TestTimePeriodViews:
    def test_list_periods(self):
        user = User.objects.create_user(email='tpuser@example.com', password='pass')
        c = Company.objects.create(name='TPComp')
        c.user_roles.create(user=user, role='admin')
        TimePeriod.objects.create(company=c, year=2025, month=1, quarter=1)

        factory = APIRequestFactory()
        request = factory.get('/v1/time-periods/')
        force_authenticate(request, user=user)
        view = TimePeriodListView.as_view()
        response = view(request)
        assert response.status_code == 200
        assert isinstance(response.data, list)

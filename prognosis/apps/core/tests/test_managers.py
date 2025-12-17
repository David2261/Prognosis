import pytest
from core.managers import ActiveScenarioManager, OpenPeriodManager
from core.models import Scenario, TimePeriod
from accounts.models import Company


@pytest.mark.django_db
class TestCoreManagers:
    def test_active_scenario_manager_returns_only_active(self):
        c = Company.objects.create(name='M')
        Scenario.objects.create(name='A', type='budget', company=c, is_active=True)
        Scenario.objects.create(name='B', type='budget', company=c, is_active=False)

        mgr = ActiveScenarioManager()
        mgr.model = Scenario
        qs = mgr.get_queryset().filter(company=c)
        assert qs.count() == 1
        assert all(s.is_active for s in qs)

    def test_open_period_manager_returns_only_open(self):
        c = Company.objects.create(name='P')
        TimePeriod.objects.create(company=c, year=2025, month=1, quarter=1, is_closed=False)
        TimePeriod.objects.create(company=c, year=2025, month=2, quarter=1, is_closed=True)

        mgrp = OpenPeriodManager()
        mgrp.model = TimePeriod
        qs = mgrp.get_queryset().filter(company=c)
        assert qs.count() == 1
        assert all(not p.is_closed for p in qs)

    def test_managers_support_chaining(self):
        c = Company.objects.create(name='Chain')
        Scenario.objects.create(name='X', type='budget', company=c, is_active=True)
        Scenario.objects.create(name='Y', type='forecast', company=c, is_active=True)

        mgr = ActiveScenarioManager()
        mgr.model = Scenario
        qs = mgr.get_queryset().filter(type='budget')
        assert qs.count() == 1

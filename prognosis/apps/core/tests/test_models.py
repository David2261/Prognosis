import pytest
from apps.core.models import TimePeriod, Scenario
from apps.accounts.models import Company


@pytest.mark.django_db
class TestTimePeriodModel:
    def test_month_requires_quarter(self):
        c = Company.objects.create(name='TCo')
        tp = TimePeriod(company=c, year=2025, month=3)
        with pytest.raises(Exception):
            tp.full_clean()

    def test_quarter_month_consistency(self):
        c = Company.objects.create(name='TCo2')
        tp = TimePeriod(company=c, year=2025, month=2, quarter=2)
        with pytest.raises(Exception):
            tp.full_clean()


@pytest.mark.django_db
class TestScenarioModel:
    def test_slug_generated_and_unique_within_company(self):
        c = Company.objects.create(name='CompA')
        s1 = Scenario.objects.create(name='Budget 2025', type='budget', company=c, version=1)
        s2 = Scenario.objects.create(name='Budget 2025', type='budget', company=c, version=2)
        assert s1.slug and s2.slug
        assert s1.slug != s2.slug

    def test_unique_name_version_per_company(self):
        c = Company.objects.create(name='CompUnique')
        Scenario.objects.create(name='S', type='plan', version=1, company=c)
        with pytest.raises(Exception):
            Scenario.objects.create(name='S', type='plan', version=1, company=c)

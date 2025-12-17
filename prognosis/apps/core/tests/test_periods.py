import pytest
from apps.core.periods import generate_periods_for_year
from apps.accounts.models import Company
from apps.core.models import TimePeriod


@pytest.mark.django_db
def test_generate_periods_creates_year_quarters_months():
	c = Company.objects.create(name='GenCo')
	created = generate_periods_for_year(c, 2025)
	# 1 year + 4 quarters + 12 months = 17
	assert len(created) == 17
	assert TimePeriod.objects.filter(company=c, year=2025).count() == 17


@pytest.mark.django_db
def test_generate_periods_idempotent():
	c = Company.objects.create(name='GenCo2')
	created1 = generate_periods_for_year(c, 2026)
	created2 = generate_periods_for_year(c, 2026)
	assert len(created1) == 17
	assert len(created2) == 0
	assert TimePeriod.objects.filter(company=c, year=2026).count() == 17

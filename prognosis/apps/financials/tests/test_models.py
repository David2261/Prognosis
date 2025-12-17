import pytest
from django.forms import ValidationError

from accounts.models import Company
from core.models import Scenario, TimePeriod
from dimensions.models import BudgetArticle
from financials.models import FinancialLine


@pytest.mark.django_db
def test_financialline_save_prevents_duplicate():
	company = Company.objects.create(name="ModelCo")
	scenario = Scenario.objects.create(
		company=company,
		name="S1",
		type="budget"
	)
	period = TimePeriod.objects.create(
		company=company,
		year=2025,
		month=1
	)
	article = BudgetArticle.add_root(
		company=company,
		code="A1",
		name="Article"
	)

	FinancialLine.objects.create(
		company=company,
		scenario=scenario,
		period=period,
		article=article,
		amount="100.00"
	)

	duplicate = FinancialLine(
		company=company,
		scenario=scenario,
		period=period,
		article=article,
		amount="50.00"
	)

	with pytest.raises(ValidationError):
		duplicate.save()

	count = FinancialLine.objects.filter(
		company=company,
		scenario=scenario,
		period=period,
		article=article
	).count()

	assert count == 1

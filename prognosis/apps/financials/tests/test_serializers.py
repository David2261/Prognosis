import pytest
from rest_framework.test import APIRequestFactory
from django.contrib.auth import get_user_model

from accounts.models import Company
from core.models import Scenario, TimePeriod
from dimensions.models import BudgetArticle
from financials.serializers import FinancialLineSerializer

User = get_user_model()


@pytest.mark.django_db
def test_financialline_serializer_accepts_slugs_and_scopes():
    user = User.objects.create_user(email='seruser@example.com', password='pass')
    company = Company.objects.create(name='SerCo')
    company.user_roles.create(user=user, role='admin')

    scenario = Scenario.objects.create(company=company, name='Budget 2026', type='budget')
    period = TimePeriod.objects.create(company=company, year=2025, month=1)
    article = BudgetArticle.add_root(company=company, code='RA', name='Revenue')

    factory = APIRequestFactory()
    request = factory.post('/v1/lines/', {})
    request.user = user

    data = {'scenario': scenario.slug, 'period': period.id, 'article': article.slug, 'amount': '10.00'}
    serializer = FinancialLineSerializer(data=data, context={'request': request})
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save(company=company)
    assert instance.company == company
    assert instance.amount == 10

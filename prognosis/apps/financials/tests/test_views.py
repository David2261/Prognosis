import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from django.core.exceptions import ValidationError

from accounts.models import Company
from core.models import Scenario, TimePeriod
from dimensions.models import BudgetArticle
from financials.models import FinancialLine
from financials.views import FinancialLineListCreateView, FinancialLineDetailView

User = get_user_model()


@pytest.fixture
def auth_client_factory():
	factory = APIRequestFactory()

	def _make_request(user, method, url, data=None, **kwargs):
		request = getattr(factory, method)(url, data or {}, **kwargs)
		force_authenticate(request, user=user)
		return request

	return _make_request


@pytest.fixture
def setup_user_company():
	user = User.objects.create_user(email='finuser@example.com', password='pass')
	company = Company.objects.create(name='FinCo')
	company.user_roles.create(user=user, role='admin')
	return user, company


@pytest.mark.django_db
class TestFinancialViews:
	def test_create_list_and_filters(self, setup_user_company, auth_client_factory):
		user, company = setup_user_company

		s1 = Scenario.objects.create(company=company, name='Budget 2026', type='budget', slug='budget-2026')
		s2 = Scenario.objects.create(company=company, name='Actuals', type='actual', slug='actuals')
		p1 = TimePeriod.objects.create(company=company, year=2025, month=1)
		p2 = TimePeriod.objects.create(company=company, year=2025, month=2)
		a1 = BudgetArticle.add_root(company=company, code='RA', name='Revenue')
		a2 = BudgetArticle.add_root(company=company, code='EX', name='Expense')

		# Создаём две строки
		create_url = reverse('financials:financialline-list-create')

		data1 = {
			'scenario': s1.slug,
			'period': p1.pk,           # ← PrimaryKeyRelatedField
			'article': a1.slug,
			'amount': '100.00',
			# Опциональные поля не передаём — благодаря default=None они будут None
		}
		request = auth_client_factory(user, 'post', create_url, data=data1, format='json')
		response = FinancialLineListCreateView.as_view()(request)
		assert response.status_code == status.HTTP_201_CREATED

		data2 = {
			'scenario': s2.slug,
			'period': p2.pk,
			'article': a2.slug,
			'amount': '200.00'
		}
		request = auth_client_factory(user, 'post', create_url, data=data2, format='json')
		response = FinancialLineListCreateView.as_view()(request)
		assert response.status_code == status.HTTP_201_CREATED

		# Список всех
		request = auth_client_factory(user, 'get', create_url)
		response = FinancialLineListCreateView.as_view()(request)
		assert response.status_code == status.HTTP_200_OK
		assert len(response.data) == 2

		# Фильтр по scenario (slug)
		request = auth_client_factory(user, 'get', f"{create_url}?scenario={s1.slug}")
		response = FinancialLineListCreateView.as_view()(request)
		assert len(response.data) == 1

		# Фильтр по period (YYYY-MM)
		period_str = f"{p2.year}-{p2.month:02d}"
		request = auth_client_factory(user, 'get', f"{create_url}?period={period_str}")
		response = FinancialLineListCreateView.as_view()(request)
		assert len(response.data) == 1

		# Фильтр по article (slug)
		request = auth_client_factory(user, 'get', f"{create_url}?article={a1.slug}")
		response = FinancialLineListCreateView.as_view()(request)
		assert len(response.data) == 1

	def test_detail_update_delete_and_permissions(self, setup_user_company, auth_client_factory):
		user, company = setup_user_company
		user.refresh_from_db()

		s = Scenario.objects.create(company=company, name='Budget 2026', type='budget')
		p = TimePeriod.objects.create(company=company, year=2025, month=1)
		a = BudgetArticle.add_root(company=company, code='RA', name='Revenue')

		fl = FinancialLine.objects.create(
			company=company,
			scenario=s,
			period=p,
			article=a,
			amount='500.00'
		)

		detail_url = reverse('financials:financialline-detail', kwargs={'pk': fl.pk})
		factory = APIRequestFactory()

		# Неавторизованный доступ — 401
		request = factory.get(detail_url)
		response = FinancialLineDetailView.as_view()(request, pk=fl.pk)
		assert response.status_code == status.HTTP_401_UNAUTHORIZED

		# GET (авторизованный)
		request = auth_client_factory(user, 'get', detail_url)
		response = FinancialLineDetailView.as_view()(request, pk=fl.pk)
		assert response.status_code == status.HTTP_200_OK
		assert response.data['id'] == fl.pk

		# PUT (полная замена)
		update_data = {
			'scenario': s.slug,
			'period': p.pk,
			'article': a.slug,
			'amount': '600.00',
			'cost_center': None,
			'department': None,
			'project': None,
			'account': None,
		}
		request = auth_client_factory(user, 'put', detail_url, data=update_data, format='json')
		response = FinancialLineDetailView.as_view()(request, pk=fl.pk)
		print(response.data)
		assert response.status_code == status.HTTP_200_OK
		assert response.data['amount'] == '600.00'

		# PATCH (частичное обновление)
		request = auth_client_factory(user, 'patch', detail_url, data={'amount': '700.00'}, format='json')
		response = FinancialLineDetailView.as_view()(request, pk=fl.pk)
		assert response.status_code == status.HTTP_200_OK
		assert response.data['amount'] == '700.00'

		# DELETE
		request = auth_client_factory(user, 'delete', detail_url)
		response = FinancialLineDetailView.as_view()(request, pk=fl.pk)
		assert response.status_code == status.HTTP_204_NO_CONTENT
		assert not FinancialLine.objects.filter(pk=fl.pk).exists()

	def test_unique_constraint_via_api(self, setup_user_company, auth_client_factory):
		"""Проверяем уникальность через API (лучше, чем напрямую через модель)"""
		user, company = setup_user_company

		s = Scenario.objects.create(company=company, name='Budget 2026', type='budget')
		p = TimePeriod.objects.create(company=company, year=2025, month=1)
		a = BudgetArticle.add_root(company=company, code='RA', name='Revenue')

		create_url = reverse('financials:financialline-list-create')

		data = {
			'scenario': s.slug,
			'period': p.pk,
			'article': a.slug,
			'amount': '100.00'
		}

		request = auth_client_factory(user, 'post', create_url, data=data, format='json')
		response = FinancialLineListCreateView.as_view()(request)
		assert response.status_code == status.HTTP_201_CREATED

		# Попытка создать дубликат — должна вернуть 400
		request = auth_client_factory(user, "post", create_url, data=data, format="json")
		with pytest.raises(ValidationError):
			FinancialLineListCreateView.as_view()(request)

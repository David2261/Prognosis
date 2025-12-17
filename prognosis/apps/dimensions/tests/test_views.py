import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.accounts.models import Company
from apps.dimensions.models import ChartOfAccounts, CostCenter, Department, Project
from apps.dimensions.views import (
	ChartOfAccountsListCreateView, ChartOfAccountsDetailView,
	BudgetArticleListCreateView, BudgetArticleDetailView,
	CostCenterDetailView, DepartmentDetailView,
	ProjectDetailView,
)

User = get_user_model()


@pytest.mark.django_db
class TestDimensionViews:
	def setup_comp_user(self):
		user = User.objects.create_user(email='dimuser@example.com', password='pass')
		company = Company.objects.create(name='DimCo')
		company.user_roles.create(user=user, role='admin')
		return user, company

	def test_chart_of_accounts_list_and_detail(self):
		user, company = self.setup_comp_user()
		coa = ChartOfAccounts.objects.create(company=company, code='100', name='Cash')

		factory = APIRequestFactory()
		request = factory.get('/v1/chart-of-accounts/')
		force_authenticate(request, user=user)
		view = ChartOfAccountsListCreateView.as_view()
		resp = view(request)
		assert resp.status_code == 200

		request = factory.get(f'/v1/chart-of-accounts/{coa.slug}/')
		force_authenticate(request, user=user)
		view = ChartOfAccountsDetailView.as_view()
		resp = view(request, slug=coa.slug)
		assert resp.status_code == 200
		assert resp.data['slug'] == coa.slug

	def test_budget_article_create_and_detail(self):
		user, company = self.setup_comp_user()
		factory = APIRequestFactory()
		data = {'code': 'RA', 'name': 'Revenue', 'article_type': 'revenue'}
		request = factory.post('/v1/budget-articles/', data, format='json')
		force_authenticate(request, user=user)
		view = BudgetArticleListCreateView.as_view()
		resp = view(request)
		assert resp.status_code == 201
		slug = resp.data['slug']

		# detail
		request = factory.get(f'/v1/budget-articles/{slug}/')
		force_authenticate(request, user=user)
		view = BudgetArticleDetailView.as_view()
		resp = view(request, slug=slug)
		assert resp.status_code == 200
		assert resp.data['slug'] == slug

	def test_costcenter_department_project_endpoints(self):
		user, company = self.setup_comp_user()
		cc = CostCenter.objects.create(company=company, code='CC1', name='Main')
		p = Project.objects.create(company=company, code='P1', name='Proj')
		d = Department.add_root(company=company, code='D1', name='Dept')

		factory = APIRequestFactory()
		# cost center detail
		request = factory.get(f'/v1/cost-centers/{cc.slug}/')
		force_authenticate(request, user=user)
		resp = CostCenterDetailView.as_view()(request, slug=cc.slug)
		assert resp.status_code == 200

		# department detail
		request = factory.get(f'/v1/departments/{d.slug}/')
		force_authenticate(request, user=user)
		resp = DepartmentDetailView.as_view()(request, slug=d.slug)
		assert resp.status_code == 200

		# project detail
		request = factory.get(f'/v1/projects/{p.slug}/')
		force_authenticate(request, user=user)
		resp = ProjectDetailView.as_view()(request, slug=p.slug)
		assert resp.status_code == 200

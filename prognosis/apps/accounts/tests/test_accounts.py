import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.accounts.models import Company
from apps.accounts.views import CompanyListCreateView, CompanyDetailView, CompanyRolesListView

User = get_user_model()


@pytest.mark.django_db
class TestCompanyModel:
    def test_slug_generated_and_unique(self):
        c1 = Company.objects.create(name='My Company')
        c2 = Company.objects.create(name='My Company')
        assert c1.slug != ''
        assert c2.slug != ''
        assert c1.slug != c2.slug

    def test_fiscal_year_start_default(self):
        c = Company.objects.create(name='FyTest')
        import datetime
        today = datetime.date.today()
        assert c.fiscal_year_start == datetime.date(today.year, 1, 1)

    def test_str_and_indexes(self):
        c = Company.objects.create(name='StrCo')
        assert str(c) == 'StrCo'


class TestUserCompanyRoleModel:
    @pytest.mark.django_db
    def test_unique_user_company(self):
        user = User.objects.create_user(email='u1@example.com', password='p')
        company = Company.objects.create(name='UC1')
        UserCompanyRole = company.user_roles.model
        UserCompanyRole.objects.create(user=user, company=company, role='admin')
        with pytest.raises(Exception):
            UserCompanyRole.objects.create(user=user, company=company, role='viewer')


@pytest.mark.django_db
class TestCompanyViews:
    def test_create_company_allows_unauthenticated(self):
        factory = APIRequestFactory()
        request = factory.post('/v1/registration/', {'name': 'NewCo'}, format='json')
        view = CompanyListCreateView.as_view()
        response = view(request)
        assert response.status_code == 201
        assert 'slug' in response.data

    def test_get_company_detail_by_slug(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        company = Company.objects.create(name='C1')
        # attach role
        company.user_roles.create(user=user, role='admin')

        factory = APIRequestFactory()
        request = factory.get(f'/v1/companies/{company.slug}/')
        force_authenticate(request, user=user)
        view = CompanyDetailView.as_view()
        response = view(request, slug=company.slug)
        assert response.status_code == 200
        assert response.data['slug'] == company.slug

    def test_company_roles_list(self):
        user = User.objects.create_user(email='test2@example.com', password='pass')
        company = Company.objects.create(name='C2')
        company.user_roles.create(user=user, role='viewer')

        factory = APIRequestFactory()
        request = factory.get(f'/v1/companies/{company.slug}/roles/')
        force_authenticate(request, user=user)
        view = CompanyRolesListView.as_view()
        response = view(request, company_slug=company.slug)
        assert response.status_code == 200
        assert isinstance(response.data, list)

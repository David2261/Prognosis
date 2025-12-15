import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.accounts.models import Company
from apps.accounts.views import CompanyListCreateView, CompanyDetailView, CompanyRolesListView

User = get_user_model()


@pytest.mark.django_db
class TestCompanyViews:
    def test_registration_allows_unauthenticated_post(self):
        factory = APIRequestFactory()
        request = factory.post('/v1/registration/', {'name': 'NewCo'}, format='json')
        view = CompanyListCreateView.as_view()
        response = view(request)
        assert response.status_code == 201
        assert 'slug' in response.data

    def test_create_assigns_creator_admin_if_authenticated(self):
        user = User.objects.create_user(email='creator@example.com', password='pass')
        factory = APIRequestFactory()
        request = factory.post('/v1/registration/', {'name': 'OwnCo'}, format='json')
        force_authenticate(request, user=user)
        view = CompanyListCreateView.as_view()
        resp = view(request)
        assert resp.status_code == 201
        created = Company.objects.get(slug=resp.data['slug'])
        # creator should have a role
        assert created.user_roles.filter(user=user, role='admin').exists()

    def test_company_detail_and_patch_and_delete(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        company = Company.objects.create(name='C1')
        company.user_roles.create(user=user, role='admin')

        factory = APIRequestFactory()
        request = factory.get(f'/v1/companies/{company.slug}/')
        force_authenticate(request, user=user)
        view = CompanyDetailView.as_view()
        response = view(request, slug=company.slug)
        assert response.status_code == 200

        # patch
        request = factory.patch(f'/v1/companies/{company.slug}/', {'name': 'C1x'}, format='json')
        force_authenticate(request, user=user)
        response = view(request, slug=company.slug)
        assert response.status_code in (200, 204, 201)

        # delete (soft)
        request = factory.delete(f'/v1/companies/{company.slug}/')
        force_authenticate(request, user=user)
        response = view(request, slug=company.slug)
        assert response.status_code in (204, 200)

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

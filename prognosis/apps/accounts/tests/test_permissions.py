import pytest
from types import SimpleNamespace
from django.contrib.auth import get_user_model
from accounts.models import Company
from accounts.permissions import IsInCompany

User = get_user_model()


@pytest.mark.django_db
class TestIsInCompanyPermission:
    def test_allows_if_user_in_company_via_company_obj(self):
        user = User.objects.create_user(email='inco@example.com', password='p')
        company = Company.objects.create(name='Co1')
        company.user_roles.create(user=user, role='admin')

        obj = SimpleNamespace(company=company)
        perm = IsInCompany()
        request = SimpleNamespace(user=user)

        assert perm.has_object_permission(request, None, obj) is True

    def test_denies_if_user_not_in_company_via_company_obj(self):
        user = User.objects.create_user(email='other@example.com', password='p')
        company = Company.objects.create(name='Co2')

        obj = SimpleNamespace(company=company)
        perm = IsInCompany()
        request = SimpleNamespace(user=user)

        assert perm.has_object_permission(request, None, obj) is False

    def test_allows_if_user_in_company_via_company_id(self):
        user = User.objects.create_user(email='idco@example.com', password='p')
        company = Company.objects.create(name='Co3')
        company.user_roles.create(user=user, role='admin')

        # ensure Company.active exists for lookup
        Company.active = Company.objects

        obj = SimpleNamespace(company_id=company.id)
        perm = IsInCompany()
        request = SimpleNamespace(user=user)

        assert perm.has_object_permission(request, None, obj) is True

    def test_denies_when_object_has_no_company_info(self):
        user = User.objects.create_user(email='noco@example.com', password='p')
        obj = SimpleNamespace()  # no company or company_id
        perm = IsInCompany()
        request = SimpleNamespace(user=user)

        assert perm.has_object_permission(request, None, obj) is False

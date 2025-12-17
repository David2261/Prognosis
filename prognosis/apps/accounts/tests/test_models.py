import datetime

import pytest
from accounts.models import Company, UserCompanyRole


@pytest.mark.django_db
class TestCompanyModel:
    def test_create_company(self):
        c = Company.objects.create(name="Acme")
        assert c.name == "Acme"
        assert c.slug

    def test_fiscal_year_start_default(self):
        c = Company.objects.create(name="FyTest")
        today = datetime.date.today()
        assert c.fiscal_year_start == datetime.date(today.year, 1, 1)

    def test_str(self):
        c = Company.objects.create(name="HelloCo")
        assert str(c) == "HelloCo"


@pytest.mark.django_db
class TestUserCompanyRoleModel:
    def test_role_unique_per_user_company(self):
        # create minimal user model via get_user_model in calling tests
        from django.contrib.auth import get_user_model

        User = get_user_model()
        u = User.objects.create_user(email="u@example.com", password="p")
        c = Company.objects.create(name="C1")
        UserCompanyRole.objects.create(user=u, company=c, role="admin")
        with pytest.raises(Exception):
            UserCompanyRole.objects.create(user=u, company=c, role="viewer")

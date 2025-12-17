import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from accounts.models import Company
from dimensions.models import ChartOfAccounts, BudgetArticle, CostCenter, Department, Project

User = get_user_model()


@pytest.fixture
def admin_client():
    admin = User.objects.create_superuser(email='admin@example.com', password='adminpass')
    client = Client()
    client.force_login(admin)
    return client


@pytest.mark.django_db
class TestDimensionsAdmin:
    def test_chartofaccounts_unfold_view(self, admin_client):
        c = Company.objects.create(name='DCo')
        ChartOfAccounts.objects.create(company=c, code='100', name='Cash')
        url = '/admin/dimensions/chartofaccounts/unfold/'
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_budgetarticle_unfold_view(self, admin_client):
        c = Company.objects.create(name='DCo2')
        BudgetArticle.add_root(company=c, code='R1', name='Rev')
        url = '/admin/dimensions/budgetarticle/unfold/'
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_costcenter_unfold_view(self, admin_client):
        c = Company.objects.create(name='DCo3')
        CostCenter.objects.create(company=c, code='CC1', name='Main')
        url = '/admin/dimensions/costcenter/unfold/'
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_department_unfold_view(self, admin_client):
        c = Company.objects.create(name='DCo4')
        Department.add_root(company=c, code='D1', name='Dept')
        url = '/admin/dimensions/department/unfold/'
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_project_unfold_view(self, admin_client):
        c = Company.objects.create(name='DCo5')
        Project.objects.create(company=c, code='P1', name='Prj')
        url = '/admin/dimensions/project/unfold/'
        resp = admin_client.get(url)
        assert resp.status_code == 200

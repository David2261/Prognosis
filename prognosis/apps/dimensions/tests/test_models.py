import pytest
from django.contrib.auth import get_user_model
from accounts.models import Company
from dimensions.models import ChartOfAccounts, BudgetArticle, CostCenter, Department, Project

User = get_user_model()


@pytest.mark.django_db
class TestDimensionModels:
    def test_chart_of_accounts_slug_and_unique_within_company(self):
        c = Company.objects.create(name='CompX')
        coa1 = ChartOfAccounts.objects.create(company=c, code='100', name='Cash')
        coa2 = ChartOfAccounts.objects.create(company=c, code='200', name='Cash')
        assert coa1.slug
        assert coa2.slug
        assert coa1.slug != coa2.slug

    def test_budget_article_add_root_and_slug(self):
        c = Company.objects.create(name='CompY')
        ba = BudgetArticle.add_root(company=c, code='R1', name='Revenue')
        assert ba.slug
        # adding same name in same company should produce unique slug
        ba2 = BudgetArticle.add_root(company=c, code='R2', name='Revenue')
        assert ba2.slug != ba.slug

    def test_costcenter_and_project_slug(self):
        c = Company.objects.create(name='CompZ')
        cc = CostCenter.objects.create(company=c, code='CC1', name='Main')
        p = Project.objects.create(company=c, code='P1', name='ProjectX')
        assert cc.slug
        assert p.slug

    def test_department_slug(self):
        c = Company.objects.create(name='CompD')
        d = Department.add_root(company=c, code='D1', name='Dept')
        assert d.slug

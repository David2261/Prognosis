import pytest
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model

from accounts.models import Company, UserCompanyRole
from core.models import Scenario
from data_ingestion.models import ImportTask
from data_ingestion.admin import ImportTaskAdmin


@pytest.mark.django_db
class TestImportTaskAdmin:
    def setup_method(self):
        self.site = AdminSite()
        self.admin = ImportTaskAdmin(ImportTask, self.site)
        self.rf = RequestFactory()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(email="admin@example.com", password="p")
        self.company1 = Company.objects.create(name="C1")
        self.company2 = Company.objects.create(name="C2")
        UserCompanyRole.objects.create(user=self.user, company=self.company1, role="admin")
        self.request = self.rf.get("/")
        self.request.user = self.user

    def test_company_queryset_limited_to_user_companies(self):
        formfield = self.admin.formfield_for_foreignkey(ImportTask._meta.get_field("company"), self.request)
        qs = formfield.queryset
        assert list(qs) == [self.company1]

    def test_save_model_sets_created_by_status_and_file_type(self):
        scenario = Scenario.objects.create(company=self.company1, name="B2025", type="budget", version=1)
        obj = ImportTask(company=self.company1, scenario=scenario)
        obj.file.save("import.xlsx", ContentFile(b""), save=False)
        self.admin.save_model(self.request, obj, form=None, change=False)
        assert obj.created_by == self.user
        assert obj.status == "pending"
        assert obj.file_type == "excel"
        assert obj.company == self.company1

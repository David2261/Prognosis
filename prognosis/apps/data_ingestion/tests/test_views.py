import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from accounts.models import Company, UserCompanyRole
from core.models import Scenario
from data_ingestion.models import ImportTask


@pytest.mark.django_db
class TestImportTaskViews:
    def setup_method(self):
        self.client = APIClient()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(email="u@example.com", password="p")
        self.client.force_authenticate(user=self.user)
        self.company1 = Company.objects.create(name="C1")
        self.company2 = Company.objects.create(name="C2")
        UserCompanyRole.objects.create(user=self.user, company=self.company1, role="admin")
        UserCompanyRole.objects.create(user=self.user, company=self.company2, role="viewer")
        self.scenario1 = Scenario.objects.create(company=self.company1, name="B2025", type="budget", version=1)

    def test_post_creates_task_and_triggers_processing(self, monkeypatch):
        called = {"delay": False, "id": None}

        from data_ingestion import views as ingestion_views

        def fake_delay(task_id):
            called["delay"] = True
            called["id"] = task_id

        monkeypatch.setattr(ingestion_views.process_import_task, "delay", fake_delay)

        file = SimpleUploadedFile("data.xlsx", b"binary", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        url = reverse("data_ingestion:import-list-create")
        resp = self.client.post(url, {"file": file, "scenario": self.scenario1.id}, format="multipart")
        assert resp.status_code == 201, resp.data
        assert called["delay"] is True
        data = resp.data
        task = ImportTask.objects.get(id=data["id"])
        assert task.file_type == "excel"
        assert task.slug

    def test_get_list_returns_user_tasks(self):
        ImportTask.objects.create(company=self.company1, scenario=self.scenario1, created_by=self.user)
        ImportTask.objects.create(company=self.company2, scenario=Scenario.objects.create(company=self.company2, name="B2026", type="budget", version=1), created_by=self.user)
        url = reverse("data_ingestion:import-list-create")
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert len(resp.data) == 2

    def test_get_detail_by_slug(self):
        task = ImportTask.objects.create(company=self.company1, scenario=self.scenario1, created_by=self.user)
        url = reverse("data_ingestion:import-detail", kwargs={"slug": task.slug})
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp.data["slug"] == task.slug

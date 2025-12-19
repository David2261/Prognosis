import pytest
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model

from accounts.models import Company
from core.models import Scenario
from data_ingestion.models import ImportTask


@pytest.mark.django_db
class TestImportTaskModel:
    def setup_method(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(email="u@example.com", password="p")
        self.company = Company.objects.create(name="C1")
        self.scenario = Scenario.objects.create(
            company=self.company,
            name="Budget 2025",
            type="budget",
            version=1,
        )

    def test_slug_generated_on_save(self):
        task = ImportTask(
            company=self.company,
            scenario=self.scenario,
            created_by=self.user,
        )
        task.file.save("import.csv", ContentFile("Статья,Период,Сумма\n"), save=False)
        task.save()
        assert task.slug

    def test_str_contains_file_and_status(self):
        task = ImportTask(
            company=self.company,
            scenario=self.scenario,
            created_by=self.user,
            status="pending",
        )
        task.file.save("import.csv", ContentFile(""), save=False)
        task.save()
        assert "Импорт" in str(task)
        assert "Ожидает" in str(task)

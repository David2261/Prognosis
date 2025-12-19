import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from accounts.models import Company
from core.models import Scenario
from data_ingestion.models import ImportTask
from data_ingestion.serializers import ImportTaskCreateSerializer, ImportTaskSerializer


User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(email="u@example.com", password="pass")


@pytest.fixture
def company():
    return Company.objects.create(name="Test Company")


@pytest.fixture
def scenario(company):
    return Scenario.objects.create(
        company=company,
        name="Budget 2025",
        type="budget",
        version=1
    )


@pytest.fixture
def csv_file():
    content = "Статья,Период,Сумма\nRA,2025-01,1000.00\nEX,2025-02,500.00\n"
    return SimpleUploadedFile("test_import.csv", content.encode('utf-8'), content_type="text/csv")


@pytest.mark.django_db
class TestImportTaskSerializers:
    def test_create_serializer_valid(self, user, company, scenario, csv_file):
        # Подвязываем пользователя к компании (чтобы в view работало company_roles)
        company.user_roles.create(user=user, role="admin")

        data = {
            "file": csv_file,
            "scenario": scenario.id,
        }

        serializer = ImportTaskCreateSerializer(data=data, context={'request': None})  # context не обязателен здесь
        assert serializer.is_valid(), serializer.errors

        # Проверяем, что сохраняется правильно
        task = serializer.save(created_by=user, company=company)
        assert task.file.name.endswith(".csv")
        assert task.scenario == scenario
        assert task.created_by == user
        assert task.company == company

    def test_create_serializer_invalid_file_extension(self, user, company, scenario):
        company.user_roles.create(user=user, role="admin")

        invalid_file = SimpleUploadedFile("data.txt", b"invalid content", content_type="text/plain")

        data = {
            "file": invalid_file,
            "scenario": scenario.id,
        }

        serializer = ImportTaskCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "file" in serializer.errors or "non_field_errors" in serializer.errors

    def test_import_task_serializer_progress_and_fields(self, user, company, scenario):
        company.user_roles.create(user=user, role="admin")

        task = ImportTask.objects.create(
            company=company,
            scenario=scenario,
            created_by=user,
            file=SimpleUploadedFile("test.csv", b"header\ndata", content_type="text/csv"),
            rows_total=10,
            rows_processed=7,
            rows_success=6,
            rows_failed=1,
            status="completed",
        )

        serializer = ImportTaskSerializer(task)
        data = serializer.data

        assert data["progress"] == 70.0
        assert data["scenario_name"] == scenario.name
        assert data["rows_total"] == 10
        assert data["rows_processed"] == 7
        assert data["rows_success"] == 6
        assert data["rows_failed"] == 1
        assert data["status"] == "completed"
        assert data["created_by"] == user.id
        assert "file" in data

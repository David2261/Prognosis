import pytest
from decimal import Decimal
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model

from accounts.models import Company
from core.models import Scenario
from dimensions.models import BudgetArticle
from financials.models import FinancialLine
from data_ingestion.models import ImportTask
from data_ingestion.tasks import process_import_task


User = get_user_model()


@pytest.mark.django_db
def test_process_import_task_creates_financial_lines_csv():
    user = User.objects.create_user(email="u@example.com", password="p")
    company = Company.objects.create(name="C1")
    scenario = Scenario.objects.create(
        company=company,
        name="B2025",
        type="budget",
        version=1
    )

    # Создаём статью правильно через add_root
    BudgetArticle.add_root(company=company, code="A1", name="Article 1")

    # CSV с двумя строками: месячная и годовая
    csv_content = (
        "Статья,Период,Сумма\n"
        "A1,2025-01,100.50\n"
        "A1,2025,200.00\n"
    )

    # Создаём задачу импорта
    task = ImportTask(
        company=company,
        scenario=scenario,
        created_by=user,
        file_type="csv"
    )
    task.file.save("import.csv", ContentFile(csv_content.encode("utf-8")))
    task.save()

    # Запускаем обработку
    process_import_task(task.id)

    # Проверяем статус задачи
    task.refresh_from_db()
    assert task.status == "completed"
    assert task.rows_total == 2
    assert task.rows_success == 2
    assert task.rows_failed == 0

    # Проверяем созданные финансовые строки
    lines = FinancialLine.objects.filter(
        company=company,
        scenario=scenario
    ).select_related("period").order_by("period__year", "period__month")

    assert lines.count() == 2

    # Первая строка — месячная
    monthly_line = lines[0]
    assert monthly_line.period.year == 2025
    assert monthly_line.period.month == 1
    assert monthly_line.period.quarter == 1  # должно заполниться автоматически
    assert monthly_line.amount == Decimal("100.50")

    # Вторая строка — годовая
    yearly_line = lines[1]
    assert yearly_line.period.year == 2025
    assert yearly_line.period.month is None
    assert yearly_line.period.quarter is None
    assert yearly_line.amount == Decimal("200.00")

    # Общие проверки
    assert monthly_line.article.code == "A1"
    assert yearly_line.article.code == "A1"

from celery import shared_task
from decimal import Decimal
import pandas as pd
from django.db import transaction
from django.utils import timezone

from .models import ImportTask
from financials.models import FinancialLine
from dimensions.models import (
	BudgetArticle, CostCenter,
	Department, Project, ChartOfAccounts
)
from core.models import TimePeriod


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_import_task(self, task_id):
	"""
	Асинхронная обработка импорта финансовых данных из Excel/CSV.
	Поддерживает создание/обновление строк,
	обработку ошибок по строкам и прогресс.
	"""
	try:
		# Блокируем задачу, чтобы избежать гонки
		task = ImportTask.objects.select_for_update().get(id=task_id)
	except ImportTask.DoesNotExist:
		return  # задача удалена — ничего не делаем

	# Начало обработки
	task.status = "processing"
	task.started_at = timezone.now()
	task.save(update_fields=["status", "started_at"])

	errors = []
	success = 0

	try:
		with transaction.atomic():
			# Чтение файла — всё как строки,
			# чтобы избежать автоматических преобразований
			if task.file_type == "excel":
				df = pd.read_excel(task.file.path, dtype=str, keep_default_na=False)
			else:  # csv
				df = pd.read_csv(
					task.file.path,
					dtype=str,
					keep_default_na=False,
					sep=None,
					engine="python")

			# Убираем пустые строки и пробелы
			df = df.dropna(how="all")
			df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

			task.rows_total = len(df)
			task.save(update_fields=["rows_total"])

			for idx, row in df.iterrows():
				try:
					# Обязательные поля
					article_code = row.get("Статья")
					if not article_code:
						raise ValueError("Колонка 'Статья' обязательна")

					period_str = row.get("Период")
					if not period_str:
						raise ValueError("Колонка 'Период' обязательна")

					amount_str = row.get("Сумма")
					if not amount_str:
						raise ValueError("Колонка 'Сумма' обязательна")
					amount_val = Decimal(str(amount_str).replace(",", "."))

					# Получаем справочники
					article = BudgetArticle.objects.get(
						company=task.company,
						code=article_code)

					# Парсинг периода
					period_str = period_str.strip()
					if "-" in period_str and len(
						period_str) == 7 and period_str.count("-") == 1:
						year_str, month_str = period_str.split("-")
						year, month = int(year_str), int(month_str)
						if not (1 <= month <= 12):
							raise ValueError(f"Некорректный месяц: {month}")
						quarter = (month - 1) // 3 + 1
						period, _ = TimePeriod.objects.get_or_create(
							company=task.company,
							year=year,
							quarter=quarter,
							month=month,
						)
					else:
						try:
							year = int(period_str)
						except ValueError:
							raise ValueError(f"Некорректный формат периода: {period_str}")
						period, _ = TimePeriod.objects.get_or_create(
							company=task.company,
							year=year,
							quarter=None,
							month=None,
						)

					# Опциональные измерения (пример — расширь по необходимости)
					cost_center = None
					if row.get("ЦФО"):
						cc_code = str(row["ЦФО"]).strip()
						if cc_code:
							cost_center = CostCenter.objects.get(company=task.company, code=cc_code)

					department = None
					if row.get("Подразделение"):
						dept_code = str(row["Подразделение"]).strip()
						if dept_code:
							department = Department.objects.get(
								company=task.company,
								code=dept_code)

					project = None
					if row.get("Проект"):
						proj_code = str(row["Проект"]).strip()
						if proj_code:
							project = Project.objects.get(company=task.company, code=proj_code)

					account = None
					if row.get("Счет"):
						acc_code = str(row["Счет"]).strip()
						if acc_code:
							account = ChartOfAccounts.objects.get(
								company=task.company,
								code=acc_code)

					# Создаём или обновляем финансовую строку
					obj, created = FinancialLine.objects.update_or_create(
						company=task.company,
						scenario=task.scenario,
						period=period,
						article=article,
						cost_center=cost_center,
						department=department,
						project=project,
						account=account,
						defaults={"amount": amount_val},
					)
					success += 1

				except Exception as e:
					errors.append(f"Строка {idx + 2}: {str(e)}")

				# Обновляем прогресс после каждой строки
				task.rows_processed = idx + 1
				task.rows_success = success
				task.rows_failed = len(errors)
				task.save(update_fields=["rows_processed", "rows_success", "rows_failed"])

			# Финальный статус
			task.status = "completed" if not errors else "failed"
			if errors:
				task.error_log = "\n".join(errors[:200])

	except Exception as e:
		# Критическая ошибка (например, файл не читается)
		task.status = "failed"
		task.error_log = f"Критическая ошибка: {str(e)}"

	finally:
		task.finished_at = timezone.now()
		task.save(update_fields=["status", "error_log", "finished_at"])

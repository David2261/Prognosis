from celery import shared_task
from django.utils import timezone
from django.core.files.base import ContentFile
from django.db import transaction
from io import BytesIO
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
	SimpleDocTemplate, Table,
	TableStyle, Paragraph, Spacer)

from .models import GeneratedReport
from .financials.generators import get_financial_data_for_report


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def generate_report_task(self, report_id: int) -> None:
	"""
	Асинхронная задача генерации отчёта.
	Поддерживает Excel для P&L / Plan-Fact / Custom и PDF для остальных типов.
	"""
	try:
		with transaction.atomic():
			report = GeneratedReport.objects.select_for_update().select_related(
				'template', 'scenario', 'start_period', 'end_period', 'company'
			).get(id=report_id)

			if report.status != "pending":
				return

			report.status = "generating"
			report.save(update_fields=["status"])

		# Получаем данные для отчёта
		data = get_financial_data_for_report(
			company=report.company,
			template=report.template,
			scenario=report.scenario,
			start_period=report.start_period,
			end_period=report.end_period,
		)

		if not data:
			raise ValueError("Нет данных для генерации отчёта")

		df = pd.DataFrame(data)

		# Определяем формат по типу отчёта
		is_excel_type = report.template.report_type in ("pnl", "plan_fact", "custom")

		buffer = BytesIO()
		filename_base = f"{report.template.code}_\
			{timezone.now().strftime('%Y%m%d_%H%M')}"

		if is_excel_type:
			# Генерация Excel
			with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
				df.to_excel(
					writer,
					sheet_name=report.template.report_type.upper()[:31],
					index=False
				)
				worksheet = writer.sheets[report.template.report_type.upper()[:31]]
				# Автоширина колонок
				for i, col in enumerate(df.columns):
					max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
					worksheet.set_column(i, i, min(max_len, 50))

			filename = f"{filename_base}.xlsx"

		else:
			# Генерация PDF
			doc = SimpleDocTemplate(
				buffer,
				pagesize=A4,
				rightMargin=inch / 2,
				leftMargin=inch / 2,
				topMargin=inch,
				bottomMargin=inch / 2
			)
			elements = []
			styles = getSampleStyleSheet()

			elements.append(Paragraph(
				f"Отчёт: {report.name}",
				styles['Title']))
			elements.append(Spacer(1, 0.3 * inch))
			elements.append(Paragraph(
				f"Шаблон: {report.template.name}",
				styles['Heading3']))
			elements.append(Paragraph(
				f"Сгенерировано: {timezone.now().strftime('%d.%m.%Y %H:%M')}",
				styles['Normal']))
			elements.append(Spacer(1, 0.5 * inch))

			table_data = [df.columns.tolist()] + df.values.tolist()
			table = Table(table_data, repeatRows=1)

			table.setStyle(TableStyle([
				('BACKGROUND', (0, 0), (-1, 0), colors.grey),
				('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
				('ALIGN', (0, 0), (-1, -1), 'CENTER'),
				('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
				('FONTSIZE', (0, 0), (-1, 0), 12),
				('BOTTOMPADDING', (0, 0), (-1, 0), 12),
				('BACKGROUND', (0, 1), (-1, -1), colors.beige),
				('GRID', (0, 0), (-1, -1), 0.5, colors.black),
				('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			]))

			elements.append(table)
			doc.build(elements)

			filename = f"{filename_base}.pdf"

		buffer.seek(0)
		report.generated_file.save(filename, ContentFile(buffer.read()))
		buffer.close()

		report.status = "ready"
		report.save(update_fields=["status", "generated_file"])

	except Exception as exc:
		try:
			report = GeneratedReport.objects.get(id=report_id)
			report.status = "failed"
			report.error_message = str(exc)[:500]
			report.save(update_fields=["status", "error_message"])
		except GeneratedReport.DoesNotExist:
			pass

		raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

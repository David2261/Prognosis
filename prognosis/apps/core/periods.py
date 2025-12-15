from datetime import date
from .models import TimePeriod


def get_current_period(company, granularity="month") -> TimePeriod:
	"""
	Возвращает текущий период для компании.
	granularity: 'year', 'quarter', 'month'
	"""
	today = date.today()
	year = today.year
	month = today.month
	quarter = (month - 1) // 3 + 1

	period, _ = TimePeriod.objects.get_or_create(
		company=company,
		year=year,
		quarter=quarter if granularity in ["quarter", "month"] else None,
		month=month if granularity == "month" else None,
	)
	return period


def generate_periods_for_year(company, year: int):
	"""Генерирует 12 месяцев + 4 квартала + год для указанного года"""
	# ... логика создания

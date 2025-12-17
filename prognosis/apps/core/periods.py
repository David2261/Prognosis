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
	created = []

	# year-level period
	y, was_created = TimePeriod.objects.get_or_create(
		company=company, year=year, quarter=None, month=None
	)
	if was_created:
		created.append(y)

	# quarters
	for q in range(1, 5):
		p, was_created = TimePeriod.objects.get_or_create(
			company=company, year=year, quarter=q, month=None
		)
		if was_created:
			created.append(p)

	# months
	for m in range(1, 13):
		q = (m - 1) // 3 + 1
		p, was_created = TimePeriod.objects.get_or_create(
			company=company, year=year, quarter=q, month=m
		)
		if was_created:
			created.append(p)

	return created

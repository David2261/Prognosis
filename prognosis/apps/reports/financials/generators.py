from decimal import Decimal
from django.db.models import Sum, Case, When, Value, DecimalField
from financials.models import FinancialLine


def _base_queryset(company, scenario=None, start_period=None, end_period=None):
	qs = FinancialLine.objects.filter(company=company)

	if start_period and end_period:
		qs = qs.filter(
			period__year__gte=start_period.year,
			period__year__lte=end_period.year)
	elif start_period:
		qs = qs.filter(period=start_period)
	elif end_period:
		qs = qs.filter(period=end_period)

	if scenario:
		qs = qs.filter(scenario=scenario)

	return qs


def get_pnl_data(
	company,
	template,
	scenario=None,
	start_period=None,
	end_period=None):
	"""
	Данные для P&L / Отчёт о прибылях и убытках
	"""
	qs = _base_queryset(company, scenario, start_period, end_period)

	data = qs.values(
		"article__code",
		"article__name",
		"article__article_type",
	).annotate(
		amount=Sum("amount")
	).order_by("article__code")

	result = []
	for row in data:
		amount = row["amount"] or Decimal("0.00")
		result.append({
			"code": row["article__code"],
			"name": row["article__name"],
			"group": "Без группы",
			"amount": float(amount),
			"type": row["article__article_type"],
		})

	# Добавить иерархическую группировку
	# через treebeard (get_descendants и т.д.)
	return result


def get_plan_fact_data(
	company,
	template,
	scenario=None,
	start_period=None,
	end_period=None):
	"""
	План-Факт анализ
	"""
	qs = _base_queryset(company, scenario, start_period, end_period)

	data = qs.values(
		"article__code",
		"article__name",
	).annotate(
		fact=Sum(
			Case(
				When(scenario__type="actual", then="amount"),
				default=Value(Decimal("0.00"), output_field=DecimalField()),
				output_field=DecimalField()
			)
		),
		plan=Sum(
			Case(
				When(scenario__type__in=["budget", "plan"], then="amount"),
				default=Value(Decimal("0.00"), output_field=DecimalField()),
				output_field=DecimalField()
			)
		),
	).order_by("article__code")

	result = []
	for row in data:
		fact = row["fact"] or Decimal("0.00")
		plan = row["plan"] or Decimal("0.00")
		deviation = fact - plan
		dev_percent = (deviation / plan * 100) if plan != 0 else Decimal("0.00")

		result.append({
			"code": row["article__code"],
			"name": row["article__name"],
			"group": "Без группы",  # ← пока нет parent
			"fact": float(fact),
			"plan": float(plan),
			"deviation": float(deviation),
			"deviation_percent": float(dev_percent),
		})

	return result


# Фабрика / диспетчер
REPORT_DATA_FUNCTIONS = {
	"pnl": get_pnl_data,
	"plan_fact": get_plan_fact_data,
	"balance": lambda *args, **kwargs: [{"error": "Баланс не реализован"}],
	"cashflow": lambda *args, **kwargs: [{"error": "Cash Flow не реализован"}],
	"custom": get_pnl_data,  # или отдельная логика
}


def get_financial_data_for_report(
	template,
	scenario=None,
	start_period=None,
	end_period=None):
	func = REPORT_DATA_FUNCTIONS.get(template.report_type)
	if not func:
		return [{"error": f"Тип отчёта {template.report_type} не поддерживается"}]

	return func(
		company=template.company,
		template=template,
		scenario=scenario,
		start_period=start_period,
		end_period=end_period)

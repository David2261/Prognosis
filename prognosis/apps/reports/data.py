from decimal import Decimal
from django.db.models import Sum, Case, When, Value, DecimalField
from financials.models import FinancialLine


def get_financial_data_for_report(
	company,
	template,
	scenario=None,
	start_period=None,
	end_period=None,
	include_dimensions=False
):
	qs = FinancialLine.objects.filter(company=company)

	if start_period and end_period:
		qs = qs.filter(period__gte=start_period, period__lte=end_period)
	elif start_period:
		qs = qs.filter(period=start_period)
	elif end_period:
		qs = qs.filter(period=end_period)

	# Фильтр по сценарию
	if scenario:
		qs = qs.filter(scenario=scenario)

	# Основная группировка — по статье бюджета
	group_by = ["article__code", "article__name"]

	if include_dimensions:
		group_by += ["cost_center__name", "department__name", "project__name"]

	data = qs.values(*group_by).annotate(
		total_amount=Sum("amount"),
		plan_amount=Sum(
			Case(
				When(scenario__type__in=["budget", "plan"], then="amount"),
				default=Value(Decimal("0.00")),
				output_field=DecimalField(),
			)
		),
		fact_amount=Sum(
			Case(
				When(scenario__type="actual", then="amount"),
				default=Value(Decimal("0.00")),
				output_field=DecimalField(),
			)
		)
	).order_by("article__code")

	result = []

	for row in data:
		fact = row["fact_amount"] or Decimal("0.00")
		plan = row["plan_amount"] or Decimal("0.00")
		deviation = fact - plan
		deviation_percent = (
			(fact - plan) / abs(plan) * 100) if plan != 0 else Decimal("0.00")

		item = {
			"article_code": row["article__code"],
			"article_name": row["article__name"],
			"parent_article": "",
			"fact": float(fact),
			"plan": float(plan),
			"deviation": float(deviation),
			"deviation_percent": float(deviation_percent),
		}

		if include_dimensions:
			item.update({
				"cost_center": row.get("cost_center__name", ""),
				"department": row.get("department__name", ""),
				"project": row.get("project__name", ""),
			})

		result.append(item)

	# Дополнительная логика в зависимости от типа отчёта
	if template.report_type == "pnl":
		# Можно добавить сортировку, подытоги, иерархию и т.д.
		# Например: группировать по parent_article
		pass

	elif template.report_type == "balance":
		# Для баланса обычно нужна другая логика:
		# активы / пассивы, начальный остаток + движение
		# это уже совсем другая история
		result = [{"warning": "Баланс пока не реализован"}]

	elif template.report_type == "cashflow":
		result = [{"warning": "Cash Flow пока не реализован"}]

	elif template.report_type == "plan_fact":
		# Здесь как раз то, что выше — план-факт анализ
		pass

	return result

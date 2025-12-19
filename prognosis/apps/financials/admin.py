from django.contrib import admin
from unfold.admin import ModelAdmin

from financials.models import FinancialLine


@admin.register(FinancialLine)
class FinancialLineAdmin(ModelAdmin):
	"""
	Админка для финансовых строк.
	"""

	list_display = (
		"company",
		"scenario",
		"period_display",
		"article",
		"amount",
		"cost_center",
		"department",
		"project",
		"account",
	)

	list_select_related = (
		"company",
		"scenario",
		"period",
		"article",
		"cost_center",
		"department",
		"project",
		"account",
	)

	list_filter = (
		"company",
		"scenario",
		"period__year",
		"period__month",
		"article",
	)

	search_fields = (
		"article__code",
		"article__name",
		"scenario__name",
		"company__name",
		"comment",
		"source",
	)

	ordering = (
		"-period__year",
		"-period__month",
		"article__code",
	)

	readonly_fields = (
		"company",
	)

	fieldsets = (
		(
			"Основное",
			{
				"fields": (
					"company",
					"scenario",
					"period",
					"article",
					"amount",
				)
			},
		),
		(
			"Измерения",
			{
				"fields": (
					"cost_center",
					"department",
					"project",
					"account",
				),
				"classes": ("collapse",),
			},
		),
		(
			"Дополнительно",
			{
				"fields": (
					"comment",
					"source",
				),
				"classes": ("collapse",),
			},
		),
	)

	def period_display(self, obj):
		return f"{obj.period.year}-{obj.period.month:02d}"

	period_display.short_description = "Период"

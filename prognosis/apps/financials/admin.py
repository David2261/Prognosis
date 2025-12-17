from django.contrib import admin
from unfold.admin import NestedModelAdmin, NestedTabularInline
from financials.models import FinancialLine


class FinancialLineAdmin(NestedModelAdmin):
	list_display = ('company', 'scenario', 'period', 'article', 'amount')
	search_fields = (
		'company__name',
		'scenario__name',
		'period__year',
		'article__code')
	list_filter = ('company', 'scenario', 'period', 'article')

	inlines = [
		NestedTabularInline(model=FinancialLine, fields=('amount',), extra=0),
	]


admin.site.register(FinancialLine, FinancialLineAdmin)

from django.urls import path
from .views import FinancialLineListCreateView, FinancialLineDetailView

app_name = 'financials'

urlpatterns = [
	path(
		'v1/lines/',
		FinancialLineListCreateView.as_view(),
		name='financialline-list-create'),
	path(
		'v1/lines/<slug:pk>/',
		FinancialLineDetailView.as_view(),
		name='financialline-detail'),
]

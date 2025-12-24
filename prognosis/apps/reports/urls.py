from django.urls import path
from .views import (
	ReportTemplateListCreateView,
	ReportTemplateDetailView,
	GenerateReportView)

app_name = 'reports'


urlpatterns = [
	path(
		'v1/templates/',
		ReportTemplateListCreateView.as_view(),
		name='template-list-create'),
	path(
		'v1/templates/<slug:slug>/',
		ReportTemplateDetailView.as_view(),
		name='template-detail'),
	path(
		'v1/generate/',
		GenerateReportView.as_view(),
		name='generate-report'),
]

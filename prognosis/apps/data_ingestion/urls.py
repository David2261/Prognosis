from django.urls import path
from .views import ImportTaskListCreateView, ImportTaskDetailView

app_name = 'data_ingestion'

urlpatterns = [
	path(
		'v1/imports/',
		ImportTaskListCreateView.as_view(),
		name='import-list-create'),
	path(
		'v1/imports/<slug:slug>/',
		ImportTaskDetailView.as_view(),
		name='import-detail'),
]

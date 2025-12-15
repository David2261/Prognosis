from django.urls import path
from .views import (
	TimePeriodListView,
	ScenarioListCreateView,
	ScenarioDetailView,
)


app_name = 'core'

urlpatterns = [
	# Периоды (только список, создание — автоматически или через админку)
	path(
		'v1/time-periods/',
		TimePeriodListView.as_view(),
		name='timeperiod-list'),
	# Сценарии: список и создание
	path(
		'v1/scenarios/',
		ScenarioListCreateView.as_view(),
		name='scenario-list-create'),
	# Активные сценарии (удобный фильтр)
	path(
		'v1/scenarios/active/',
		ScenarioListCreateView.as_view(),
		name='scenario-active-list'),
	# Детали сценария (по slug)
	path(
		'v1/scenarios/<slug:slug>/',
		ScenarioDetailView.as_view(),
		name='scenario-detail'),
]

from django.urls import path
from .views import (
	CompanyListCreateView,
	CompanyDetailView,
	CompanyRolesListView,
)


app_name = 'accounts'

urlpatterns = [
	path(
		'v1/companies/',
		CompanyListCreateView.as_view(),
		name='company-list-create'),
	# Отдельный эндпоинт для регистрации (для удобства фронта)
	path(
		'v1/registration/',
		CompanyListCreateView.as_view(),
		name='company_registration'),
	# Детали компании
	path(
		'v1/companies/<slug:slug>/',
		CompanyDetailView.as_view(),
		name='company-detail'),
	# Роли в компании
	path(
		'v1/companies/<slug:company_slug>/roles/',
		CompanyRolesListView.as_view(),
		name='company-roles'),
]

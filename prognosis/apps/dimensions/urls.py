from django.urls import path
from .views import (
	ChartOfAccountsListCreateView,
	ChartOfAccountsDetailView,
	BudgetArticleListCreateView,
	BudgetArticleDetailView,
	CostCenterListCreateView,
	CostCenterDetailView,
	DepartmentListCreateView,
	DepartmentDetailView,
	ProjectListCreateView,
	ProjectDetailView,
)

app_name = 'dimensions'

urlpatterns = [
	path(
		'v1/chart-of-accounts/',
		ChartOfAccountsListCreateView.as_view(),
		name='chart-of-accounts-list'),
	path(
		'v1/budget-articles/',
		BudgetArticleListCreateView.as_view(),
		name='budget-articles-list'),
	path(
		'v1/cost-centers/',
		CostCenterListCreateView.as_view(),
		name='cost-centers-list'),
	path(
		'v1/departments/',
		DepartmentListCreateView.as_view(),
		name='departments-list'),
	path(
		'v1/projects/',
		ProjectListCreateView.as_view(),
		name='projects-list'),

	# Detail (Retrieve, Update, Partial Update, Delete)
	path(
		'v1/chart-of-accounts/<slug:slug>/',
		ChartOfAccountsDetailView.as_view(),
		name='chart-of-accounts-detail'),
	path(
		'v1/budget-articles/<slug:slug>/',
		BudgetArticleDetailView.as_view(),
		name='budget-articles-detail'),
	path(
		'v1/cost-centers/<slug:slug>/',
		CostCenterDetailView.as_view(),
		name='cost-centers-detail'),
	path(
		'v1/departments/<slug:slug>/',
		DepartmentDetailView.as_view(),
		name='departments-detail'),
	path(
		'v1/projects/<slug:slug>/',
		ProjectDetailView.as_view(),
		name='projects-detail'),
]

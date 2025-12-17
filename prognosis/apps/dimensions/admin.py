from django.contrib import admin
from django.db import models
from django.urls import path
from unfold.views import UnfoldModelAdminViewMixin
from unfold.widgets import UnfoldAdminTextInputWidget, UnfoldAdminDateWidget
from django.views.generic import TemplateView

from .models import (
	ChartOfAccounts, BudgetArticle,
	CostCenter, Department, Project
)


_FORMFIELD_OVERRIDES = {
	models.CharField: {"widget": UnfoldAdminTextInputWidget},
	models.DateField: {"widget": UnfoldAdminDateWidget},
}


class UnfoldListView(UnfoldModelAdminViewMixin, TemplateView):
	template_name = "unfold/admin_list.html"

	def __init__(self, model_admin, **kwargs):
		UnfoldModelAdminViewMixin.__init__(self, model_admin=model_admin, **kwargs)
		TemplateView.__init__(self)

	def get(self, request, *args, **kwargs):
		# ensure request and title are available for UnfoldModelAdminViewMixin
		self.request = request
		self.title = str(self.model_admin.model._meta.verbose_name_plural).title()
		self.object_list = self.model_admin.get_queryset(request)
		context = self.get_context_data(object_list=self.object_list)
		return self.render_to_response(context)


@admin.register(ChartOfAccounts)
class ChartOfAccountsAdmin(admin.ModelAdmin):
	list_display = ("company", "code", "name", "slug", "is_active")
	search_fields = ("code", "name")
	list_filter = ("is_active",)
	readonly_fields = ("slug",)
	formfield_overrides = _FORMFIELD_OVERRIDES

	def get_urls(self):
		urls = super().get_urls()
		custom = [path(
			"unfold/",
			self.admin_site.admin_view(
				lambda request: UnfoldListView(self).get(request)),
			name="dimensions_chartofaccounts_unfold")]
		return custom + urls


@admin.register(BudgetArticle)
class BudgetArticleAdmin(admin.ModelAdmin):
	list_display = (
		"company",
		"code",
		"name",
		"slug",
		"article_type",
		"is_active")
	search_fields = ("code", "name")
	readonly_fields = ("slug",)
	formfield_overrides = _FORMFIELD_OVERRIDES

	def get_urls(self):
		urls = super().get_urls()
		custom = [path(
			"unfold/",
			self.admin_site.admin_view(
				lambda request: UnfoldListView(self).get(request)),
			name="dimensions_budgetarticle_unfold")]
		return custom + urls


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
	list_display = ("company", "code", "name", "slug")
	search_fields = ("code", "name")
	readonly_fields = ("slug",)
	formfield_overrides = _FORMFIELD_OVERRIDES

	def get_urls(self):
		urls = super().get_urls()
		custom = [path(
			"unfold/",
			self.admin_site.admin_view(
				lambda request: UnfoldListView(self).get(request)),
			name="dimensions_costcenter_unfold")]
		return custom + urls


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
	list_display = ("company", "code", "name", "slug")
	search_fields = ("code", "name")
	readonly_fields = ("slug",)
	formfield_overrides = _FORMFIELD_OVERRIDES

	def get_urls(self):
		urls = super().get_urls()
		custom = [path(
			"unfold/",
			self.admin_site.admin_view(
				lambda request: UnfoldListView(self).get(request)),
			name="dimensions_department_unfold")]
		return custom + urls


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
	list_display = ("company", "code", "name", "slug", "start_date", "end_date")
	search_fields = ("code", "name")
	readonly_fields = ("slug",)
	formfield_overrides = _FORMFIELD_OVERRIDES

	def get_urls(self):
		urls = super().get_urls()
		custom = [path(
			"unfold/",
			self.admin_site.admin_view(
				lambda request: UnfoldListView(self).get(request)),
			name="dimensions_project_unfold")]
		return custom + urls

from django.contrib import admin
from django.urls import path
from django.db import models
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
	title = None
	model_admin = None
	template_name = "unfold/admin_list.html"

	def get_permission_required(self):
		opts = self.model_admin.model._meta
		return [f"{opts.app_label}.view_{opts.model_name}"]

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context.setdefault(
			"title",
			str(self.model_admin.model._meta.verbose_name_plural).title())
		return context


class BaseUnfoldAdmin(admin.ModelAdmin):
	formfield_overrides = _FORMFIELD_OVERRIDES
	readonly_fields = ("slug",)

	def get_urls(self):
		urls = super().get_urls()
		info = self.model._meta.app_label, self.model._meta.model_name
		custom_urls = [
			path(
				"unfold/",
				self.admin_site.admin_view(
					UnfoldListView.as_view(
						model_admin=self,
						title=str(self.model._meta.verbose_name_plural).title(),
					)
				),
				name=f"{info[0]}_{info[1]}_unfold",
			),
		]
		return custom_urls + urls


@admin.register(ChartOfAccounts)
class ChartOfAccountsAdmin(BaseUnfoldAdmin):
	list_display = ("company", "code", "name", "slug", "is_active")
	search_fields = ("code", "name")
	list_filter = ("is_active",)


@admin.register(BudgetArticle)
class BudgetArticleAdmin(BaseUnfoldAdmin):
	list_display = (
		"company",
		"code",
		"name",
		"slug",
		"article_type",
		"is_active")
	search_fields = ("code", "name")


@admin.register(CostCenter)
class CostCenterAdmin(BaseUnfoldAdmin):
	list_display = ("company", "code", "name", "slug")
	search_fields = ("code", "name")


@admin.register(Department)
class DepartmentAdmin(BaseUnfoldAdmin):
	list_display = ("company", "code", "name", "slug")
	search_fields = ("code", "name")


@admin.register(Project)
class ProjectAdmin(BaseUnfoldAdmin):
	list_display = ("company", "code", "name", "slug", "start_date", "end_date")
	search_fields = ("code", "name")

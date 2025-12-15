from django.contrib import admin
from django.db import models
from django.urls import path
from django.shortcuts import render
from unfold.views import UnfoldModelAdminViewMixin
from unfold.widgets import (
	UnfoldAdminTextInputWidget,
	UnfoldAdminExpandableTextareaWidget,
	UnfoldAdminDateWidget,
)

from .models import Company, UserCompanyRole


_FORMFIELD_OVERRIDES = {
	models.CharField: {"widget": UnfoldAdminTextInputWidget},
	models.TextField: {"widget": UnfoldAdminExpandableTextareaWidget},
	models.DateField: {"widget": UnfoldAdminDateWidget},
}


class UnfoldListView(UnfoldModelAdminViewMixin):
	template_name = "unfold/admin_list.html"

	def __init__(self, model_admin, **kwargs):
		super().__init__(model_admin=model_admin, **kwargs)

	def get(self, request, *args, **kwargs):
		qs = self.model_admin.get_queryset(request)
		context = self.get_context_data(object_list=qs)
		return render(request, self.template_name, context)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
	list_display = (
		"name",
		"slug",
		"inn",
		"currency_default",
		"fiscal_year_start",
		"is_active",
		"created_at")
	list_filter = ("is_active", "currency_default", "fiscal_year_start")
	search_fields = ("name", "inn")
	readonly_fields = ("created_at", "updated_at", "slug")
	formfield_overrides = _FORMFIELD_OVERRIDES

	def get_urls(self):
		urls = super().get_urls()
		custom = [path(
			"unfold/",
			self.admin_site.admin_view(
				lambda request: UnfoldListView(self).get(request)),
			name="accounts_company_unfold")]
		return custom + urls


@admin.register(UserCompanyRole)
class UserCompanyRoleAdmin(admin.ModelAdmin):
	list_display = ("user", "company", "role")
	list_filter = ("role", "company")
	search_fields = ("user__email", "user__username", "company__name")
	formfield_overrides = _FORMFIELD_OVERRIDES

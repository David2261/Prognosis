from django.contrib import admin
from django.db import models
from django.urls import path
from django.shortcuts import render
from unfold.views import UnfoldModelAdminViewMixin
from unfold.widgets import (
    UnfoldAdminTextInputWidget,
    UnfoldAdminDateWidget,
)

from .models import TimePeriod, Scenario


_FORMFIELD_OVERRIDES = {
    models.CharField: {"widget": UnfoldAdminTextInputWidget},
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


@admin.register(TimePeriod)
class TimePeriodAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "year",
        "quarter",
        "month",
        "is_closed",
        "created_at")
    list_filter = ("company", "year", "is_closed")
    search_fields = ("company__name",)
    formfield_overrides = _FORMFIELD_OVERRIDES


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "slug",
        "name",
        "type",
        "version",
        "is_active",
        "created_at")
    list_filter = ("company", "type", "is_active")
    search_fields = ("name", "company__name")
    readonly_fields = ("slug",)
    formfield_overrides = _FORMFIELD_OVERRIDES

    def get_urls(self):
        urls = super().get_urls()
        custom = [path(
            "unfold/",
            self.admin_site.admin_view(
                lambda request: UnfoldListView(self).get(request)),
            name="core_scenario_unfold")]
        return custom + urls

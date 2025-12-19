from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ImportTask
from accounts.models import Company


@admin.register(ImportTask)
class ImportTaskAdmin(ModelAdmin):
    list_display = (
        "company",
        "slug",
        "file",
        "file_type",
        "status",
        "scenario",
        "rows_total",
        "rows_processed",
        "rows_success",
        "rows_failed",
        "started_at",
        "finished_at",
        "created_by",
    )

    list_filter = (
        "company",
        "status",
        "file_type",
        "scenario",
    )

    search_fields = (
        "file",
        "scenario__name",
        "created_by__email",
        "error_log",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "slug",
        "status",
        "created_by",
        "rows_total",
        "rows_processed",
        "rows_success",
        "rows_failed",
        "started_at",
        "finished_at",
    )

    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    "company",
                    "slug",
                    "file",
                    "file_type",
                    "status",
                    "scenario",
                    "created_by",
                )
            },
        ),
        (
            "Статистика",
            {
                "fields": (
                    "rows_total",
                    "rows_processed",
                    "rows_success",
                    "rows_failed",
                    "started_at",
                    "finished_at",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Ошибки",
            {
                "fields": (
                    "error_log",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            # Автоматически проставляем компанию и автора
            # Компания выбирается вручную пользователем
            # из доступных ему компаний
            obj.created_by = request.user

            # Статус по умолчанию
            if not obj.status:
                obj.status = "pending"

        # Автоматически определяем тип файла
        if obj.file and obj.file.name:
            ext = obj.file.name.lower().split(".")[-1]
            obj.file_type = "excel" if ext in ("xlsx", "xls") else "csv"

        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "company":
            kwargs["queryset"] = Company.objects.filter(
                user_roles__user=request.user
            ).distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

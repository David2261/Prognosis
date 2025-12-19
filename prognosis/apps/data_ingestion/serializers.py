from rest_framework import serializers
from .models import ImportTask


class ImportTaskCreateSerializer(serializers.ModelSerializer):
	class Meta:
		model = ImportTask
		fields = ("file", "scenario")

	def validate_file(self, value):
		if value is None:
			raise serializers.ValidationError("Файл обязателен")

		# Проверяем расширение
		file_name = value.name.lower()
		allowed_extensions = {'.csv', '.xls', '.xlsx'}
		if not any(file_name.endswith(ext) for ext in allowed_extensions):
			raise serializers.ValidationError(
				"Поддерживаются только файлы с расширениями: .csv, .xls, .xlsx"
			)

		# Ограничение размера
		max_size = 50 * 1024 * 1024  # 50 MB
		if value.size > max_size:
			raise serializers.ValidationError("Файл слишком большой (максимум 50 МБ)")

		return value


class ImportTaskSerializer(serializers.ModelSerializer):
	progress = serializers.SerializerMethodField()
	scenario_name = serializers.CharField(source="scenario.name", read_only=True)

	class Meta:
		model = ImportTask
		fields = "__all__"
		read_only_fields = (
			"status",
			"rows_total",
			"rows_processed",
			"rows_success",
			"rows_failed",
			"error_log",
			"started_at",
			"finished_at",
			"created_by",
			"company")

	def get_progress(self, obj):
		if obj.rows_total == 0:
			return 0
		return round((obj.rows_processed / obj.rows_total) * 100, 1)

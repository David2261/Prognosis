from rest_framework import serializers
from .models import ReportTemplate, GeneratedReport


class ReportTemplateSerializer(serializers.ModelSerializer):
	class Meta:
		model = ReportTemplate
		fields = "__all__"


class GeneratedReportSerializer(serializers.ModelSerializer):
	template_name = serializers.CharField(source="template.name", read_only=True)
	scenario_name = serializers.SerializerMethodField()

	class Meta:
		model = GeneratedReport
		fields = "__all__"
		read_only_fields = (
			"status",
			"generated_file",
			"error_message",
			"created_at",
			"updated_at",
			"company",
		)

	def get_scenario_name(self, obj):
		return obj.scenario.name if obj.scenario else None

	def create(self, validated_data):
		validated_data.pop("status", None)
		validated_data.pop("generated_file", None)
		validated_data.pop("error_message", None)
		validated_data.pop("company", None)

		template = validated_data["template"]
		validated_data["company"] = template.company

		return super().create(validated_data)

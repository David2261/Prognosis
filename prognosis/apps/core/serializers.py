from rest_framework import serializers
from .models import TimePeriod, Scenario


class TimePeriodSerializer(serializers.ModelSerializer):
	class Meta:
		model = TimePeriod
		fields = ("id", "year", "quarter", "month", "is_closed", "company")


class ScenarioSerializer(serializers.ModelSerializer):
	type_display = serializers.CharField(
		source="get_type_display",
		read_only=True)

	class Meta:
		model = Scenario
		fields = (
			"id",
			"slug",
			"name",
			"type",
			"type_display",
			"version",
			"is_active",
			"base_scenario",
			"start_period",
			"end_period",
			"company")
		read_only_fields = ("slug",)

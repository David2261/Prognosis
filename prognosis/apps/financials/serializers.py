from rest_framework import serializers
from .models import FinancialLine
from core.models import Scenario, TimePeriod
from dimensions.models import (
	BudgetArticle, CostCenter,
	Department, Project, ChartOfAccounts
)


class FinancialLineSerializer(serializers.ModelSerializer):
	scenario_name = serializers.CharField(
		source="scenario.name",
		read_only=True)
	period_display = serializers.CharField(
		source="period.__str__",
		read_only=True)
	article_name = serializers.CharField(
		source="article.name",
		read_only=True)
	scenario = serializers.SlugRelatedField(
		slug_field="slug",
		queryset=Scenario.objects.none())
	period = serializers.PrimaryKeyRelatedField(
		queryset=TimePeriod.objects.none(),
		required=True)
	article = serializers.SlugRelatedField(
		slug_field="slug",
		queryset=BudgetArticle.objects.none())
	cost_center = serializers.SlugRelatedField(
		slug_field="slug",
		queryset=CostCenter.objects.none(),
		allow_null=True,
		required=False,
		default=None)
	department = serializers.SlugRelatedField(
		slug_field="slug",
		queryset=Department.objects.none(),
		allow_null=True,
		required=False,
		default=None)
	project = serializers.SlugRelatedField(
		slug_field="slug",
		queryset=Project.objects.none(),
		allow_null=True,
		required=False,
		default=None)
	account = serializers.SlugRelatedField(
		slug_field="slug",
		queryset=ChartOfAccounts.objects.none(),
		allow_null=True,
		required=False,
		default=None)

	class Meta:
		model = FinancialLine
		fields = (
			"id", "scenario", "scenario_name",
			"period", "period_display",
			"article", "article_name",
			"cost_center", "department", "project", "account",
			"amount", "comment", "source",
			"company", "created_at", "updated_at"
		)
		read_only_fields = ("company", "created_at", "updated_at")

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		request = self.context.get('request')
		if request and hasattr(request.user, 'company_roles'):
			company = request.user.company_roles.first().company
			self.fields['scenario'].queryset = Scenario.objects.filter(
				company=company)
			self.fields['article'].queryset = BudgetArticle.objects.filter(
				company=company)
			self.fields['period'].queryset = TimePeriod.objects.filter(
				company=company)
			self.fields['cost_center'].queryset = CostCenter.objects.filter(
				company=company)
			self.fields['department'].queryset = Department.objects.filter(
				company=company)
			self.fields['project'].queryset = Project.objects.filter(
				company=company)
			self.fields['account'].queryset = ChartOfAccounts.objects.filter(
				company=company)

from rest_framework import serializers
from .models import (
	ChartOfAccounts, BudgetArticle,
	CostCenter, Department, Project
)


class ChartOfAccountsSerializer(serializers.ModelSerializer):
	class Meta:
		model = ChartOfAccounts
		fields = ("id", "slug", "code", "name", "parent", "is_active", "company")
		read_only_fields = ("slug",)


class BudgetArticleSerializer(serializers.ModelSerializer):
	class Meta:
		model = BudgetArticle
		fields = (
			"id",
			"slug",
			"code",
			"name",
			"article_type",
			"is_active",
			"company",
			"path")
		read_only_fields = ("slug", "company", "path")

	def create(self, validated_data, **kwargs):
		"""Create an MP_Node root node for BudgetArticle using treebeard API."""
		# `company` is passed via serializer.save(company=...)
		company = kwargs.get('company') or validated_data.pop('company', None)
		if company is None:
			raise serializers.ValidationError({'company': 'Company must be provided.'})
		return BudgetArticle.add_root(company=company, **validated_data)

	def update(self, instance, validated_data, **kwargs):
		# Regular field updates work for MP_Node instances
		for attr, value in validated_data.items():
			setattr(instance, attr, value)
		instance.save()
		return instance


class CostCenterSerializer(serializers.ModelSerializer):
	class Meta:
		model = CostCenter
		fields = (
			"id",
			"slug",
			"code",
			"name",
			"parent",
			"manager",
			"company")
		read_only_fields = ("slug",)


class DepartmentSerializer(serializers.ModelSerializer):
	class Meta:
		model = Department
		fields = ("id", "slug", "code", "name", "head", "company")
		read_only_fields = ("slug",)


class ProjectSerializer(serializers.ModelSerializer):
	class Meta:
		model = Project
		fields = (
			"id",
			"slug",
			"code",
			"name",
			"start_date",
			"end_date",
			"manager",
			"company")
		read_only_fields = ("slug",)

from rest_framework import serializers
from .models import Company, UserCompanyRole


class CompanySerializer(serializers.ModelSerializer):
	class Meta:
		model = Company
		fields = (
			"id",
			"slug",
			"name",
			"inn",
			"currency_default",
			"fiscal_year_start",
			"is_active",
			"created_at")
		read_only_fields = ("created_at", "slug")


class UserCompanyRoleSerializer(serializers.ModelSerializer):
	company_name = serializers.CharField(source="company.name", read_only=True)
	user_email = serializers.EmailField(source="user.email", read_only=True)

	class Meta:
		model = UserCompanyRole
		fields = ("id", "user", "user_email", "company", "company_name", "role")

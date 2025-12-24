from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from accounts.models import Company
from .models import ReportTemplate, GeneratedReport
from .serializers import ReportTemplateSerializer, GeneratedReportSerializer
from .tasks import generate_report_task


class ReportTemplateListCreateView(APIView):
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		user_companies = Company.objects.filter(
			user_roles__user=self.request.user
		).distinct()

		return ReportTemplate.objects.filter(company__in=user_companies)

	def get_current_company(self):
		"""
		Возвращает текущую компанию пользователя.
		Логика: если у пользователя только одна компания — возвращаем её.
		"""
		user_companies = Company.objects.filter(
			user_roles__user=self.request.user
		).distinct()

		if user_companies.count() == 1:
			return user_companies.first()
		return None

	def get(self, request):
		templates = self.get_queryset()
		serializer = ReportTemplateSerializer(templates, many=True)
		return Response(serializer.data)

	def post(self, request):
		serializer = ReportTemplateSerializer(data=request.data)
		if serializer.is_valid():
			company = self.get_current_company()
			serializer.save(company=company, created_by=request.user)
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=400)


class ReportTemplateDetailView(APIView):
	permission_classes = [IsAuthenticated]

	def get_object(self, slug):
		return get_object_or_404(
			ReportTemplate,
			slug=slug,
			company__user_roles__user=self.request.user)

	def get(self, request, slug):
		obj = self.get_object(slug)
		serializer = ReportTemplateSerializer(obj)
		return Response(serializer.data)

	def put(self, request, slug):
		obj = self.get_object(slug)
		serializer = ReportTemplateSerializer(obj, data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GenerateReportView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		template_slug = request.data.get("slug")
		scenario_id = request.data.get("scenario_id")
		start_period_id = request.data.get("start_period_id")
		end_period_id = request.data.get("end_period_id")
		custom_name = request.data.get("name", "").strip() or "Отчёт"

		if not template_slug:
			return Response({"error": "Поле slug обязательно"}, status=400)

		template = get_object_or_404(
			ReportTemplate,
			slug=template_slug,
			company__user_roles__user=request.user
		)

		# Защита от дублирующихся запусков (опционально, но полезно)
		existing_pending = GeneratedReport.objects.filter(
			template=template,
			scenario_id=scenario_id,
			start_period_id=start_period_id,
			end_period_id=end_period_id,
			status__in=["pending", "generating"]
		).exists()

		if existing_pending:
			return Response(
				{"warning": "Такой отчёт уже генерируется или в очереди"},
				status=409
			)

		report = GeneratedReport.objects.create(
			company=template.company,
			template=template,
			name=custom_name or f"{template.name} \
				{timezone.now().strftime('%Y-%m-%d %H:%M')}",
			scenario_id=scenario_id,
			start_period_id=start_period_id,
			end_period_id=end_period_id,
			created_by=request.user,
			status="pending"
		)

		generate_report_task.delay(report.id)

		return Response(
			GeneratedReportSerializer(report).data,
			status=status.HTTP_202_ACCEPTED
		)

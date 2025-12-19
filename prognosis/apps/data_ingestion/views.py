from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from pathlib import Path
from .models import ImportTask
from .serializers import ImportTaskSerializer, ImportTaskCreateSerializer
from .tasks import process_import_task


class ImportTaskListCreateView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		tasks = ImportTask.objects.filter(
			company__user_roles__user=request.user
		).order_by("-created_at")
		serializer = ImportTaskSerializer(tasks, many=True)
		return Response(serializer.data)

	def post(self, request):
		serializer = ImportTaskCreateSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		# Проверяем привязку пользователя к компании
		company_role = request.user.company_roles.first()
		if not company_role:
			return Response(
				{"detail": "Пользователь не привязан ни к одной компании"},
				status=status.HTTP_403_FORBIDDEN
			)
		company = company_role.company

		# Сохраняем задачу импорта
		task = serializer.save(created_by=request.user, company=company)

		# Определяем и валидируем тип файла
		allowed_extensions = {".xlsx", ".xls", ".csv"}
		file_ext = Path(task.file.name).suffix.lower()
		if file_ext not in allowed_extensions:
			return Response(
				{"file": "Поддерживаются только файлы CSV, XLS, XLSX"},
				status=status.HTTP_400_BAD_REQUEST
			)

		if file_ext in {".xlsx", ".xls"}:
			task.file_type = "excel"
		else:
			task.file_type = "csv"

		task.save(update_fields=["file_type"])

		# Запускаем обработку в Celery
		process_import_task.delay(task.id)

		return Response(
			ImportTaskSerializer(task).data,
			status=status.HTTP_201_CREATED)


class ImportTaskDetailView(APIView):
	permission_classes = [IsAuthenticated]

	def get_object(self, slug):
		return get_object_or_404(
			ImportTask,
			slug=slug,
			company__user_roles__user=self.request.user
		)

	def get(self, request, slug):
		task = self.get_object(slug)
		serializer = ImportTaskSerializer(task)
		return Response(serializer.data)

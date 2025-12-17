from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import (
	ChartOfAccounts, BudgetArticle,
	CostCenter, Department, Project
)
from .serializers import (
	ChartOfAccountsSerializer, BudgetArticleSerializer,
	CostCenterSerializer, DepartmentSerializer, ProjectSerializer,
)


class BaseDimensionListCreateView(APIView):
	permission_classes = [IsAuthenticated]
	model = None
	serializer_class = None

	def get_queryset(self):
		return self.model.objects.filter(company__user_roles__user=self.request.user)

	def get(self, request):
		items = self.get_queryset()
		serializer = self.serializer_class(items, many=True)
		return Response(serializer.data)

	def post(self, request):
		serializer = self.serializer_class(data=request.data)
		if serializer.is_valid():
			user_role = request.user.company_roles.first()
			if not user_role:
				return Response(
					{"detail": "Пользователь не привязан к компании"},
					status=status.HTTP_400_BAD_REQUEST
				)
			serializer.save(company=user_role.company)
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChartOfAccountsListCreateView(BaseDimensionListCreateView):
	model = ChartOfAccounts
	serializer_class = ChartOfAccountsSerializer


class BudgetArticleListCreateView(BaseDimensionListCreateView):
	model = BudgetArticle
	serializer_class = BudgetArticleSerializer


class CostCenterListCreateView(BaseDimensionListCreateView):
	model = CostCenter
	serializer_class = CostCenterSerializer


class DepartmentListCreateView(BaseDimensionListCreateView):
	model = Department
	serializer_class = DepartmentSerializer


class ProjectListCreateView(BaseDimensionListCreateView):
	model = Project
	serializer_class = ProjectSerializer


class BaseDimensionDetailView(APIView):
	"""
	Базовый класс для детальных операций (GET, PUT, PATCH, DELETE)
	над любым dimension (ChartOfAccounts, BudgetArticle и т.д.)
	"""
	permission_classes = [IsAuthenticated]
	model = None
	serializer_class = None

	def get_object(self, slug):
		"""
		Возвращает объект или 404, с проверкой принадлежности компании пользователя
		"""
		return get_object_or_404(
			self.model,
			slug=slug,
			company__user_roles__user=self.request.user
		)

	def get(self, request, slug):
		obj = self.get_object(slug)
		serializer = self.serializer_class(obj)
		return Response(serializer.data)

	def put(self, request, slug):
		obj = self.get_object(slug)
		serializer = self.serializer_class(obj, data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def patch(self, request, slug):
		"""
		Частичное обновление (PATCH)
		"""
		obj = self.get_object(slug)
		serializer = self.serializer_class(obj, data=request.data, partial=True)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, slug):
		"""
		Удаление объекта (или мягкое удаление, если есть is_active)
		"""
		obj = self.get_object(slug)

		if hasattr(obj, 'is_active'):
			obj.is_active = False
			obj.save()
			return Response(status=status.HTTP_204_NO_CONTENT)

		obj.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)


class ChartOfAccountsDetailView(BaseDimensionDetailView):
	model = ChartOfAccounts
	serializer_class = ChartOfAccountsSerializer


class BudgetArticleDetailView(BaseDimensionDetailView):
	model = BudgetArticle
	serializer_class = BudgetArticleSerializer


class CostCenterDetailView(BaseDimensionDetailView):
	model = CostCenter
	serializer_class = CostCenterSerializer


class DepartmentDetailView(BaseDimensionDetailView):
	model = Department
	serializer_class = DepartmentSerializer


class ProjectDetailView(BaseDimensionDetailView):
	model = Project
	serializer_class = ProjectSerializer

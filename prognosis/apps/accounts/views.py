from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import Company, UserCompanyRole
from .serializers import CompanySerializer, UserCompanyRoleSerializer


class CompanyListCreateView(APIView):
	"""
	GET: список компаний, к которым имеет доступ текущий пользователь
	POST: создание новой компании (регистрация)
	"""
	permission_classes = [IsAuthenticated]

	def get_permissions(self):
		# Allow unauthenticated POST for registration
		if self.request.method == 'POST':
			return [AllowAny()]
		return [IsAuthenticated()]

	def get(self, request):
		companies = Company.objects.filter(user_roles__user=request.user).distinct()
		serializer = CompanySerializer(companies, many=True)
		return Response(serializer.data)

	def post(self, request):
		# Разрешаем создание компании без авторизации (регистрация)
		self.permission_classes = [AllowAny]
		serializer = CompanySerializer(data=request.data)
		if serializer.is_valid():
			company = serializer.save()
			# Опционально: автоматически сделать создателя админом компании
			# (предполагаем, что пользователь уже зарегистрирован в Auth)
			if request.user.is_authenticated:
				UserCompanyRole.objects.create(
					user=request.user,
					company=company,
					role="admin"
				)
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompanyDetailView(APIView):
	"""
	GET, PUT, PATCH, DELETE для конкретной компании
	Доступ только если пользователь привязан к компании
	"""
	permission_classes = [IsAuthenticated]

	def get_object(self, slug, user):
		return get_object_or_404(Company, slug=slug, user_roles__user=user)

	def get(self, request, slug):
		company = self.get_object(slug, request.user)
		serializer = CompanySerializer(company)
		return Response(serializer.data)

	def put(self, request, slug):
		company = self.get_object(slug, request.user)
		serializer = CompanySerializer(company, data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def patch(self, request, slug):
		company = self.get_object(slug, request.user)
		serializer = CompanySerializer(company, data=request.data, partial=True)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, slug):
		company = self.get_object(slug, request.user)
		company.is_active = False
		company.save()
		return Response(status=status.HTTP_204_NO_CONTENT)


class CompanyRolesListView(APIView):
	"""
	GET: список ролей пользователей в конкретной компании
	"""
	permission_classes = [IsAuthenticated]

	def get(self, request, company_slug):
		company = get_object_or_404(
			Company,
			slug=company_slug,
			user_roles__user=request.user)
		roles = company.user_roles.all()
		serializer = UserCompanyRoleSerializer(roles, many=True)
		return Response(serializer.data)

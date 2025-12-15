from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import TimePeriod, Scenario
from .serializers import TimePeriodSerializer, ScenarioSerializer


class TimePeriodListView(APIView):
	"""
	GET: список доступных периодов для компаний пользователя
	"""
	permission_classes = [IsAuthenticated]

	def get(self, request):
		periods = TimePeriod.objects.filter(
			company__user_roles__user=request.user).distinct()
		serializer = TimePeriodSerializer(periods, many=True)
		return Response(serializer.data)


class ScenarioListCreateView(APIView):
	"""
	GET: список сценариев
	POST: создание нового сценария
	"""
	permission_classes = [IsAuthenticated]

	def get(self, request):
		scenarios = Scenario.objects.filter(
			company__user_roles__user=request.user).distinct()
		# Опционально: фильтр по ?active=true
		if request.query_params.get('active') == 'true':
			scenarios = scenarios.filter(is_active=True)
		serializer = ScenarioSerializer(scenarios, many=True)
		return Response(serializer.data)

	def post(self, request):
		serializer = ScenarioSerializer(
			data=request.data,
			context={'request': request})
		if serializer.is_valid():
			# Можно добавить автоматическую проверку прав на компанию
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScenarioDetailView(APIView):
	"""
	GET, PUT, PATCH, DELETE для конкретного сценария
	"""
	permission_classes = [IsAuthenticated]

	def get_object(self, pk, user):
		return get_object_or_404(
			Scenario,
			slug=pk,
			company__user_roles__user=user
		)

	def get(self, request, slug):
		scenario = self.get_object(slug, request.user)
		serializer = ScenarioSerializer(scenario)
		return Response(serializer.data)

	def put(self, request, slug):
		scenario = self.get_object(slug, request.user)
		serializer = ScenarioSerializer(scenario, data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def patch(self, request, slug):
		scenario = self.get_object(slug, request.user)
		serializer = ScenarioSerializer(scenario, data=request.data, partial=True)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, slug):
		scenario = self.get_object(slug, request.user)
		scenario.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)

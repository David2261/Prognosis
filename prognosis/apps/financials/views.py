from prognosis.apps.data_ingestion.tests.test_serializers import scenario
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import FinancialLine
from .serializers import FinancialLineSerializer


class FinancialLineListCreateView(APIView):
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		return FinancialLine.objects.filter(
			company__user_roles__user=self.request.user
		).select_related(
			"scenario", "period",
			"article", "cost_center",
			"department", "project", "account"
		).prefetch_related()

	def get(self, request):
		queryset = self.get_queryset()

		# Filters (examples:
		scenario_q = request.query_params.get("scenario")
		period_q = request.query_params.get("period")
		article_q = request.query_params.get("article")
		company_q = request.query_params.get("company")

		if company_q:
			if request.user.company_roles.filter(company_id=company_q).exists():
				queryset = queryset.filter(company_id=company_q)
			else:
				return Response(
					{"detail": "You do not have access to this company."},
					status=status.HTTP_403_FORBIDDEN)

		if scenario_q:
			if scenario_q.isdigit():
				queryset = queryset.filter(scenario_id=int(scenario_q))
			else:
				queryset = queryset.filter(scenario__slug=scenario_q)

		if period_q:
			if period_q.isdigit():
				if len(period_q) == 4:  # год
					queryset = queryset.filter(period__year=int(period_q))
				else:
					queryset = queryset.filter(period_id=int(period_q))
			elif '-' in period_q and len(period_q) == 7:  # YYYY-MM
				year, month = period_q.split('-')
				if year.isdigit() and month.isdigit():
					queryset = queryset.filter(
						period__year=int(year),
						period__month=int(month))
			elif period_q.startswith('Q'):  # 2025-Q1
				parts = period_q.split('-Q')
				if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
					queryset = queryset.filter(
						period__year=int(parts[0]),
						period__quarter=int(parts[1]))

		if article_q:
			# accept either numeric id or slug
			if article_q.isdigit():
				queryset = queryset.filter(article_id=int(article_q))
			else:
				queryset = queryset.filter(article__slug=article_q)

		serializer = FinancialLineSerializer(queryset, many=True)
		return Response(serializer.data)

	def post(self, request):
		# Определяем компанию: либо из данных, либо из первой доступной роли
		company_id = request.data.get("company")

		if company_id:
			# Проверяем, имеет ли пользователь доступ к указанной компании
			if not request.user.company_roles.filter(company_id=company_id).exists():
				return Response(
					{"detail": "You do not have permission to create data for this company."},
					status=status.HTTP_403_FORBIDDEN
				)
		else:
			# Если не указана — берём первую доступную компанию пользователя
			user_role = request.user.company_roles.first()
			if not user_role:
				return Response(
					{"detail": "User is not associated with any company."},
					status=status.HTTP_400_BAD_REQUEST
				)
			company_id = user_role.company_id
			request.data["company"] = company_id

		serializer = FinancialLineSerializer(
			data=request.data,
			context={'request': request}
		)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)

		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FinancialLineDetailView(APIView):
	permission_classes = [IsAuthenticated]

	def get_object(self, slug):
		user = self.request.user
		company_ids = user.company_roles.values_list('company_id', flat=True)

		return get_object_or_404(
			FinancialLine,
			slug=slug,
			company_id__in=company_ids
		)

	def get(self, request, slug):
		obj = self.get_object(slug)
		serializer = FinancialLineSerializer(obj)
		return Response(serializer.data)

	def put(self, request, slug):
		obj = self.get_object(slug)
		serializer = FinancialLineSerializer(obj, data=request.data, context={'request': request})
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def patch(self, request, slug):
		obj = self.get_object(slug)
		serializer = FinancialLineSerializer(obj, data=request.data, partial=True, context={'request': request})
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, slug):
		obj = self.get_object(slug)
		obj.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)

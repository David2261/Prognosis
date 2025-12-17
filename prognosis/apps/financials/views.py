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
		)

	def get(self, request):
		queryset = self.get_queryset()

		# Filters (examples:
		# ?scenario=slug-or-id, ?period=YYYY-MM or id, ?article=slug-or-id)
		scenario_q = request.query_params.get("scenario")
		period_q = request.query_params.get("period")
		article_q = request.query_params.get("article")

		if scenario_q:
			# accept either numeric id or slug
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
		serializer = FinancialLineSerializer(
			data=request.data,
			context={'request': request})
		if serializer.is_valid():
			user_role = request.user.company_roles.first()
			if not user_role:
				return Response(
					{"detail": "User not associated with any company."},
					status=status.HTTP_400_BAD_REQUEST)
			serializer.save(company=user_role.company)
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FinancialLineDetailView(APIView):
	permission_classes = [IsAuthenticated]

	def get_object(self, pk):
		return get_object_or_404(
			FinancialLine,
			pk=pk,
			company__user_roles__user=self.request.user
		)

	def get(self, request, pk):
		obj = self.get_object(pk)
		serializer = FinancialLineSerializer(obj)
		return Response(serializer.data)

	def put(self, request, pk):
		obj = self.get_object(pk)
		serializer = FinancialLineSerializer(
			obj,
			data=request.data,
			context={"request": request})
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def patch(self, request, pk):
		obj = self.get_object(pk)
		serializer = FinancialLineSerializer(
			obj,
			data=request.data,
			partial=True,
			context={"request": request})
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, pk):
		obj = self.get_object(pk)
		obj.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)

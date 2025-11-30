from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from prognosis.settings import DEBUG
from .models import User
from .serializers import LoginSerializer, UserSerializer

class LoginView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		serializer = LoginSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		email = serializer.validated_data['email']
		password = serializer.validated_data['password']

		user = authenticate(request, email=email, password=password)
		if not user:
			return Response(
				{"detail": "Неверные учетные данные"},
				status=status.HTTP_401_UNAUTHORIZED
			)

		if not user.is_active:
			return Response(
				{"detail": "Аккаунт заблокирован"},
				status=status.HTTP_401_UNAUTHORIZED
			)

		refresh = RefreshToken.for_user(user)

		response = Response({
			"user": UserSerializer(user).data,
			"message": "Успешный вход"
		}, status=status.HTTP_200_OK)

		# HttpOnly куки
		response.set_cookie(
			key='access',
			value=str(refresh.access_token),
			httponly=True,
			secure=not request.is_secure() if DEBUG else True,
			samesite='Lax',
			max_age=15*60
		)
		response.set_cookie(
			key='refresh',
			value=str(refresh),
			httponly=True,
			secure=not request.is_secure() if DEBUG else True,
			samesite='Lax',
			max_age=7*24*60*60
		)

		return response


class LogoutView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		try:
			refresh_token = request.COOKIES.get('refresh')
			token = RefreshToken(refresh_token)
			token.blacklist()

			response = Response({"detail": "Успешный выход"}, status=status.HTTP_205_RESET_CONTENT)
			response.delete_cookie('access')
			response.delete_cookie('refresh')
			return response
		except Exception as e:
			return Response({"detail": "Ошибка выхода"}, status=status.HTTP_400_BAD_REQUEST)


class UserView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		return Response(UserSerializer(request.user).data)
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from authentication.views import LoginView, LogoutView, UserView

User = get_user_model()


@pytest.mark.django_db
class TestAuthViews:
	def test_login_success_sets_cookies_and_returns_user(self, monkeypatch):
		user = User.objects.create_user(email='test@example.com', password='testpass123')

		class DummyRefresh:
			def __init__(self):
				self.access_token = 'access-token-123'

			def __str__(self):
				return 'refresh-token-456'

		class DummyRT:
			@classmethod
			def for_user(cls, _user):
				return DummyRefresh()

		monkeypatch.setattr('authentication.views.RefreshToken', DummyRT)

		factory = APIRequestFactory()
		request = factory.post('/login/', {'email': 'test@example.com', 'password': 'testpass123'}, format='json')
		view = LoginView.as_view()
		response = view(request)

		assert response.status_code == 200
		assert response.data['user']['email'] == user.email
		assert 'access' in response.cookies
		assert 'refresh' in response.cookies

	def test_login_invalid_credentials_returns_401(self):
		User.objects.create_user(email='test@example.com', password='correctpass')
		factory = APIRequestFactory()
		request = factory.post('/login/', {'email': 'test@example.com', 'password': 'wrongpass'}, format='json')
		view = LoginView.as_view()
		response = view(request)

		assert response.status_code == 401
		assert 'detail' in response.data

	def test_logout_calls_blacklist_and_returns_205(self, monkeypatch):
		user = User.objects.create_user(email='test@example.com', password='testpass123')

		called = {'blacklisted': False}

		class DummyToken:
			def __init__(self, token_str):
				self.token_str = token_str

			def blacklist(self):
				called['blacklisted'] = True

		# Возвращаем объект с методом blacklist при вызове RefreshToken(...)
		monkeypatch.setattr('authentication.views.RefreshToken', lambda token: DummyToken(token))

		factory = APIRequestFactory()
		request = factory.post('/logout/', {}, format='json')
		request.COOKIES['refresh'] = 'some-refresh-token'
		force_authenticate(request, user=user)

		view = LogoutView.as_view()
		response = view(request)

		assert response.status_code == 205
		assert called['blacklisted'] is True

	def test_logout_with_invalid_token_returns_400(self, monkeypatch):
		def bad_init(token):
			raise Exception("bad token")

		monkeypatch.setattr('authentication.views.RefreshToken', lambda token: (_ for _ in ()).throw(Exception("bad token")))

		user = User.objects.create_user(email='test2@example.com', password='testpass123')
		factory = APIRequestFactory()
		request = factory.post('/logout/', {}, format='json')
		request.COOKIES['refresh'] = 'invalid'
		force_authenticate(request, user=user)

		view = LogoutView.as_view()
		response = view(request)

		assert response.status_code == 400
		assert 'detail' in response.data

	def test_user_view_requires_auth_and_returns_user(self):
		user = User.objects.create_user(email='test@example.com', password='testpass123')
		factory = APIRequestFactory()
		request = factory.get('/user/')
		force_authenticate(request, user=user)

		view = UserView.as_view()
		response = view(request)

		assert response.status_code == 200
		assert response.data['email'] == user.email

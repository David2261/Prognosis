import pytest
from django.contrib.auth import get_user_model
from apps.authentication.models import Role, UserRole


User = get_user_model()

@pytest.mark.django_db
class TestUserManager:
	def test_create_user_success(self):
		user = User.objects.create_user(email='test@example.com', password='testpass123')
		assert user.email == 'test@example.com'
		assert user.is_active is True
		assert user.is_staff is False

	def test_create_user_without_email_raises_error(self):
		with pytest.raises(ValueError):
			User.objects.create_user(email='', password='testpass123')

	def test_create_user_normalizes_email(self):
		user = User.objects.create_user(email='TEST@EXAMPLE.COM', password='testpass123')
		assert user.email == 'TEST@example.com'

	def test_create_superuser_success(self):
		user = User.objects.create_superuser(email='admin@example.com', password='testpass123')
		assert user.is_staff is True
		assert user.is_superuser is True

	def test_create_user_with_extra_fields(self):
		user = User.objects.create_user(email='test@example.com', password='testpass123', full_name='John Doe')
		assert user.full_name == 'John Doe'


@pytest.mark.django_db
class TestUser:
	def test_user_string_representation(self):
		user = User.objects.create_user(email='test@example.com', password='testpass123')
		assert str(user) == 'test@example.com'

	def test_user_email_unique(self):
		User.objects.create_user(email='test@example.com', password='testpass123')
		with pytest.raises(Exception):
			User.objects.create_user(email='test@example.com', password='testpass123')

	def test_user_default_values(self):
		user = User.objects.create_user(email='test@example.com', password='testpass123')
		assert user.is_active is True
		assert user.is_staff is False
		assert user.created_at is not None


@pytest.mark.django_db
class TestRole:
	def test_role_creation(self):
		role = Role.objects.create(name='admin', description='Administrator role')
		assert role.name == 'admin'
		assert role.description == 'Administrator role'

	def test_role_string_representation(self):
		role = Role.objects.create(name='editor')
		assert str(role) == 'editor'

	def test_role_name_unique(self):
		Role.objects.create(name='viewer')
		with pytest.raises(Exception):
			Role.objects.create(name='viewer')


@pytest.mark.django_db
class TestUserRole:
	def test_user_role_creation(self):
		user = User.objects.create_user(email='test@example.com', password='testpass123')
		role = Role.objects.create(name='admin')
		user_role = UserRole.objects.create(user=user, role=role)
		assert user_role.user == user
		assert user_role.role == role

	def test_user_role_string_representation(self):
		user = User.objects.create_user(email='test@example.com', password='testpass123')
		role = Role.objects.create(name='admin')
		user_role = UserRole.objects.create(user=user, role=role)
		assert str(user_role) == 'test@example.com — admin'

	def test_user_role_unique_constraint(self):
		user = User.objects.create_user(email='test@example.com', password='testpass123')
		role = Role.objects.create(name='admin')
		UserRole.objects.create(user=user, role=role)
		with pytest.raises(Exception):
			UserRole.objects.create(user=user, role=role)

	def test_user_role_cascade_delete(self):
		user = User.objects.create_user(email='test@example.com', password='testpass123')
		role = Role.objects.create(name='admin')
		UserRole.objects.create(user=user, role=role)
		user.delete()
		assert UserRole.objects.count() == 0

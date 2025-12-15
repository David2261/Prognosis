from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.models import BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
	def create_user(self, email, password=None, **extra_fields):
		if not email:
			raise ValueError('Email обязателен')
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)
		return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
	email = models.EmailField(unique=True)
	full_name = models.CharField(max_length=255, blank=True, null=True)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(auto_now=True)

	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)

	objects = UserManager()

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []

	def __str__(self):
		return self.email

	def get_full_name(self):
		"""Return the full name for the user."""
		return self.full_name or self.email

	def get_short_name(self):
		"""Return a short name for the user."""
		if self.full_name:
			return self.full_name.split(' ')[0]
		return self.email

	@property
	def username(self):
		"""Compatibility property for code expecting `user.username`."""
		return self.email

	class Meta:
		verbose_name = 'User'
		verbose_name_plural = 'Users'


class Role(models.Model):
	name = models.CharField(max_length=50, unique=True)
	description = models.TextField(blank=True)

	def __str__(self):
		return self.name


class UserRole(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	role = models.ForeignKey(Role, on_delete=models.CASCADE)

	class Meta:
		unique_together = ('user', 'role')

	def __str__(self):
		return f"{self.user.email} — {self.role.name}"

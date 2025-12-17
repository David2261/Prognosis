from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator
from django.utils.text import slugify
from core.models import TimeStampedModel
import datetime


def fiscal_year_start_default():
	"""Return Jan 1st of the current year.
	Top-level function so Django migrations can serialize it."""
	today = datetime.date.today()
	return datetime.date(today.year, 1, 1)


class Company(TimeStampedModel):
	"""
	Тенант — компания / юрлицо.
	Все данные в системе (финансовые, справочники, пользователи)
	привязываются к Company.
	"""
	name = models.CharField(
		_("Название компании"),
		max_length=255,
		help_text=_("Полное или краткое наименование компании")
	)

	inn = models.CharField(
		_("ИНН"),
		max_length=12,
		null=True,
		blank=True,
		validators=[MinLengthValidator(10)],
		help_text=_("ИНН компании (10 или 12 символов)")
	)

	currency_default = models.CharField(
		_("Основная валюта"),
		max_length=3,
		default="RUB",
		help_text=_("ISO-код валюты по умолчанию (RUB, USD, EUR и т.д.)")
	)

	fiscal_year_start = models.DateField(
		_("Начало финансового года"),
		default=fiscal_year_start_default,
		help_text=_("Дата начала финансового года (обычно 1 января)")
	)

	slug = models.SlugField(max_length=255, unique=True, blank=True)

	is_active = models.BooleanField(
		_("Активна"),
		default=True,
		help_text=_("Если False — компания архивирована, доступ запрещён")
	)

	class Meta:
		verbose_name = _("Компания")
		verbose_name_plural = _("Компании")
		ordering = ["name"]
		indexes = [
			models.Index(fields=["name"]),
			models.Index(fields=["inn"]),
			models.Index(fields=["is_active"]),
		]

	def __str__(self) -> str:
		return self.name

	def _generate_unique_slug(self):
		base = slugify(self.name) or "company"
		slug = base
		count = 1
		while Company.objects.filter(
			slug=slug).exclude(pk=getattr(self, 'pk', None)).exists():
			slug = f"{base}-{count}"
			count += 1
		return slug

	def save(self, *args, **kwargs):
		if not self.slug or not self.pk:
			base = slugify(self.name) or "company"
			slug = base
			i = 1
			while Company.objects.exclude(pk=self.pk).filter(slug=slug).exists():
				slug = f"{base}-{i}"
				i += 1
			self.slug = slug
		super().save(*args, **kwargs)


class UserCompanyRole(models.Model):
	"""
	Связь пользователя с компанией и его роль в ней.
	Позволяет одному пользователю работать
	в нескольких компаниях с разными ролями.
	"""
	user = models.ForeignKey(
		"authentication.User",  # ссылка на модель пользователя из auth сервиса
		on_delete=models.CASCADE,
		related_name="company_roles"
	)
	company = models.ForeignKey(
		Company,
		on_delete=models.CASCADE,
		related_name="user_roles"
	)
	role = models.CharField(  # можно вынести в отдельный справочник ролей
		_("Роль"),
		max_length=50,
		choices=[
			("admin", _("Администратор компании")),
			("finance", _("Финансист")),
			("analyst", _("Аналитик")),
			("viewer", _("Просмотр")),
		],
		default="viewer"
	)

	class Meta:
		unique_together = ("user", "company")
		verbose_name = _("Роль пользователя в компании")
		verbose_name_plural = _("Роли пользователей в компаниях")

	def __str__(self) -> str:
		return f"{self.user} — {self.company} ({self.role})"

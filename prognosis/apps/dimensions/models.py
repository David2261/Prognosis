from django.db import models
from django.utils.translation import gettext_lazy as _
from treebeard.mp_tree import MP_Node
from core.models import CompanyRelatedModel


class ChartOfAccounts(CompanyRelatedModel):
	"""План счетов (счета бухгалтерского учёта)"""
	code = models.CharField(_("Код счета"), max_length=20, unique=True)
	name = models.CharField(_("Наименование"), max_length=255)
	slug = models.SlugField(max_length=255, blank=True)
	parent = models.ForeignKey(
		'self',
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		verbose_name=_("Родительский счет"))
	is_active = models.BooleanField(_("Активен"), default=True)

	class Meta:
		verbose_name = _("Счет плана счетов")
		verbose_name_plural = _("План счетов")
		unique_together = ("company", "code")
		ordering = ["code"]

	def __str__(self):
		return f"{self.code} {self.name}"

	def _generate_unique_slug(self):
		from django.utils.text import slugify
		base = slugify(self.name) or slugify(self.code) or "coa"
		slug = base
		count = 1
		while ChartOfAccounts.objects.filter(
			company=self.company,
			slug=slug).exclude(pk=getattr(self, 'pk', None)).exists():
			slug = f"{base}-{count}"
			count += 1
		return slug

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = self._generate_unique_slug()
		super().save(*args, **kwargs)


class BudgetArticle(MP_Node):
	"""Статьи бюджета — иерархические (доходы, расходы, OPEX, CAPEX и т.д.)"""
	company = models.ForeignKey(
		"accounts.Company",
		on_delete=models.CASCADE,
		verbose_name=_("Компания"))
	code = models.CharField(_("Код статьи"), max_length=50)
	name = models.CharField(_("Наименование"), max_length=255)
	slug = models.SlugField(max_length=255, blank=True)
	article_type = models.CharField(
		_("Тип статьи"),
		max_length=20,
		choices=[
			("revenue", _("Доход")),
			("expense", _("Расход")),
			("capex", _("Капитальные затраты")),
			("opex", _("Операционные затраты")),
			("other", _("Прочее")),
		]
	)
	is_active = models.BooleanField(_("Активна"), default=True)

	class Meta:
		verbose_name = _("Статья бюджета")
		verbose_name_plural = _("Статьи бюджета")
		unique_together = ("company", "code")

	def __str__(self):
		return f"{self.code} {self.name}"

	def _generate_unique_slug(self):
		from django.utils.text import slugify
		base = slugify(self.name) or slugify(self.code) or "article"
		slug = base
		count = 1
		while BudgetArticle.objects.filter(
			company=self.company,
			slug=slug).exclude(pk=getattr(self, 'pk', None)).exists():
			slug = f"{base}-{count}"
			count += 1
		return slug

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = self._generate_unique_slug()
		super().save(*args, **kwargs)


class CostCenter(CompanyRelatedModel):
	"""Центры финансовой ответственности (ЦФО)"""
	code = models.CharField(_("Код ЦФО"), max_length=50)
	name = models.CharField(_("Наименование"), max_length=255)
	slug = models.SlugField(max_length=255, blank=True)
	parent = models.ForeignKey(
		'self',
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		verbose_name=_("Родительский ЦФО"))
	manager = models.ForeignKey(
		"authentication.User",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		verbose_name=_("Ответственный"))

	class Meta:
		verbose_name = _("Центр финансовой ответственности")
		verbose_name_plural = _("Центры финансовой ответственности")
		unique_together = ("company", "code")

	def __str__(self):
		return f"{self.code} {self.name}"

	def _generate_unique_slug(self):
		from django.utils.text import slugify
		base = slugify(self.name) or slugify(self.code) or "cc"
		slug = base
		count = 1
		while CostCenter.objects.filter(
			company=self.company,
			slug=slug).exclude(pk=getattr(self, 'pk', None)).exists():
			slug = f"{base}-{count}"
			count += 1
		return slug

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = self._generate_unique_slug()
		super().save(*args, **kwargs)


class Department(MP_Node, CompanyRelatedModel):
	"""Подразделения — иерархические"""
	company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE)
	code = models.CharField(_("Код"), max_length=50)
	name = models.CharField(_("Наименование"), max_length=255)
	slug = models.SlugField(max_length=255, blank=True)
	head = models.ForeignKey(
		"authentication.User",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		verbose_name=_("Руководитель"))

	class Meta(MP_Node.Meta, CompanyRelatedModel.Meta):
		verbose_name = _("Подразделение")
		verbose_name_plural = _("Подразделения")
		unique_together = ("company", "code")

	def __str__(self):
		return self.name

	def _generate_unique_slug(self):
		from django.utils.text import slugify
		base = slugify(self.name) or "dept"
		slug = base
		count = 1
		while Department.objects.filter(
			company=self.company,
			slug=slug).exclude(pk=getattr(self, 'pk', None)).exists():
			slug = f"{base}-{count}"
			count += 1
		return slug

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = self._generate_unique_slug()
		super().save(*args, **kwargs)


class Project(CompanyRelatedModel):
	"""Проекты"""
	code = models.CharField(_("Код проекта"), max_length=50)
	name = models.CharField(_("Наименование"), max_length=255)
	slug = models.SlugField(max_length=255, blank=True)
	start_date = models.DateField(_("Дата начала"), null=True, blank=True)
	end_date = models.DateField(_("Дата окончания"), null=True, blank=True)
	manager = models.ForeignKey(
		"authentication.User",
		null=True,
		blank=True,
		on_delete=models.SET_NULL)

	class Meta:
		verbose_name = _("Проект")
		verbose_name_plural = _("Проекты")
		unique_together = ("company", "code")

	def __str__(self):
		return f"{self.code} {self.name}"

	def _generate_unique_slug(self):
		from django.utils.text import slugify
		base = slugify(self.name) or slugify(self.code) or "project"
		slug = base
		count = 1
		while Project.objects.filter(
			company=self.company,
			slug=slug).exclude(pk=getattr(self, 'pk', None)).exists():
			slug = f"{base}-{count}"
			count += 1
		return slug

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = self._generate_unique_slug()
		super().save(*args, **kwargs)

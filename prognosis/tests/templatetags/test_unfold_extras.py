import pytest
from django.template import Template, Context
from django.conf import settings
from django.template.engine import Engine


def get_template_engine():
    return Engine(
        dirs=settings.TEMPLATES[0]['DIRS'],
        app_dirs=True,
        context_processors=settings.TEMPLATES[0]['OPTIONS'].get('context_processors', []),
        debug=settings.DEBUG,
        loaders=settings.TEMPLATES[0]['OPTIONS'].get('loaders'),
        string_if_invalid=settings.TEMPLATES[0]['OPTIONS'].get('string_if_invalid'),
        libraries={
            'unfold_extras': 'prognosis.templatetags.unfold_extras',
        },
        builtins=['prognosis.templatetags.unfold_extras'],
    )

engine = get_template_engine()


class TestGetAttrFilter:
	def render_template(self, template_string, context_dict=None):
		"""Удобная обёртка для рендеринга шаблона с контекстом"""
		context_dict = context_dict or {}
		template = engine.from_string(template_string)
		return template.render(Context(context_dict))

	def test_getattr_simple_attribute(self):
		"""Тест получения простого атрибута"""
		class Obj:
			name = "John"

		result = self.render_template(
			"{% load unfold_extras %}"
			"{{ obj|getattr:'name' }}",
			{"obj": Obj()}
		)
		assert result.strip() == "John"

	def test_getattr_callable_attribute(self):
		"""Тест получения вызываемого атрибута"""
		class Obj:
			def get_name(self):
				return "Called method"

		result = self.render_template(
			"{% load unfold_extras %}"
			"{{ obj|getattr:'get_name' }}",
			{"obj": Obj()}
		)
		assert result.strip() == "Called method"

	def test_getattr_callable_without_parentheses(self):
		"""Фильтр должен вызывать callable автоматически"""
		class Obj:
			def __call__(self):
				return "Instance called"

		obj = Obj()
		result = self.render_template(
			"{% load unfold_extras %}"
			"{{ obj|getattr:'__call__' }}",
			{"obj": obj}
		)
		assert result.strip() == "Instance called"

	def test_getattr_non_existent_attribute_returns_default(self):
		"""Тест получения несуществующего атрибута"""
		class Obj:
			pass

		result = self.render_template(
			"{% load unfold_extras %}"
			"{{ obj|getattr:'missing' }}",
			{"obj": Obj()}
		)
		assert result.strip() == ""  # Возвращает default=''

	def test_getattr_non_existent_attribute_with_custom_default(self):
		"""Тест получения несуществующего атрибута с кастомным default"""
		class Obj:
			pass

		result = self.render_template(
			"{% load unfold_extras %}"
			"{{ obj|getattr:'missing':'Not found' }}",
			{"obj": Obj()}
		)
		assert result.strip() == "Not found"

	def test_getattr_exception_in_callable_returns_default(self):
		"""Если callable падает — возвращается default"""
		class Obj:
			def bad_method(self):
				raise ValueError("Boom!")

		result = self.render_template(
			"{% load unfold_extras %}"
			"{{ obj|getattr:'bad_method' }}",
			{"obj": Obj()}
		)
		assert result.strip() == ""  # Согласно логике фильтра

	def test_getattr_on_none_returns_empty(self):
		"""Тест работы с None объектом"""
		result = self.render_template(
			"{% load unfold_extras %}"
			"{{ none_obj|getattr:'anything' }}",
			{"none_obj": None}
		)
		assert result.strip() == ""

	def test_getattr_on_none_with_custom_default(self):
		"""Тест работы с None объектом с кастомным default"""
		result = self.render_template(
			"{% load unfold_extras %}"
			"{{ none_obj|getattr:'anything':'Default for None' }}",
			{"none_obj": None}
		)
		assert result.strip() == "Default for None"

	def test_getattr_with_dynamic_attribute_name(self):
		"""Тест с динамическим именем атрибута"""
		class Obj:
			dynamic = "Dynamic value"

		result = self.render_template(
			"{% load unfold_extras %}"
			"{{ obj|getattr:attribute_name }}",
			{"obj": Obj(), "attribute_name": "dynamic"}
		)
		assert result.strip() == "Dynamic value"

	def test_getattr_nested_attribute(self):
		"""Тест получения вложенного атрибута"""
		class Inner:
			value = "Nested"
		
		class Obj:
			inner = Inner()

		result = self.render_template(
			"{% load unfold_extras %}"
			"{{ obj|getattr:'inner'|getattr:'value' }}",
			{"obj": Obj()}
		)
		assert result.strip() == "Nested"

	def test_getattr_property(self):
		"""Тест получения property"""
		class Obj:
			@property
			def computed(self):
				return "Property value"

		result = self.render_template(
			"{% load unfold_extras %}"
			"{{ obj|getattr:'computed' }}",
			{"obj": Obj()}
		)
		assert result.strip() == "Property value"

	def test_getattr_with_boolean_attribute(self):
		"""Тест получения boolean атрибута"""
		class Obj:
			is_active = True
			is_disabled = False

		result1 = self.render_template(
			"{% load unfold_extras %}"
			"{{ obj|getattr:'is_active' }}",
			{"obj": Obj()}
		)
		assert result1.strip() == "True"

		result2 = self.render_template(
			"{% load unfold_extras %}"
			"{{ obj|getattr:'is_disabled' }}",
			{"obj": Obj()}
		)
		assert result2.strip() == "False"

	def test_getattr_with_numeric_attribute(self):
		"""Тест получения числового атрибута"""
		class Obj:
			count = 42
			price = 19.99

		result1 = self.render_template(
			"{% load unfold_extras %}"
			"{{ obj|getattr:'count' }}",
			{"obj": Obj()}
		)
		assert result1.strip() == "42"

		result2 = self.render_template(
			"{% load unfold_extras %}"
			"{{ obj|getattr:'price' }}",
			{"obj": Obj()}
		)
		assert result2.strip() == "19.99"


# Дополнительные тесты для проверки edge cases
def test_getattr_filter_directly():
	"""Прямой тест фильтра без рендеринга шаблона"""
	from prognosis.templatetags.unfold_extras import getattr as getattr_filter
	
	class TestClass:
		name = "Direct Test"
		def method(self):
			return "Method result"
	
	obj = TestClass()
	
	# Простой атрибут
	assert getattr_filter(obj, 'name') == "Direct Test"
	
	# Вызываемый атрибут
	assert getattr_filter(obj, 'method') == "Method result"
	
	# Несуществующий атрибут
	assert getattr_filter(obj, 'missing') == ""
	
	# Несуществующий атрибут с default
	assert getattr_filter(obj, 'missing', 'Custom default') == "Custom default"
	
	# None объект
	assert getattr_filter(None, 'anything') == ""
	
	# None объект с default
	assert getattr_filter(None, 'anything', 'None default') == "None default"

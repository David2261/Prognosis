import os
import django
import pytest
from django.conf import settings


def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prognosis.settings')
    django.setup()


@pytest.fixture
def django_db_setup():
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
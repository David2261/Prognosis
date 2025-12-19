import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prognosis.settings')

app = Celery('prognosis')

# Read Celery config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks from installed apps
app.autodiscover_tasks()

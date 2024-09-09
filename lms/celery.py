from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.settings')

# Create the Celery app instance
app = Celery('lms')

# Load settings from Django's settings.py, using the CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover tasks from all registered Django app configs
app.autodiscover_tasks()

# Optional: Set some default configuration
app.conf.broker_url = 'redis://localhost:6379/0'  # Pointing to Redis running locally

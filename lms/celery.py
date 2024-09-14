from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab


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

app.conf.beat_schedule = {
    'cancel-expired-reservations-daily': {
        'task': 'libraryMS.tasks.cancel_expired_reservations',
        'schedule': crontab(minute=0, hour=9),
    },
    'send-reservation-available-notifications': {
        'task': 'libraryMS.tasks.send_reservation_available_notifications',
        'schedule': crontab(minute=0, hour=9),
    },
    'send-due-date-notifications': {
        'task': 'libraryMS.tasks.send_due_date_notifications',
        'schedule': crontab(minute=0, hour=9),
    },
    'send_overdue_notifications': {
        'task': 'libraryMS.tasks.send_overdue_notifications',
        'schedule': crontab(minute=0, hour=9),
    }
}

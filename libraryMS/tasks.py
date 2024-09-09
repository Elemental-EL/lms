from celery import shared_task
from libraryMS.models import Notification
from django.contrib.auth.models import User


@shared_task
def send_in_app_notification(user_id, message):
    pass

from celery import shared_task
from .utils import send_newsletter_email


@shared_task
def send_newsletter_task(subject, message, recipient_list):
    send_newsletter_email(subject, message, recipient_list)

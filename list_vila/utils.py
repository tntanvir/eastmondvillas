from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
import random
from django.utils import timezone
from django.conf import settings

User = get_user_model()

def send_email(subject, name, email, phone, message):
    try:
        

        subject = subject
        to_email = settings.EMAIL_HOST_USER

        context = {'message': message, 'name': name, 'email': email, 'phone': phone}

        html_content = render_to_string('email.html', context)
        text_content = message

        msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False

from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Notification

User = get_user_model()

def create_notification_for_customers(user,title: str, data=None):
    data = data or {}
    customers = User.objects.exclude(id=user.id)

    channel_layer = get_channel_layer()

    for user in customers:
        notif = Notification.objects.create(
            user=user,
            title=title,
            data=data,
        )

        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}",               
            {
                "type": "notify",           
                "payload": {
                    "id": notif.id,
                    "title": notif.title,
                    "data": notif.data,
                    "is_read": notif.is_read,
                    "created_at": notif.created_at.isoformat(),
                },
            },
        )


def create_notification_for_admin_manager_agent(user,title: str, data=None):
    data = data or {}
    customers = User.objects.exclude(id=user.id,role__in=["customer"])

    channel_layer = get_channel_layer()

    for user in customers:
        notif = Notification.objects.create(
            user=user,
            title=title,
            data=data,
        )

        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}",               
            {
                "type": "notify",           
                "payload": {
                    "id": notif.id,
                    "title": notif.title,
                    "data": notif.data,
                    "is_read": notif.is_read,
                    "created_at": notif.created_at.isoformat(),
                },
            },
        )



def notify_admins_and_managers(title: str, data=None):
    
    data = data or {}

    users = User.objects.filter(role__in=["admin", "manager", "agent"])

    channel_layer = get_channel_layer()

    for user in users:
        notif = Notification.objects.create(
            user=user,
            title=title,
            data=data,
        )

        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}",
            {
                "type": "notify",
                "payload": {
                    "id": notif.id,
                    "title": notif.title,
                    "data": notif.data,
                    "is_read": notif.is_read,
                    "created_at": notif.created_at.isoformat(),
                },
            },
        )

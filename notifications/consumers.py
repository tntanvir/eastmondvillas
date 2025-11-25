# # notifications/consumers.py
# from urllib.parse import parse_qs
# from channels.generic.websocket import AsyncJsonWebsocketConsumer
# from channels.db import database_sync_to_async


# class NotificationsConsumer(AsyncJsonWebsocketConsumer):
#     async def connect(self):
#         qs = parse_qs(self.scope["query_string"].decode())
#         token = qs.get("token", [None])[0]

#         user = await self.get_user_from_jwt(token)
#         if user:
#             self.user = user
#             self.group_name = f"user_{user.id}"
#             await self.channel_layer.group_add(self.group_name, self.channel_name)
#             await self.accept()
#         else:
#             await self.close()

#     async def disconnect(self, close_code):
#         if hasattr(self, "group_name"):
#             await self.channel_layer.group_discard(self.group_name, self.channel_name)

#     async def receive_json(self, content):
#         action = content.get("action")
#         if action == "mark_read":
#             nid = content.get("notification_id")
#             if nid:
#                 await self.mark_read(nid, self.user.id)

#     async def notify(self, event):
#         """
#         Called by:
#             channel_layer.group_send(
#                 f"user_{user.id}",
#                 {"type": "notify", "payload": {...}}
#             )
#         """
#         await self.send_json(event["payload"])

#     @database_sync_to_async
#     def get_user_from_jwt(self, token):
#         """
#         Validate JWT and return User instance or None.
#         """
#         if not token:
#             return None

#         if token.startswith("Bearer "):
#             token = token.split(" ", 1)[1]

#         try:
#             from rest_framework_simplejwt.tokens import UntypedToken
#             from django.contrib.auth import get_user_model
#             from django.conf import settings
#             import jwt
#         except Exception:
#             return None

#         User = get_user_model()

#         try:
#             # validate token (signature, expiry, etc.)
#             UntypedToken(token)

#             decoded = jwt.decode(
#                 token,
#                 settings.SECRET_KEY,
#                 algorithms=["HS256"],
#                 options={"verify_signature": False},
#             )

#             user_id = decoded.get("user_id") or decoded.get("user") or decoded.get("sub")
#             if not user_id:
#                 return None

#             return User.objects.filter(id=user_id).first()
#         except Exception:
#             try:
#                 decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
#                 user_id = decoded.get("user_id") or decoded.get("user") or decoded.get("sub")
#                 if not user_id:
#                     return None
#                 return User.objects.filter(id=user_id).first()
#             except Exception:
#                 return None

#     @database_sync_to_async
#     def mark_read(self, nid, user_id):
#         try:
#             from .models import Notification
#             Notification.objects.filter(id=nid, user_id=user_id).update(is_read=True)
#         except Exception:
#             pass










# notifications/consumers.py
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async


class NotificationsConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        qs = parse_qs(self.scope["query_string"].decode())
        token = qs.get("token", [None])[0]

        user = await self.get_user_from_jwt(token)
        if user:
            self.user = user
            self.group_name = f"user_{user.id}"

            # join group
            await self.channel_layer.group_add(self.group_name, self.channel_name)

            # accept connection
            await self.accept()

            # send unseen notifications count immediately after connect
            unseen_count = await self.get_unseen_count(self.user.id)
            await self.send_json(
                {
                    "type": "unseen_notifications",
                    "count": unseen_count,
                }
            )
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content):
        action = content.get("action")
        if action == "mark_read":
            nid = content.get("notification_id")
            if nid:
                await self.mark_read(nid, self.user.id)

                # Optionally send updated unseen count after marking read
                unseen_count = await self.get_unseen_count(self.user.id)
                await self.send_json(
                    {
                        "type": "unseen_notifications",
                        "count": unseen_count,
                    }
                )

    # async def notify(self, event):
    #     """
    #     Called by:
    #         channel_layer.group_send(
    #             f"user_{user.id}",
    #             {"type": "notify", "payload": {...}}
    #         )
    #     """
    #     await self.send_json(event["payload"])
    async def notify(self, event):
        """
        Called by:
            channel_layer.group_send(
                f"user_{user.id}",
                {"type": "notify", "payload": {...}}
            )
        """
        unseen_count = await self.get_unseen_count(self.user.id)

        payload = event.get("payload", {}) or {}
        # add unseen_count to the payload
        payload["unseen_notifications"] = unseen_count

        await self.send_json(payload)
    
    @database_sync_to_async
    def get_user_from_jwt(self, token):
        """
        Validate JWT and return User instance or None.
        """
        if not token:
            return None

        if token.startswith("Bearer "):
            token = token.split(" ", 1)[1]

        try:
            from rest_framework_simplejwt.tokens import UntypedToken
            from django.contrib.auth import get_user_model
            from django.conf import settings
            import jwt
        except Exception:
            return None

        User = get_user_model()

        try:
            # validate token (signature, expiry, etc.)
            UntypedToken(token)

            decoded = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_signature": False},
            )

            user_id = decoded.get("user_id") or decoded.get("user") or decoded.get("sub")
            if not user_id:
                return None

            return User.objects.filter(id=user_id).first()
        except Exception:
            try:
                decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user_id = decoded.get("user_id") or decoded.get("user") or decoded.get("sub")
                if not user_id:
                    return None
                return User.objects.filter(id=user_id).first()
            except Exception:
                return None

    @database_sync_to_async
    def get_unseen_count(self, user_id):
        """
        Return count of unseen notifications for a user.
        """
        from .models import Notification  # <- this is the correct import
        return Notification.objects.filter(user_id=user_id, is_read=False).count()

    @database_sync_to_async
    def mark_read(self, nid, user_id):
        try:
            from .models import Notification
            Notification.objects.filter(id=nid, user_id=user_id).update(is_read=True)
        except Exception:
            pass

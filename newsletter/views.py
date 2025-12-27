from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import NewsLetter
from .serializers import NewsLetterSerializer
from .tasks import send_newsletter_task
from villas.models import Property
from django.contrib.auth import get_user_model

User = get_user_model()


class NewsLetterAPIView(APIView):
    def post(self, request):
        serializer = NewsLetterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        
        manual_users = serializer.validated_data.get("user", [])
        property_obj = serializer.validated_data["property"]

       
        role = request.data.get("role")

        final_user_ids = set()

        if role:
            role_user_ids = User.objects.filter(
                role=role
            ).values_list("id", flat=True)
            final_user_ids.update(role_user_ids)

        if manual_users:
            manual_user_ids = [user.id for user in manual_users]
            final_user_ids.update(manual_user_ids)

        
        if not final_user_ids:
            return Response(
                {"error": "No users found to send newsletter"},
                status=status.HTTP_400_BAD_REQUEST
            )

        
        final_users = User.objects.filter(id__in=final_user_ids)

       
        newsletter = NewsLetter.objects.create(property=property_obj)
        newsletter.user.set(final_users)

        
        recipient_emails = final_users.values_list("email", flat=True)

        send_newsletter_task.delay(
            subject="New Newsletter",
            message=f"Property available: {property_obj.title}",
            recipient_list=list(recipient_emails)
        )

        return Response(
            {
                "message": "Newsletter sent successfully",
                "sent_to_user_ids": list(final_user_ids)
            },
            status=status.HTTP_201_CREATED
        )
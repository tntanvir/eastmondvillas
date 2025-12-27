from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from .serializers import NewsLetterSerializer
from .tasks import send_newsletter_task


class NewsLetterAPIView(APIView):
    def post(self, request):
        serializer = NewsLetterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        newsletter = serializer.save()

        # get all user emails
        users = newsletter.user.all()
        recipient_emails = users.values_list("email", flat=True)

        # background email send
        send_newsletter_task.delay(
            subject="New Newsletter",
            message=f"Property available: {newsletter.property.name}",
            recipient_list=list(recipient_emails)
        )

        return Response(
            {"message": "Newsletter scheduled successfully"},
            status=status.HTTP_201_CREATED
        )

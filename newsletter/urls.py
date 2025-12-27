from django.urls import path
from .views import NewsLetterAPIView


urlpatterns = [
    path("", NewsLetterAPIView.as_view(), name="newsletter-create"),
]

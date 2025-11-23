from django.urls import path
from .views import *

urlpatterns = [
    path("", ResourceListAPIView.as_view(), name="resource-list"),
]

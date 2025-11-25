from django.urls import path
from .views import ActivityLogView

urlpatterns = [
    path('list/', ActivityLogView.as_view(), name='activity-log'),
]
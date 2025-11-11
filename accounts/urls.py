from django.urls import path, include
from .views import UserDeleteView


urlpatterns = [
    path('auth/', include('dj_rest_auth.urls')),
    path('registration/', include('dj_rest_auth.registration.urls')),
    # Admin-only delete of a user by pk
    path('auth/users/<int:pk>/', UserDeleteView.as_view(), name='user-delete'),

]
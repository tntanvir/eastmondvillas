from django.urls import path, include
from .views import UserDeleteView, AdminUserListCreateView, AdminUserDetailView, UserUpdateView


urlpatterns = [
    path('auth/', include('dj_rest_auth.urls')),
    path('registration/', include('dj_rest_auth.registration.urls')),
    # Admin-only delete of a user by pk
    path('auth/users/<int:pk>/', UserDeleteView.as_view(), name='user-delete'),
    # Admin-managed users (list/create and detail/update/delete)
    path('admin/users/', AdminUserListCreateView.as_view(), name='admin-user-list-create'),
    path('admin/users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('auth/user/update/', UserUpdateView.as_view(), name='user-update'),

]
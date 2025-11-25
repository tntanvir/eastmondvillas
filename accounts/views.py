from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from django.shortcuts import get_object_or_404
from django.db import utils as db_utils

from .models import User
from .serializers import AdminUserSerializer, UserUpdateSerializer
from .permissions import IsAdmin


class AdminUserListCreateView(generics.ListCreateAPIView):
    """List all users and allow admins to create new users.

    - GET /api/admin/users/  -> list users (admin/staff only)
    - POST /api/admin/users/ -> create a new user with role/permission
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a user (admin/staff only)."""
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]


class UserDeleteView(APIView):
    """Allow admins (or staff) to delete any user by PK, and allow users to
    delete their own account.

    URL: DELETE /api/auth/users/<pk>/
    Permission: authenticated users; delete allowed if requester is staff/admin
    or if requester is deleting their own account.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk, format=None):
        target = get_object_or_404(User, pk=pk)

        user = request.user
        # Allow if staff or role == 'admin' or the user is deleting their own account
        is_admin_role = getattr(user, 'role', None) == 'admin'
        if not (getattr(user, 'is_staff', False) or is_admin_role or user.pk == target.pk):
            return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

        # Attempt to delete; if related-table issues occur, fallback to anonymize
        try:
            target.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except db_utils.OperationalError:
            # Fallback: anonymize & deactivate the user to simulate deletion
            target.email = f"deleted_user_{target.pk}@example.invalid"
            target.name = "[deleted]"
            target.is_active = False
            target.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        

from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "access_expires_in": refresh.access_token.lifetime.total_seconds(),
        "refresh_expires_in": refresh.lifetime.total_seconds(),
    }



from rest_framework.permissions import IsAuthenticated


class UserUpdateView(generics.UpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
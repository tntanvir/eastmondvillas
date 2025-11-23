# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from .models import Resource
from .serializers import ResourceSerializer
from rest_framework.permissions import IsAuthenticated
from notifications.utils import create_notification_for_admin_manager_agent


class ResourceListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request): 
        """
        Supports:
        - ?category=branding
        - ?search=template
        - ?category=legal_forms&search=contract
        """
        if request.user.is_authenticated and request.user.role in ['admin','manager','agent']:
            queryset = Resource.objects.all()

            category = request.GET.get("category")
            search = request.GET.get("search")

            if category:
                queryset = queryset.filter(category=category)

            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search)
                )

            serializer = ResourceSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not permitted to access this resource"}, status=status.HTTP_401_UNAUTHORIZED)

    def post(self, request):
        if request.user.is_authenticated and request.user.role in ['admin']:
            serializer = ResourceSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                create_notification_for_admin_manager_agent(request.user,"New Resource Added", data=serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not permitted to access this resource"}, status=status.HTTP_401_UNAUTHORIZED)    

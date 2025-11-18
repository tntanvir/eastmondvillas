from django.db import transaction
import json
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated

from . import google_calendar_service


from .models import Property, Media, Booking
from .serializers import PropertySerializer , BookingSerializer


from accounts.permissions import IsAdminOrManager, IsAgentWithFullAccess, IsAssignedAgentReadOnly, IsOwnerOrAdminOrManager

class PropertyViewSet(viewsets.ModelViewSet):

    serializer_class = PropertySerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        
        user = self.request.user

        if not user.is_authenticated:
            return Property.objects.filter(status=Property.StatusType.PUBLISHED).order_by('-created_at')
        
        if user.role in ['admin', 'manager']:
            return Property.objects.all().order_by('-created_at')
        if user.role == 'agent':
            return Property.objects.filter(assigned_agent=user).order_by('-created_at')
        
        return Property.objects.filter(status=Property.StatusType.PUBLISHED).order_by('-created_at')

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [AllowAny]
        elif self.action == 'create':
            self.permission_classes = [IsAdminOrManager]
        elif self.action in ['update', 'partial_update']:
            self.permission_classes = [IsAdminOrManager | IsAgentWithFullAccess]
        elif self.action == 'destroy':
            self.permission_classes = [IsAdminOrManager]
        else:
            self.permission_classes = [IsAuthenticated]
            
        return super().get_permissions()
    
    def perform_create(self, serializer):
        property_instance = serializer.save(created_by=self.request.user)
        try:
            calendar_id = google_calendar_service.create_calendar_for_property(property_instance)
            property_instance.google_calendar_id = calendar_id
            property_instance.save()
        except Exception as e:
            print(f"Could not create Google Calendar for {property_instance.title}: {e}")

    def create(self, request, *args, **kwargs):

        try:
            with transaction.atomic():
                property_serializer = self.get_serializer(data=request.data)
                property_serializer.is_valid(raise_exception=True)
                self.perform_create(property_serializer)
                property_instance = property_serializer.instance
                media_files = request.FILES.getlist('media_files')
                media_metadata_str_list = request.POST.getlist('media_metadata')

                if len(media_files) != len(media_metadata_str_list):
                    raise serializers.ValidationError("Mismatch between files and metadata.")

                for i, file_obj in enumerate(media_files):
                    try:
                        metadata = json.loads(media_metadata_str_list[i])
                    except json.JSONDecodeError:
                        raise serializers.ValidationError(f"Invalid JSON metadata at index {i}.")
                    Media.objects.create(
                        listing=property_instance,
                        file=file_obj,
                        category=metadata.get('category', Media.CategoryType.MEDIA),
                        caption=metadata.get('caption', ''),
                        is_primary=metadata.get('is_primary', False),
                        order=metadata.get('order', i)
                    )
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        final_serializer = self.get_serializer(property_instance)
        headers = self.get_success_headers(final_serializer.data)
        return Response(final_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Booking.objects.none()
        if user.role in ['admin', 'manager']:
            return Booking.objects.all().select_related('property', 'user')
        return Booking.objects.filter(user=user).select_related('property', 'user')
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [IsAuthenticated]
        elif self.action == 'retrieve':
            permission_classes = [IsOwnerOrAdminOrManager]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrManager]
        else: # list action
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
        




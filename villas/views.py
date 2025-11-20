from django.db import transaction
import json
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from datetime import datetime, timedelta

from . import google_calendar_service


from .models import Property, Media, Booking, PropertyImage, BedroomImage, Review, ReviewImage, Favorite
from .serializers import PropertySerializer , BookingSerializer, MediaSerializer, PropertyImageSerializer, BedroomImageSerializer, ReviewSerializer, ReviewImageSerializer, FavoriteSerializer


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

                media_images = request.FILES.getlist('media_images')

                if not media_images:
                    return Response({"error": "At least one media image is required."}, status=status.HTTP_400_BAD_REQUEST)

                # Only save images that are not empty to avoid validation errors
                for img in media_images:
                    if not img:
                        continue
                    if hasattr(img, 'name') and getattr(img, 'size', None) and img.size > 0:
                        PropertyImage.objects.create(property=property_instance, image=img)

                bedrooms_images = request.FILES.getlist('bedrooms_images')
                
                for img in bedrooms_images:
                    if not img:
                        print("Skipped empty bedroom image file.")
                        continue
                    if hasattr(img, 'name') and getattr(img, 'size', None) and img.size > 0:
                        BedroomImage.objects.create(property=property_instance, image=img)
                
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
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status=Booking.StatusType.PENDING)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        booking = self.get_object()
        new_status = request.data.get('status')
        if new_status and new_status != booking.status:
            if new_status == 'approved':
                try:
                    event_id = google_calendar_service.create_event_for_booking(booking.property.google_calendar_id, booking)
                    booking.google_event_id = event_id
                except Exception as e:
                    return Response({"error": f"Failed to create Google Calendar event: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif new_status in ['cancelled', 'rejected'] and booking.google_event_id:
                google_calendar_service.delete_event_for_booking(booking.property.google_calendar_id, booking.google_event_id)
                booking.google_event_id = None
        
        booking.save() 
        
        return super().update(request, *args, **kwargs)
    

    def destroy(self, request, *args, **kwargs):
        booking = self.get_object()
        
        if booking.google_event_id:
            google_calendar_service.delete_event_for_booking(
                booking.property.google_calendar_id, 
                booking.google_event_id
            )
        
        self.perform_destroy(booking)
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_property_availability(request, property_pk):
    try:
        prop = Property.objects.get(pk=property_pk)
    except Property.DoesNotExist:
        return Response({"error": "Property not found."}, status=status.HTTP_404_NOT_FOUND)

    if not prop.google_calendar_id:
        return Response({"error": "Booking calendar is not configured for this property."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        month = int(request.query_params.get('month', datetime.now().month))
        year = int(request.query_params.get('year', datetime.now().year))
    except (ValueError, TypeError):
        return Response({"error": "Invalid month or year parameter."}, status=status.HTTP_400_BAD_REQUEST)
    
    start_of_month = datetime(year, month, 1)
    next_month_start = (start_of_month.replace(day=28) + timedelta(days=4)).replace(day=1)
    end_of_month = next_month_start - timedelta(days=1)

    try:
        events_result = google_calendar_service.service.events().list(
            calendarId=prop.google_calendar_id,
            timeMin=start_of_month.isoformat() + 'Z',
            timeMax=end_of_month.isoformat() + 'Z',
            singleEvents=True, 
            orderBy='startTime'
        ).execute()
    except Exception as e:
        return Response({"error": f"Could not fetch calendar events: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    booked_dates = []
    for event in events_result.get('items', []):
        if 'date' in event['start']:
            start_date_str = event['start']['date']
            end_date = datetime.fromisoformat(event['end']['date']) - timedelta(days=1)
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            booked_dates.append({'start': start_date_str, 'end': end_date_str})
        
    return Response(booked_dates, status=status.HTTP_200_OK)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'manager']:
            return Review.objects.all().select_related('property', 'user')
        return Review.objects.filter(user=user).select_related('property', 'user')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)




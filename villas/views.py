from django.db import transaction
import json
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, action
from datetime import datetime, timedelta
from django.db.models import Exists, OuterRef

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from . import google_calendar_service


from .models import Property, Media, Booking, PropertyImage, BedroomImage, Review, ReviewImage, Favorite
from .serializers import PropertySerializer , BookingSerializer, MediaSerializer, PropertyImageSerializer, BedroomImageSerializer, ReviewSerializer, ReviewImageSerializer, FavoriteSerializer


from accounts.permissions import IsAdminOrManager, IsAgentWithFullAccess, IsAssignedAgentReadOnly, IsOwnerOrAdminOrManager


from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


from .filters import PropertyFilter

class PropertyViewSet(viewsets.ModelViewSet):

    serializer_class = PropertySerializer
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [SearchFilter, OrderingFilter]
    filterset_class = PropertyFilter
    # search_fields = ['title', 'city', 'description', 'interior_amenities', 'outdoor_amenities']
    # ordering_fields = ['price', 'created_at', 'bedrooms', 'bathrooms']
    

    def get_queryset(self):
        
        user = self.request.user

        queryset = Property.objects.prefetch_related("media_images", "bedrooms_images")

        if user.is_authenticated:
            queryset = queryset.annotate(is_favorited=Exists(Favorite.objects.filter(property=OuterRef('pk'), user=user))).prefetch_related('favorited_by')

        if not user.is_authenticated:
            return Property.objects.filter(status=Property.StatusType.PUBLISHED).order_by('-created_at')
        
        if user.role in ['admin', 'manager']:
            return Property.objects.all().order_by('-created_at')
        if user.role == 'agent':
            return Property.objects.filter(assigned_agent=user).order_by('-created_at')
        
        return queryset.filter(status=Property.StatusType.PUBLISHED).order_by('-created_at')

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
        serializer.save(user=self.request.user, status=Booking.STATUS.Pending)
    
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
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'manager']:
            return Review.objects.all().select_related('property', 'user')
        return Review.objects.filter(user=user).select_related('property', 'user')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                review_instance = serializer.save(user=request.user)

                images = request.FILES.getlist('images')
                if len(images) > 5:
                    return Response({"error": "You can upload a maximum of 5 images."}, status=status.HTTP_400_BAD_REQUEST)

                for img in images:
                    if img and getattr(img, 'size', 0) > 0:
                        ReviewImage.objects.create(review=review_instance, image=img)
                
                final_serializer = self.get_serializer(review_instance).data
                return Response(final_serializer, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(
            user=self.request.user
        ).select_related('property').prefetch_related(
        'property__media_images',
        'property__bedrooms_images'
    )

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        property_id = request.data.get("property")

        if not property_id:
            return Response({"detail": "property is required"}, status=400)

        user = request.user

        favorite = Favorite.objects.filter(user=user, property_id=property_id).first()

        if favorite:
            favorite.delete()
            return Response(
                {"detail": "Removed from favorites", "is_favorited": False},
                status=200
            )

        new_fav = Favorite.objects.create(user=user, property_id=property_id)
        return Response(
            {
                "detail": "Added to favorites",
                "is_favorited": True,
                "data": FavoriteSerializer(new_fav).data
            },
            status=201
        )





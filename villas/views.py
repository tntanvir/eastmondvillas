from django.db import transaction
import json
from rest_framework import viewsets, status, serializers, filters
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, action
from datetime import datetime, timedelta, date
from calendar import monthrange
from django.db.models import Exists, OuterRef

from .utils import update_daily_analytics, validate_date_range

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter


from .models import Property, Media, Booking, PropertyImage, BedroomImage, Review, ReviewImage, Favorite
from .serializers import PropertySerializer , BookingSerializer, MediaSerializer, PropertyImageSerializer, BedroomImageSerializer, ReviewSerializer, ReviewImageSerializer, FavoriteSerializer


from accounts.permissions import IsAdminOrManager, IsAgentWithFullAccess, IsAssignedAgentReadOnly, IsOwnerOrAdminOrManager
from rest_framework.permissions import IsAdminUser


from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


from .filters import PropertyFilter
from datetime import datetime

from django.db.models import Q
from rest_framework.views import APIView

from django.contrib.auth import get_user_model
User = get_user_model()









# Property ViewSet

class PropertyViewSet(viewsets.ModelViewSet):

    serializer_class = PropertySerializer
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [SearchFilter, OrderingFilter]
    filterset_class = PropertyFilter
    search_fields = ['^title', '^city', '^description', '^interior_amenities', '^outdoor_amenities']
    ordering_fields = ['price', 'created_at', 'bedrooms', 'bathrooms']
    

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
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        # Update daily analytics for views
        update_daily_analytics(instance, "views")

        return Response(serializer.data)

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
    

def property_downloaded(request, pk):
    try:
        prop = Property.objects.get(pk=pk)
    except Property.DoesNotExist:
        return Response({"error": "Property not found."}, status=status.HTTP_404_NOT_FOUND)

    update_daily_analytics(prop, "downloads")
    return Response({"detail": "Download recorded."}, status=status.HTTP_200_OK) 

class BookingViewSet(viewsets.ModelViewSet):
   
    serializer_class = BookingSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'property__id', 'user__id']
    search_fields = ['property__title', 'user__username', 'user__email']
    ordering_fields = ['check_in', 'check_out', 'created_at', 'status']
    pagination_class = StandardResultsSetPagination


    # optional: you can leave this out; we override filter_queryset anyway
    # filter_backends = []

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            queryset = Booking.objects.none()
        elif getattr(user, "role", None) in ["admin", "manager"]:
            queryset = Booking.objects.all().select_related("property", "user")
        else:
            queryset = Booking.objects.filter(user=user).select_related("property", "user")

        return queryset

    def filter_queryset(self, queryset):
        """
        Completely bypass DRF's DEFAULT_FILTER_BACKENDS (SearchFilter, etc.)
        and implement our own ?search= logic.
        """
        search = self.request.query_params.get("search")
        if not search:
            return queryset

        # Try to parse search as date YYYY-MM-DD
        date_value = None
        try:
            date_value = datetime.strptime(search, "%Y-%m-%d").date()
        except ValueError:
            pass

        # Text search
        q = (
            Q(full_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )

        # If looks like a date, include check_in / check_out
        if date_value:
            q |= Q(check_in=date_value) | Q(check_out=date_value)

        return queryset.filter(q)

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [IsAuthenticated]
        elif self.action == 'retrieve':
            permission_classes = [IsOwnerOrAdminOrManager]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrManager]
        else:  # list action
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

        if not new_status:
            return Response({"error": "Status required"}, status=400)

        if new_status != booking.status:

            if new_status == 'approved':
                if validate_date_range(booking.property, booking.check_in, booking.check_out):
                    return Response(
                        {"error": "The selected date range overlaps with existing bookings or is invalid."},
                        status=400
                    )
                booking.status = new_status
                update_daily_analytics(booking.property, "bookings")

            elif new_status in ['cancelled', 'rejected', 'completed', 'pending']:
                booking.status = new_status
            else:
                return Response({"error": "Invalid status"}, status=400)
            booking.save()

        # return updated instance ONLY
        serializer = self.get_serializer(booking)
        return Response(serializer.data, status=200)
    

@api_view(['GET'])
@permission_classes([AllowAny])
def get_property_availability(request, property_pk):
    try:
        prop = Property.objects.get(pk=property_pk)
    except Property.DoesNotExist:
        return Response({"error": "Property not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        month = int(request.query_params.get('month', datetime.now().month))
        year = int(request.query_params.get('year', datetime.now().year))
    except (ValueError, TypeError):
        return Response({"error": "Invalid month or year parameter."}, status=status.HTTP_400_BAD_REQUEST)

    start_of_month = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_of_month = date(year, month, last_day)

    bookings = Booking.objects.filter(
        property=prop,
        status__in=['approved'],
        check_in__lte=end_of_month,
        check_out__gte=start_of_month
    )

    booked_dates = []
    for booking in bookings:
        start = max(booking.check_in, start_of_month)
        end = min(booking.check_out, end_of_month)

        booked_dates.append({
            "start": start.strftime('%Y-%m-%d'),
            "end": end.strftime('%Y-%m-%d')
        })

    return Response(booked_dates, status=status.HTTP_200_OK)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['property__id', 'rating', 'user__id']
    search_fields = ['comment', 'property__title', 'user__username']
    ordering_fields = ['rating', 'created_at']

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
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['property__id']
    search_fields = ['property__title', 'property__city']
    ordering_fields = ['created_at']

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




class DeshboardViewApi(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        properties = Property.objects.all().count()
        properties_active = Property.objects.filter(status='active').count()
        reviews = Review.objects.all().count()
        users = User.objects.filter(role='agent').count()

        return Response({
            "properties": properties,
            "properties_active": properties_active,
            "reviews": reviews,
            "users": users
        },status=status.HTTP_200_OK)
        
        
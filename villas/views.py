from django.db import transaction
import json
from rest_framework import viewsets, status, serializers, filters
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, action
from datetime import datetime, timedelta, date
from calendar import monthrange
from django.db.models import Exists, OuterRef, F, Count, Avg, Sum, Q

from .utils import update_daily_analytics, validate_date_range

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from auditlog.registry import auditlog

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

        queryset = Property.objects.annotate(total_reviews=Count("reviews"),avg_rating=Avg("reviews__rating")).prefetch_related("media_images", "bedrooms_images")

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
        

from django.db.models import Sum, Count, Q
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import timedelta
from .models import DailyAnalytics
from list_vila.models import ContectUs
from django.db.models.functions import TruncMonth


# class AnalyticsSummaryView(APIView):
#     """
#     Fully optimized analytics summary.
#     Supports:
#     - ?range=7d | month | 6m | year | 1y | custom days (e.g. range=90)
#     - or ?start=YYYY-MM-DD&end=YYYY-MM-DD
#     """

#     def get(self, request):
#         today = now().date()

#         start_param = request.GET.get("start")
#         end_param = request.GET.get("end")

#         if start_param and end_param:
#             try:
#                 start_date = date.fromisoformat(start_param)
#                 end_date = date.fromisoformat(end_param)
#             except:
#                 return Response({"error": "Use YYYY-MM-DD for start & end"}, status=400)

#         else:

#             range_type = request.GET.get("range", "7d")

#             if range_type == "7d":
#                 start_date = today - timedelta(days=7)
#             elif range_type == "month":
#                 start_date = today.replace(day=1)
#             elif range_type == "6m":
#                 start_date = today - timedelta(days=180)
#             elif range_type == "year":
#                 start_date = today.replace(month=1, day=1)
#             elif range_type == "1y":
#                 start_date = today - timedelta(days=365)
#             elif range_type.isdigit():
#                 start_date = today - timedelta(days=int(range_type))
#             else:
#                 start_date = today - timedelta(days=7)

#             end_date = today

#         analytics_qs = DailyAnalytics.objects.filter(
#             date__gte=start_date, date__lte=end_date
#         )

#         totals = analytics_qs.aggregate(
#             total_views=Sum("views"),
#             total_downloads=Sum("downloads"),
#             total_bookings=Sum("bookings")
#         )

#         total_inquiries = ContectUs.objects.filter(
#             created_at__date__gte=start_date,
#             created_at__date__lte=end_date
#         ).count()

  
#         villas_type_count = dict(
#             Property.objects.values("listing_type")
#             .annotate(total=Count("id"))
#             .values_list("listing_type", "total")
#         )


#         monthly_stats = (
#             analytics_qs
#             .annotate(month=TruncMonth("date"))
#             .values("month")
#             .annotate(
#                 views=Sum("views"),
#                 downloads=Sum("downloads"),
#                 bookings=Sum("bookings")
#             )
#             .order_by("month")
#         )


#         monthly_inquiries = (
#             ContectUs.objects.filter(
#                 created_at__date__gte=start_date,
#                 created_at__date__lte=end_date
#             )
#             .annotate(month=TruncMonth("created_at"))
#             .values("month")
#             .annotate(inquiries=Count("id"))
#             .order_by("month")
#         )

#         inquiry_map = {m["month"]: m["inquiries"] for m in monthly_inquiries}

#         performance_overview = []
#         for m in monthly_stats:
#             month = m["month"]
#             performance_overview.append({
#                 "month": month.strftime("%Y-%m"),
#                 "views": m["views"],
#                 "downloads": m["downloads"],
#                 "bookings": m["bookings"],
#                 "inquiries": inquiry_map.get(month, 0),
#             })

#         agents_analytics = (
#             User.objects.filter(role="agent")
#             .annotate(
#                 total_properties=Count("assigned_villas", distinct=True),
#                 total_views=Sum("assigned_villas__daily_analytics__views"),
#                 total_downloads=Sum("assigned_villas__daily_analytics__downloads"),
#                 total_bookings=Sum("assigned_villas__daily_analytics__bookings"),
#             )
#             .values(
#                 "id", "name", "total_properties",
#                 "total_views", "total_downloads", "total_bookings"
#             )
#         )


#         return Response({
#             "start_date": start_date,
#             "end_date": end_date,

#             "totals": {
#                 "views": totals["total_views"] or 0,
#                 "downloads": totals["total_downloads"] or 0,
#                 "bookings": totals["total_bookings"] or 0,
#                 "inquiries": total_inquiries,
#             },

#             "villas_type_count": villas_type_count,

#             "monthly_performance": performance_overview,

#             "agents": list(agents_analytics),
#         })

from django.db.models import Sum, Count
from django.db.models.functions import TruncDay, TruncMonth
from datetime import date, timedelta
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response


class AnalyticsSummaryView(APIView):

    def get(self, request):

        today = now().date()

        # --- RANGE OR CUSTOM DATE ---
        start_param = request.GET.get("start")
        end_param = request.GET.get("end")
        range_type = request.GET.get("range", "7d")

        if start_param and end_param:
            start_date = date.fromisoformat(start_param)
            end_date = date.fromisoformat(end_param)
        else:
            if range_type == "7d":
                start_date = today - timedelta(days=7)
            elif range_type == "30d":
                start_date = today - timedelta(days=30)
            elif range_type == "90d":
                start_date = today - timedelta(days=90)
            elif range_type == "month":
                start_date = today.replace(day=1)
            elif range_type == "6m":
                start_date = today - timedelta(days=180)
            elif range_type in ["1y", "year"]:
                start_date = today - timedelta(days=365)
            elif range_type.isdigit():
                start_date = today - timedelta(days=int(range_type))
            else:
                start_date = today - timedelta(days=7)

            end_date = today

        range_days = (end_date - start_date).days

        # Grouping logic => ≤60 days = daily, otherwise monthly
        is_monthly = range_days > 60

        # --- BASE QS ---
        analytics_qs = DailyAnalytics.objects.filter(
            date__gte=start_date, date__lte=end_date
        )

        # --- TOTALS ---
        totals = analytics_qs.aggregate(
            total_views=Sum("views"),
            total_downloads=Sum("downloads"),
            total_bookings=Sum("bookings"),
        )

        total_inquiries = ContectUs.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        ).count()

        # --- PERFORMANCE (Daily or Monthly) ---
        if not is_monthly:
            # DAY-WISE
            performance = (
                analytics_qs
                .annotate(day=TruncDay("date"))
                .values("day")
                .annotate(
                    total_views=Sum("views"),
                    total_downloads=Sum("downloads"),
                    total_bookings=Sum("bookings"),
                )
                .order_by("day")
            )

            # inquiries daily
            inquiry_qs = (
                ContectUs.objects.filter(
                    created_at__date__gte=start_date,
                    created_at__date__lte=end_date,
                )
                .annotate(day=TruncDay("created_at"))
                .values("day")
                .annotate(inquiries=Count("id"))
            )

            inquiry_map = {i["day"]: i["inquiries"] for i in inquiry_qs}

            performance_list = []
            for p in performance:
                day_name = p["day"].strftime("%a")  # Mon, Tue, Wed
                performance_list.append({
                    "name": day_name,
                    "views": p["total_views"] or 0,
                    "downloads": p["total_downloads"] or 0,
                    "bookings": p["total_bookings"] or 0,
                    "inquiries": inquiry_map.get(p["day"], 0),
                })

        else:
            # MONTH-WISE
            performance = (
                analytics_qs
                .annotate(month=TruncMonth("date"))
                .values("month")
                .annotate(
                    total_views=Sum("views"),
                    total_downloads=Sum("downloads"),
                    total_bookings=Sum("bookings")
                )
                .order_by("month")
            )

            # inquiries month-wise
            inquiry_qs = (
                ContectUs.objects.filter(
                    created_at__date__gte=start_date,
                    created_at__date__lte=end_date
                )
                .annotate(month=TruncMonth("created_at"))
                .values("month")
                .annotate(inquiries=Count("id"))
            )

            inquiry_map = {i["month"]: i["inquiries"] for i in inquiry_qs}

            performance_list = []
            for p in performance:
                label = p["month"].strftime("%b")  # Jan, Feb, Mar
                performance_list.append({
                    "name": label,
                    "views": p["total_views"] or 0,
                    "downloads": p["total_downloads"] or 0,
                    "bookings": p["total_bookings"] or 0,
                    "inquiries": inquiry_map.get(p["month"], 0),
                })

        # --- AGENT ANALYTICS ---
        agents = (
            User.objects.filter(role="agent")
            .annotate(
                total_properties=Count("assigned_villas"),
                total_views=Sum("assigned_villas__daily_analytics__views"),
                total_downloads=Sum("assigned_villas__daily_analytics__downloads"),
                total_bookings=Sum("assigned_villas__daily_analytics__bookings"),
            )
            .values(
                "id", "name", "total_properties",
                "total_views", "total_downloads", "total_bookings"
            )
        )

        return Response({
            "range": range_type,
            "start_date": start_date,
            "end_date": end_date,

            "totals": {
                "views": totals["total_views"] or 0,
                "downloads": totals["total_downloads"] or 0,
                "bookings": totals["total_bookings"] or 0,
                "inquiries": total_inquiries,
            },

            "performance": performance_list,
            "agents": list(agents),
        })


auditlog.register(Property)
auditlog.register(Media)
auditlog.register(Booking)
auditlog.register(PropertyImage)
auditlog.register(BedroomImage)
auditlog.register(Review)
auditlog.register(ReviewImage)
auditlog.register(Favorite)
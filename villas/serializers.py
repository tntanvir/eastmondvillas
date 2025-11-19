from rest_framework import serializers
from .models import Property, Media, Booking
from accounts.models import User
from datetime import date, datetime
from . import google_calendar_service



class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ['id', 'media_type', 'category', 'file', 'file_url', 'caption', 'is_primary', 'order']
        read_only_fields = ['media_type', 'file_url']



class PropertySerializer(serializers.ModelSerializer):
    media = MediaSerializer(many=True, read_only=True)
    created_by_name = serializers.SerializerMethodField()
    location_coords = serializers.SerializerMethodField()
    media_count = serializers.SerializerMethodField()
    booking_count = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    property_stats = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'title', 'slug', 'description', 'price', 'price_display', 'booking_rate',
            'listing_type', 'status', 'address', 'city', 'max_guests',
            'bedrooms', 'bathrooms', 'pool', 'amenities', 'latitude',
            'longitude', 'place_id', 'seo_title', 'seo_description',
            'signature_distinctions', 'staff', 'calendar_link', 'google_calendar_id',
            'created_at', 'updated_at', 'assigned_agent', 'created_by', 'created_by_name',
            'media', 'media_count', 'booking_count', 'location_coords', 'property_stats'
        ]
        read_only_fields = [
            'slug', 'created_by', 'created_by_name', 'media', 'media_count', 'booking_count',
            'created_at', 'updated_at', 'location_coords', 'price_display', 'property_stats'
        ]

    def get_created_by_name(self, obj):
        return obj.created_by.name if obj.created_by else None

    def get_location_coords(self, obj):
        if obj.latitude is not None and obj.longitude is not None:
            try:
                return {
                    'lat': float(obj.latitude),
                    'lng': float(obj.longitude)
                }
            except (TypeError, ValueError):
                return None
        return None

    def get_media_count(self, obj):
        return getattr(obj, 'media', []).count() if hasattr(obj, 'media') else 0

    def get_booking_count(self, obj):
        return getattr(obj, 'bookings', []).count() if hasattr(obj, 'bookings') else 0

    def get_price_display(self, obj):
        try:
            return f"{obj.price:.2f}"
        except Exception:
            return "0.00"

    def get_property_stats(self, obj):
        # Aggregate booking statuses for quick overview
        stats = {
            'total_bookings': 0,
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'completed': 0,
            'cancelled': 0,
        }
        qs = getattr(obj, 'bookings', None)
        if qs is not None:
            stats['total_bookings'] = qs.count()
            # Use values_list to avoid N+1
            for status in qs.values_list('status', flat=True):
                if status in stats:
                    stats[status] += 1
        return stats

    def validate(self, data):
        lat = data.get('latitude')
        lng = data.get('longitude')
        if (lat is not None and lng is None) or (lat is None and lng is not None):
            raise serializers.ValidationError("Both latitude and longitude must be provided together.")
        return data



class BookingPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ['id', 'title']


class BookingUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email']

class BookingSerializer(serializers.ModelSerializer):
    property_details = BookingPropertySerializer(source='property', read_only=True)
    user_details = BookingUserSerializer(source='user', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'property', 'full_name', 'email', 'phone', 'check_in', 'check_out',
            'total_price', 'user', 'status', 'google_event_id', 'created_at',
            'property_details', 'user_details'
        ]
        read_only_fields = ['user', 'status', 'google_event_id', 'created_at']
        extra_kwargs = {
            'property': {'write_only': True}
        }

    def validate(self, data):
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        prop = data.get('property')

        if check_in and check_out and check_in >= check_out:
            raise serializers.ValidationError({"check_out": "Check-out date must be after check-in date."})
        if check_in and check_in < date.today():
            raise serializers.ValidationError({"check_in": "Check-in date cannot be in the past."})

        # Only check calendar availability if property has a calendar configured
        if check_in and check_out and prop and prop.google_calendar_id:
            start_time = datetime.combine(check_in, datetime.min.time())
            end_time = datetime.combine(check_out, datetime.max.time())
            try:
                is_available = google_calendar_service.check_availability(
                    prop.google_calendar_id,
                    start_time,
                    end_time
                )
                if not is_available:
                    raise serializers.ValidationError({
                        "non_field_errors": ["The selected dates are not available for this property. Please choose different dates."]
                    })
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Could not verify availability: {e}")
        return data






        

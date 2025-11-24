from rest_framework import serializers
from .models import Property, Media, Booking, PropertyImage, BedroomImage, Review, ReviewImage, Favorite, DailyAnalytics
from accounts.models import User
from datetime import date, datetime
from .utils import validate_date_range, is_valid_date



class PropertyMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ['id', 'title', 'city', 'price', 'bedrooms', 'bathrooms', 'pool', 'outdoor_amenities', 'interior_amenities']






class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ['id', 'media_type', 'category', 'file', 'file_url', 'caption', 'is_primary', 'order']
        read_only_fields = ['media_type', 'file_url']


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ["id", "image"]



class BedroomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BedroomImage
        fields = ["id", "image"]


class PropertyFavoriteSerializer(serializers.ModelSerializer):
    media_images = PropertyImageSerializer(many=True, read_only=True)
    bedrooms_images = BedroomImageSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = [
            'id', 'title', 'slug', 'city', 'price', 'bedrooms', 'bathrooms', 'pool', 'outdoor_amenities','interior_amenities',
            'media_images', 'bedrooms_images'
        ]
        read_only_fields = [
            'slug', 'media_images', 'bedrooms_images'
        ]



class FavoriteSerializer(serializers.ModelSerializer):
    property_details = PropertyFavoriteSerializer(source='property', read_only=True)
    class Meta:
        model = Favorite
        fields = ['id', 'property', 'user', 'created_at', 'property_details',]
        read_only_fields = ['id','user', 'created_at', 'property_details',]

    def validate_property(self, value):
        user = self.context['request'].user
        if Favorite.objects.select_related('property', 'user').prefetch_related('property__media_images', 'property__bedrooms_images').filter(property=value, user=user).exists():
            raise serializers.ValidationError("This property is already in your favorites.")
        return value


class PropertySerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    location_coords = serializers.SerializerMethodField()
    booking_count = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    property_stats = serializers.SerializerMethodField()
    media_images = PropertyImageSerializer(many=True, read_only=True)
    bedrooms_images = BedroomImageSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()


    class Meta:
        model = Property
        fields = [
            'id', 'title', 'slug', 'description', 'price', 'price_display', 'booking_rate',
            'listing_type', 'status', 'address', 'city', 'add_guest',
            'bedrooms', 'bathrooms', 'pool', 'outdoor_amenities','interior_amenities', 'latitude',
            'longitude', 'place_id', 'seo_title', 'seo_description',
            'signature_distinctions', 'staff', 'calendar_link',
            'created_at', 'updated_at', 'assigned_agent', 'created_by', 'created_by_name',
            'booking_count', 'location_coords', 'property_stats', 'media_images', 'bedrooms_images', 'is_favorited', 'check_in', 'check_out', 'rules_and_etiquette'
        ]
        read_only_fields = [
            'slug', 'created_by', 'created_by_name', 'booking_count', 'media_images', 'bedrooms_images',
            'created_at', 'updated_at', 'location_coords', 'price_display', 'property_stats'
        ]
    
    def get_is_favorited(self, obj):
        return getattr(obj, "is_favorited", False)

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
            'total_price', 'user', 'status', 'created_at',
            'property_details', 'user_details'
        ]
        read_only_fields = ['user', 'status', 'created_at']
        extra_kwargs = {
            'property': {'write_only': True}
        }

    def validate(self, data):
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        prop = data.get('property')

        if check_in is None or check_out is None:
            raise serializers.ValidationError("Both check-in and check-out dates are required.")
        
        if check_in == check_out:
            print("Check-in and check-out dates cannot be the same.")
            print(check_in, check_out)
            raise serializers.ValidationError("Check-in and check-out dates cannot be the same.")
        
        if check_in :
            is_valid = is_valid_date(check_in)
            if not is_valid:
                raise serializers.ValidationError({"check_in": "Check-in date is invalid."})
        if check_out :
            is_valid = is_valid_date(check_out)
            if not is_valid:
                raise serializers.ValidationError({"check_out": "Check-out date is invalid."})
            

        if check_in and check_out and check_in >= check_out:
            raise serializers.ValidationError({"check_out": "Check-out date must be after check-in date."})
        if check_in and check_in < date.today():
            raise serializers.ValidationError({"check_in": "Check-in date cannot be in the past."})
        
        validate_date_range(prop, check_in, check_out)

        if validate_date_range(prop, check_in, check_out):
            raise serializers.ValidationError({
                "non_field_errors": ["The selected dates are not available for this property. Please choose different dates."]
            })
        
        # check_availability = self.context.get('check_availability', True)
        # if check_availability:
        #     is_unavailable = validate_date_range(prop, check_in, check_out)
        #     if is_unavailable:
        #         raise serializers.ValidationError({
        #             "non_field_errors": ["The selected dates are not available for this property. Please choose different dates."]
        #         })
        return data


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image']

class ReviewSerializer(serializers.ModelSerializer):
    images = ReviewImageSerializer(many=True, read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'property', 'user', 'rating', 'comment', 'created_at', 'images']
        read_only_fields = ['user', 'created_at', 'images']

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, data):
        property = data.get('property')
        user = self.context['request'].user

        if Review.objects.filter(property=property, user=user).exists():
            raise serializers.ValidationError("You have already reviewed this property.")
        return data


class DailyAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyAnalytics
        fields = ['id', 'date', 'views', 'inquiries', 'bookings', 'downloads', 'property']
        read_only_fields = ['id', 'property']
    
    def validate_date(self, value):
        if value > date.today():
            raise serializers.ValidationError("Date cannot be in the future.")
        return value
    
    def validate(self, data):
        property = self.context['property']
        date_value = data.get('date')

        if DailyAnalytics.objects.filter(property=property, date=date_value).exists():
            raise serializers.ValidationError("Analytics for this property on the given date already exists.")
        return data

        

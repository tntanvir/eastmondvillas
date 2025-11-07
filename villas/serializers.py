from rest_framework import serializers
from .models import Villa, VillaImage, Amenity, Booking


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ('id', 'name')


class VillaImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = VillaImage
        fields = ('id', 'image', 'url', 'caption', 'type', 'is_primary', 'order')


class VillaSerializer(serializers.ModelSerializer):
    images = VillaImageSerializer(many=True, read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)

    class Meta:
        model = Villa
        fields = ('id', 'owner', 'title', 'description', 'price', 'property_type', 'max_guests', 'address', 'city', 'bedrooms', 'bathrooms', 'has_pool', 'amenities', 'latitude', 'longitude', 'place_id', 'seo_title', 'seo_description', 'signature_distinctions', 'staff', 'calendar_link', 'status', 'images')


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ('id', 'villa', 'user', 'full_name', 'email', 'phone', 'check_in', 'check_out', 'status', 'total_price', 'google_event_id', 'created_at')

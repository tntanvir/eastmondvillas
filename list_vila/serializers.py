from rest_framework import serializers
from .models import VilaListing

class VilaListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = VilaListing
        fields = '__all__'
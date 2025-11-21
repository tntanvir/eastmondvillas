from rest_framework import serializers
from .models import VilaListing,ContectUs

class VilaListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = VilaListing
        fields = '__all__'
    
class ContectUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContectUs
        fields = '__all__'
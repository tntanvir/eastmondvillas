from rest_framework import serializers
from .models import NewsLetter
from accounts.models import User
from villas.models import VilaListing


class NewsLetterSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True
    )
    property = serializers.PrimaryKeyRelatedField(
        queryset=VilaListing.objects.all()
    )

    class Meta:
        model = NewsLetter
        fields = ["user", "property"]

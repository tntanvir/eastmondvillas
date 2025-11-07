from rest_framework import viewsets, permissions
from .models import Villa, Booking, Amenity, VillaImage
from .serializers import VillaSerializer, BookingSerializer, AmenitySerializer, VillaImageSerializer


class VillaViewSet(viewsets.ModelViewSet):
    queryset = Villa.objects.all()
    serializer_class = VillaSerializer
    permission_classes = [permissions.AllowAny]


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]


class AmenityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    permission_classes = [permissions.AllowAny]


class VillaImageViewSet(viewsets.ModelViewSet):
    queryset = VillaImage.objects.all()
    serializer_class = VillaImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

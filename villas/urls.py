from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VillaViewSet, BookingViewSet, AmenityViewSet, VillaImageViewSet

router = DefaultRouter()
router.register('villas', VillaViewSet, basename='villa')
router.register('bookings', BookingViewSet, basename='booking')
router.register('amenities', AmenityViewSet, basename='amenity')
router.register('villa-images', VillaImageViewSet, basename='villaimage')

urlpatterns = [
    path('', include(router.urls)),
]

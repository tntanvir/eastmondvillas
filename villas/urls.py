from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, BookingViewSet, get_property_availability, FavoriteViewSet, ReviewViewSet, property_downloaded, DeshboardViewApi


router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'reviews', ReviewViewSet, basename='review')



urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', DeshboardViewApi.as_view(), name='dashboard'),
    path('properties/<int:property_pk>/availability/', get_property_availability, name='property-availability'),
    path('properties/<int:pk>/downloaded/', property_downloaded, name='property-downloaded'),
]
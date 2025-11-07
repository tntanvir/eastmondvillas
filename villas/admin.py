from django.contrib import admin
from .models import Amenity, Villa, VillaImage, BookingRate, Booking


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


class VillaImageInline(admin.TabularInline):
    model = VillaImage
    extra = 0


@admin.register(Villa)
class VillaAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'slug', 'city', 'price', 'status')
    inlines = [VillaImageInline]
    search_fields = ('title', 'city', 'address')


@admin.register(BookingRate)
class BookingRateAdmin(admin.ModelAdmin):
    list_display = ('id', 'villa', 'period', 'rate', 'minimum_stay')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'villa', 'full_name', 'check_in', 'check_out', 'status')
    list_filter = ('status',)
    search_fields = ('full_name', 'email')

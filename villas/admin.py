from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from unfold.decorators import display
from .models import Property, Media, Booking


class MediaInline(TabularInline):
    """Inline admin for Media files associated with a Property."""
    model = Media
    extra = 1
    fields = ('file', 'category', 'media_type', 'caption', 'is_primary', 'order', 'file_preview')
    readonly_fields = ('media_type', 'file_preview')
    ordering = ('order', 'id')

    @display(description='Preview', header=True)
    def file_preview(self, obj):
        """Display a thumbnail preview for image files."""
        if obj.file and obj.media_type == 'image':
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.file_url
            )
        elif obj.file:
            return format_html('<span>📄 {}</span>', obj.get_media_type_display())
        return '-'


class BookingInline(TabularInline):
    """Inline admin for Bookings associated with a Property."""
    model = Booking
    extra = 0
    fields = ('full_name', 'email', 'check_in', 'check_out', 'status', 'total_price')
    readonly_fields = ('created_at',)
    can_delete = False
    ordering = ('-created_at',)


@admin.register(Property)
class PropertyAdmin(ModelAdmin):
    """Admin interface for Property model with Unfold styling."""
    
    list_display = (
        'title', 
        'city', 
        'listing_type', 
        'status', 
        'price_display',
        'property_stats',
        'assigned_agent',
        'created_at'
    )
    
    list_filter = (
        'listing_type',
        'status',
        'has_pool',
        'city',
        'created_at',
    )
    
    search_fields = (
        'title',
        'description',
        'city',
        'address',
        'slug',
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'slug',
        'media_count',
        'booking_count',
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title',
                'description',
                'listing_type',
                'status',
            )
        }),
        ('Pricing', {
            'fields': (
                'price',
                'booking_rate',
            )
        }),
        ('Property Details', {
            'fields': (
                'max_guests',
                'bedrooms',
                'bathrooms',
                'has_pool',
                'amenities',
            )
        }),
        ('Location', {
            'fields': (
                'address',
                'city',
                'latitude',
                'longitude',
                'place_id',
            )
        }),
        ('SEO & Marketing', {
            'fields': (
                'slug',
                'seo_title',
                'seo_description',
                'signature_distinctions',
            ),
            'classes': ('collapse',)
        }),
        ('Staff & Management', {
            'fields': (
                'staff',
                'calendar_link',
                'assigned_agent',
                'created_by',
            )
        }),
        ('Statistics', {
            'fields': (
                'media_count',
                'booking_count',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [MediaInline, BookingInline]
    
    @display(description='Price', ordering='price')
    def price_display(self, obj):
        """Display formatted price."""
        return format_html(
            '<strong>${:,.2f}</strong>',
            obj.price
        )
    
    @display(description='Details', header=True)
    def property_stats(self, obj):
        """Display property statistics in a compact format."""
        return format_html(
            '🛏️ {} | 🚿 {} | 👥 {}',
            obj.bedrooms,
            obj.bathrooms,
            obj.max_guests
        )
    
    @display(description='Media Files')
    def media_count(self, obj):
        """Count of associated media files."""
        if obj.pk:
            count = obj.media.count()
            return format_html(
                '<a href="{}?listing__id__exact={}">{} file(s)</a>',
                reverse('admin:villas_media_changelist'),
                obj.pk,
                count
            )
        return '-'
    
    @display(description='Bookings')
    def booking_count(self, obj):
        """Count of associated bookings."""
        if obj.pk:
            count = obj.bookings.count()
            return format_html(
                '<a href="{}?property__id__exact={}">{} booking(s)</a>',
                reverse('admin:villas_booking_changelist'),
                obj.pk,
                count
            )
        return '-'
    
    def get_queryset(self, request):
        """Optimize queries with select_related and prefetch_related."""
        qs = super().get_queryset(request)
        return qs.select_related('assigned_agent', 'created_by').prefetch_related('media', 'bookings')


@admin.register(Media)
class MediaAdmin(ModelAdmin):
    """Admin interface for Media model with Unfold styling."""
    
    list_display = (
        'id',
        'listing_link',
        'media_type',
        'category',
        'file_preview',
        'is_primary',
        'order',
        'caption',
    )
    
    list_filter = (
        'media_type',
        'category',
        'is_primary',
    )
    
    search_fields = (
        'listing__title',
        'caption',
    )
    
    list_editable = ('order', 'is_primary')
    
    readonly_fields = ('media_type', 'file_preview_large')
    
    fieldsets = (
        ('File Information', {
            'fields': (
                'listing',
                'file',
                'file_preview_large',
                'media_type',
            )
        }),
        ('Classification & Display', {
            'fields': (
                'category',
                'caption',
                'is_primary',
                'order',
            )
        }),
    )
    
    @display(description='Property', ordering='listing__title')
    def listing_link(self, obj):
        """Link to the associated property."""
        url = reverse('admin:villas_property_change', args=[obj.listing.pk])
        return format_html('<a href="{}">{}</a>', url, obj.listing.title)
    
    @display(description='Preview', header=True)
    def file_preview(self, obj):
        """Display a small thumbnail preview."""
        if obj.file and obj.media_type == 'image':
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px; border-radius: 4px;" />',
                obj.file_url
            )
        elif obj.file:
            return format_html('📄 {}', obj.get_media_type_display())
        return '-'
    
    @display(description='File Preview')
    def file_preview_large(self, obj):
        """Display a larger preview in the detail view."""
        if obj.file and obj.media_type == 'image':
            return format_html(
                '<img src="{}" style="max-width: 500px; border-radius: 8px;" />',
                obj.file_url
            )
        elif obj.file:
            return format_html(
                '<a href="{}" target="_blank">📄 Download {}</a>',
                obj.file_url,
                obj.get_media_type_display()
            )
        return '-'
    
    def get_queryset(self, request):
        """Optimize queries."""
        qs = super().get_queryset(request)
        return qs.select_related('listing')


@admin.register(Booking)
class BookingAdmin(ModelAdmin):
    """Admin interface for Booking model with Unfold styling."""
    
    list_display = (
        'id',
        'property_link',
        'full_name',
        'email',
        'check_in',
        'check_out',
        'duration',
        'status',
        'total_price',
        'created_at',
    )
    
    list_filter = (
        'status',
        'check_in',
        'check_out',
        'created_at',
    )
    
    search_fields = (
        'full_name',
        'email',
        'phone',
        'property__title',
    )
    
    list_editable = ('status',)
    
    readonly_fields = ('created_at', 'duration', 'google_event_id')
    
    fieldsets = (
        ('Booking Details', {
            'fields': (
                'property',
                'user',
                'status',
            )
        }),
        ('Guest Information', {
            'fields': (
                'full_name',
                'email',
                'phone',
            )
        }),
        ('Dates & Pricing', {
            'fields': (
                'check_in',
                'check_out',
                'duration',
                'total_price',
            )
        }),
        ('Integration & Metadata', {
            'fields': (
                'google_event_id',
                'created_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'check_in'
    
    @display(description='Property', ordering='property__title')
    def property_link(self, obj):
        """Link to the associated property."""
        url = reverse('admin:villas_property_change', args=[obj.property.pk])
        return format_html('<a href="{}">{}</a>', url, obj.property.title)
    
    @display(description='Status', header=True)
    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'pending': '#FFA500',
            'approved': '#28A745',
            'rejected': '#DC3545',
            'completed': '#6C757D',
            'cancelled': '#343A40',
        }
        color = colors.get(obj.status, '#6C757D')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    @display(description='Duration')
    def duration(self, obj):
        """Calculate booking duration in days."""
        if obj.check_in and obj.check_out:
            delta = obj.check_out - obj.check_in
            return f"{delta.days} day(s)"
        return '-'
    
    def get_queryset(self, request):
        """Optimize queries."""
        qs = super().get_queryset(request)
        return qs.select_related('property', 'user')




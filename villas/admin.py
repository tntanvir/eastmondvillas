from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from unfold.decorators import display
from .models import Property, Media, Booking, PropertyImage, BedroomImage, Review, ReviewImage, Favorite


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


from django.utils.html import format_html
from django.contrib import admin


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ('image', 'preview')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height: 80px;" />', obj.image.url)
        return "-"
    
class BedroomImageInline(admin.TabularInline):
    model = BedroomImage
    extra = 1
    fields = ('image', 'preview')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height: 80px;" />', obj.image.url)
        return "-"

@admin.register(Property)
class PropertyAdmin(ModelAdmin):
    list_display = ( 'id', 'title', 'status', 'listing_type', 'price', 'assigned_agent_link', 'booking_count', 'created_at' )
    list_filter = ( 'status', 'listing_type', 'city', 'created_at', )
    search_fields = ( 'title', 'description', 'address', 'city', 'assigned_agent__name', )
    readonly_fields = ( 'slug', 'created_at', 'updated_at', 'booking_count', 'assigned_agent_link' )
    inlines = [ BookingInline, PropertyImageInline, BedroomImageInline ]
    ordering = ('-created_at',)


    @display(description='Assigned Agent', ordering='assigned_agent__name')
    def assigned_agent_link(self, obj):
        """Link to the assigned agent's admin page."""
        if obj.assigned_agent:
            url = reverse('admin:accounts_user_change', args=[obj.assigned_agent.pk])
            return format_html('<a href="{}">{}</a>', url, obj.assigned_agent.name)
        return '-'
    @display(description='Booking Count')
    def booking_count(self, obj):
        """Display the number of bookings for the property."""
        return obj.bookings.count()
    
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
    
    readonly_fields = ('created_at', 'duration',)
    
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




@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    """Admin interface for Review model with Unfold styling."""
    
    list_display = (
        'id',
        'property_link',
        'user_link',
        'rating',
        'created_at',
    )
    
    list_filter = (
        'rating',
        'created_at',
    )
    
    search_fields = (
        'property__title',
        'user__name',
        'comment',
    )
    
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Review Details', {
            'fields': (
                'property',
                'user',
                'rating',
                'comment',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    @display(description='Property', ordering='property__title')
    def property_link(self, obj):
        """Link to the associated property."""
        url = reverse('admin:villas_property_change', args=[obj.property.pk])
        return format_html('<a href="{}">{}</a>', url, obj.property.title)
    
    @display(description='User', ordering='user__name')
    def user_link(self, obj):
        """Link to the user who wrote the review."""
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.name)
    
    def get_queryset(self, request):
        """Optimize queries."""
        qs = super().get_queryset(request)
        return qs.select_related('property', 'user')
    
@admin.register(Favorite)
class FavoriteAdmin(ModelAdmin):
    """Admin interface for Favorite model with Unfold styling."""
    
    list_display = (
        'id',
        'property_link',
        'user_link',
        'created_at',
    )
    
    list_filter = (
        'created_at',
    )
    
    search_fields = (
        'property__title',
        'user__name',
    )
    
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Favorite Details', {
            'fields': (
                'property',
                'user',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    @display(description='Property', ordering='property__title')
    def property_link(self, obj):
        """Link to the associated property."""
        url = reverse('admin:villas_property_change', args=[obj.property.pk])
        return format_html('<a href="{}">{}</a>', url, obj.property.title)
    
    @display(description='User', ordering='user__name')
    def user_link(self, obj):
        """Link to the user who favorited the property."""
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.name)
    
    def get_queryset(self, request):
        """Optimize queries."""
        qs = super().get_queryset(request)
        return qs.select_related('property', 'user')
    

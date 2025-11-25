from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
import random
import string
from django.core.exceptions import ValidationError
import os 




class Property(models.Model):

    class ListingType(models.TextChoices):
        FOR_RENT = 'rent', 'For Rent'
        FOR_SALE = 'sale', 'For Sale'
    
    class StatusType(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING_REVIEW = 'pending_review', 'Pending Review'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'
        SOLD = 'sold', 'Sold'

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_properties')

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)

    # pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    booking_rate = models.JSONField(default=dict, blank=True, help_text="JSON format, e.g., { booking:  ['day':2, 'price': 500] }")

    # property details
    listing_type = models.CharField(max_length=10, choices=ListingType.choices, default=ListingType.FOR_RENT)
    status = models.CharField(max_length=20, choices=StatusType.choices, default=StatusType.DRAFT)


    address = models.TextField(blank=True)
    city = models.CharField(max_length=120, blank=True)

    add_guest = models.PositiveIntegerField(default=1)
    bedrooms = models.PositiveIntegerField(default=0)
    bathrooms = models.PositiveIntegerField(default=0)
    pool = models.PositiveIntegerField(default=0)
    
    outdoor_amenities = models.JSONField(default=dict, blank=True, help_text="JSON format, e.g., {'wifi': true, 'pool': 'private'}")

    interior_amenities = models.JSONField(default=dict, blank=True, help_text="JSON format, e.g., {'wifi': true, 'pool': 'private'}")



    # location
    latitude = models.DecimalField(max_digits=100, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=100, decimal_places=6, null=True, blank=True)

    place_id = models.CharField(max_length=255, blank=True, null=True)

    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)
    signature_distinctions = models.JSONField(blank=True, null=True, help_text="List of unique features in JSON format, e.g., ['Ocean view', 'Private beach access']")
    staff = models.JSONField(blank=True, null=True, help_text="List of staff details in JSON format, e.g., [{'role': 'chef', 'name': 'John Doe'}]")
    calendar_link = models.URLField(blank=True, null=True, help_text="Link to external booking calendar (e.g., Google Calendar)")

    # google  
    # google_calendar_id = models.CharField(max_length=255, blank=True, null=True, help_text="The ID of the Google Calendar for this property.")

    check_in = models.CharField(blank=True, null=True, help_text="Standard check-in time.")
    check_out = models.CharField(blank=True, null=True, help_text="Standard check-out time.")

    rules_and_etiquette = models.JSONField(blank=True, null=True, help_text="List of rules in JSON format, e.g., ['No smoking', 'No pets allowed']")


    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # agent details
    assigned_agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_villas', help_text='Agent assigned to manage this villa', limit_choices_to={'role': 'agent'})

    def __str__(self):
        return f"{self.title} ({self.city})"

    def _generate_unique_slug(self):
        base = slugify(self.title)[:200]
        slug = base
        n = 0
        while Property.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            n += 1
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            slug = f"{base}-{suffix}"
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)


# Media model for Villa images

class Media(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = 'image', 'Image'
        VIDEO = 'video', 'Video'
        BROCHURE = 'brochure', 'Brochure'
        OTHER = 'other', 'Other'
    
    class CategoryType(models.TextChoices):
        MEDIA = 'media', 'Media'       
        BEDROOM = 'bedroom', 'Bedroom'
        BATHROOM = 'bathroom', 'Bathroom' 
        EXTERIOR = 'exterior', 'Exterior' 
        OTHER = 'other', 'Other'
    
    # === Relationships and File Storage ===
    listing = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='media')
    
    file = models.FileField(
        upload_to='property_media/', 
        help_text='Upload any file (image, video, PDF, etc.)'
    )

     # === Automatic & User-Defined Classification ===
    media_type = models.CharField(
        max_length=10, 
        choices=MediaType.choices, 
        editable=False, # This is set automatically, not by the user
        help_text='The technical type of the file (auto-detected)'
    )
    category = models.CharField(
        max_length=30, 
        choices=CategoryType.choices, 
        default=CategoryType.MEDIA, 
        help_text='Categorize this media file (e.g., Bedroom, Exterior)'
    )
    # === Display and Metadata ===

    caption = models.CharField(max_length=255, blank=True, help_text='Optional caption or description for the media file.', null=True)

    is_primary = models.BooleanField(
        default=False, 
        help_text='Mark this as the main/cover image for the listing.'
    )

    order = models.PositiveIntegerField(
        default=0, 
        help_text='Set the display order (0 comes first).'
    )

    class Meta:
        ordering = ['order', 'id'] # Order by the 'order' field first, then by ID as a fallback

    def __str__(self):
        filename = os.path.basename(self.file.name) if self.file else 'no-file'
        return f"{self.get_category_display()} for {self.listing.title} - {filename}"

     # === Helper Property for URL ===
    @property
    def file_url(self):
        """Returns the absolute URL of the stored file."""
        if self.file:
            try:
                return self.file.url
            except (ValueError, Exception):
                return ''
        return ''
    
     # === Automatic Logic ===
    def _detect_media_type(self):
        """Private method to determine media type from the filename extension."""
        if not self.file:
            return self.MediaType.OTHER
            
        filename = self.file.name
        extension = os.path.splitext(filename)[1].lower()
        
        if extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            return self.MediaType.IMAGE
        elif extension in ['.mp4', '.mov', '.avi', '.wmv', '.mkv']:
            return self.MediaType.VIDEO
        elif extension in ['.pdf', '.doc', '.docx']:
            return self.MediaType.BROCHURE
        else:
            return self.MediaType.OTHER
    def save(self, *args, **kwargs):
        """
        Overrides the default save method to add custom logic:
        1. Automatically detects and sets the `media_type`.
        2. Ensures only one `is_primary` media exists per listing.
        """
        # 1. Auto-detect media_type before saving
        self.media_type = self._detect_media_type()

        # 2. If this instance is being set as primary, ensure no others are.
        if self.is_primary:
            # Find all other media for the same listing and un-set their primary status.
            Media.objects.filter(listing=self.listing, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        
        super().save(*args, **kwargs)

    def clean(self):
        """Adds model-level validation."""
        if not self.file:
            raise ValidationError('A file must be uploaded.')
        super().clean()


class Booking(models.Model):
    class STATUS(models.TextChoices):
        Pending = 'pending'
        Approved = 'approved'
        Rejected = 'rejected'
        Completed = 'completed'
        Cancelled = 'cancelled'
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    check_in = models.DateField()
    check_out = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS.choices, default=STATUS.Pending)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    google_event_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.id} - {self.property_id} ({self.check_in} → {self.check_out})"



class PropertyImage(models.Model):
    property = models.ForeignKey("Property", on_delete=models.CASCADE, related_name="media_images")
    image = models.ImageField(upload_to="properties/")


class BedroomImage(models.Model):
    property = models.ForeignKey("Property", on_delete=models.CASCADE, related_name="bedrooms_images")
    image = models.ImageField(upload_to="properties/bedrooms/")


class Review(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    rating = models.PositiveIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review {self.id} - {self.property.title} ({self.rating} stars)"
    

class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/')


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'property')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} favorited {self.property.title}"
    

class DailyAnalytics(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="daily_analytics")
    date = models.DateField()

    views = models.PositiveIntegerField(default=0)
    bookings = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('property', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"Analytics for {self.property.title} on {self.date}"
    




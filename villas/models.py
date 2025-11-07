from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
import random
import string
from django.core.exceptions import ValidationError


class Amenity(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class Villa(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='villas')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    property_type = models.CharField(max_length=50, blank=True)
    max_guests = models.PositiveIntegerField(default=1)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=120, blank=True)
    bedrooms = models.PositiveIntegerField(default=0)
    bathrooms = models.PositiveIntegerField(default=0)
    has_pool = models.BooleanField(default=False)
    amenities = models.ManyToManyField(Amenity, blank=True, related_name='villas')

    # location
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    place_id = models.CharField(max_length=255, blank=True, null=True)

    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)
    signature_distinctions = models.JSONField(blank=True, null=True)
    staff = models.JSONField(blank=True, null=True)
    calendar_link = models.URLField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.city})"

    def _generate_unique_slug(self):
        base = slugify(self.title)[:200]
        slug = base
        n = 0
        while Villa.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            n += 1
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            slug = f"{base}-{suffix}"
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)


class VillaImage(models.Model):
    TYPE_CHOICES = (
        ('media', 'Media'),
        ('bedroom', 'Bedroom'),
        ('other', 'Other'),
    )
    villa = models.ForeignKey(Villa, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='villa_images/', blank=True, null=True, help_text='Upload image file (preferred)')
    # URL field removed. Provide a read-only property for compatibility with existing code.
    @property
    def url(self):
        return ''

    def clean(self):
        # require at least one source of image
        if not self.image and not self.url:
            raise ValidationError('Provide either an uploaded image or an image URL.')
        super().clean()

    @property
    def image_url(self):
        # prefer uploaded ImageField, fall back to URLField
        if self.image:
            try:
                return self.image.url
            except ValueError:
                pass
        return self.url or ''
    caption = models.CharField(max_length=255, blank=True)
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='media')
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        identifier = self.image.name if self.image else (self.url or '')
        return f"Image for {self.villa_id} - {identifier}"


class BookingRate(models.Model):
    PERIOD_CHOICES = (
        ('per_night', 'Per Night'),
        ('per_week', 'Per Week'),
        ('per_month', 'Per Month'),
    )
    villa = models.ForeignKey(Villa, on_delete=models.CASCADE, related_name='rates')
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    minimum_stay = models.PositiveIntegerField(default=1)
    rate = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.villa_id} - {self.period} @ {self.rate}"


class Booking(models.Model):
    STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    villa = models.ForeignKey(Villa, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    check_in = models.DateField()
    check_out = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    google_event_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.id} - {self.villa_id} ({self.check_in} → {self.check_out})"

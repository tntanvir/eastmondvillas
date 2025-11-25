from django.utils import timezone
from django.db import models
from auditlog.registry import auditlog



# Create your models here.

class VilaListing(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    property_name = models.CharField(max_length=255)
    property_photo = models.ImageField(upload_to='vila_listings/')
    property_document = models.FileField(upload_to='vila_listings/docs/', blank=True, null=True)
    property_brief = models.TextField()
    created_at = models.DateTimeField( auto_now_add=True)
    updated_at = models.DateTimeField( auto_now=True)
    def __str__(self):
        return f'{self.name} - {self.email} - {self.property_name}'



class ContectUs(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'{self.name} - {self.email}'



auditlog.register(VilaListing)
auditlog.register(ContectUs)

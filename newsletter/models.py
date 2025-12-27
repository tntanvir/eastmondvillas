from django.db import models
from villas.models import VilaListing
from django.conf import settings
User = settings.AUTH_USER_MODEL
# Create your models here.

class NewsLetter(models.Model):
    user = models.ManyToManyField(User)
    property = models.ForeignKey(VilaListing, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.property.name

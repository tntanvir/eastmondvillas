from django.db import models
from villas.models import Property
from django.conf import settings
User = settings.AUTH_USER_MODEL
# Create your models here.

class NewsLetter(models.Model):
    user = models.ManyToManyField(User)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    


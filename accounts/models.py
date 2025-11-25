from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import datetime 
import random
import string



class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, name, password=None, **extra_fields):
        
        if not email:
            raise ValueError("Users must have an email address")

        if not name:
            raise ValueError("Users must have a name")
        
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("permission", "full_access")
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("role") != "admin":
            raise ValueError("Superuser must have role of Admin")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")  
        if not password:
            raise ValueError("Superusers must have a password.")
        
        return self.create_user(email, name, password, **extra_fields)
    
    





class User(AbstractUser, PermissionsMixin):
    username = None 
    ROLE_CHOICES = (
        ("customer", "Customer"),
        ("agent", "Agent"),
        ("manager", "Manager"),
        ("admin", "Admin"),
    )
    PERMISSION_CHOICES = (
        ('download','Download'),
        ('only_view','Only View'),
        ('full_access','Full Access'),
    )
    email = models.EmailField(unique=True)
    image = models.ImageField(upload_to='user_images/', blank=True, null=True)
    name = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="customer")
    permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='only_view')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()
    def __str__(self):
        return self.email

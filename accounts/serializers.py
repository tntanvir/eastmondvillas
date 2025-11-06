from datetime import date 
from dj_rest_auth.serializers import UserDetailsSerializer 
from dj_rest_auth.registration.serializers import RegisterSerializer 

from rest_framework import serializers
from rest_framework.validators  import UniqueValidator 

from .models import User 
from allauth.account.models import EmailAddress

class CustomUserDetailsSerializer(UserDetailsSerializer):
    class Meta(UserDetailsSerializer.Meta):
        model = User 
        fields = ('id', 'email', 'name','role', 'permission', 'is_verified', 'phone', 'address', 'date_joined', 'is_active', 'is_staff')

class CustomRegisterSerializer(RegisterSerializer):
    username = None
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    name = serializers.CharField(required=True, max_length=255)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=15)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('username', None)
    
    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['email'] = self.validated_data.get('email', '')
        data['name'] = self.validated_data.get('name', '')
        data['phone'] = self.validated_data.get('phone', '')
        return data
    
    def save(self, request):
        user = super().save(request)
        for fields, value in self.validated_data.items():
            if hasattr(user, fields):
                setattr(user, fields, value)
        user.is_active = True
        user.save()
        return user

    def validate_email(self, email):
        """
        Avoid calling EmailAddress.objects.is_verified (not available on all versions).
        Use a safe DB lookup to check whether the email is already verified.
        """
        # If allauth's EmailAddress manager provides is_verified, you could use it,
        # but some versions don't expose it. Use a filter lookup which is stable.
        if EmailAddress.objects.filter(email__iexact=email, verified=True).exists():
            raise serializers.ValidationError("This email address is already verified.")
        return email

from datetime import date 
from dj_rest_auth.serializers import UserDetailsSerializer 
from dj_rest_auth.registration.serializers import RegisterSerializer 

from rest_framework import serializers
from rest_framework.validators  import UniqueValidator 

from .models import User 
from allauth.account.models import EmailAddress

class CustomUserDetailsSerializer(UserDetailsSerializer):
    # Provide `pk` for clients that expect that key name in responses.
    pk = serializers.IntegerField(source='id', read_only=True)
    class Meta(UserDetailsSerializer.Meta):
        model = User 
        # Include pk (alias to id) and the project-specific fields consumers expect.
        fields = ('pk', 'id', 'email', 'name', 'role', 'permission', 'is_verified', 'phone', 'address', 'date_joined', 'is_active', 'is_staff', 'image')

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
        # Only allow these fields to be set during registration.
        data['email'] = self.validated_data.get('email', '')
        data['name'] = self.validated_data.get('name', '')
        data['phone'] = self.validated_data.get('phone', '')
        # Do NOT include role or permission here — roles must be assigned by admins.
        return data
    
    def save(self, request):
        # Use the parent save to create the user, then set only allowed fields.
        user = super().save(request)
        # Only copy a whitelist of fields from validated_data to the user to
        # prevent clients from assigning roles/permissions during registration.
        allowed = ('name', 'phone')
        for field in allowed:
            if field in self.validated_data:
                setattr(user, field, self.validated_data[field])
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


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer used by admins to create/update users including role and permission."""
    # For creation password is required; for updates it's optional.
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'name', 'role', 'permission', 'phone', 'address',
            'is_verified', 'is_active', 'is_staff', 'password', 'date_joined', 'image'
        )
        read_only_fields = ('is_verified',)

    def validate_email(self, value):
        # Ensure unique email except when updating the same instance
        qs = User.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('A user with that email already exists.')
        return value

    def validate(self, attrs):
        """Ensure required fields are provided when creating a new user via admin.

        Required on create: email, name, phone, role, permission, password
        """
        # If instance is None we're creating
        if not getattr(self, 'instance', None):
            required = ('email', 'name', 'phone', 'role', 'permission', 'password')
            missing = [f for f in required if not attrs.get(f)]
            if missing:
                raise serializers.ValidationError({f: 'This field is required.' for f in missing})
        return attrs

    def create(self, validated_data):
        # Extract password and required identity fields
        password = validated_data.pop('password')
        email = validated_data.pop('email')
        name = validated_data.pop('name')

        # Use the manager's create_user to ensure email normalization and
        # proper password handling. Remaining validated_data may include
        # phone, role, permission, address, is_active, is_staff, etc.
        user = User.objects.create_user(email=email, name=name, password=password, **validated_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


from dj_rest_auth.serializers import LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken

class CustomLoginSerializer(LoginSerializer):

    def get_response_data(self):
        data = super().get_response_data()

        # Token lifetime যোগ করা
        refresh = RefreshToken(self.token)
        data["access_expires_in"] = refresh.access_token.lifetime.total_seconds()
        data["refresh_expires_in"] = refresh.lifetime.total_seconds()

        return data

# accounts/serializers.py

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'image', 'phone', 'address'] 
        read_only_fields = ['email'] 
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
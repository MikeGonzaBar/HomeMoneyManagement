from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with proper validation.
    """
    
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = (
            "id",
            "username", 
            "password",
            "password_confirm",
            "first_name",
            "last_name"
        )
        read_only_fields = ("id",)
        extra_kwargs = {
            "username": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True}
        }
    
    def validate(self, attrs):
        """Validate that password and password_confirm match if provided."""
        if 'password_confirm' in attrs and attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def validate_username(self, value):
        """Validate username uniqueness."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists")
        return value
    
    def create(self, validated_data):
        """Create user with hashed password."""
        if 'password_confirm' in validated_data:
            validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    username_or_email = serializers.CharField()
    password = serializers.CharField()


class UserResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for user response (without sensitive data).
    """
    
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name"
        )
        read_only_fields = fields

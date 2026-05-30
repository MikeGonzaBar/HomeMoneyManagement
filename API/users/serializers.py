from typing import Any

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
            "last_name",
            "theme_preference",
            "is_admin",
        )
        read_only_fields = ("id", "theme_preference", "is_admin")
        extra_kwargs = {
            "username": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True}
        }
    
    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate that password and password_confirm match if provided."""
        if 'password_confirm' in attrs and attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def validate_username(self, value: str) -> str:
        """Validate username uniqueness."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists")
        return value
    
    def create(self, validated_data: dict[str, Any]) -> User:
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
            "last_name",
            "theme_preference",
            "is_admin",
        )
        read_only_fields = fields


class AdminUserSerializer(serializers.ModelSerializer):
    """Read-only representation of API users for admin-mode endpoints."""

    active_token_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "theme_preference",
            "is_admin",
            "active_token_count",
        )
        read_only_fields = fields


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Validate safe user fields that API admins may update."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "theme_preference", "is_admin")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Require at least one field in partial admin user updates."""
        if not attrs:
            raise serializers.ValidationError("At least one user field is required")
        return attrs

import secrets

from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class User(models.Model):
    """
    Model class representing a User.
    """
    
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.username}"

    @property
    def is_authenticated(self):
        """Allow DRF's IsAuthenticated permission to work with this app user."""
        return True

    @property
    def is_anonymous(self):
        return False
    
    def set_password(self, raw_password):
        """Set password with secure hashing."""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Check password against hash."""
        return check_password(raw_password, self.password)


class AuthToken(models.Model):
    """Opaque bearer token for API authentication."""

    key = models.CharField(max_length=64, primary_key=True)
    user = models.ForeignKey(User, related_name="auth_tokens", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "revoked_at"]),
            models.Index(fields=["revoked_at"]),
        ]

    def __str__(self):
        return f"Token for {self.user.username}"

    @classmethod
    def issue_for_user(cls, user):
        return cls.objects.create(key=secrets.token_hex(32), user=user)

    @property
    def is_active(self):
        return self.revoked_at is None

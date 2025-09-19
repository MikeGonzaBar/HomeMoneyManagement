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
    
    def set_password(self, raw_password):
        """Set password with secure hashing."""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Check password against hash."""
        return check_password(raw_password, self.password)

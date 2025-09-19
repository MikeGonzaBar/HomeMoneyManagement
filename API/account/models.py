from django.db import models


class Account(models.Model):
    """
    Represents an account in the system.
    """
    
    id = models.AutoField(primary_key=True)
    account_type = models.CharField(max_length=30)
    bank = models.CharField(max_length=30)
    total = models.FloatField(default=0.0)
    account_name = models.CharField(max_length=30)
    owner = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.account_name} ({self.bank})"

from django.db import models


class Transaction(models.Model):
    """
    Represents a transaction in the system.
    """
    
    id = models.AutoField(primary_key=True)
    transaction_type = models.CharField(max_length=30)
    category = models.CharField(max_length=30)
    date = models.DateField(editable=True)
    title = models.CharField(max_length=120)
    total = models.FloatField(default=0.0)
    owner_id = models.CharField(max_length=20)
    account_id = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.title} - {self.total} ({self.date})"

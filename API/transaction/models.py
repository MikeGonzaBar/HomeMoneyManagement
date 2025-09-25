from django.db import models


class Transaction(models.Model):
    """
    Represents a transaction in the system.
    Enhanced to support inter-account transfers.
    """
    
    TRANSACTION_TYPES = [
        ('Income', 'Income'),
        ('Expense', 'Expense'),
        ('Transfer', 'Transfer'),
    ]
    
    id = models.AutoField(primary_key=True)
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=30)
    date = models.DateField(editable=True)
    title = models.CharField(max_length=120)
    total = models.FloatField(default=0.0)
    owner_id = models.CharField(max_length=20)
    
    # Account fields - for transfers, from_account is source, to_account is destination
    from_account_id = models.CharField(max_length=20, null=True, blank=True, help_text="Source account (for transfers)")
    to_account_id = models.CharField(max_length=20, null=True, blank=True, help_text="Destination account (for transfers)")
    
    # Legacy field for backward compatibility
    account_id = models.CharField(max_length=20, null=True, blank=True, help_text="Legacy: single account for income/expense")

    def __str__(self):
        if self.transaction_type == 'Transfer':
            return f"Transfer: {self.title} - ${self.total} ({self.date})"
        return f"{self.title} - ${self.total} ({self.date})"
    
    @property
    def is_transfer(self):
        """Check if this is a transfer transaction."""
        return self.transaction_type == 'Transfer'
    
    @property
    def source_account(self):
        """Get the source account for transfers or the main account for income/expense."""
        if self.is_transfer:
            return self.from_account_id
        return self.account_id
    
    @property
    def destination_account(self):
        """Get the destination account for transfers."""
        if self.is_transfer:
            return self.to_account_id
        return None
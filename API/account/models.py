from django.db import models


class Account(models.Model):
    """
    Represents an account in the system.
    Enhanced to support credit card limits.
    """
    
    id = models.AutoField(primary_key=True)
    account_type = models.CharField(max_length=30)
    bank = models.CharField(max_length=30)
    total = models.FloatField(default=0.0)
    account_name = models.CharField(max_length=30)
    owner = models.CharField(max_length=150)
    
    # Credit card specific fields
    credit_limit = models.FloatField(null=True, blank=True, help_text="Credit limit for credit card accounts")
    
    def __str__(self):
        return f"{self.account_name} ({self.bank})"
    
    @property
    def is_credit_card(self):
        """Check if this is a credit card account."""
        return self.account_type == 'Crédito'
    
    @property
    def available_credit(self):
        """Get available credit for credit cards."""
        if self.is_credit_card and self.credit_limit:
            return self.total  # For credit cards, total represents available credit
        return None
    
    @property
    def used_credit(self):
        """Get used credit amount for credit cards."""
        if self.is_credit_card and self.credit_limit:
            return self.credit_limit - self.total
        return None

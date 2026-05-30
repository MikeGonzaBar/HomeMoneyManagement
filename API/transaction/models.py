from typing import Any

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
    title = models.CharField(max_length=255)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    owner_id = models.CharField(max_length=150)
    owner_user = models.ForeignKey(
        "users.User",
        related_name="transactions",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    
    # Account fields - for transfers, from_account is source, to_account is destination
    from_account_id = models.CharField(max_length=20, null=True, blank=True, help_text="Source account (for transfers)")
    to_account_id = models.CharField(max_length=20, null=True, blank=True, help_text="Destination account (for transfers)")
    from_account_fk = models.ForeignKey(
        "account.Account",
        related_name="outgoing_transfers",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    to_account_fk = models.ForeignKey(
        "account.Account",
        related_name="incoming_transfers",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    
    # Legacy field for backward compatibility
    account_id = models.CharField(max_length=20, null=True, blank=True, help_text="Legacy: single account for income/expense")
    account_fk = models.ForeignKey(
        "account.Account",
        related_name="transactions",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    class Meta:
        indexes = [
            models.Index(fields=["owner_user", "date"]),
            models.Index(fields=["owner_id", "date"]),
        ]

    def __str__(self) -> str:
        """Return a readable transaction label for admin displays."""
        if self.transaction_type == 'Transfer':
            return f"Transfer: {self.title} - ${self.total} ({self.date})"
        return f"{self.title} - ${self.total} ({self.date})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Keep legacy owner/account string fields aligned with foreign keys."""
        if self.owner_user_id:
            self.owner_id = self.owner_user.username
        if self.account_fk_id:
            self.account_id = str(self.account_fk_id)
        if self.from_account_fk_id:
            self.from_account_id = str(self.from_account_fk_id)
        if self.to_account_fk_id:
            self.to_account_id = str(self.to_account_fk_id)
        super().save(*args, **kwargs)
    
    @property
    def is_transfer(self) -> bool:
        """Check if this is a transfer transaction."""
        return self.transaction_type == 'Transfer'
    
    @property
    def source_account(self) -> str | None:
        """Get the source account for transfers or the main account for income/expense."""
        if self.is_transfer:
            return self.from_account_id
        return self.account_id
    
    @property
    def destination_account(self) -> str | None:
        """Get the destination account for transfers."""
        if self.is_transfer:
            return self.to_account_id
        return None

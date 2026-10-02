import os
from typing import Any

from django.core.validators import FileExtensionValidator
from django.db import models


def bank_statement_upload_path(instance: "BankStatement", filename: str) -> str:
    """Generate upload path for bank statement files."""
    # Create a path like: bank_statements/username/2024/01/filename.pdf
    from datetime import datetime
    now = datetime.now()
    return f'bank_statements/{instance.user_id}/{now.year}/{now.month:02d}/{filename}'


class BankStatement(models.Model):
    """
    Model to store uploaded bank statement files.
    """
    
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=150, help_text="Username of the user who uploaded the statement")
    owner_user = models.ForeignKey(
        "users.User",
        related_name="bank_statements",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    file = models.FileField(
        upload_to=bank_statement_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="PDF file of the bank statement"
    )
    original_filename = models.CharField(max_length=255, help_text="Original filename of the uploaded file")
    file_size = models.BigIntegerField(help_text="Size of the file in bytes")
    upload_date = models.DateTimeField(auto_now_add=True, help_text="Date and time when the file was uploaded")
    processed = models.BooleanField(default=False, help_text="Whether the statement has been processed by AI")
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending',
        help_text="Current processing status"
    )
    error_message = models.TextField(blank=True, null=True, help_text="Error message if processing failed")
    
    class Meta:
        ordering = ['-upload_date']
        verbose_name = "Bank Statement"
        verbose_name_plural = "Bank Statements"
        indexes = [
            models.Index(fields=["owner_user", "-upload_date"]),
            models.Index(fields=["user_id", "-upload_date"]),
        ]
    
    def __str__(self) -> str:
        """Return a readable statement label for admin displays."""
        return f"{self.user_id} - {self.original_filename} ({self.upload_date.strftime('%Y-%m-%d')})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Keep the legacy user_id string aligned with the owner foreign key."""
        if self.owner_user_id:
            self.user_id = self.owner_user.username
        super().save(*args, **kwargs)
    
    def get_file_size_display(self) -> str:
        """Return human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def delete(self, *args: Any, **kwargs: Any) -> None:
        """Override delete to also remove the file from filesystem."""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)


class BankStatementImportBatch(models.Model):
    """Review batch created from AI-extracted bank statement transactions."""

    STATUS_REVIEW = "review"
    STATUS_COMMITTED = "committed"
    STATUS_CHOICES = [
        (STATUS_REVIEW, "Review"),
        (STATUS_COMMITTED, "Committed"),
    ]

    bank_statement = models.ForeignKey(
        BankStatement,
        related_name="import_batches",
        on_delete=models.CASCADE,
    )
    owner_user = models.ForeignKey(
        "users.User",
        related_name="bank_statement_import_batches",
        on_delete=models.CASCADE,
    )
    detected_account_name = models.CharField(max_length=255, blank=True, null=True)
    detected_account_type = models.CharField(max_length=60, blank=True, null=True)
    initial_balance = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    statement_period_start = models.DateField(null=True, blank=True)
    statement_period_end = models.DateField(null=True, blank=True)
    statement_kind = models.CharField(max_length=30, default="bank", db_index=True)
    balance_period_start = models.DateField(null=True, blank=True)
    balance_period_end = models.DateField(null=True, blank=True)
    movements_period_start = models.DateField(null=True, blank=True)
    movements_period_end = models.DateField(null=True, blank=True)
    retirement_breakdown = models.JSONField(default=dict, blank=True)
    card_summary = models.JSONField(default=dict, blank=True)
    deferred_purchases = models.JSONField(default=list, blank=True)
    reconciliation = models.JSONField(default=dict, blank=True)
    linked_account = models.ForeignKey(
        "account.Account", related_name="retirement_import_batches", null=True,
        blank=True, on_delete=models.PROTECT,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_REVIEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner_user", "status", "-created_at"]),
            models.Index(fields=["bank_statement", "status"]),
        ]

    def __str__(self) -> str:
        """Return a readable batch label for admin displays."""
        return f"Import batch {self.id} for {self.bank_statement.original_filename}"


class RetirementStatementSnapshot(models.Model):
    """Immutable verified AFORE/retirement statement snapshot."""

    account = models.ForeignKey("account.Account", related_name="retirement_snapshots", on_delete=models.CASCADE)
    import_batch = models.OneToOneField(BankStatementImportBatch, related_name="retirement_snapshot", on_delete=models.CASCADE)
    statement_date = models.DateField()
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=14, decimal_places=2)
    breakdown = models.JSONField(default=dict)
    balance_period_start = models.DateField(null=True, blank=True)
    balance_period_end = models.DateField(null=True, blank=True)
    movements_period_start = models.DateField(null=True, blank=True)
    movements_period_end = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-statement_date", "-id"]
        indexes = [models.Index(fields=["account", "-statement_date"], name="bankstateme_account_dc80e1_idx")]


class BankStatementImportProduct(models.Model):
    """One balance-bearing product detected in a multi-product statement."""

    import_batch = models.ForeignKey(BankStatementImportBatch, related_name="products", on_delete=models.CASCADE)
    source_product_id = models.CharField(max_length=120)
    name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=120, blank=True)
    product_type = models.CharField(max_length=60)
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    closing_balance = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    reconciliation = models.JSONField(default=dict, blank=True)
    positions = models.JSONField(default=list, blank=True)
    linked_account = models.ForeignKey("account.Account", related_name="statement_import_products", null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["import_batch", "source_product_id"], name="unique_import_product_source")]


class ProductStatementSnapshot(models.Model):
    """Immutable verified balance snapshot for a checking or investment product."""

    account = models.ForeignKey("account.Account", related_name="product_statement_snapshots", on_delete=models.CASCADE)
    import_product = models.OneToOneField(BankStatementImportProduct, related_name="snapshot", on_delete=models.CASCADE)
    closing_balance = models.DecimalField(max_digits=14, decimal_places=2)
    statement_date = models.DateField()
    positions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CreditCardStatementSnapshot(models.Model):
    """Immutable verified card statement, including its MSI schedule."""

    account = models.ForeignKey("account.Account", related_name="credit_card_statement_snapshots", on_delete=models.CASCADE)
    import_batch = models.OneToOneField(BankStatementImportBatch, related_name="credit_card_snapshot", on_delete=models.CASCADE)
    statement_date = models.DateField()
    summary = models.JSONField(default=dict)
    deferred_purchases = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-statement_date", "-id"]
        indexes = [models.Index(fields=["account", "-statement_date"], name="card_snapshot_account_date_idx")]


class DeferredPurchase(models.Model):
    """Latest known state of one MSI/deferred purchase on a credit card."""

    account = models.ForeignKey("account.Account", related_name="deferred_purchases", on_delete=models.CASCADE)
    source_key = models.CharField(max_length=180)
    merchant = models.CharField(max_length=255)
    original_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    remaining_balance = models.DecimalField(max_digits=14, decimal_places=2)
    current_installment = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    installment_number = models.PositiveIntegerField(null=True, blank=True)
    installment_count = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["account", "source_key"], name="unique_deferred_purchase_key")]


class BankStatementTransactionCandidate(models.Model):
    """One extracted transaction candidate awaiting import review."""

    STATUS_PENDING = "pending"
    STATUS_IMPORTED = "imported"
    STATUS_SKIPPED = "skipped"
    STATUS_LINKED = "linked"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_IMPORTED, "Imported"),
        (STATUS_SKIPPED, "Skipped"),
        (STATUS_LINKED, "Linked"),
    ]

    import_batch = models.ForeignKey(
        BankStatementImportBatch,
        related_name="candidates",
        on_delete=models.CASCADE,
    )
    owner_user = models.ForeignKey(
        "users.User",
        related_name="bank_statement_candidates",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    transaction_type = models.CharField(max_length=30)
    category = models.CharField(max_length=60)
    date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    # Products and their candidates are both derived from an import batch.  They
    # must be removed together when the source statement is deleted; PROTECT
    # blocks that otherwise-valid cascade.
    source_product = models.ForeignKey(BankStatementImportProduct, related_name="outgoing_candidates", null=True, blank=True, on_delete=models.CASCADE)
    destination_product = models.ForeignKey(BankStatementImportProduct, related_name="incoming_candidates", null=True, blank=True, on_delete=models.CASCADE)
    account_fk = models.ForeignKey(
        "account.Account",
        related_name="bank_statement_candidates",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    from_account_fk = models.ForeignKey(
        "account.Account",
        related_name="outgoing_bank_statement_candidates",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    to_account_fk = models.ForeignKey(
        "account.Account",
        related_name="incoming_bank_statement_candidates",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    possible_matches = models.JSONField(default=list, blank=True)
    linked_transaction = models.ForeignKey(
        "transaction.Transaction",
        related_name="linked_bank_statement_candidates",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    imported_transaction = models.ForeignKey(
        "transaction.Transaction",
        related_name="imported_bank_statement_candidates",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_message = models.TextField(blank=True, null=True)
    raw_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner_user", "status", "date"]),
            models.Index(fields=["import_batch", "status"]),
        ]

    def __str__(self) -> str:
        """Return a readable candidate label for admin displays."""
        return f"{self.title} {self.amount} {self.date}"

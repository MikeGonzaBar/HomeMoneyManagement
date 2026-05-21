from django.db import models


class RecurringTransaction(models.Model):
    FREQUENCY_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]
    TRANSACTION_TYPES = [
        ("Income", "Income"),
        ("Expense", "Expense"),
        ("Transfer", "Transfer"),
    ]

    owner_user = models.ForeignKey(
        "users.User",
        related_name="recurring_transactions",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=60)
    total = models.DecimalField(max_digits=14, decimal_places=2)
    account_fk = models.ForeignKey(
        "account.Account",
        related_name="recurring_transactions",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    from_account_fk = models.ForeignKey(
        "account.Account",
        related_name="outgoing_recurring_transfers",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    to_account_fk = models.ForeignKey(
        "account.Account",
        related_name="incoming_recurring_transfers",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    interval = models.PositiveIntegerField(default=1)
    start_date = models.DateField()
    next_due_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner_user", "active", "next_due_date"]),
            models.Index(fields=["owner_user", "transaction_type"]),
        ]

    def __str__(self):
        return f"{self.owner_user.username}: {self.title}"


class RecurringOccurrence(models.Model):
    STATUS_DUE = "due"
    STATUS_POSTED = "posted"
    STATUS_SKIPPED = "skipped"
    STATUS_CHOICES = [
        (STATUS_DUE, "Due"),
        (STATUS_POSTED, "Posted"),
        (STATUS_SKIPPED, "Skipped"),
    ]

    recurring_transaction = models.ForeignKey(
        RecurringTransaction,
        related_name="occurrences",
        on_delete=models.CASCADE,
    )
    owner_user = models.ForeignKey(
        "users.User",
        related_name="recurring_occurrences",
        on_delete=models.CASCADE,
    )
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DUE)
    posted_transaction = models.ForeignKey(
        "transaction.Transaction",
        related_name="recurring_occurrences",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recurring_transaction", "due_date"],
                name="unique_recurring_occurrence_due_date",
            )
        ]
        indexes = [
            models.Index(fields=["owner_user", "status", "due_date"]),
        ]

    def __str__(self):
        return f"{self.recurring_transaction.title} due {self.due_date}"

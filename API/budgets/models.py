from django.db import models


class Budget(models.Model):
    """Monthly spending limit scoped to one API user."""

    SCOPE_OVERALL = "overall"
    SCOPE_CATEGORY = "category"
    SCOPE_CHOICES = [
        (SCOPE_OVERALL, "Overall"),
        (SCOPE_CATEGORY, "Category"),
    ]

    owner_user = models.ForeignKey(
        "users.User",
        related_name="budgets",
        on_delete=models.CASCADE,
    )
    month = models.DateField(help_text="First day of the budget month")
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES)
    category = models.CharField(max_length=60, blank=True, null=True)
    limit_amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner_user", "month"]),
            models.Index(fields=["owner_user", "scope", "category"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["owner_user", "month", "scope", "category"],
                name="unique_user_month_scope_category_budget",
            )
        ]

    def __str__(self) -> str:
        """Return a readable owner/month label for admin displays."""
        label = self.category if self.scope == self.SCOPE_CATEGORY else "Overall"
        return f"{self.owner_user.username} {label} {self.month:%Y-%m}"

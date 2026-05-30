from django.db import models


class Alert(models.Model):
    """In-app alert generated from financial rules and review workflows."""

    SEVERITY_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ]

    owner_user = models.ForeignKey(
        "users.User",
        related_name="alerts",
        on_delete=models.CASCADE,
    )
    alert_type = models.CharField(max_length=60)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="info")
    title = models.CharField(max_length=160)
    message = models.TextField()
    object_key = models.CharField(max_length=255)
    read_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner_user", "dismissed_at", "-created_at"]),
            models.Index(fields=["owner_user", "alert_type", "object_key"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["owner_user", "object_key"],
                name="unique_active_alert_object_key",
            )
        ]

    def __str__(self) -> str:
        """Return a readable owner/title label for admin displays."""
        return f"{self.owner_user.username}: {self.title}"

from django.apps import AppConfig


class RecurringConfig(AppConfig):
    """Django app configuration for recurring transactions."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "recurring"

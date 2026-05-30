from django.apps import AppConfig


class TransactionConfig(AppConfig):
    """Django app configuration for transactions."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transaction'

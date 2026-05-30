from django.apps import AppConfig


class BankstatementsConfig(AppConfig):
    """Django app configuration for bank statement uploads and imports."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bankstatements'
    verbose_name = 'Bank Statements'

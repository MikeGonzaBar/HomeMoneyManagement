from django.contrib import admin

from .models import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    """Django admin configuration for budgets."""

    list_display = ("id", "owner_user", "month", "scope", "category", "limit_amount")
    list_filter = ("scope", "month")
    search_fields = ("owner_user__username", "category")

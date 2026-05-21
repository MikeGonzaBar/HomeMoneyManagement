from django.contrib import admin

from .models import RecurringOccurrence, RecurringTransaction


@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "owner_user", "title", "transaction_type", "total", "frequency", "next_due_date", "active")
    list_filter = ("transaction_type", "frequency", "active")
    search_fields = ("owner_user__username", "title", "category")


@admin.register(RecurringOccurrence)
class RecurringOccurrenceAdmin(admin.ModelAdmin):
    list_display = ("id", "owner_user", "recurring_transaction", "due_date", "status")
    list_filter = ("status", "due_date")

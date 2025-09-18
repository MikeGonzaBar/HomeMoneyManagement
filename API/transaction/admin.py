from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'transaction_type', 'category', 'total', 'date', 'owner_id', 'account_id')
    list_filter = ('transaction_type', 'category', 'date', 'owner_id', 'account_id')
    search_fields = ('title', 'owner_id', 'account_id')
    ordering = ('-date', 'title')
    readonly_fields = ('id',)
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('title', 'transaction_type', 'category', 'total')
        }),
        ('Date Information', {
            'fields': ('date',)
        }),
        ('Ownership & Account', {
            'fields': ('owner_id', 'account_id')
        }),
    )

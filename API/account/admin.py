from django.contrib import admin
from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'account_name', 'account_type', 'bank', 'total', 'owner')
    list_filter = ('account_type', 'bank', 'owner')
    search_fields = ('account_name', 'owner', 'bank')
    ordering = ('owner', 'account_name')
    readonly_fields = ('id',)
    
    fieldsets = (
        ('Account Information', {
            'fields': ('account_name', 'account_type', 'bank')
        }),
        ('Financial Information', {
            'fields': ('total',)
        }),
        ('Ownership', {
            'fields': ('owner',)
        }),
    )

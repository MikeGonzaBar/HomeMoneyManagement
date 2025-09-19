from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name', 'last_name')
    list_filter = ('first_name', 'last_name')
    search_fields = ('username', 'first_name', 'last_name')
    ordering = ('username',)
    readonly_fields = ('id',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('username', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name')
        }),
    )

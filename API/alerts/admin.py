from django.contrib import admin

from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("id", "owner_user", "alert_type", "severity", "title", "read_at", "dismissed_at")
    list_filter = ("alert_type", "severity", "dismissed_at")
    search_fields = ("owner_user__username", "title", "message")

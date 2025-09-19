from django.contrib import admin
from .models import BankStatement


@admin.register(BankStatement)
class BankStatementAdmin(admin.ModelAdmin):
    """
    Admin interface for BankStatement model.
    """
    
    list_display = [
        'id',
        'user_id',
        'original_filename',
        'file_size_display',
        'upload_date',
        'processing_status',
        'processed'
    ]
    
    list_filter = [
        'processing_status',
        'processed',
        'upload_date',
        'user_id'
    ]
    
    search_fields = [
        'user_id',
        'original_filename',
        'error_message'
    ]
    
    readonly_fields = [
        'id',
        'file_size',
        'upload_date',
        'file_size_display'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user_id', 'original_filename', 'file_size_display', 'upload_date')
        }),
        ('File Information', {
            'fields': ('file', 'file_size')
        }),
        ('Processing Status', {
            'fields': ('processed', 'processing_status', 'error_message')
        }),
    )
    
    ordering = ['-upload_date']
    
    def file_size_display(self, obj):
        """Display human-readable file size."""
        return obj.get_file_size_display()
    file_size_display.short_description = 'File Size'
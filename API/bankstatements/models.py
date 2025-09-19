from django.db import models
from django.core.validators import FileExtensionValidator
import os


def bank_statement_upload_path(instance, filename):
    """Generate upload path for bank statement files."""
    # Create a path like: bank_statements/username/2024/01/filename.pdf
    from datetime import datetime
    now = datetime.now()
    return f'bank_statements/{instance.user_id}/{now.year}/{now.month:02d}/{filename}'


class BankStatement(models.Model):
    """
    Model to store uploaded bank statement files.
    """
    
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=150, help_text="Username of the user who uploaded the statement")
    file = models.FileField(
        upload_to=bank_statement_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="PDF file of the bank statement"
    )
    original_filename = models.CharField(max_length=255, help_text="Original filename of the uploaded file")
    file_size = models.BigIntegerField(help_text="Size of the file in bytes")
    upload_date = models.DateTimeField(auto_now_add=True, help_text="Date and time when the file was uploaded")
    processed = models.BooleanField(default=False, help_text="Whether the statement has been processed by AI")
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending',
        help_text="Current processing status"
    )
    error_message = models.TextField(blank=True, null=True, help_text="Error message if processing failed")
    
    class Meta:
        ordering = ['-upload_date']
        verbose_name = "Bank Statement"
        verbose_name_plural = "Bank Statements"
    
    def __str__(self):
        return f"{self.user_id} - {self.original_filename} ({self.upload_date.strftime('%Y-%m-%d')})"
    
    def get_file_size_display(self):
        """Return human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def delete(self, *args, **kwargs):
        """Override delete to also remove the file from filesystem."""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)
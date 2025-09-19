from rest_framework import serializers
from .models import BankStatement


class BankStatementUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading bank statement files.
    """
    
    class Meta:
        model = BankStatement
        fields = ['file', 'user_id']
        extra_kwargs = {
            'file': {'write_only': True},
            'user_id': {'write_only': True}
        }
    
    def validate_file(self, value):
        """Validate the uploaded file."""
        if not value:
            raise serializers.ValidationError("No file provided.")
        
        # Check file extension
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed.")
        
        # Check file size (10MB limit)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 10MB.")
        
        # Check if file is actually a PDF by reading the first few bytes
        value.seek(0)
        header = value.read(4)
        value.seek(0)  # Reset file pointer
        
        if not header.startswith(b'%PDF'):
            raise serializers.ValidationError("File does not appear to be a valid PDF.")
        
        return value


class BankStatementResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for bank statement response data.
    """
    
    file_size_display = serializers.SerializerMethodField()
    upload_date_display = serializers.SerializerMethodField()
    
    class Meta:
        model = BankStatement
        fields = [
            'id',
            'original_filename',
            'file_size',
            'file_size_display',
            'upload_date',
            'upload_date_display',
            'processed',
            'processing_status',
            'error_message'
        ]
        read_only_fields = fields
    
    def get_file_size_display(self, obj):
        """Return human-readable file size."""
        return obj.get_file_size_display()
    
    def get_upload_date_display(self, obj):
        """Return formatted upload date."""
        return obj.upload_date.strftime('%Y-%m-%d %H:%M:%S')

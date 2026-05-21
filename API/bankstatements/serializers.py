from rest_framework import serializers
from .models import BankStatement


class BankStatementUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading bank statement files.
    """
    
    class Meta:
        model = BankStatement
        fields = ['file', 'user_id', 'owner_user']
        extra_kwargs = {
            'file': {'write_only': True},
            'user_id': {'write_only': True},
            'owner_user': {'read_only': True},
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
    review_batch_id = serializers.SerializerMethodField()
    review_batch_status = serializers.SerializerMethodField()
    review_candidate_count = serializers.SerializerMethodField()
    
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
            'error_message',
            'review_batch_id',
            'review_batch_status',
            'review_candidate_count',
        ]
        read_only_fields = fields
    
    def get_file_size_display(self, obj):
        """Return human-readable file size."""
        return obj.get_file_size_display()
    
    def get_upload_date_display(self, obj):
        """Return formatted upload date."""
        return obj.upload_date.strftime('%Y-%m-%d %H:%M:%S')

    def get_review_batch(self, obj):
        return obj.import_batches.order_by('-created_at').first()

    def get_review_batch_id(self, obj):
        batch = self.get_review_batch(obj)
        return batch.id if batch else None

    def get_review_batch_status(self, obj):
        batch = self.get_review_batch(obj)
        return batch.status if batch else None

    def get_review_candidate_count(self, obj):
        batch = self.get_review_batch(obj)
        return batch.candidates.count() if batch else 0

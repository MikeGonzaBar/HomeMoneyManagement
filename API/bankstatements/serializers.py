from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import Coalesce
from rest_framework import serializers

from .models import BankStatement, BankStatementImportBatch, BankStatementTransactionCandidate


def with_review_data(queryset):
    """Annotate each statement with its latest review batch data in the same query."""
    latest_batch = BankStatementImportBatch.objects.filter(
        bank_statement=OuterRef("pk"),
    ).order_by("-created_at")
    latest_batch_id = Subquery(latest_batch.values("id")[:1])
    candidate_count = (
        BankStatementTransactionCandidate.objects
        .filter(import_batch=OuterRef("review_batch_id"))
        .values("import_batch")
        .annotate(total=Count("id"))
        .values("total")[:1]
    )
    return queryset.annotate(
        review_batch_id=latest_batch_id,
        review_batch_status=Subquery(latest_batch.values("status")[:1]),
        review_candidate_count=Coalesce(Subquery(candidate_count), 0),
    )


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
    
    def validate_file(self, value: object) -> object:
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
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._review_batches = {}

    def get_file_size_display(self, obj: BankStatement) -> str:
        """Return human-readable file size."""
        return obj.get_file_size_display()
    
    def get_upload_date_display(self, obj: BankStatement) -> str:
        """Return formatted upload date."""
        return obj.upload_date.strftime('%Y-%m-%d %H:%M:%S')

    def get_review_batch(self, obj: BankStatement) -> BankStatementImportBatch | None:
        """Return or cache the latest review batch for an unannotated statement."""
        if obj.pk not in self._review_batches:
            self._review_batches[obj.pk] = obj.import_batches.order_by('-created_at').first()
        return self._review_batches[obj.pk]

    def get_review_batch_id(self, obj: BankStatement) -> int | None:
        """Return the most recent import review batch ID."""
        if hasattr(obj, "review_batch_id"):
            return obj.review_batch_id
        batch = self.get_review_batch(obj)
        return batch.id if batch else None

    def get_review_batch_status(self, obj: BankStatement) -> str | None:
        """Return the most recent import review batch status."""
        if hasattr(obj, "review_batch_status"):
            return obj.review_batch_status
        batch = self.get_review_batch(obj)
        return batch.status if batch else None

    def get_review_candidate_count(self, obj: BankStatement) -> int:
        """Return the number of candidates in the most recent review batch."""
        if hasattr(obj, "review_candidate_count"):
            return obj.review_candidate_count
        batch = self.get_review_batch(obj)
        return batch.candidates.count() if batch else 0

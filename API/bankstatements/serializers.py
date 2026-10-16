from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import Coalesce
from rest_framework import serializers

from .models import BankStatement, BankStatementImportBatch, BankStatementTransactionCandidate


def with_review_data(queryset):
    """Annotate each statement with its latest review batch data in the same query."""
    latest_batch = BankStatementImportBatch.objects.filter(
        bank_statement=OuterRef("pk"),
    ).order_by("-created_at", "-id")
    latest_batch_id = Subquery(latest_batch.values("id")[:1])
    candidate_count = (
        BankStatementTransactionCandidate.objects
        .filter(import_batch=OuterRef("review_batch_id"))
        .values("import_batch")
        .annotate(total=Count("id"))
        .values("total")[:1]
    )
    resolved_count = (
        BankStatementTransactionCandidate.objects
        .filter(import_batch=OuterRef("review_batch_id"))
        .exclude(status=BankStatementTransactionCandidate.STATUS_PENDING)
        .values("import_batch")
        .annotate(total=Count("id"))
        .values("total")[:1]
    )
    return queryset.annotate(
        review_batch_id=latest_batch_id,
        review_batch_status=Subquery(latest_batch.values("status")[:1]),
        review_candidate_count=Coalesce(Subquery(candidate_count), 0),
        review_resolved_count=Coalesce(Subquery(resolved_count), 0),
        review_period_start=Subquery(latest_batch.values("statement_period_start")[:1]),
        review_period_end=Subquery(latest_batch.values("statement_period_end")[:1]),
        review_account_name=Subquery(latest_batch.values("detected_account_name")[:1]),
        review_account_type=Subquery(latest_batch.values("detected_account_type")[:1]),
        review_draft_account_id=Subquery(latest_batch.values("draft_account_id")[:1]),
        review_draft_account_name=Subquery(latest_batch.values("draft_account__account_name")[:1]),
        review_draft_account_type=Subquery(latest_batch.values("draft_account__account_type")[:1]),
        review_draft_new_account=Subquery(latest_batch.values("draft_new_account")[:1]),
        review_scan_summary=Subquery(latest_batch.values("scan_summary")[:1]),
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
    review_resolved_count = serializers.SerializerMethodField()
    review_period_start = serializers.SerializerMethodField()
    review_period_end = serializers.SerializerMethodField()
    review_account_name = serializers.SerializerMethodField()
    review_account_type = serializers.SerializerMethodField()
    review_draft_assignment = serializers.SerializerMethodField()
    review_scan_summary = serializers.SerializerMethodField()
    
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
            'retry_count',
            'next_retry_at',
            'failure_class',
            'review_batch_id',
            'review_batch_status',
            'review_candidate_count',
            'review_resolved_count',
            'review_period_start',
            'review_period_end',
            'review_account_name',
            'review_account_type',
            'review_draft_assignment',
            'review_scan_summary',
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
            self._review_batches[obj.pk] = obj.import_batches.order_by('-created_at', '-id').first()
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

    def get_review_resolved_count(self, obj: BankStatement) -> int:
        """Return the resolved (non-pending) candidates in the most recent review batch."""
        if hasattr(obj, "review_resolved_count"):
            return obj.review_resolved_count
        batch = self.get_review_batch(obj)
        if not batch:
            return 0
        return batch.candidates.exclude(
            status=BankStatementTransactionCandidate.STATUS_PENDING
        ).count()

    def get_review_period_start(self, obj: BankStatement) -> str | None:
        """Return the statement period start detected during extraction."""
        if hasattr(obj, "review_period_start"):
            value = obj.review_period_start
        else:
            batch = self.get_review_batch(obj)
            value = batch.statement_period_start if batch else None
        return value.isoformat() if value else None

    def get_review_period_end(self, obj: BankStatement) -> str | None:
        """Return the statement period end detected during extraction."""
        if hasattr(obj, "review_period_end"):
            value = obj.review_period_end
        else:
            batch = self.get_review_batch(obj)
            value = batch.statement_period_end if batch else None
        return value.isoformat() if value else None

    def get_review_account_name(self, obj: BankStatement) -> str | None:
        """Return the bank/account detected during extraction."""
        if hasattr(obj, "review_account_name"):
            return obj.review_account_name
        batch = self.get_review_batch(obj)
        return batch.detected_account_name if batch else None

    def get_review_account_type(self, obj: BankStatement) -> str | None:
        if hasattr(obj, "review_account_type"):
            return obj.review_account_type
        batch = self.get_review_batch(obj)
        return batch.detected_account_type if batch else None

    def get_review_draft_assignment(self, obj: BankStatement) -> dict | None:
        if hasattr(obj, "review_draft_account_id"):
            if obj.review_draft_account_id:
                return {
                    "kind": "existing", "account_id": obj.review_draft_account_id,
                    "account_name": obj.review_draft_account_name,
                    "account_type": obj.review_draft_account_type,
                }
            if obj.review_draft_new_account:
                return {"kind": "new", **obj.review_draft_new_account}
            return None
        batch = self.get_review_batch(obj)
        if not batch:
            return None
        if batch.draft_account_id:
            return {"kind": "existing", "account_id": batch.draft_account_id,
                    "account_name": batch.draft_account.account_name, "account_type": batch.draft_account.account_type}
        return {"kind": "new", **batch.draft_new_account} if batch.draft_new_account else None

    def get_review_scan_summary(self, obj: BankStatement) -> dict:
        if hasattr(obj, "review_scan_summary"):
            if obj.review_scan_summary is not None:
                return obj.review_scan_summary
            candidate_count = self.get_review_candidate_count(obj)
            return {
                "raw_transaction_count": candidate_count,
                "importable_candidate_count": candidate_count,
                "zero_result_reason": "No importable transactions are available from this scan." if not candidate_count else "",
            }
        batch = self.get_review_batch(obj)
        if batch and batch.scan_summary:
            return batch.scan_summary
        candidate_count = self.get_review_candidate_count(obj)
        return {
            "raw_transaction_count": candidate_count,
            "importable_candidate_count": candidate_count,
            "zero_result_reason": "No importable transactions are available from this scan." if not candidate_count else "",
        }

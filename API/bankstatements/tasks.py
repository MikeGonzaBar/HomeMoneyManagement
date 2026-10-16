"""Background processing operations for uploaded bank statements."""
import logging
import random
from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from .models import BankStatement
from .reconciliation import create_import_batch
from .services import classify_gemini_error, extract_transactions_from_pdf

logger = logging.getLogger(__name__)


class StatementProcessingError(RuntimeError):
    """Preserves safe retry metadata returned by the extraction service."""

    def __init__(self, message: str, failure_class: str = "permanent", retry_after_seconds: int | None = None) -> None:
        super().__init__(message)
        self.failure_class = failure_class
        self.retry_after_seconds = retry_after_seconds


def _retry_delay_seconds(
    retry_count: int,
    provider_delay: int | None,
    failure_class: str = "",
) -> int:
    """Use Gemini's reset guidance when present, otherwise bounded exponential backoff."""
    if provider_delay:
        return provider_delay
    if failure_class == "rate_limited":
        base = max(1, int(getattr(settings, "BANK_STATEMENT_RATE_LIMIT_RETRY_BASE_SECONDS", 300)))
        maximum = max(base, int(getattr(settings, "BANK_STATEMENT_RATE_LIMIT_RETRY_MAX_SECONDS", 3600)))
        jitter = max(0, int(getattr(settings, "BANK_STATEMENT_RATE_LIMIT_JITTER_SECONDS", 30)))
        return min(maximum, base * (2 ** max(0, retry_count - 1))) + random.randint(0, jitter)
    base = max(1, int(getattr(settings, "BANK_STATEMENT_RETRY_BASE_SECONDS", 60)))
    maximum = max(base, int(getattr(settings, "BANK_STATEMENT_RETRY_MAX_SECONDS", 3600)))
    return min(maximum, base * (2 ** max(0, retry_count - 1)))


def _pause_pending_statement_queue(retry_at) -> int:
    """Prevent other queued PDFs from consuming the same rate-limited API quota."""
    return BankStatement.objects.filter(processing_status="pending").filter(
        Q(next_retry_at__isnull=True) | Q(next_retry_at__lt=retry_at)
    ).update(next_retry_at=retry_at)


def _schedule_or_fail(statement_id: int, error: StatementProcessingError) -> None:
    """Schedule only retryable provider failures; all others remain terminal."""
    retryable = error.failure_class in {"rate_limited", "timeout", "provider_unavailable"}
    statement = BankStatement.objects.filter(id=statement_id).values("retry_count").first()
    if statement is None:
        return

    retry_count = int(statement["retry_count"])
    max_retries = max(0, int(getattr(settings, "BANK_STATEMENT_MAX_AUTO_RETRIES", 3)))
    if retryable and retry_count < max_retries:
        next_count = retry_count + 1
        retry_at = timezone.now() + timedelta(seconds=_retry_delay_seconds(
            next_count, error.retry_after_seconds, error.failure_class,
        ))
        BankStatement.objects.filter(id=statement_id).update(
            processing_status="pending",
            processed=False,
            retry_count=next_count,
            next_retry_at=retry_at,
            failure_class=error.failure_class,
            error_message=(
                f"Temporary AI provider issue. Retrying automatically at "
                f"{timezone.localtime(retry_at).strftime('%Y-%m-%d %H:%M:%S %Z')}."
            ),
        )
        logger.warning(
            "Bank statement %s scheduled automatic retry %s/%s at %s after %s",
            statement_id, next_count, max_retries, retry_at.isoformat(), error.failure_class,
        )
        if error.failure_class == "rate_limited":
            paused_count = _pause_pending_statement_queue(retry_at)
            logger.warning(
                "Gemini rate limit paused %s pending bank-statement jobs until %s",
                paused_count, retry_at.isoformat(),
            )
        return

    detail = (
        "The AI provider remained temporarily unavailable after automatic retries."
        if retryable
        else str(error)
    )
    BankStatement.objects.filter(id=statement_id).update(
        processing_status="failed",
        processed=False,
        next_retry_at=None,
        failure_class=error.failure_class,
        error_message=f"{detail} You can retry this statement manually.",
    )


def process_bank_statement(statement_id: int) -> None:
    """Extract one saved statement and persist its review batch."""
    try:
        statement = BankStatement.objects.get(id=statement_id)
    except BankStatement.DoesNotExist:
        return

    # Use queryset updates for state transitions.  The user may delete a
    # statement while its PDF is being sent to Gemini; in that case a model
    # instance save would raise and terminate the whole worker process.
    if not BankStatement.objects.filter(id=statement_id).update(
        processing_status="processing", error_message=None
    ):
        logger.info("Bank statement %s was deleted before processing started", statement_id)
        return

    logger.info("Bank statement %s processing started", statement_id)

    try:
        extracted_data = extract_transactions_from_pdf(statement.file.path)
        if extracted_data.get("error"):
            error_message = str(extracted_data["error"])
            failure_class = extracted_data.get("failure_class")
            retry_after_seconds = extracted_data.get("retry_after_seconds")
            if not failure_class:
                failure_class, inferred_delay = classify_gemini_error(error_message)
                retry_after_seconds = retry_after_seconds or inferred_delay
            raise StatementProcessingError(error_message, failure_class, retry_after_seconds)

        # The database row is the queue entry. A user may delete a queued or
        # in-flight upload while Gemini is working; never turn that stale
        # result into a review batch after its queue entry has gone away.
        if not BankStatement.objects.filter(id=statement_id).exists():
            logger.info("Bank statement %s was deleted while processing; discarding result", statement_id)
            return

        create_import_batch(statement, extracted_data)
        completed = BankStatement.objects.filter(id=statement_id).update(
            processing_status="completed", processed=True, error_message=None,
            next_retry_at=None, failure_class="",
        )
        if completed:
            logger.info("Bank statement %s processing completed", statement_id)
        else:
            logger.info("Bank statement %s was deleted before completion; discarding result", statement_id)
    except StatementProcessingError as exc:
        logger.warning("Bank statement %s processing failed: %s", statement_id, exc)
        _schedule_or_fail(statement_id, exc)
    except Exception as exc:
        logger.exception("Bank statement %s processing failed", statement_id)
        _schedule_or_fail(statement_id, StatementProcessingError(str(exc)))

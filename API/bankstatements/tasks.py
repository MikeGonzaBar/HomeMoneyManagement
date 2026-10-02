"""Background processing operations for uploaded bank statements."""
import logging

from .models import BankStatement
from .reconciliation import create_import_batch
from .services import extract_transactions_from_pdf

logger = logging.getLogger(__name__)


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

    try:
        extracted_data = extract_transactions_from_pdf(statement.file.path)
        if extracted_data.get("error"):
            raise RuntimeError(str(extracted_data["error"]))

        create_import_batch(statement, extracted_data)
        BankStatement.objects.filter(id=statement_id).update(
            processing_status="completed", processed=True, error_message=None
        )
        logger.info("Bank statement %s processing completed", statement_id)
    except Exception as exc:
        logger.exception("Bank statement %s processing failed", statement_id)
        updated = BankStatement.objects.filter(id=statement_id).update(
            processing_status="failed",
            processed=False,
            error_message=f"AI processing error: {exc}",
        )
        if not updated:
            logger.info("Bank statement %s was deleted while it was processing", statement_id)

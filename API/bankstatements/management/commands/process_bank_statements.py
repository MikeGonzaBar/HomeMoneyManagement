import time
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from bankstatements.models import BankStatement
from bankstatements.tasks import process_bank_statement

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process pending bank statement uploads."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--poll-interval", type=float, default=2.0)

    def handle(self, *args, **options) -> None:
        # Recover jobs interrupted by a worker/container restart.
        BankStatement.objects.filter(processing_status="processing").update(processing_status="pending")

        while True:
            statement_id = self._claim_next()
            if statement_id is not None:
                try:
                    process_bank_statement(statement_id)
                except Exception:
                    # A single malformed provider response or database race
                    # must never stop the queue and leave later uploads stuck.
                    logger.exception("Unhandled worker failure for bank statement %s", statement_id)
                    BankStatement.objects.filter(id=statement_id).update(
                        processing_status="failed",
                        processed=False,
                        error_message="Unexpected background-processing failure. Please retry the upload.",
                    )
                continue
            if options["once"]:
                return
            time.sleep(max(0.25, options["poll_interval"]))

    @staticmethod
    def _claim_next() -> int | None:
        with transaction.atomic():
            statement = (
                BankStatement.objects.select_for_update(skip_locked=True)
                .filter(processing_status="pending")
                .order_by("upload_date")
                .first()
            )
            if statement is None:
                return None
            statement.processing_status = "processing"
            statement.save(update_fields=["processing_status"])
            return statement.id

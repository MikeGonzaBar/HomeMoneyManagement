import time
import logging

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import OperationalError, close_old_connections, transaction
from django.db.models import Q
from django.utils import timezone

from bankstatements.models import BankStatement
from bankstatements.tasks import process_bank_statement

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process pending bank statement uploads."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--poll-interval", type=float, default=2.0)

    def handle(self, *args, **options) -> None:
        logger.info("Bank statement worker started (poll_interval=%ss)", options["poll_interval"])

        recovered_interrupted_jobs = False
        db_retry_delay = 1.0
        max_db_retry_delay = max(1, int(getattr(settings, "BANK_STATEMENT_DB_RETRY_MAX_SECONDS", 30)))
        while True:
            try:
                # Recover jobs interrupted by a worker/container restart only
                # after the database becomes reachable.
                if not recovered_interrupted_jobs:
                    BankStatement.objects.filter(processing_status="processing").update(processing_status="pending")
                    recovered_interrupted_jobs = True
                statement_id = self._claim_next()
                db_retry_delay = 1.0
            except OperationalError as exc:
                logger.warning(
                    "Bank statement worker cannot reach PostgreSQL; retrying in %ss: %s",
                    db_retry_delay, exc,
                )
                close_old_connections()
                time.sleep(db_retry_delay)
                db_retry_delay = min(max_db_retry_delay, db_retry_delay * 2)
                continue
            if statement_id is not None:
                try:
                    process_bank_statement(statement_id)
                except OperationalError as exc:
                    # Do not overwrite a recoverable statement with a terminal
                    # processing failure when PostgreSQL disappears mid-job.
                    logger.warning(
                        "PostgreSQL became unavailable while processing bank statement %s: %s",
                        statement_id, exc,
                    )
                    close_old_connections()
                    time.sleep(db_retry_delay)
                    db_retry_delay = min(max_db_retry_delay, db_retry_delay * 2)
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
                .filter(Q(next_retry_at__isnull=True) | Q(next_retry_at__lte=timezone.now()))
                .order_by("upload_date")
                .first()
            )
            if statement is None:
                return None
            statement.processing_status = "processing"
            statement.save(update_fields=["processing_status"])
            return statement.id

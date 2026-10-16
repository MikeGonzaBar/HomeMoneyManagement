import argparse

from django.core.management.base import BaseCommand, CommandError

from account.models import Account
from bankstatements.models import (
    BankStatementImportBatch,
    CreditCardStatementSnapshot,
    DeferredPurchase,
)
from bankstatements.reconciliation import persist_card_deferred_purchases


class Command(BaseCommand):
    help = (
        "Restore credit-card MSI/deferred-purchase plans that were extracted into "
        "an import batch's deferred_purchases but never promoted to the account's "
        "statement snapshot (for example after an 'import transactions only' "
        "review). Dry-run by default; pass --apply to write."
    )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--batch-id",
            type=int,
            action="append",
            dest="batch_ids",
            help="Only repair this import batch id (repeatable). Default: every "
            "credit-card batch with plans missing from its account.",
        )
        parser.add_argument(
            "--account-id",
            type=int,
            help="Force the destination account for a single --batch-id repair "
            "instead of resolving it from the batch.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write the changes. Without it the command only reports what it "
            "would do (dry run).",
        )

    def handle(self, *args, **options) -> None:
        batch_ids = options.get("batch_ids")
        batches = BankStatementImportBatch.objects.filter(
            statement_kind="credit_card_deferred_payments",
            status=BankStatementImportBatch.STATUS_COMMITTED,
        ).select_related("linked_account", "owner_user")
        if batch_ids:
            batches = batches.filter(id__in=batch_ids)
        else:
            # Only touch committed batches whose plans were never
            # promoted. A batch that already has its snapshot is
            # complete and left untouched, and a batch still in
            # review is promoted by its own commit.
            promoted = CreditCardStatementSnapshot.objects.values_list("import_batch_id", flat=True)
            batches = batches.exclude(id__in=promoted)

        repaired = 0
        for batch in batches.order_by("id"):
            plans = [p for p in (batch.deferred_purchases or []) if p.get("remaining_balance") not in (None, "")]
            if not plans:
                self.stdout.write(f"batch {batch.id}: no deferred plans with a remaining balance; skipping")
                continue

            account, source = self._resolve_account(batch, options.get("account_id"))
            if account is None:
                self.stdout.write(
                    f"batch {batch.id}: could not resolve a destination credit-card "
                    "account; pass --account-id to repair it"
                )
                continue
            if not account.is_credit_card:
                self.stdout.write(
                    f"batch {batch.id}: resolved account {account.id} "
                    f"({account.account_name}) is not a credit card; skipping"
                )
                continue

            existing = {dp.source_key for dp in DeferredPurchase.objects.filter(account=account)}
            statement_date = batch.statement_period_end or batch.movements_period_end
            if statement_date is None:
                self.stdout.write(
                    f"batch {batch.id}: no statement end date; cannot build a snapshot, skipping"
                )
                continue
            self.stdout.write(
                f"batch {batch.id} ({batch.bank_statement.original_filename}) -> "
                f"account {account.id} '{account.account_name}' [{source}], "
                f"statement_date={statement_date}"
            )
            for plan in plans:
                key = str(plan.get("source_key"))[:180]
                state = "update" if key in existing else "create"
                self.stdout.write(
                    f"  {state}: {plan.get('merchant')} "
                    f"({plan.get('installment_number')}/{plan.get('installment_count')}) "
                    f"remaining={plan.get('remaining_balance')} "
                    f"monthly={plan.get('current_installment')}"
                )

            if not options.get("apply"):
                self.stdout.write("  dry run: no changes written (pass --apply)")
                continue

            persist_card_deferred_purchases(account, batch, statement_date, batch.card_summary or {})
            if batch.linked_account_id != account.id:
                batch.linked_account = account
                batch.save(update_fields=["linked_account", "updated_at"])
            repaired += 1

        self.stdout.write(
            ("Repaired " if options.get("apply") else "Would repair ") + f"{repaired} batch(es)."
        )

    def _resolve_account(self, batch: BankStatementImportBatch, account_id):
        """Return (account, human_source) for a batch without inventing data."""
        if account_id:
            try:
                account = Account.objects.get(id=account_id, owner_user=batch.owner_user)
            except Account.DoesNotExist as exc:
                raise CommandError(f"account {account_id} not found for this owner") from exc
            return account, "--account-id"
        if batch.linked_account_id:
            return batch.linked_account, "linked_account"
        # Fall back to the account the committed transactions were actually
        # imported into; that is the account the user already reconciled.
        candidate = (
            batch.candidates.filter(imported_transaction__isnull=False)
            .exclude(imported_transaction__account_fk__isnull=True)
            .values_list("imported_transaction__account_fk", flat=True)
            .first()
        )
        if candidate:
            account = Account.objects.filter(id=candidate).first()
            if account:
                return account, "imported transaction account"
        if batch.draft_account_id:
            return batch.draft_account, "draft_account"
        return None, "unresolved"


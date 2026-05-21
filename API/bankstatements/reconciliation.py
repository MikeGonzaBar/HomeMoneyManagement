import re
from datetime import date
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction

from account.models import Account
from transaction.models import Transaction
from transaction.services import create_transaction, transaction_payload

from .models import BankStatementImportBatch, BankStatementTransactionCandidate


def normalize_title(value):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(value).lower())).strip()


def parse_date(value):
    if not value:
        raise ValidationError("date is required")
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise ValidationError("date must use YYYY-MM-DD format") from exc


def parse_decimal(value, field_name="amount"):
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a valid decimal number") from exc
    if amount <= 0:
        raise ValidationError(f"{field_name} must be greater than 0")
    return amount


def optional_account(user, value, field_name):
    if value in (None, ""):
        return None
    try:
        return Account.objects.get(owner_user=user, id=value)
    except Account.DoesNotExist as exc:
        raise ValidationError(f"Invalid {field_name}") from exc


def transaction_match_payload(item):
    return {
        "id": item.id,
        "title": item.title,
        "transaction_type": item.transaction_type,
        "category": item.category,
        "date": item.date.isoformat(),
        "total": float(item.total),
        "account_id": str(item.account_fk_id) if item.account_fk_id else item.account_id,
        "from_account_id": str(item.from_account_fk_id) if item.from_account_fk_id else item.from_account_id,
        "to_account_id": str(item.to_account_fk_id) if item.to_account_fk_id else item.to_account_id,
    }


def find_possible_matches(candidate):
    query = Transaction.objects.filter(
        owner_user=candidate.owner_user,
        transaction_type=candidate.transaction_type,
        date=candidate.date,
        total=candidate.amount,
    )
    if candidate.transaction_type == "Transfer":
        if candidate.from_account_fk_id:
            query = query.filter(from_account_fk=candidate.from_account_fk)
        if candidate.to_account_fk_id:
            query = query.filter(to_account_fk=candidate.to_account_fk)
    elif candidate.account_fk_id:
        query = query.filter(account_fk=candidate.account_fk)
    normalized = normalize_title(candidate.title)
    exact = []
    fuzzy = []
    for item in query[:25]:
        item_norm = normalize_title(item.title)
        if item_norm == normalized:
            exact.append(transaction_match_payload(item))
        elif normalized in item_norm or item_norm in normalized:
            fuzzy.append(transaction_match_payload(item))
    return exact + fuzzy


def candidate_payload(candidate):
    return {
        "id": candidate.id,
        "title": candidate.title,
        "transaction_type": candidate.transaction_type,
        "category": candidate.category,
        "date": candidate.date.isoformat(),
        "amount": float(candidate.amount),
        "account_id": str(candidate.account_fk_id) if candidate.account_fk_id else None,
        "from_account_id": str(candidate.from_account_fk_id) if candidate.from_account_fk_id else None,
        "to_account_id": str(candidate.to_account_fk_id) if candidate.to_account_fk_id else None,
        "possible_matches": candidate.possible_matches,
        "linked_transaction_id": candidate.linked_transaction_id,
        "imported_transaction": transaction_payload(candidate.imported_transaction) if candidate.imported_transaction else None,
        "status": candidate.status,
        "error_message": candidate.error_message,
    }


def batch_payload(batch):
    return {
        "id": batch.id,
        "bank_statement_id": batch.bank_statement_id,
        "status": batch.status,
        "detected_account_name": batch.detected_account_name,
        "detected_account_type": batch.detected_account_type,
        "initial_balance": float(batch.initial_balance) if batch.initial_balance is not None else None,
        "statement_period": {
            "start": batch.statement_period_start.isoformat() if batch.statement_period_start else None,
            "end": batch.statement_period_end.isoformat() if batch.statement_period_end else None,
        },
        "candidates": [candidate_payload(item) for item in batch.candidates.order_by("date", "id")],
    }


def create_import_batch(bank_statement, extracted_data):
    period = extracted_data.get("statement_period") or {}
    batch = BankStatementImportBatch.objects.create(
        bank_statement=bank_statement,
        owner_user=bank_statement.owner_user,
        detected_account_name=extracted_data.get("account_name") or "",
        detected_account_type=extracted_data.get("account_type") or "",
        initial_balance=extracted_data.get("initial_balance") if extracted_data.get("initial_balance") is not None else None,
        statement_period_start=parse_date(period["start"]) if period.get("start") else None,
        statement_period_end=parse_date(period["end"]) if period.get("end") else None,
    )
    for raw in extracted_data.get("transactions", []):
        amount = raw.get("amount", raw.get("total"))
        candidate = BankStatementTransactionCandidate.objects.create(
            import_batch=batch,
            owner_user=bank_statement.owner_user,
            title=raw.get("title") or raw.get("description") or "Imported transaction",
            transaction_type=raw.get("transaction_type") or "Expense",
            category=raw.get("category") or "Others",
            date=parse_date(raw.get("date")),
            amount=parse_decimal(amount),
            raw_data=raw,
        )
        candidate.possible_matches = find_possible_matches(candidate)
        candidate.save(update_fields=["possible_matches"])
    return batch


def update_candidate(user, candidate_id, data):
    try:
        candidate = BankStatementTransactionCandidate.objects.get(owner_user=user, id=candidate_id)
    except BankStatementTransactionCandidate.DoesNotExist as exc:
        raise BankStatementTransactionCandidate.DoesNotExist("Candidate not found") from exc
    allowed_statuses = {
        BankStatementTransactionCandidate.STATUS_PENDING,
        BankStatementTransactionCandidate.STATUS_SKIPPED,
        BankStatementTransactionCandidate.STATUS_LINKED,
    }
    if "title" in data:
        candidate.title = data["title"]
    if "transaction_type" in data:
        candidate.transaction_type = data["transaction_type"]
    if "category" in data:
        candidate.category = data["category"]
    if "date" in data:
        candidate.date = parse_date(data["date"])
    if "amount" in data:
        candidate.amount = parse_decimal(data["amount"])
    if "account_id" in data:
        candidate.account_fk = optional_account(user, data.get("account_id"), "account_id")
    if "from_account_id" in data:
        candidate.from_account_fk = optional_account(user, data.get("from_account_id"), "from_account_id")
    if "to_account_id" in data:
        candidate.to_account_fk = optional_account(user, data.get("to_account_id"), "to_account_id")
    if "status" in data:
        if data["status"] not in allowed_statuses:
            raise ValidationError("status must be pending, skipped, or linked")
        candidate.status = data["status"]
    if "linked_transaction_id" in data and data.get("linked_transaction_id"):
        try:
            linked = Transaction.objects.get(owner_user=user, id=data["linked_transaction_id"])
        except Transaction.DoesNotExist as exc:
            raise ValidationError("Invalid linked_transaction_id") from exc
        candidate.linked_transaction = linked
        candidate.status = BankStatementTransactionCandidate.STATUS_LINKED
    candidate.possible_matches = find_possible_matches(candidate)
    candidate.save()
    return candidate


@db_transaction.atomic
def commit_batch(user, batch_id, data):
    try:
        batch = BankStatementImportBatch.objects.select_for_update().get(owner_user=user, id=batch_id)
    except BankStatementImportBatch.DoesNotExist as exc:
        raise BankStatementImportBatch.DoesNotExist("Import batch not found") from exc
    default_account = optional_account(user, data.get("account_id"), "account_id") if data.get("account_id") else None
    imported = []
    skipped = []
    failed = []
    for candidate in batch.candidates.select_for_update().order_by("id"):
        if candidate.status in {
            BankStatementTransactionCandidate.STATUS_IMPORTED,
            BankStatementTransactionCandidate.STATUS_SKIPPED,
            BankStatementTransactionCandidate.STATUS_LINKED,
        }:
            skipped.append(candidate_payload(candidate))
            continue
        if default_account and not candidate.account_fk_id and candidate.transaction_type != "Transfer":
            candidate.account_fk = default_account
        try:
            payload = {
                "title": candidate.title,
                "transaction_type": candidate.transaction_type,
                "category": candidate.category,
                "date": candidate.date.isoformat(),
                "total": str(candidate.amount),
            }
            if candidate.transaction_type == "Transfer":
                if not candidate.from_account_fk_id or not candidate.to_account_fk_id:
                    raise ValidationError("Transfer candidates require from_account_id and to_account_id")
                payload["from_account_id"] = str(candidate.from_account_fk_id)
                payload["to_account_id"] = str(candidate.to_account_fk_id)
            else:
                if not candidate.account_fk_id:
                    raise ValidationError("Candidate requires account_id")
                payload["account_id"] = str(candidate.account_fk_id)
            transaction = create_transaction(user, payload)
            candidate.imported_transaction = transaction
            candidate.status = BankStatementTransactionCandidate.STATUS_IMPORTED
            candidate.error_message = None
            candidate.save(update_fields=["account_fk", "imported_transaction", "status", "error_message", "updated_at"])
            imported.append(candidate_payload(candidate))
        except Exception as exc:
            candidate.error_message = str(exc)
            candidate.save(update_fields=["error_message", "updated_at"])
            failed.append(candidate_payload(candidate))
    if not batch.candidates.filter(status=BankStatementTransactionCandidate.STATUS_PENDING).exists():
        batch.status = BankStatementImportBatch.STATUS_COMMITTED
        batch.save(update_fields=["status", "updated_at"])
    return {
        "batch": batch_payload(batch),
        "imported": imported,
        "skipped": skipped,
        "failed": failed,
    }

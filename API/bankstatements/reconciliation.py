import re
from datetime import date
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.db.models import Q

from account.models import Account
from transaction.models import Transaction
from transaction.services import create_transaction, transaction_payload
from users.models import User

from .models import (
    BankStatement, BankStatementImportBatch, BankStatementTransactionCandidate,
    RetirementStatementSnapshot, BankStatementImportProduct, ProductStatementSnapshot,
    CreditCardStatementSnapshot, DeferredPurchase,
)

MATCH_CHUNK_SIZE = 200


def normalize_title(value: object) -> str:
    """Normalize titles for lightweight duplicate matching."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(value).lower())).strip()


def parse_date(value: object) -> date:
    """Parse a required ISO date from imported statement data."""
    if not value:
        raise ValidationError("date is required")
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise ValidationError("date must use YYYY-MM-DD format") from exc


def parse_decimal(value: object, field_name: str = "amount") -> Decimal:
    """Parse a positive decimal from imported statement data."""
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a valid decimal number") from exc
    if amount <= 0:
        raise ValidationError(f"{field_name} must be greater than 0")
    return amount


def optional_account(user: User, value: object, field_name: str) -> Account | None:
    """Return an optional account owned by the user."""
    if value in (None, ""):
        return None
    try:
        return Account.objects.get(owner_user=user, id=value)
    except Account.DoesNotExist as exc:
        raise ValidationError(f"Invalid {field_name}") from exc


def parse_balance(value: object, field_name: str) -> Decimal:
    """Parse a balance, allowing zero and signed liability values."""
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a valid decimal number") from exc


def product_movement_totals(batch: BankStatementImportBatch) -> dict[int, Decimal]:
    """Calculate the net reviewed movement assigned to every statement product."""
    totals = {product_id: Decimal("0.00") for product_id in batch.products.values_list("id", flat=True)}
    candidates = batch.candidates.exclude(status=BankStatementTransactionCandidate.STATUS_SKIPPED)
    for candidate in candidates:
        amount = candidate.amount
        if candidate.transaction_type == "Transfer":
            if candidate.source_product_id in totals:
                totals[candidate.source_product_id] -= amount
            if candidate.destination_product_id in totals:
                totals[candidate.destination_product_id] += amount
        elif candidate.source_product_id in totals:
            totals[candidate.source_product_id] += amount if candidate.transaction_type == "Income" else -amount
    return totals


def refresh_product_reconciliations(batch: BankStatementImportBatch) -> None:
    """Recalculate product endings after user edits to balances or assignments."""
    movements = product_movement_totals(batch)
    products = list(batch.products.all())
    for product in products:
        reconciliation = dict(product.reconciliation or {})
        valuation = Decimal(str(reconciliation.get("valuation_change") or 0)).quantize(Decimal("0.01"))
        movement = movements.get(product.id, Decimal("0.00"))
        calculated = product.opening_balance + movement + valuation if product.opening_balance is not None else None
        is_reconciled = calculated is not None and product.closing_balance is not None and calculated == product.closing_balance
        reconciliation.update({
            "opening_balance": float(product.opening_balance) if product.opening_balance is not None else None,
            "closing_balance": float(product.closing_balance) if product.closing_balance is not None else None,
            "cash_movements": float(movement),
            "valuation_change": float(valuation),
            "calculated_closing_balance": float(calculated) if calculated is not None else None,
            "is_reconciled": is_reconciled,
            "reason": "" if is_reconciled else "Opening balance plus assigned transactions does not match the expected ending balance.",
        })
        product.reconciliation = reconciliation
    if products:
        BankStatementImportProduct.objects.bulk_update(products, ["reconciliation"])


def transaction_match_payload(item: Transaction) -> dict[str, object]:
    """Return a compact transaction match candidate."""
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


def _rank_matches(
    candidate: BankStatementTransactionCandidate,
    items,
) -> list[dict[str, object]]:
    """Return exact title matches first, followed by the existing fuzzy matches."""
    normalized = normalize_title(candidate.title)
    exact = []
    fuzzy = []
    for item in items:
        item_normalized = normalize_title(item.title)
        if item_normalized == normalized:
            exact.append(transaction_match_payload(item))
        elif normalized in item_normalized or item_normalized in normalized:
            fuzzy.append(transaction_match_payload(item))
    return exact + fuzzy


def _transaction_match_key(item: BankStatementTransactionCandidate | Transaction) -> tuple:
    """Return the required fields used to narrow statement duplicate matching."""
    return (
        item.transaction_type,
        item.date,
        item.amount if isinstance(item, BankStatementTransactionCandidate) else item.total,
    )


def _candidate_match_query(
    candidate: BankStatementTransactionCandidate,
) -> Q:
    lookup = {
        "transaction_type": candidate.transaction_type,
        "date": candidate.date,
        "total": candidate.amount,
    }
    if candidate.transaction_type == "Transfer":
        if candidate.from_account_fk_id:
            lookup["from_account_fk_id"] = candidate.from_account_fk_id
        if candidate.to_account_fk_id:
            lookup["to_account_fk_id"] = candidate.to_account_fk_id
    elif candidate.account_fk_id:
        lookup["account_fk_id"] = candidate.account_fk_id
    return Q(**lookup)


def find_possible_matches_for_candidates(
    candidates: list[BankStatementTransactionCandidate],
) -> dict[int, list[dict[str, object]]]:
    """Find duplicate candidates for a batch using chunked database queries."""
    matches = {candidate.id: [] for candidate in candidates}
    if not candidates:
        return matches

    for offset in range(0, len(candidates), MATCH_CHUNK_SIZE):
        chunk = candidates[offset:offset + MATCH_CHUNK_SIZE]
        query = Q()
        for condition in {_candidate_match_query(candidate) for candidate in chunk}:
            query |= condition
        transactions = Transaction.objects.filter(
            owner_user=chunk[0].owner_user_id
        ).filter(query)
        grouped: dict[tuple, list[Transaction]] = {}
        for item in transactions:
            grouped.setdefault(_transaction_match_key(item), []).append(item)
        for candidate in chunk:
            candidate_items = grouped.get(_transaction_match_key(candidate), [])
            if candidate.transaction_type == "Transfer":
                if candidate.from_account_fk_id:
                    candidate_items = [
                        item for item in candidate_items
                        if item.from_account_fk_id == candidate.from_account_fk_id
                    ]
                if candidate.to_account_fk_id:
                    candidate_items = [
                        item for item in candidate_items
                        if item.to_account_fk_id == candidate.to_account_fk_id
                    ]
            elif candidate.account_fk_id:
                candidate_items = [
                    item for item in candidate_items
                    if item.account_fk_id == candidate.account_fk_id
                ]
            matches[candidate.id] = _rank_matches(candidate, candidate_items[:25])
    return matches


def find_possible_matches(candidate: BankStatementTransactionCandidate) -> list[dict[str, object]]:
    """Find likely existing transactions for an import candidate."""
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
    return _rank_matches(candidate, query[:25])


def candidate_payload(candidate: BankStatementTransactionCandidate) -> dict[str, object]:
    """Return the API representation for one import candidate."""
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
        "source_product_id": candidate.source_product.source_product_id if candidate.source_product_id else None,
        "destination_product_id": candidate.destination_product.source_product_id if candidate.destination_product_id else None,
        "requires_resolution": bool(candidate.raw_data.get("unresolved_transfer")),
        "possible_matches": candidate.possible_matches,
        "linked_transaction_id": candidate.linked_transaction_id,
        "imported_transaction": (
            transaction_payload(candidate.imported_transaction)
            if candidate.imported_transaction
            else None
        ),
        "status": candidate.status,
        "error_message": candidate.error_message,
    }


def batch_payload(batch: BankStatementImportBatch) -> dict[str, object]:
    """Return the API representation for an import review batch."""
    candidates = batch.candidates.select_related("imported_transaction", "source_product", "destination_product").order_by("date", "id")
    products = []
    if batch.statement_kind == "multi_product":
        movements = product_movement_totals(batch)
        products = [
            {"id": item.id, "source_product_id": item.source_product_id, "name": item.name, "bank_name": item.bank_name,
             "product_type": item.product_type, "opening_balance": float(item.opening_balance) if item.opening_balance is not None else None,
             "closing_balance": float(item.closing_balance) if item.closing_balance is not None else None,
             "calculated_closing_balance": (
                 float(item.opening_balance + movements.get(item.id, Decimal("0.00")) + Decimal(str((item.reconciliation or {}).get("valuation_change") or 0)))
                 if item.opening_balance is not None else None
             ),
             "reconciliation": item.reconciliation, "positions": item.positions,
             "linked_account_id": item.linked_account_id}
            for item in batch.products.select_related("linked_account").order_by("id")
        ]
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
        "statement_kind": batch.statement_kind,
        "balance_period": {
            "start": batch.balance_period_start.isoformat() if batch.balance_period_start else None,
            "end": batch.balance_period_end.isoformat() if batch.balance_period_end else None,
        },
        "movements_period": {
            "start": batch.movements_period_start.isoformat() if batch.movements_period_start else None,
            "end": batch.movements_period_end.isoformat() if batch.movements_period_end else None,
        },
        "retirement_breakdown": batch.retirement_breakdown,
        "card_summary": batch.card_summary,
        "deferred_purchases": batch.deferred_purchases,
        "reconciliation": batch.reconciliation,
        "linked_account_id": batch.linked_account_id,
        "products": products,
        "candidates": [candidate_payload(item) for item in candidates],
    }


@db_transaction.atomic
def create_import_batch(
    bank_statement: BankStatement,
    extracted_data: dict[str, object],
) -> BankStatementImportBatch:
    """Create import review candidates from extracted statement data."""
    period = extracted_data.get("statement_period") or {}
    balance_period = extracted_data.get("balance_period") or period
    movements_period = extracted_data.get("movements_period") or period
    batch = BankStatementImportBatch.objects.create(
        bank_statement=bank_statement,
        owner_user=bank_statement.owner_user,
        detected_account_name=extracted_data.get("account_name") or "",
        detected_account_type=extracted_data.get("account_type") or "",
        initial_balance=(
            extracted_data.get("initial_balance")
            if extracted_data.get("initial_balance") is not None
            else None
        ),
        statement_period_start=parse_date(period["start"]) if period.get("start") else None,
        statement_period_end=parse_date(period["end"]) if period.get("end") else None,
        statement_kind=extracted_data.get("statement_kind") or "bank",
        balance_period_start=parse_date(balance_period["start"]) if balance_period.get("start") else None,
        balance_period_end=parse_date(balance_period["end"]) if balance_period.get("end") else None,
        movements_period_start=parse_date(movements_period["start"]) if movements_period.get("start") else None,
        movements_period_end=parse_date(movements_period["end"]) if movements_period.get("end") else None,
        retirement_breakdown=extracted_data.get("retirement_breakdown") or {},
        card_summary=extracted_data.get("card_summary") or {},
        deferred_purchases=extracted_data.get("deferred_purchases") or [],
        reconciliation=extracted_data.get("reconciliation") or {},
    )
    product_by_source: dict[str, BankStatementImportProduct] = {}
    if batch.statement_kind == "multi_product":
        for raw_product in extracted_data.get("accounts", []):
            source_id = str(raw_product.get("source_product_id") or "").strip()
            if not source_id or source_id in product_by_source:
                continue
            product_by_source[source_id] = BankStatementImportProduct.objects.create(
                import_batch=batch, source_product_id=source_id,
                name=raw_product.get("name") or source_id,
                bank_name=raw_product.get("bank_name") or extracted_data.get("account_name") or "",
                product_type=raw_product.get("product_type") or raw_product.get("type") or "Other",
                opening_balance=raw_product.get("opening_balance"), closing_balance=raw_product.get("closing_balance"),
                reconciliation=raw_product.get("reconciliation") or {}, positions=raw_product.get("positions") or [],
            )
    candidates = []
    raw_transactions = list(extracted_data.get("transactions", []))
    if batch.statement_kind == "multi_product":
        raw_transactions.extend({**item, "transaction_type": "Transfer", "unresolved_transfer": True} for item in extracted_data.get("unresolved_transfers", []))
    for raw in raw_transactions:
        if raw.get("importable") is False:
            continue
        amount = raw.get("amount", raw.get("total"))
        candidate_date = raw.get("date")
        # Aggregate retirement movements are valid at the statement-period end,
        # but rows with neither a date nor a usable period are review-only.
        if not candidate_date and batch.statement_kind == "retirement":
            candidate_date = movements_period.get("end")
        if not candidate_date:
            continue
        candidates.append(
            BankStatementTransactionCandidate(
                import_batch=batch,
                owner_user=bank_statement.owner_user,
                title=raw.get("title") or raw.get("description") or "Imported transaction",
                transaction_type=raw.get("transaction_type") or "Expense",
                category=raw.get("category") or "Others",
                date=parse_date(candidate_date),
                amount=parse_decimal(amount),
                source_product=product_by_source.get(str(raw.get("source_product_id") or "")),
                destination_product=product_by_source.get(str(raw.get("destination_product_id") or "")),
                raw_data=raw,
            )
        )
    if not candidates:
        return batch

    BankStatementTransactionCandidate.objects.bulk_create(candidates, batch_size=500)
    matches = find_possible_matches_for_candidates(candidates)
    matched_candidates = [candidate for candidate in candidates if matches[candidate.id]]
    if matched_candidates:
        for candidate in matched_candidates:
            candidate.possible_matches = matches[candidate.id]
        BankStatementTransactionCandidate.objects.bulk_update(
            matched_candidates,
            ["possible_matches"],
            batch_size=500,
        )
    return batch


def update_candidate(
    user: User,
    candidate_id: int,
    data: dict[str, object],
) -> BankStatementTransactionCandidate:
    """Update one import review candidate owned by a user."""
    try:
        candidate = (
            BankStatementTransactionCandidate.objects
            .select_related("imported_transaction")
            .get(owner_user=user, id=candidate_id)
        )
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
    if "source_product_id" in data:
        source_id = data.get("source_product_id")
        candidate.source_product = (
            candidate.import_batch.products.filter(source_product_id=source_id).first()
            if source_id else None
        )
        if source_id and not candidate.source_product:
            raise ValidationError("Invalid source_product_id")
    if "destination_product_id" in data:
        destination_id = data.get("destination_product_id")
        candidate.destination_product = (
            candidate.import_batch.products.filter(source_product_id=destination_id).first()
            if destination_id else None
        )
        if destination_id and not candidate.destination_product:
            raise ValidationError("Invalid destination_product_id")
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
    if candidate.transaction_type != "Transfer":
        candidate.destination_product = None
    elif candidate.source_product_id and candidate.source_product_id == candidate.destination_product_id:
        raise ValidationError("Transfer source and destination products must be different")
    elif candidate.from_account_fk_id and candidate.from_account_fk_id == candidate.to_account_fk_id:
        raise ValidationError("Transfer source and destination accounts must be different")
    candidate.possible_matches = find_possible_matches(candidate)
    candidate.save()
    if candidate.import_batch.statement_kind == "multi_product":
        refresh_product_reconciliations(candidate.import_batch)
    return candidate


def create_candidate(user: User, batch_id: int, data: dict[str, object]) -> BankStatementTransactionCandidate:
    """Add a user-entered transaction to an import-review batch."""
    try:
        batch = BankStatementImportBatch.objects.get(owner_user=user, id=batch_id)
    except BankStatementImportBatch.DoesNotExist as exc:
        raise BankStatementImportBatch.DoesNotExist("Import batch not found") from exc
    required = ("title", "transaction_type", "category", "date", "amount")
    missing = [name for name in required if not data.get(name)]
    if missing:
        raise ValidationError(f"Missing required candidate fields: {', '.join(missing)}")
    source_product = None
    destination_product = None
    if batch.statement_kind == "multi_product":
        source_product = batch.products.filter(source_product_id=data.get("source_product_id")).first()
        destination_product = batch.products.filter(source_product_id=data.get("destination_product_id")).first()
        if not source_product:
            raise ValidationError("Select a product for the transaction")
        if data["transaction_type"] == "Transfer" and not destination_product:
            raise ValidationError("Select a destination product for the transfer")
    candidate = BankStatementTransactionCandidate.objects.create(
        import_batch=batch,
        owner_user=user,
        title=str(data["title"]).strip(),
        transaction_type=str(data["transaction_type"]),
        category=str(data["category"]),
        date=parse_date(data["date"]),
        amount=parse_decimal(data["amount"]),
        source_product=source_product,
        destination_product=destination_product,
        raw_data={"entered_manually": True},
    )
    candidate.possible_matches = find_possible_matches(candidate)
    candidate.save(update_fields=["possible_matches", "updated_at"])
    if batch.statement_kind == "multi_product":
        refresh_product_reconciliations(batch)
    return candidate


def update_import_product(user: User, product_id: int, data: dict[str, object]) -> BankStatementImportProduct:
    """Update editable detected-account details while a statement is in review."""
    try:
        product = BankStatementImportProduct.objects.select_related("import_batch").get(
            id=product_id,
            import_batch__owner_user=user,
        )
    except BankStatementImportProduct.DoesNotExist as exc:
        raise BankStatementImportProduct.DoesNotExist("Statement product not found") from exc
    if product.import_batch.status != BankStatementImportBatch.STATUS_REVIEW:
        raise ValidationError("Statement products can only be edited while the statement is in review")

    if "name" in data:
        product.name = str(data["name"]).strip()
        if not product.name:
            raise ValidationError("Account name is required")
    if "bank_name" in data:
        product.bank_name = str(data["bank_name"] or "").strip()
    if "product_type" in data:
        product.product_type = str(data["product_type"]).strip()
        if not product.product_type:
            raise ValidationError("Account type is required")
    balances_changed = False
    if "opening_balance" in data:
        product.opening_balance = parse_balance(data["opening_balance"], "opening_balance")
        balances_changed = True
    if "closing_balance" in data:
        product.closing_balance = parse_balance(data["closing_balance"], "closing_balance")
        balances_changed = True
    product.save(update_fields=["name", "bank_name", "product_type", "opening_balance", "closing_balance"])
    if balances_changed:
        refresh_product_reconciliations(product.import_batch)
        product.refresh_from_db()
    return product


def update_deferred_purchases(user: User, batch_id: int, plans: object) -> BankStatementImportBatch:
    """Persist user-reviewed MSI schedule fields before a batch is committed."""
    try:
        batch = BankStatementImportBatch.objects.get(owner_user=user, id=batch_id)
    except BankStatementImportBatch.DoesNotExist as exc:
        raise BankStatementImportBatch.DoesNotExist("Import batch not found") from exc
    if batch.status != BankStatementImportBatch.STATUS_REVIEW:
        raise ValidationError("MSI details can only be edited while the statement is in review")
    if not isinstance(plans, list):
        raise ValidationError("deferred_purchases must be a list")

    existing = {str(plan.get("source_key")): dict(plan) for plan in batch.deferred_purchases or []}
    if set(str(plan.get("source_key")) for plan in plans) != set(existing):
        raise ValidationError("MSI plans must match the statement's detected plans")

    updated = []
    for submitted in plans:
        source_key = str(submitted.get("source_key"))
        plan = existing[source_key]
        current_installment = submitted.get("current_installment")
        plan["current_installment"] = (
            None if current_installment in (None, "")
            else str(parse_decimal(current_installment, "current_installment"))
        )
        remaining_balance = submitted.get("remaining_balance")
        if remaining_balance in (None, ""):
            plan["remaining_balance"] = None
        else:
            try:
                remaining = Decimal(str(remaining_balance)).quantize(Decimal("0.01"))
            except (InvalidOperation, TypeError, ValueError) as exc:
                raise ValidationError("remaining_balance must be a valid decimal number") from exc
            if remaining < 0:
                raise ValidationError("remaining_balance cannot be negative")
            # Zero is valid for a plan whose final installment was paid.
            plan["remaining_balance"] = str(remaining)
        for field in ("installment_number", "installment_count"):
            value = submitted.get(field)
            if value in (None, ""):
                plan[field] = None
                continue
            try:
                number = int(value)
            except (TypeError, ValueError) as exc:
                raise ValidationError(f"{field} must be a whole number") from exc
            if number <= 0:
                raise ValidationError(f"{field} must be greater than zero")
            plan[field] = number
        if plan.get("installment_number") and plan.get("installment_count") and plan["installment_number"] > plan["installment_count"]:
            raise ValidationError("installment_number cannot exceed installment_count")
        updated.append(plan)
    batch.deferred_purchases = updated
    batch.save(update_fields=["deferred_purchases", "updated_at"])
    return batch


@db_transaction.atomic
def commit_batch(user: User, batch_id: int, data: dict[str, object]) -> dict[str, object]:
    """Commit an import batch by creating transactions for pending candidates."""
    try:
        batch = BankStatementImportBatch.objects.select_for_update().get(owner_user=user, id=batch_id)
    except BankStatementImportBatch.DoesNotExist as exc:
        raise BankStatementImportBatch.DoesNotExist("Import batch not found") from exc
    default_account = optional_account(user, data.get("account_id"), "account_id") if data.get("account_id") else None
    if batch.statement_kind == "multi_product":
        raw_map = data.get("product_account_map") or {}
        products = list(batch.products.select_for_update())
        if not products:
            raise ValidationError("Multi-product statement has no detected products")
        for product in products:
            if product.reconciliation.get("is_reconciled") is not True:
                raise ValidationError(f"{product.name} does not reconcile and must remain in review")
            if product.closing_balance is None:
                raise ValidationError(f"{product.name} is missing a closing balance")
            account = optional_account(user, raw_map.get(str(product.id)), "product_account_map")
            if not account:
                raise ValidationError(f"Assign an account to {product.name} before importing")
            product.linked_account = account
        BankStatementImportProduct.objects.bulk_update(products, ["linked_account"])
        unresolved = batch.candidates.filter(raw_data__unresolved_transfer=True).exists()
        if unresolved:
            raise ValidationError("Resolve the unmatched credit-card payment before committing this multi-product statement")
        product_lookup = {item.id: item.linked_account for item in products}
        for candidate in batch.candidates.select_for_update(of=("self",)).filter(status=BankStatementTransactionCandidate.STATUS_PENDING):
            if candidate.raw_data.get("unresolved_transfer"):
                raise ValidationError(f"Resolve or skip the unmatched transfer: {candidate.title}")
            if candidate.transaction_type == "Transfer":
                candidate.from_account_fk = product_lookup.get(candidate.source_product_id)
                candidate.to_account_fk = product_lookup.get(candidate.destination_product_id)
                if not candidate.from_account_fk_id or not candidate.to_account_fk_id:
                    raise ValidationError(f"Resolve both products for transfer: {candidate.title}")
            else:
                candidate.account_fk = product_lookup.get(candidate.source_product_id)
                if not candidate.account_fk_id:
                    raise ValidationError(f"Resolve product for transaction: {candidate.title}")
            candidate.save(update_fields=["account_fk", "from_account_fk", "to_account_fk", "updated_at"])
    if batch.statement_kind == "retirement":
        reconciliation = batch.reconciliation or {}
        use_opening_balance_only = bool(data.get("use_retirement_opening_balance_only"))
        opening_balance = None
        opening_balance_value = reconciliation.get("opening_balance")
        if opening_balance_value is None:
            opening_balance_value = batch.initial_balance
        if use_opening_balance_only and reconciliation.get("is_reconciled"):
            raise ValidationError("Opening-balance-only import is only available for unreconciled retirement statements")
        if not reconciliation.get("is_reconciled") and not use_opening_balance_only:
            raise ValidationError("Retirement statements require a reconciled opening and closing balance before import")
        if not default_account or default_account.account_type != "Retirement":
            raise ValidationError("Retirement statement imports require a Retirement account")
        if use_opening_balance_only:
            try:
                opening_balance = Decimal(str(opening_balance_value)).quantize(Decimal("0.01"))
            except Exception as exc:
                raise ValidationError("An opening balance is required for an opening-balance-only retirement import") from exc
            if default_account.total != opening_balance:
                raise ValidationError("The selected Retirement account must start at the detected opening balance for this import")
        statement_date = batch.balance_period_end or batch.movements_period_end
        if not statement_date:
            raise ValidationError("Retirement statement is missing a statement date")
        prior_date = (default_account.retirement_metadata or {}).get("statement_date")
        if prior_date and str(statement_date) <= str(prior_date):
            raise ValidationError("This retirement statement is not newer than the latest snapshot")
        if prior_date and not use_opening_balance_only and not data.get("confirm_retirement_snapshot"):
            raise ValidationError("Confirm that this retirement statement is newer than the latest snapshot")
        if not use_opening_balance_only and batch.candidates.filter(status=BankStatementTransactionCandidate.STATUS_SKIPPED).exists():
            raise ValidationError("A reconciled retirement snapshot requires every economic movement to be imported or linked")
    if batch.statement_kind == "credit_card_deferred_payments":
        reconciliation = batch.reconciliation or {}
        summary = batch.card_summary or {}
        import_transactions_only = bool(data.get("import_transactions_only"))
        if not reconciliation.get("is_reconciled") and not import_transactions_only:
            raise ValidationError("Credit-card deferred-payment statements require a reconciled limit, debt, and available credit before import")
        if import_transactions_only:
            # The user reviewed individual ledger rows but chose not to trust
            # an incomplete card summary. Do not create a card snapshot or
            # overwrite card metadata in this mode.
            reconciliation = {**reconciliation, "import_transactions_only": True}
        if not default_account or not default_account.is_credit_card:
            raise ValidationError("Credit-card deferred-payment imports require a Credit Card account")
        statement_date = batch.statement_period_end or batch.movements_period_end
        if not statement_date:
            raise ValidationError("Credit-card statement is missing a statement date")
        expected_limit = Decimal(str(summary.get("credit_limit")))
        if not import_transactions_only and default_account.credit_limit != expected_limit:
            raise ValidationError("The account credit limit must match the verified statement credit limit")
        previous = default_account.credit_card_statement_snapshots.order_by("-statement_date", "-id").first()
        if previous and statement_date <= previous.statement_date:
            raise ValidationError("This credit-card statement is not newer than the latest snapshot")
        if previous and not import_transactions_only and not data.get("confirm_credit_card_snapshot"):
            raise ValidationError("Confirm that this credit-card statement is newer than the latest snapshot")
        if not import_transactions_only and batch.candidates.filter(status=BankStatementTransactionCandidate.STATUS_SKIPPED).exists():
            raise ValidationError("A reconciled credit-card snapshot requires every economic movement to be imported or linked")
    imported = []
    skipped = []
    failed = []
    candidates = (
        batch.candidates
        .select_for_update(of=("self",))
        .select_related("imported_transaction")
    )
    for candidate in candidates.order_by("id"):
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
            candidate.save(update_fields=["account_fk", "from_account_fk", "to_account_fk", "imported_transaction", "status", "error_message", "updated_at"])
            imported.append(candidate_payload(candidate))
        except Exception as exc:
            candidate.error_message = str(exc)
            candidate.save(update_fields=["error_message", "updated_at"])
            failed.append(candidate_payload(candidate))
    if not batch.candidates.filter(status=BankStatementTransactionCandidate.STATUS_PENDING).exists():
        if batch.statement_kind == "multi_product":
            for product in products:
                product.linked_account.refresh_from_db()
                if product.linked_account.total != product.closing_balance:
                    raise ValidationError(
                        f"{product.name} calculates to {product.linked_account.total}, "
                        f"not the expected ending balance {product.closing_balance}"
                    )
        batch.status = BankStatementImportBatch.STATUS_COMMITTED
        if batch.statement_kind == "retirement":
            breakdown = batch.retirement_breakdown or {}
            reconciliation = batch.reconciliation or {}
            opening_balance_value = reconciliation.get("opening_balance")
            if opening_balance_value is None:
                opening_balance_value = batch.initial_balance
            opening_balance = Decimal(str(opening_balance_value))
            statement_date = batch.balance_period_end or batch.movements_period_end
            opening_balance_only = bool(data.get("use_retirement_opening_balance_only"))
            metadata = {
                "institution": breakdown.get("institution"), "subtype": "AFORE",
                "statement_date": statement_date.isoformat(), "opening_balance": float(opening_balance), "breakdown": breakdown,
                "balance_period": {"start": batch.balance_period_start.isoformat() if batch.balance_period_start else None, "end": batch.balance_period_end.isoformat() if batch.balance_period_end else None},
                "movements_period": {"start": batch.movements_period_start.isoformat() if batch.movements_period_start else None, "end": batch.movements_period_end.isoformat() if batch.movements_period_end else None},
                "source_statement_id": batch.bank_statement_id, "import_batch_id": batch.id,
            }
            if opening_balance_only:
                metadata["import_mode"] = "opening_balance_only"
                metadata["reconciliation_status"] = "unreconciled"
            else:
                closing_balance = Decimal(str(reconciliation.get("closing_balance")))
                RetirementStatementSnapshot.objects.get_or_create(
                    import_batch=batch,
                    defaults={
                        "account": default_account,
                        "statement_date": statement_date,
                        "opening_balance": opening_balance,
                        "closing_balance": closing_balance,
                        "breakdown": breakdown,
                        "balance_period_start": batch.balance_period_start,
                        "balance_period_end": batch.balance_period_end,
                        "movements_period_start": batch.movements_period_start,
                        "movements_period_end": batch.movements_period_end,
                    },
                )
                metadata["closing_balance"] = float(closing_balance)
            default_account.retirement_metadata = metadata
            default_account.save(update_fields=["retirement_metadata"])
            batch.linked_account = default_account
        if batch.statement_kind == "multi_product":
            statement_date = batch.statement_period_end
            if not statement_date:
                raise ValidationError("Multi-product statement is missing its end date")
            for product in batch.products.select_related("linked_account"):
                ProductStatementSnapshot.objects.get_or_create(
                    import_product=product,
                    defaults={"account": product.linked_account, "closing_balance": product.closing_balance,
                              "statement_date": statement_date, "positions": product.positions},
                )
        if batch.statement_kind == "credit_card_deferred_payments" and not bool(data.get("import_transactions_only")):
            summary = batch.card_summary or {}
            statement_date = batch.statement_period_end or batch.movements_period_end
            closing_available = Decimal(str(summary.get("available_credit"))).quantize(Decimal("0.01"))
            default_account.refresh_from_db()
            if default_account.total != closing_available:
                raise ValidationError("Imported card movements do not reach the verified available-credit balance")
            CreditCardStatementSnapshot.objects.get_or_create(
                import_batch=batch,
                defaults={"account": default_account, "statement_date": statement_date,
                          "summary": summary, "deferred_purchases": batch.deferred_purchases or []},
            )
            for plan in batch.deferred_purchases or []:
                remaining = plan.get("remaining_balance")
                if remaining in (None, ""):
                    continue
                DeferredPurchase.objects.update_or_create(
                    account=default_account,
                    source_key=str(plan.get("source_key"))[:180],
                    defaults={
                        "merchant": str(plan.get("merchant") or "Deferred purchase")[:255],
                        "original_amount": plan.get("original_amount") or None,
                        "remaining_balance": remaining,
                        "current_installment": plan.get("current_installment") or None,
                        "installment_number": plan.get("installment_number") or None,
                        "installment_count": plan.get("installment_count") or plan.get("total_installments") or None,
                        "metadata": plan,
                    },
                )
            default_account.credit_card_metadata = {
                "statement_date": statement_date.isoformat(), "summary": summary,
                "deferred_purchase_count": len(batch.deferred_purchases or []),
                "source_statement_id": batch.bank_statement_id, "import_batch_id": batch.id,
            }
            default_account.save(update_fields=["credit_card_metadata"])
            batch.linked_account = default_account
        batch.save(update_fields=["status", "linked_account", "updated_at"])
    return {
        "batch": batch_payload(batch),
        "imported": imported,
        "skipped": skipped,
        "failed": failed,
    }

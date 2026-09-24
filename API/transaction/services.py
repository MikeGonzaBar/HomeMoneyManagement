from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.db.models import F

from account.models import Account
from users.models import User

from .models import Transaction


VALID_TRANSACTION_TYPES = {"Income", "Expense", "Transfer"}


def decimal_value(value: object, field_name: str = "total") -> Decimal:
    """Parse a required positive transaction amount."""
    if value in (None, ""):
        raise ValidationError(f"{field_name} is required")
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a valid decimal number") from exc
    if amount <= 0:
        raise ValidationError(f"{field_name} must be greater than 0")
    return amount


def transaction_payload(item: Transaction) -> dict[str, object]:
    """Return the public API representation for a transaction."""
    return {
        "id": item.id,
        "transaction_type": item.transaction_type,
        "category": item.category,
        "date": item.date,
        "title": item.title,
        "total": float(item.total),
        "owner_id": item.owner_id,
        "account_id": str(item.account_fk_id) if item.account_fk_id else item.account_id,
        "from_account_id": str(item.from_account_fk_id) if item.from_account_fk_id else item.from_account_id,
        "to_account_id": str(item.to_account_fk_id) if item.to_account_fk_id else item.to_account_id,
    }


def _account_id(value: object, field_name: str) -> int:
    """Normalize and validate an account identifier."""
    if value in (None, ""):
        raise ValidationError(f"{field_name} is required")
    try:
        account_id = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"Invalid {field_name}") from exc
    if account_id <= 0:
        raise ValidationError(f"Invalid {field_name}")
    return account_id


def _account_values_from_data(
    data: dict[str, object],
    existing: Transaction | None = None,
) -> dict[str, object]:
    """Return the account identifiers required by the resulting transaction type."""
    transaction_type = data.get(
        "transaction_type",
        existing.transaction_type if existing else None,
    )
    if transaction_type == "Transfer":
        return {
            "from_account_id": data.get(
                "from_account_id",
                existing.from_account_fk_id if existing and existing.from_account_fk_id else existing.from_account_id if existing else None,
            ),
            "to_account_id": data.get(
                "to_account_id",
                existing.to_account_fk_id if existing and existing.to_account_fk_id else existing.to_account_id if existing else None,
            ),
        }
    return {
        "account_id": data.get(
            "account_id",
            existing.account_fk_id if existing and existing.account_fk_id else existing.account_id if existing else None,
        )
    }


def _lock_owned_accounts(
    user: User,
    account_values: list[object],
) -> dict[int, Account]:
    """Lock all owned accounts in ascending primary-key order."""
    account_ids = sorted({_account_id(value, "account_id") for value in account_values})
    return {
        account.id: account
        for account in Account.objects.select_for_update()
        .filter(owner_user=user, id__in=account_ids)
        .order_by("id")
    }


def _set_account_attrs(
    attrs: dict[str, object],
    transaction_type: str,
    account_ids: dict[str, int],
    accounts: dict[int, Account],
) -> None:
    """Attach locked accounts to transaction attributes."""
    if transaction_type == "Transfer":
        from_account_id = account_ids["from_account_id"]
        to_account_id = account_ids["to_account_id"]
        if from_account_id == to_account_id:
            raise ValidationError("Transfers require two different accounts")
        attrs["from_account_fk"] = accounts[from_account_id]
        attrs["to_account_fk"] = accounts[to_account_id]
    else:
        account_id = account_ids["account_id"]
        attrs["account_fk"] = accounts[account_id]


def _lock_existing_accounts(
    item: Transaction,
    accounts: dict[int, Account],
) -> None:
    """Attach already locked accounts to an existing transaction."""
    account_values = _account_values_from_data({}, item)
    account_ids = {
        field_name: _account_id(value, field_name)
        for field_name, value in account_values.items()
    }
    for field_name, account_id in account_ids.items():
        if account_id not in accounts:
            raise ValidationError(f"Invalid {field_name}")
    if item.transaction_type in {"Income", "Expense"}:
        item.account_fk = accounts[item.account_fk_id]
    elif item.transaction_type == "Transfer":
        item.from_account_fk = accounts[item.from_account_fk_id]
        item.to_account_fk = accounts[item.to_account_fk_id]


def _attrs_from_data(
    data: dict[str, object],
    user: User,
    existing: Transaction | None = None,
    accounts: dict[int, Account] | None = None,
) -> dict[str, object]:
    """Validate transaction request data and build model attributes."""
    transaction_type = data.get(
        "transaction_type",
        existing.transaction_type if existing else None,
    )
    if transaction_type not in VALID_TRANSACTION_TYPES:
        raise ValidationError("transaction_type must be Income, Expense, or Transfer")

    total = decimal_value(data.get("total", existing.total if existing else None))
    attrs = {
        "transaction_type": transaction_type,
        "category": data.get("category", existing.category if existing else None),
        "date": data.get("date", existing.date if existing else None),
        "title": data.get("title", existing.title if existing else None),
        "total": total,
        "owner_user": user,
        "account_fk": None,
        "from_account_fk": None,
        "to_account_fk": None,
    }
    missing = [key for key in ("category", "date", "title") if not attrs[key]]
    if missing:
        raise ValidationError(f"Missing required field(s): {', '.join(missing)}")

    account_values = _account_values_from_data(data, existing)
    account_ids = {
        field_name: _account_id(value, field_name)
        for field_name, value in account_values.items()
    }
    if accounts is None:
        accounts = _lock_owned_accounts(user, list(account_ids.values()))
    for field_name, account_id in account_ids.items():
        if account_id not in accounts:
            raise ValidationError(f"Invalid {field_name}")
    _set_account_attrs(attrs, transaction_type, account_ids, accounts)

    return attrs


def _apply_delta(account: Account, delta: Decimal) -> None:
    """Apply and persist a balance delta in one database expression."""
    Account.objects.filter(pk=account.pk).update(total=F("total") + delta)
    account.total = Decimal(account.total) + delta


def _apply_effect(item: Transaction, reverse: bool = False) -> None:
    """Apply or reverse the balance effect of a transaction."""
    multiplier = Decimal("-1") if reverse else Decimal("1")
    amount = item.total * multiplier

    if item.transaction_type == "Income":
        _apply_delta(item.account_fk, amount)
    elif item.transaction_type == "Expense":
        _apply_delta(item.account_fk, -amount)
    elif item.transaction_type == "Transfer":
        _apply_delta(item.from_account_fk, -amount)
        _apply_delta(item.to_account_fk, amount)


@db_transaction.atomic
def create_transaction(user: User, data: dict[str, object]) -> Transaction:
    """Create a transaction and apply its account balance effect."""
    attrs = _attrs_from_data(data, user)
    item = Transaction.objects.create(**attrs)
    _apply_effect(item)
    return item


@db_transaction.atomic
def update_transaction(user: User, transaction_id: str, data: dict[str, object]) -> Transaction:
    """Update a transaction and rebalance all affected accounts."""
    try:
        item = (
            Transaction.objects.select_for_update()
            .get(id=transaction_id, owner_user=user)
        )
    except Transaction.DoesNotExist as exc:
        raise Transaction.DoesNotExist("Transaction not found") from exc

    old_account_values = _account_values_from_data({}, item)
    new_account_values = _account_values_from_data(data, item)
    for field_name, value in new_account_values.items():
        _account_id(value, field_name)
    accounts = _lock_owned_accounts(
        user,
        [*old_account_values.values(), *new_account_values.values()],
    )
    _lock_existing_accounts(item, accounts)
    _apply_effect(item, reverse=True)
    attrs = _attrs_from_data(data, user, existing=item, accounts=accounts)
    for key, value in attrs.items():
        setattr(item, key, value)
    item.save()
    _apply_effect(item)
    return item


@db_transaction.atomic
def delete_transaction(user: User, transaction_id: str) -> dict[str, object]:
    """Delete a transaction and reverse its account balance effect."""
    try:
        item = (
            Transaction.objects.select_for_update()
            .get(id=transaction_id, owner_user=user)
        )
    except Transaction.DoesNotExist as exc:
        raise Transaction.DoesNotExist("Transaction not found") from exc

    account_values = _account_values_from_data({}, item)
    accounts = _lock_owned_accounts(user, list(account_values.values()))
    _lock_existing_accounts(item, accounts)
    payload = transaction_payload(item)
    _apply_effect(item, reverse=True)
    item.delete()
    return payload

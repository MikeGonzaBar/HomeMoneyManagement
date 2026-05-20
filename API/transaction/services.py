from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction

from account.models import Account
from .models import Transaction


VALID_TRANSACTION_TYPES = {"Income", "Expense", "Transfer"}


def decimal_value(value, field_name="total"):
    if value in (None, ""):
        raise ValidationError(f"{field_name} is required")
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a valid decimal number") from exc
    if amount <= 0:
        raise ValidationError(f"{field_name} must be greater than 0")
    return amount


def transaction_payload(item):
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


def _owned_account(user, account_id, field_name):
    if not account_id:
        raise ValidationError(f"{field_name} is required")
    try:
        return Account.objects.select_for_update().get(owner_user=user, id=account_id)
    except Account.DoesNotExist as exc:
        raise ValidationError(f"Invalid {field_name}") from exc


def _lock_existing_accounts(item):
    if item.transaction_type in {"Income", "Expense"}:
        if not item.account_fk_id:
            raise ValidationError("Transaction is missing account_id")
        item.account_fk = _owned_account(item.owner_user, item.account_fk_id, "account_id")
    elif item.transaction_type == "Transfer":
        if not item.from_account_fk_id or not item.to_account_fk_id:
            raise ValidationError("Transaction is missing transfer account details")
        item.from_account_fk = _owned_account(item.owner_user, item.from_account_fk_id, "from_account_id")
        item.to_account_fk = _owned_account(item.owner_user, item.to_account_fk_id, "to_account_id")


def _attrs_from_data(data, user, existing=None):
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

    if transaction_type == "Transfer":
        from_account_id = data.get(
            "from_account_id",
            existing.from_account_fk_id if existing and existing.from_account_fk_id else existing.from_account_id if existing else None,
        )
        to_account_id = data.get(
            "to_account_id",
            existing.to_account_fk_id if existing and existing.to_account_fk_id else existing.to_account_id if existing else None,
        )
        from_account = _owned_account(user, from_account_id, "from_account_id")
        to_account = _owned_account(user, to_account_id, "to_account_id")
        if from_account.id == to_account.id:
            raise ValidationError("Transfers require two different accounts")
        attrs["from_account_fk"] = from_account
        attrs["to_account_fk"] = to_account
    else:
        account_id = data.get(
            "account_id",
            existing.account_fk_id if existing and existing.account_fk_id else existing.account_id if existing else None,
        )
        attrs["account_fk"] = _owned_account(user, account_id, "account_id")

    return attrs


def _apply_delta(account, delta):
    account.total = account.total + delta
    account.save(update_fields=["total"])


def _apply_effect(item, reverse=False):
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
def create_transaction(user, data):
    attrs = _attrs_from_data(data, user)
    item = Transaction.objects.create(**attrs)
    _apply_effect(item)
    return item


@db_transaction.atomic
def update_transaction(user, transaction_id, data):
    try:
        item = (
            Transaction.objects.select_for_update()
            .get(id=transaction_id, owner_user=user)
        )
    except Transaction.DoesNotExist as exc:
        raise Transaction.DoesNotExist("Transaction not found") from exc

    _lock_existing_accounts(item)
    _apply_effect(item, reverse=True)
    attrs = _attrs_from_data(data, user, existing=item)
    for key, value in attrs.items():
        setattr(item, key, value)
    item.save()
    _apply_effect(item)
    return item


@db_transaction.atomic
def delete_transaction(user, transaction_id):
    try:
        item = (
            Transaction.objects.select_for_update()
            .get(id=transaction_id, owner_user=user)
        )
    except Transaction.DoesNotExist as exc:
        raise Transaction.DoesNotExist("Transaction not found") from exc

    _lock_existing_accounts(item)
    payload = transaction_payload(item)
    _apply_effect(item, reverse=True)
    item.delete()
    return payload

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction

from account.models import Account
from transaction.services import create_transaction, transaction_payload

from .models import RecurringOccurrence, RecurringTransaction


VALID_TYPES = {"Income", "Expense", "Transfer"}
VALID_FREQUENCIES = {"daily", "weekly", "monthly", "yearly"}


def parse_date(value, field_name):
    if isinstance(value, date):
        return value
    if not value:
        raise ValidationError(f"{field_name} is required")
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValidationError(f"{field_name} must use YYYY-MM-DD format") from exc


def parse_optional_date(value, field_name):
    if value in (None, ""):
        return None
    return parse_date(value, field_name)


def parse_money(value, field_name="total"):
    if value in (None, ""):
        raise ValidationError(f"{field_name} is required")
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a valid decimal number") from exc
    if amount <= 0:
        raise ValidationError(f"{field_name} must be greater than 0")
    return amount


def owned_account(user, value, field_name):
    if not value:
        raise ValidationError(f"{field_name} is required")
    try:
        return Account.objects.get(owner_user=user, id=value)
    except Account.DoesNotExist as exc:
        raise ValidationError(f"Invalid {field_name}") from exc


def add_months(value, months):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def advance_date(value, frequency, interval):
    if frequency == "daily":
        return value + timedelta(days=interval)
    if frequency == "weekly":
        return value + timedelta(weeks=interval)
    if frequency == "monthly":
        return add_months(value, interval)
    if frequency == "yearly":
        return add_months(value, interval * 12)
    raise ValidationError("frequency must be daily, weekly, monthly, or yearly")


def attrs_from_data(user, data, existing=None):
    transaction_type = data.get("transaction_type", existing.transaction_type if existing else None)
    if transaction_type not in VALID_TYPES:
        raise ValidationError("transaction_type must be Income, Expense, or Transfer")
    frequency = data.get("frequency", existing.frequency if existing else None)
    if frequency not in VALID_FREQUENCIES:
        raise ValidationError("frequency must be daily, weekly, monthly, or yearly")
    interval = int(data.get("interval", existing.interval if existing else 1) or 1)
    if interval <= 0:
        raise ValidationError("interval must be greater than 0")
    start_date = parse_date(data.get("start_date", existing.start_date if existing else None), "start_date")
    next_due = parse_optional_date(data.get("next_due_date", existing.next_due_date if existing else None), "next_due_date") or start_date
    end_date = parse_optional_date(data.get("end_date", existing.end_date if existing else None), "end_date")
    if end_date and end_date < start_date:
        raise ValidationError("end_date cannot be before start_date")
    attrs = {
        "title": data.get("title", existing.title if existing else None),
        "transaction_type": transaction_type,
        "category": data.get("category", existing.category if existing else None),
        "total": parse_money(data.get("total", existing.total if existing else None)),
        "frequency": frequency,
        "interval": interval,
        "start_date": start_date,
        "next_due_date": next_due,
        "end_date": end_date,
        "active": data.get("active", existing.active if existing else True),
        "account_fk": None,
        "from_account_fk": None,
        "to_account_fk": None,
    }
    if not attrs["title"] or not attrs["category"]:
        raise ValidationError("title and category are required")
    if transaction_type == "Transfer":
        from_account = owned_account(
            user,
            data.get("from_account_id", existing.from_account_fk_id if existing else None),
            "from_account_id",
        )
        to_account = owned_account(
            user,
            data.get("to_account_id", existing.to_account_fk_id if existing else None),
            "to_account_id",
        )
        if from_account.id == to_account.id:
            raise ValidationError("Transfers require two different accounts")
        attrs["from_account_fk"] = from_account
        attrs["to_account_fk"] = to_account
    else:
        attrs["account_fk"] = owned_account(
            user,
            data.get("account_id", existing.account_fk_id if existing else None),
            "account_id",
        )
    return attrs


def recurring_payload(item):
    return {
        "id": item.id,
        "title": item.title,
        "transaction_type": item.transaction_type,
        "category": item.category,
        "total": float(item.total),
        "account_id": str(item.account_fk_id) if item.account_fk_id else None,
        "from_account_id": str(item.from_account_fk_id) if item.from_account_fk_id else None,
        "to_account_id": str(item.to_account_fk_id) if item.to_account_fk_id else None,
        "frequency": item.frequency,
        "interval": item.interval,
        "start_date": item.start_date.isoformat(),
        "next_due_date": item.next_due_date.isoformat(),
        "end_date": item.end_date.isoformat() if item.end_date else None,
        "active": item.active,
    }


def occurrence_payload(item):
    rule = item.recurring_transaction
    payload = recurring_payload(rule)
    payload.update(
        {
            "occurrence_id": item.id,
            "due_date": item.due_date.isoformat(),
            "status": item.status,
            "posted_transaction": transaction_payload(item.posted_transaction) if item.posted_transaction else None,
        }
    )
    return payload


@db_transaction.atomic
def generate_due_occurrences(user, through):
    through_date = parse_date(through, "through")
    rules = RecurringTransaction.objects.select_for_update().filter(
        owner_user=user,
        active=True,
        next_due_date__lte=through_date,
    )
    for rule in rules:
        due = rule.next_due_date
        while due <= through_date and (not rule.end_date or due <= rule.end_date):
            RecurringOccurrence.objects.get_or_create(
                recurring_transaction=rule,
                owner_user=user,
                due_date=due,
            )
            due = advance_date(due, rule.frequency, rule.interval)
        rule.next_due_date = due
        if rule.end_date and due > rule.end_date:
            rule.active = False
        rule.save(update_fields=["next_due_date", "active", "updated_at"])
    return RecurringOccurrence.objects.filter(owner_user=user, due_date__lte=through_date).order_by("due_date", "id")


@db_transaction.atomic
def post_occurrence(user, occurrence_id):
    try:
        occurrence = RecurringOccurrence.objects.select_for_update().select_related("recurring_transaction").get(
            owner_user=user,
            id=occurrence_id,
        )
    except RecurringOccurrence.DoesNotExist as exc:
        raise RecurringOccurrence.DoesNotExist("Recurring occurrence not found") from exc
    if occurrence.status == RecurringOccurrence.STATUS_POSTED:
        return occurrence
    if occurrence.status == RecurringOccurrence.STATUS_SKIPPED:
        raise ValidationError("Skipped occurrences cannot be posted")
    rule = occurrence.recurring_transaction
    data = {
        "title": rule.title,
        "transaction_type": rule.transaction_type,
        "category": rule.category,
        "date": occurrence.due_date.isoformat(),
        "total": str(rule.total),
    }
    if rule.transaction_type == "Transfer":
        data["from_account_id"] = str(rule.from_account_fk_id)
        data["to_account_id"] = str(rule.to_account_fk_id)
    else:
        data["account_id"] = str(rule.account_fk_id)
    transaction = create_transaction(user, data)
    occurrence.posted_transaction = transaction
    occurrence.status = RecurringOccurrence.STATUS_POSTED
    occurrence.save(update_fields=["posted_transaction", "status", "updated_at"])
    return occurrence


@db_transaction.atomic
def skip_occurrence(user, occurrence_id):
    try:
        occurrence = RecurringOccurrence.objects.select_for_update().get(owner_user=user, id=occurrence_id)
    except RecurringOccurrence.DoesNotExist as exc:
        raise RecurringOccurrence.DoesNotExist("Recurring occurrence not found") from exc
    if occurrence.status == RecurringOccurrence.STATUS_POSTED:
        raise ValidationError("Posted occurrences cannot be skipped")
    occurrence.status = RecurringOccurrence.STATUS_SKIPPED
    occurrence.save(update_fields=["status", "updated_at"])
    return occurrence

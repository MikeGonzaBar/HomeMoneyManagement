from datetime import date, timedelta

from bankstatements.models import BankStatementTransactionCandidate
from budgets.models import Budget
from budgets.views import budget_payload, parse_month, spending_totals_by_month
from recurring.models import RecurringOccurrence
from recurring.services import generate_due_occurrences
from reports.views import build_forecast
from users.models import User

from .models import Alert


def upsert_alert(
    user: User,
    object_key: str,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
) -> Alert:
    """Create or update one active alert for a stable object key."""
    alert, _ = Alert.objects.update_or_create(
        owner_user=user,
        object_key=object_key,
        defaults={
            "alert_type": alert_type,
            "severity": severity,
            "title": title,
            "message": message,
            "dismissed_at": None,
        },
    )
    return alert


def alert_payload(alert: Alert) -> dict[str, object]:
    """Return the API representation for an alert."""
    return {
        "id": alert.id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "title": alert.title,
        "message": alert.message,
        "object_key": alert.object_key,
        "read": alert.read_at is not None,
        "dismissed": alert.dismissed_at is not None,
        "created_at": alert.created_at.isoformat(),
    }


def refresh_alerts_for_user(user: User) -> list[Alert]:
    """Regenerate budget, recurring, forecast, and import-review alerts."""
    generated = []
    current_month = parse_month(date.today().strftime("%Y-%m"))
    budgets = list(Budget.objects.filter(owner_user=user, month=current_month))
    spending = spending_totals_by_month(user, [current_month])
    for budget in budgets:
        data = budget_payload(user, budget, spending[current_month])
        if data["status"] in {"warning", "exceeded"}:
            label = data["category"] or "Overall budget"
            severity = "critical" if data["status"] == "exceeded" else "warning"
            generated.append(
                upsert_alert(
                    user,
                    f"budget:{budget.id}:{data['status']}",
                    "budget",
                    severity,
                    f"{label} budget {data['status'].replace('_', ' ')}",
                    f"{label} is {data['percent_used']}% used for {data['month']}.",
                )
            )

    through = date.today() + timedelta(days=3)
    for occurrence in generate_due_occurrences(user, through.isoformat()).filter(status=RecurringOccurrence.STATUS_DUE):
        overdue = occurrence.due_date < date.today()
        generated.append(
            upsert_alert(
                user,
                f"recurring:{occurrence.id}",
                "recurring_due",
                "critical" if overdue else "warning",
                "Recurring transaction overdue" if overdue else "Recurring transaction due soon",
                f"{occurrence.recurring_transaction.title} is due on {occurrence.due_date.isoformat()}.",
            )
        )

    forecast = build_forecast(user, 1)
    for month in forecast["forecast"]:
        for account in month["account_balances"]:
            if account["balance"] < 0:
                generated.append(
                    upsert_alert(
                        user,
                        f"forecast-negative:{account['account_id']}:{month['month']}",
                        "forecast_negative_balance",
                        "critical",
                        "Forecasted negative balance",
                        f"{account['account_name']} is forecasted to reach ${account['balance']:.2f} in {month['month']}.",
                    )
                )

    duplicate_count = BankStatementTransactionCandidate.objects.filter(
        owner_user=user,
        status=BankStatementTransactionCandidate.STATUS_PENDING,
    ).exclude(possible_matches=[]).count()
    if duplicate_count:
        generated.append(
            upsert_alert(
                user,
                "import-duplicates:pending",
                "import_duplicates",
                "warning",
                "Import candidates need review",
                f"{duplicate_count} imported transaction candidate(s) have possible duplicate matches.",
            )
        )
    return generated

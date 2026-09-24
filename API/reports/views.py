"""
Reports API - Financial analytics and smart insights.
"""
from calendar import monthrange
from datetime import date, datetime, timedelta
from collections import defaultdict
from decimal import Decimal

from django.db.models import Case, DecimalField, Sum, Value, When
from django.db.models.functions import Abs, Coalesce, TruncMonth
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from transaction.models import Transaction
from account.models import Account
from reports.services import generate_smart_insights_with_ai
from users.models import User


def _parse_dates(start_str: str, end_str: str) -> tuple[date, date]:
    """Parse start/end date strings. Default to current month."""
    today = datetime.now().date()
    if start_str and end_str:
        try:
            start = datetime.strptime(start_str, "%Y-%m-%d").date()
            end = datetime.strptime(end_str, "%Y-%m-%d").date()
            return start, end
        except ValueError:
            pass
    # Default: first to last day of current month
    start = today.replace(day=1)
    if today.month == 12:
        end = today.replace(day=31)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
        end = next_month - timedelta(days=1)
    return start, end


def _get_prev_period(start: date, end: date) -> tuple[date, date]:
    """Return previous period of same length."""
    delta = end - start
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - delta
    return prev_start, prev_end


MONEY_FIELD = DecimalField(max_digits=14, decimal_places=2)


def _period_summary(
    user: User,
    start: date,
    end: date,
) -> tuple[float, float, dict[str, float]]:
    """Aggregate period income, expense, and expense categories in the database."""
    income = Case(
        When(transaction_type="Income", then="total"),
        default=Value(Decimal("0.00")),
        output_field=MONEY_FIELD,
    )
    expense = Case(
        When(transaction_type="Expense", then=Abs("total")),
        default=Value(Decimal("0.00")),
        output_field=MONEY_FIELD,
    )
    rows = (
        Transaction.objects.filter(owner_user=user, date__gte=start, date__lte=end)
        .exclude(transaction_type="Transfer")
        .values("category")
        .annotate(
            income=Coalesce(Sum(income), Value(Decimal("0.00")), output_field=MONEY_FIELD),
            expense=Coalesce(Sum(expense), Value(Decimal("0.00")), output_field=MONEY_FIELD),
        )
    )
    total_income = sum((row["income"] for row in rows), Decimal("0.00"))
    total_expense = sum((row["expense"] for row in rows), Decimal("0.00"))
    categories = {
        row["category"]: float(row["expense"])
        for row in rows
        if row["expense"]
    }
    return float(total_income), float(total_expense), categories


def _monthly_summary(user: User, start: date, end: date) -> dict[str, dict[str, float]]:
    """Aggregate income and expense by calendar month."""
    income = Case(
        When(transaction_type="Income", then="total"),
        default=Value(Decimal("0.00")),
        output_field=MONEY_FIELD,
    )
    expense = Case(
        When(transaction_type="Expense", then=Abs("total")),
        default=Value(Decimal("0.00")),
        output_field=MONEY_FIELD,
    )
    rows = (
        Transaction.objects.filter(owner_user=user, date__gte=start, date__lte=end)
        .exclude(transaction_type="Transfer")
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(
            income=Coalesce(Sum(income), Value(Decimal("0.00")), output_field=MONEY_FIELD),
            expense=Coalesce(Sum(expense), Value(Decimal("0.00")), output_field=MONEY_FIELD),
        )
        .order_by("month")
    )
    return {
        row["month"].strftime("%Y-%m"): {
            "income": float(row["income"]),
            "expense": float(row["expense"]),
        }
        for row in rows
    }


def _monthly_category_summary(
    user: User,
    start: date,
    end: date,
) -> dict[str, dict[str, float]]:
    """Aggregate expense totals by calendar month and category."""
    rows = (
        Transaction.objects.filter(
            owner_user=user,
            transaction_type="Expense",
            date__gte=start,
            date__lte=end,
        )
        .annotate(month=TruncMonth("date"))
        .values("month", "category")
        .annotate(expense=Sum(Abs("total")))
        .order_by("month", "category")
    )
    summary: dict[str, dict[str, float]] = defaultdict(dict)
    for row in rows:
        summary[row["month"].strftime("%Y-%m")][row["category"]] = float(row["expense"])
    return dict(summary)



def _savings_rate(income: float, expense: float) -> float:
    """Return savings rate as a percentage for income and expense totals."""
    if income <= 0:
        return 0.0
    net = income - expense
    return round((net / income) * 100, 1)


def _pct_change(old_val: float, new_val: float) -> float:
    """Return percentage change. Returns 0 if old_val is 0."""
    if old_val == 0:
        return 0.0 if new_val == 0 else 100.0
    return round(((new_val - old_val) / old_val) * 100, 1)


def _forbid_other_user(request: Request, username: str) -> Response | None:
    """Reject report routes whose legacy username does not match the token."""
    if username != request.user.username:
        return Response({"error": "Cannot access another user's reports"}, status=status.HTTP_403_FORBIDDEN)
    return None


class ReportsAnalytics(APIView):
    """GET /reports/analytics/<username>/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD"""

    @extend_schema(
        tags=["Reports"],
        parameters=[
            OpenApiParameter("start_date", str, OpenApiParameter.QUERY),
            OpenApiParameter("end_date", str, OpenApiParameter.QUERY),
        ],
        responses={200: OpenApiResponse(description="Analytics report")},
    )
    def get(self, request: Request, username: str) -> Response:
        """Return analytics, charts, KPIs, and smart insights."""
        mismatch = _forbid_other_user(request, username)
        if mismatch:
            return mismatch

        start_str = request.GET.get("start_date", "")
        end_str = request.GET.get("end_date", "")
        start, end = _parse_dates(start_str, end_str)
        prev_start, prev_end = _get_prev_period(start, end)

        # Current and previous period totals/categories are aggregated by PostgreSQL.
        curr_income, curr_expense, cat_totals = _period_summary(request.user, start, end)
        curr_net = curr_income - curr_expense
        curr_savings_rate = _savings_rate(curr_income, curr_expense)

        prev_income, prev_expense, prev_cat = _period_summary(
            request.user,
            prev_start,
            prev_end,
        )
        prev_net = prev_income - prev_expense
        prev_savings_rate = _savings_rate(prev_income, prev_expense)

        # % changes
        income_pct = _pct_change(prev_income, curr_income)
        expense_pct = _pct_change(prev_expense, curr_expense)
        net_pct = _pct_change(prev_net, curr_net) if prev_net != 0 else 0
        savings_rate_pct = curr_savings_rate - prev_savings_rate  # diff in pp

        # Monthly income/expenses for last 6 months (bar chart)
        six_months_ago = end - timedelta(days=180)
        monthly = _monthly_summary(request.user, six_months_ago, end)

        months_sorted = sorted(monthly.keys())[-6:]
        monthly_chart = [
            {
                "month": m,
                "label": datetime.strptime(m + "-01", "%Y-%m-%d").strftime("%b"),
                "income": round(monthly[m]["income"], 2),
                "expense": round(monthly[m]["expense"], 2),
            }
            for m in months_sorted
        ]

        # Net worth (sum of account totals for assets; credit cards use available credit)
        accounts = Account.objects.filter(owner_user=request.user)
        net_worth = sum(getattr(a, "net_worth_value", a.total) for a in accounts)

        # Net worth this month vs last month (simplified: use account totals now; in reality we'd need historical)
        net_worth_change = curr_net  # Approximate: net savings this month adds to net worth

        # Spending by category over time (last 3 months, by month)
        cat_monthly = _monthly_category_summary(request.user, six_months_ago, end)

        spending_by_category = []
        for m in months_sorted:
            entry = {"month": m, "label": datetime.strptime(m + "-01", "%Y-%m-%d").strftime("%b"), "categories": {}}
            for cat, amt in cat_monthly.get(m, {}).items():
                entry["categories"][cat] = round(amt, 2)
            spending_by_category.append(entry)

        # Top categories (current period)
        top_categories = [
            {"category": cat, "amount": round(amt, 2)}
            for cat, amt in sorted(cat_totals.items(), key=lambda x: -x[1])
        ][:10]

        insights = generate_smart_insights_with_ai(
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            prev_start_date=prev_start.isoformat(),
            prev_end_date=prev_end.isoformat(),
            current_period={
                "total_income": curr_income,
                "total_expenses": curr_expense,
                "net_savings": curr_net,
                "savings_rate": curr_savings_rate,
            },
            previous_period={
                "total_income": prev_income,
                "total_expenses": prev_expense,
                "net_savings": prev_net,
                "savings_rate": prev_savings_rate,
            },
            top_categories=top_categories,
            net_worth=net_worth,
            net_worth_change=net_worth_change,
        )

        if insights is None:
            insights = _generate_smart_insights(
                curr_income, curr_expense, curr_net, curr_savings_rate,
                prev_income, prev_expense, prev_net, prev_savings_rate,
                dict(cat_totals), dict(prev_cat),
            )

        response = {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "kpis": {
                "total_income": round(curr_income, 2),
                "total_income_pct_change": income_pct,
                "total_expenses": round(curr_expense, 2),
                "total_expenses_pct_change": expense_pct,
                "net_savings": round(curr_net, 2),
                "net_savings_pct_change": net_pct,
                "savings_rate": curr_savings_rate,
                "savings_rate_pct_change": savings_rate_pct,
            },
            "monthly_income_expenses": monthly_chart,
            "net_worth": round(net_worth, 2),
            "net_worth_change": round(net_worth_change, 2),
            "spending_by_category": spending_by_category,
            "top_categories": top_categories,
            "smart_insights": insights,
        }
        return Response(response, status=status.HTTP_200_OK)


def _generate_smart_insights(
    curr_income: float,
    curr_expense: float,
    curr_net: float,
    curr_savings_rate: float,
    prev_income: float,
    prev_expense: float,
    prev_net: float,
    prev_savings_rate: float,
    curr_cat_totals: dict[str, float],
    prev_cat_totals: dict[str, float],
) -> dict[str, object]:
    """Generate smart insights comparing current vs previous period."""
    parts = []
    tags = []

    # Savings rate change
    sr_diff = curr_savings_rate - prev_savings_rate
    if sr_diff > 0:
        parts.append(f"Your savings rate increased by {abs(sr_diff):.1f}% compared to last period.")
        tags.append("#SavingMaster")
    elif sr_diff < 0:
        parts.append(f"Your savings rate decreased by {abs(sr_diff):.1f}% compared to last period.")

    # Category spending comparison - find biggest improvement
    best_cat = None
    best_pct = 0
    for cat, curr_amt in curr_cat_totals.items():
        prev_amt = prev_cat_totals.get(cat, 0)
        if prev_amt > 0 and curr_amt < prev_amt:
            pct = ((prev_amt - curr_amt) / prev_amt) * 100
            if pct > best_pct:
                best_pct = pct
                best_cat = cat

    if best_cat and best_pct > 5:
        parts.append(f"You've spent {best_pct:.0f}% less on \"{best_cat}\" than your previous average.")
        tags.append("#BelowBudget")

    if not parts:
        if curr_net > 0:
            parts.append(f"You saved ${curr_net:,.2f} this period. Keep it up!")
            tags.append("#OnTrack")
        else:
            parts.append("Review your spending to improve your savings next period.")

    return {
        "message": " ".join(parts),
        "tags": tags[:3],
    }


class ReportsInsights(APIView):
    """GET /reports/insights/<username>/?start_date=&end_date= - Smart Insights only."""

    @extend_schema(
        tags=["Reports"],
        parameters=[
            OpenApiParameter("start_date", str, OpenApiParameter.QUERY),
            OpenApiParameter("end_date", str, OpenApiParameter.QUERY),
        ],
        responses={200: OpenApiResponse(description="Smart insights")},
    )
    def get(self, request: Request, username: str) -> Response:
        """Return only smart insights for the requested period."""
        mismatch = _forbid_other_user(request, username)
        if mismatch:
            return mismatch

        start_str = request.GET.get("start_date", "")
        end_str = request.GET.get("end_date", "")
        start, end = _parse_dates(start_str, end_str)
        prev_start, prev_end = _get_prev_period(start, end)

        curr_income, curr_expense, curr_cat = _period_summary(request.user, start, end)
        curr_net = curr_income - curr_expense
        curr_savings_rate = _savings_rate(curr_income, curr_expense)

        prev_income, prev_expense, prev_cat = _period_summary(
            request.user,
            prev_start,
            prev_end,
        )
        prev_net = prev_income - prev_expense
        prev_savings_rate = _savings_rate(prev_income, prev_expense)

        top_categories = [
            {"category": c, "amount": round(a, 2)}
            for c, a in sorted(curr_cat.items(), key=lambda x: -x[1])[:10]
        ]
        net_worth = sum(getattr(a, "net_worth_value", a.total) for a in Account.objects.filter(owner_user=request.user))
        net_worth_change = curr_net

        insights = generate_smart_insights_with_ai(
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            prev_start_date=prev_start.isoformat(),
            prev_end_date=prev_end.isoformat(),
            current_period={
                "total_income": curr_income,
                "total_expenses": curr_expense,
                "net_savings": curr_net,
                "savings_rate": curr_savings_rate,
            },
            previous_period={
                "total_income": prev_income,
                "total_expenses": prev_expense,
                "net_savings": prev_net,
                "savings_rate": prev_savings_rate,
            },
            top_categories=top_categories,
            net_worth=net_worth,
            net_worth_change=net_worth_change,
        )

        if insights is None:
            insights = _generate_smart_insights(
                curr_income, curr_expense, curr_net, curr_savings_rate,
                prev_income, prev_expense, prev_net, prev_savings_rate,
                dict(curr_cat), dict(prev_cat),
            )
        return Response(insights, status=status.HTTP_200_OK)


def _add_months(value: date, months: int) -> date:
    """Add calendar months while clamping to valid target days."""
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def _month_start(value: date) -> date:
    """Return the first day of a date's month."""
    return value.replace(day=1)


def build_forecast(user: User, months: int = 6) -> dict[str, object]:
    """Build a month-by-month balance forecast for the authenticated user."""
    from budgets.models import Budget
    from recurring.models import RecurringTransaction
    from recurring.services import advance_date

    months = max(1, min(int(months or 6), 12))
    today = date.today()
    start_month = _month_start(today)
    accounts = list(Account.objects.filter(owner_user=user).order_by("id"))
    balances = {account.id: float(account.total) for account in accounts}
    results = []

    trailing_start = today - timedelta(days=90)
    trailing_income, trailing_expense, _ = _period_summary(user, trailing_start, today - timedelta(days=1))
    avg_income = trailing_income / 3 if trailing_income else 0.0
    avg_expense = trailing_expense / 3 if trailing_expense else 0.0

    recurring_rules = list(RecurringTransaction.objects.filter(owner_user=user, active=True))

    for offset in range(months):
        month = _add_months(start_month, offset)
        month_end = date(month.year, month.month, monthrange(month.year, month.month)[1])
        recurring_income = 0.0
        recurring_expense = 0.0

        for rule in recurring_rules:
            due = rule.next_due_date
            if due < month:
                while due < month:
                    due = advance_date(due, rule.frequency, rule.interval)
            while due <= month_end and (not rule.end_date or due <= rule.end_date):
                amount = float(rule.total)
                if rule.transaction_type == "Income":
                    recurring_income += amount
                    if rule.account_fk_id in balances:
                        balances[rule.account_fk_id] += amount
                elif rule.transaction_type == "Expense":
                    recurring_expense += amount
                    if rule.account_fk_id in balances:
                        balances[rule.account_fk_id] -= amount
                elif rule.transaction_type == "Transfer":
                    if rule.from_account_fk_id in balances:
                        balances[rule.from_account_fk_id] -= amount
                    if rule.to_account_fk_id in balances:
                        balances[rule.to_account_fk_id] += amount
                due = advance_date(due, rule.frequency, rule.interval)

        budgets = Budget.objects.filter(owner_user=user, month=month)
        budgeted_expense = sum(float(item.limit_amount) for item in budgets if item.scope == Budget.SCOPE_CATEGORY)
        overall = next((item for item in budgets if item.scope == Budget.SCOPE_OVERALL), None)
        if budgeted_expense == 0 and overall:
            budgeted_expense = float(overall.limit_amount)

        expected_income = recurring_income if recurring_income > 0 else avg_income
        expected_expense = max(recurring_expense, budgeted_expense, avg_expense)
        results.append(
            {
                "month": month.strftime("%Y-%m"),
                "expected_income": round(expected_income, 2),
                "expected_expenses": round(expected_expense, 2),
                "expected_net": round(expected_income - expected_expense, 2),
                "recurring_income": round(recurring_income, 2),
                "recurring_expenses": round(recurring_expense, 2),
                "budgeted_expenses": round(budgeted_expense, 2),
                "historical_income_fallback": round(avg_income, 2),
                "historical_expense_fallback": round(avg_expense, 2),
                "account_balances": [
                    {
                        "account_id": account.id,
                        "account_name": account.account_name,
                        "balance": round(balances.get(account.id, 0.0), 2),
                    }
                    for account in accounts
                ],
            }
        )
    return {
        "start_month": start_month.strftime("%Y-%m"),
        "months": months,
        "forecast": results,
    }


class ReportsForecast(APIView):
    """GET /reports/forecast/<username>/?months=6"""

    @extend_schema(
        tags=["Reports"],
        parameters=[OpenApiParameter("months", int, OpenApiParameter.QUERY)],
        responses={200: OpenApiResponse(description="Balance forecast")},
    )
    def get(self, request: Request, username: str) -> Response:
        """Return a balance forecast for the authenticated user."""
        mismatch = _forbid_other_user(request, username)
        if mismatch:
            return mismatch
        try:
            months = int(request.GET.get("months", 6))
        except ValueError:
            return Response({"error": "months must be a number"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(build_forecast(request.user, months), status=status.HTTP_200_OK)

"""
Reports API - Financial analytics and smart insights.
"""
from datetime import datetime, timedelta
from collections import defaultdict
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from transaction.models import Transaction
from account.models import Account
from reports.services import generate_smart_insights_with_ai


def _parse_dates(start_str, end_str):
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


def _get_prev_period(start, end):
    """Return previous period of same length."""
    delta = end - start
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - delta
    return prev_start, prev_end


def _aggregate_income_expense(transactions):
    """Return (income, expense) totals. Excludes Transfer."""
    income = 0.0
    expense = 0.0
    for t in transactions:
        if t.transaction_type == "Income":
            income += float(t.total)
        elif t.transaction_type == "Expense":
            expense += abs(float(t.total))
    return income, expense


def _savings_rate(income, expense):
    if income <= 0:
        return 0.0
    net = income - expense
    return round((net / income) * 100, 1)


def _pct_change(old_val, new_val):
    """Return percentage change. Returns 0 if old_val is 0."""
    if old_val == 0:
        return 0.0 if new_val == 0 else 100.0
    return round(((new_val - old_val) / old_val) * 100, 1)


def _forbid_other_user(request, username):
    if username != request.user.username:
        return Response({"error": "Cannot access another user's reports"}, status=status.HTTP_403_FORBIDDEN)
    return None


class ReportsAnalytics(APIView):
    """GET /reports/analytics/<username>/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD"""

    def get(self, request, username: str):
        mismatch = _forbid_other_user(request, username)
        if mismatch:
            return mismatch

        start_str = request.GET.get("start_date", "")
        end_str = request.GET.get("end_date", "")
        start, end = _parse_dates(start_str, end_str)
        prev_start, prev_end = _get_prev_period(start, end)

        # Current period transactions
        curr_tx = list(
            Transaction.objects.filter(owner_user=request.user).filter(
                date__gte=start, date__lte=end
            ).exclude(transaction_type="Transfer")
        )
        curr_income, curr_expense = _aggregate_income_expense(curr_tx)
        curr_net = curr_income - curr_expense
        curr_savings_rate = _savings_rate(curr_income, curr_expense)

        # Previous period
        prev_tx = list(
            Transaction.objects.filter(owner_user=request.user).filter(
                date__gte=prev_start, date__lte=prev_end
            ).exclude(transaction_type="Transfer")
        )
        prev_income, prev_expense = _aggregate_income_expense(prev_tx)
        prev_net = prev_income - prev_expense
        prev_savings_rate = _savings_rate(prev_income, prev_expense)

        # % changes
        income_pct = _pct_change(prev_income, curr_income)
        expense_pct = _pct_change(prev_expense, curr_expense)
        net_pct = _pct_change(prev_net, curr_net) if prev_net != 0 else 0
        savings_rate_pct = curr_savings_rate - prev_savings_rate  # diff in pp

        # Monthly income/expenses for last 6 months (bar chart)
        six_months_ago = end - timedelta(days=180)
        monthly_tx = Transaction.objects.filter(owner_user=request.user).filter(
            date__gte=six_months_ago, date__lte=end
        ).exclude(transaction_type="Transfer")

        monthly = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
        for t in monthly_tx:
            key = t.date.strftime("%Y-%m")
            if t.transaction_type == "Income":
                monthly[key]["income"] += float(t.total)
            else:
                monthly[key]["expense"] += abs(float(t.total))

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
        cat_monthly = defaultdict(lambda: defaultdict(float))
        for t in Transaction.objects.filter(owner_user=request.user).filter(
            date__gte=six_months_ago, date__lte=end
        ):
            if t.transaction_type != "Expense":
                continue
            key = t.date.strftime("%Y-%m")
            cat_monthly[key][t.category] = cat_monthly[key][t.category] + abs(float(t.total))

        spending_by_category = []
        for m in months_sorted:
            entry = {"month": m, "label": datetime.strptime(m + "-01", "%Y-%m-%d").strftime("%b"), "categories": {}}
            for cat, amt in cat_monthly[m].items():
                entry["categories"][cat] = round(amt, 2)
            spending_by_category.append(entry)

        # Top categories (current period)
        cat_totals = defaultdict(float)
        for t in curr_tx:
            if t.transaction_type == "Expense":
                cat_totals[t.category] += abs(float(t.total))

        top_categories = [
            {"category": cat, "amount": round(amt, 2)}
            for cat, amt in sorted(cat_totals.items(), key=lambda x: -x[1])
        ][:10]

        # Smart Insights: use Gemini (financial advisor style) if available, else fallback to data-driven
        prev_cat = defaultdict(float)
        for t in prev_tx:
            if t.transaction_type == "Expense":
                prev_cat[t.category] += abs(float(t.total))

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
    curr_income,
    curr_expense,
    curr_net,
    curr_savings_rate,
    prev_income,
    prev_expense,
    prev_net,
    prev_savings_rate,
    curr_cat_totals,
    prev_cat_totals,
):
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

    def get(self, request, username: str):
        mismatch = _forbid_other_user(request, username)
        if mismatch:
            return mismatch

        start_str = request.GET.get("start_date", "")
        end_str = request.GET.get("end_date", "")
        start, end = _parse_dates(start_str, end_str)
        prev_start, prev_end = _get_prev_period(start, end)

        curr_tx = list(
            Transaction.objects.filter(owner_user=request.user).filter(
                date__gte=start, date__lte=end
            ).exclude(transaction_type="Transfer")
        )
        prev_tx = list(
            Transaction.objects.filter(owner_user=request.user).filter(
                date__gte=prev_start, date__lte=prev_end
            ).exclude(transaction_type="Transfer")
        )

        curr_income, curr_expense = _aggregate_income_expense(curr_tx)
        curr_net = curr_income - curr_expense
        curr_savings_rate = _savings_rate(curr_income, curr_expense)

        prev_income, prev_expense = _aggregate_income_expense(prev_tx)
        prev_net = prev_income - prev_expense
        prev_savings_rate = _savings_rate(prev_income, prev_expense)

        curr_cat = defaultdict(float)
        for t in curr_tx:
            if t.transaction_type == "Expense":
                curr_cat[t.category] += abs(float(t.total))
        prev_cat = defaultdict(float)
        for t in prev_tx:
            if t.transaction_type == "Expense":
                prev_cat[t.category] += abs(float(t.total))

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

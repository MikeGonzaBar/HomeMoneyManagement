from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from transaction.models import Transaction

from .models import Budget


def parse_month(value):
    if not value:
        today = date.today()
        return today.replace(day=1)
    try:
        year_str, month_str = value.split("-", 1)
        return date(int(year_str), int(month_str), 1)
    except (TypeError, ValueError):
        raise ValueError("month must use YYYY-MM format")


def month_bounds(month):
    last_day = monthrange(month.year, month.month)[1]
    return month, date(month.year, month.month, last_day)


def money(value, field_name):
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid decimal number") from exc
    if amount < 0:
        raise ValueError(f"{field_name} must be greater than or equal to 0")
    return amount


def spending_for_budget(user, budget):
    start, end = month_bounds(budget.month)
    query = Transaction.objects.filter(
        owner_user=user,
        transaction_type="Expense",
        date__gte=start,
        date__lte=end,
    )
    if budget.scope == Budget.SCOPE_CATEGORY:
        query = query.filter(category=budget.category)
    total = Decimal("0.00")
    for item in query:
        total += abs(item.total)
    return total.quantize(Decimal("0.01"))


def budget_payload(user, budget):
    spent = spending_for_budget(user, budget)
    remaining = (budget.limit_amount - spent).quantize(Decimal("0.01"))
    percent = Decimal("0.00")
    if budget.limit_amount > 0:
        percent = ((spent / budget.limit_amount) * Decimal("100")).quantize(Decimal("0.1"))
    status_label = "on_track"
    if percent >= 100:
        status_label = "exceeded"
    elif percent >= 80:
        status_label = "warning"
    return {
        "id": budget.id,
        "month": budget.month.strftime("%Y-%m"),
        "scope": budget.scope,
        "category": budget.category,
        "limit_amount": float(budget.limit_amount),
        "spent_amount": float(spent),
        "remaining_amount": float(remaining),
        "percent_used": float(percent),
        "status": status_label,
    }


def validate_payload(data, existing=None):
    month = parse_month(data.get("month", existing.month.strftime("%Y-%m") if existing else None))
    scope_value = data.get("scope", existing.scope if existing else None)
    if scope_value not in {Budget.SCOPE_OVERALL, Budget.SCOPE_CATEGORY}:
        raise ValueError("scope must be overall or category")
    category = data.get("category", existing.category if existing else None)
    if scope_value == Budget.SCOPE_CATEGORY and not category:
        raise ValueError("category is required for category budgets")
    if scope_value == Budget.SCOPE_OVERALL:
        category = None
    limit = money(data.get("limit_amount", existing.limit_amount if existing else None), "limit_amount")
    return {
        "month": month,
        "scope": scope_value,
        "category": category,
        "limit_amount": limit,
    }


class BudgetListCreate(APIView):
    def get(self, request):
        month_param = request.GET.get("month")
        query = Budget.objects.filter(owner_user=request.user).order_by("-month", "scope", "category")
        if month_param:
            try:
                query = query.filter(month=parse_month(month_param))
            except ValueError as exc:
                return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response([budget_payload(request.user, item) for item in query])

    def post(self, request):
        try:
            attrs = validate_payload(request.data)
            if Budget.objects.filter(
                owner_user=request.user,
                month=attrs["month"],
                scope=attrs["scope"],
                category=attrs["category"],
            ).exists():
                return Response(
                    {"error": "A budget already exists for this month and scope"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            budget = Budget.objects.create(owner_user=request.user, **attrs)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response(
                {"error": "A budget already exists for this month and scope"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(budget_payload(request.user, budget), status=status.HTTP_201_CREATED)


class BudgetDetail(APIView):
    def get_object(self, request, budget_id):
        try:
            return Budget.objects.get(owner_user=request.user, id=budget_id)
        except Budget.DoesNotExist:
            return None

    def get(self, request, budget_id):
        budget = self.get_object(request, budget_id)
        if not budget:
            return Response({"error": "Budget not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(budget_payload(request.user, budget))

    def patch(self, request, budget_id):
        budget = self.get_object(request, budget_id)
        if not budget:
            return Response({"error": "Budget not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            attrs = validate_payload(request.data, existing=budget)
            duplicate = Budget.objects.filter(
                owner_user=request.user,
                month=attrs["month"],
                scope=attrs["scope"],
                category=attrs["category"],
            ).exclude(id=budget.id).exists()
            if duplicate:
                return Response(
                    {"error": "A budget already exists for this month and scope"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            for key, value in attrs.items():
                setattr(budget, key, value)
            budget.save()
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response(
                {"error": "A budget already exists for this month and scope"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(budget_payload(request.user, budget))

    def delete(self, request, budget_id):
        budget = self.get_object(request, budget_id)
        if not budget:
            return Response({"error": "Budget not found"}, status=status.HTTP_404_NOT_FOUND)
        budget.delete()
        return Response({"message": "Budget deleted successfully"})


class BudgetSummary(APIView):
    def get(self, request):
        try:
            month = parse_month(request.GET.get("month"))
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        budgets = Budget.objects.filter(owner_user=request.user, month=month).order_by("scope", "category")
        payloads = [budget_payload(request.user, item) for item in budgets]
        overall = next((item for item in payloads if item["scope"] == Budget.SCOPE_OVERALL), None)
        categories = [item for item in payloads if item["scope"] == Budget.SCOPE_CATEGORY]
        return Response(
            {
                "month": month.strftime("%Y-%m"),
                "overall": overall,
                "categories": categories,
                "over_budget": [item for item in payloads if item["status"] == "exceeded"],
                "warnings": [item for item in payloads if item["status"] == "warning"],
            }
        )

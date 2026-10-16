from collections.abc import Iterable
from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import IntegrityError
from django.db.models import Sum
from django.db.models.functions import Abs, TruncMonth
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import generics, serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from transaction.models import Transaction
from users.models import User

from .models import Budget


class BudgetSchemaSerializer(serializers.Serializer):
    """Named schema placeholder for hand-built budget API responses."""


def parse_month(value: object) -> date:
    """Parse a YYYY-MM month value, defaulting to the current month."""
    if not value:
        today = date.today()
        return today.replace(day=1)
    try:
        year_str, month_str = value.split("-", 1)
        return date(int(year_str), int(month_str), 1)
    except (TypeError, ValueError):
        raise ValueError("month must use YYYY-MM format")


def month_bounds(month: date) -> tuple[date, date]:
    """Return the inclusive first and last dates for a month."""
    last_day = monthrange(month.year, month.month)[1]
    return month, date(month.year, month.month, last_day)


def money(value: object, field_name: str) -> Decimal:
    """Parse a non-negative money value to two decimal places."""
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid decimal number") from exc
    if amount < 0:
        raise ValueError(f"{field_name} must be greater than or equal to 0")
    return amount


def spending_totals_by_month(
    user: User,
    months: Iterable[date],
) -> dict[date, tuple[Decimal, dict[str, Decimal]]]:
    """Return overall and per-category spending for all requested months in one query."""
    month_starts = sorted({month.replace(day=1) for month in months})
    if not month_starts:
        return {}
    start = month_starts[0]
    end = month_bounds(month_starts[-1])[1]
    rows = (
        Transaction.objects.filter(
            owner_user=user,
            transaction_type="Expense",
            date__gte=start,
            date__lte=end,
        )
        .annotate(month=TruncMonth("date"))
        .values("month", "category")
        .annotate(spent=Sum(Abs("total")))
        .order_by("month", "category")
    )

    result: dict[date, dict[str, Decimal]] = {month: {} for month in month_starts}
    for row in rows:
        result[row["month"]][row["category"]] = row["spent"]
    return {
        month: (
            sum(category_totals.values(), Decimal("0.00")).quantize(Decimal("0.01")),
            {
                category: amount.quantize(Decimal("0.01"))
                for category, amount in category_totals.items()
            },
        )
        for month, category_totals in result.items()
    }


def spending_for_budget(user: User, budget: Budget) -> Decimal:
    """Calculate current spending that counts against a budget."""
    start, end = month_bounds(budget.month)
    query = Transaction.objects.filter(
        owner_user=user,
        transaction_type="Expense",
        date__gte=start,
        date__lte=end,
    )
    if budget.scope == Budget.SCOPE_CATEGORY:
        query = query.filter(category=budget.category)
    total = query.aggregate(spent=Sum(Abs("total")))["spent"] or Decimal("0.00")
    return abs(total).quantize(Decimal("0.01"))


def budget_payload(
    user: User,
    budget: Budget,
    spending: tuple[Decimal, dict[str, Decimal]] | None = None,
) -> dict[str, object]:
    """Return the API representation for a budget with spending status."""
    if spending is None:
        spent = spending_for_budget(user, budget)
    elif budget.scope == Budget.SCOPE_CATEGORY:
        spent = spending[1].get(budget.category, Decimal("0.00"))
    else:
        spent = spending[0]
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


def validate_payload(data: dict[str, object], existing: Budget | None = None) -> dict[str, object]:
    """Validate request data for creating or updating a budget."""
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


class BudgetListCreate(generics.GenericAPIView):
    """List and create monthly budgets for the authenticated user."""

    serializer_class = BudgetSchemaSerializer

    @extend_schema(
        tags=["Budgets"],
        operation_id="budget_list",
        parameters=[OpenApiParameter("month", str, OpenApiParameter.QUERY)],
        responses={200: OpenApiResponse(description="Budgets for the authenticated user")},
    )
    def get(self, request: Request) -> Response:
        """Return budgets for the authenticated user, optionally by month."""
        month_param = request.GET.get("month")
        query = Budget.objects.filter(owner_user=request.user).order_by("-month", "scope", "category")
        if month_param:
            try:
                query = query.filter(month=parse_month(month_param))
            except ValueError as exc:
                return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        budgets = list(query)
        spending = spending_totals_by_month(request.user, [item.month for item in budgets])
        return Response(
            [
                budget_payload(
                    request.user,
                    item,
                    spending.get(item.month),
                )
                for item in budgets
            ]
        )

    @extend_schema(
        tags=["Budgets"],
        operation_id="budget_create",
        responses={201: OpenApiResponse(description="Budget created")},
    )
    def post(self, request: Request) -> Response:
        """Create a unique budget for the authenticated user and month."""
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


class BudgetDetail(generics.GenericAPIView):
    """Retrieve, update, or delete one authenticated user's budget."""

    serializer_class = BudgetSchemaSerializer

    def get_object(self, request: Request, budget_id: int) -> Budget | None:
        """Return one owned budget or None when it does not exist."""
        try:
            return Budget.objects.get(owner_user=request.user, id=budget_id)
        except Budget.DoesNotExist:
            return None

    @extend_schema(
        tags=["Budgets"],
        operation_id="budget_retrieve",
        responses={200: OpenApiResponse(description="Budget details")},
    )
    def get(self, request: Request, budget_id: int) -> Response:
        """Return one budget owned by the authenticated user."""
        budget = self.get_object(request, budget_id)
        if not budget:
            return Response({"error": "Budget not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(budget_payload(request.user, budget))

    @extend_schema(
        tags=["Budgets"],
        operation_id="budget_update",
        responses={200: OpenApiResponse(description="Budget updated")},
    )
    def patch(self, request: Request, budget_id: int) -> Response:
        """Update one budget owned by the authenticated user."""
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

    @extend_schema(
        tags=["Budgets"],
        operation_id="budget_delete",
        responses={200: OpenApiResponse(description="Budget deleted")},
    )
    def delete(self, request: Request, budget_id: int) -> Response:
        """Delete one budget owned by the authenticated user."""
        budget = self.get_object(request, budget_id)
        if not budget:
            return Response({"error": "Budget not found"}, status=status.HTTP_404_NOT_FOUND)
        budget.delete()
        return Response({"message": "Budget deleted successfully"})


class BudgetSummary(APIView):
    """Return budget rollups for one month."""

    @extend_schema(
        tags=["Budgets"],
        operation_id="budget_summary",
        parameters=[OpenApiParameter("month", str, OpenApiParameter.QUERY)],
        responses={200: OpenApiResponse(description="Budget summary")},
    )
    def get(self, request: Request) -> Response:
        """Return overall, category, warning, and over-budget summaries."""
        try:
            month = parse_month(request.GET.get("month"))
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        budgets = list(Budget.objects.filter(owner_user=request.user, month=month).order_by("scope", "category"))
        spending = spending_totals_by_month(request.user, [month])
        payloads = [
            budget_payload(request.user, item, spending[month])
            for item in budgets
        ]
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

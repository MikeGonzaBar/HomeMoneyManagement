from datetime import date
from decimal import Decimal

from rest_framework.test import APITestCase

from account.models import Account
from transaction.models import Transaction
from users.models import AuthToken, User

from .models import Budget
from .views import spending_totals_by_month


class BudgetTests(APITestCase):
    """Budget calculation and ownership tests."""

    def setUp(self) -> None:
        """Create a user, account, transaction, and auth token."""
        self.user = User.objects.create(username="alice", first_name="Alice", last_name="User")
        self.user.set_password("password123")
        self.user.save()
        self.other = User.objects.create(username="bob", first_name="Bob", last_name="User")
        self.token = AuthToken.issue_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.account = Account.objects.create(
            owner_user=self.user,
            account_name="Checking",
            account_type="Checking",
            bank="Bank",
            total="1000.00",
        )
        Transaction.objects.create(
            owner_user=self.user,
            transaction_type="Expense",
            category="Food and drinks",
            date="2026-05-10",
            title="Market",
            total=Decimal("85.00"),
            account_fk=self.account,
        )

    def test_budget_summary_calculates_category_spend(self) -> None:
        response = self.client.post(
            "/budgets/",
            {
                "month": "2026-05",
                "scope": "category",
                "category": "Food and drinks",
                "limit_amount": "100.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["spent_amount"], 85.0)
        self.assertEqual(response.data["status"], "warning")

        summary = self.client.get("/budgets/summary/?month=2026-05")
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(len(summary.data["warnings"]), 1)

    def test_budget_spending_uses_one_grouped_query_for_all_categories(self) -> None:
        Transaction.objects.create(
            owner_user=self.user,
            transaction_type="Expense",
            category="Transport",
            date="2026-05-12",
            title="Bus",
            total=Decimal("15.00"),
            account_fk=self.account,
        )
        Budget.objects.create(
            owner_user=self.user,
            month="2026-05-01",
            scope="overall",
            limit_amount="200.00",
        )
        Budget.objects.create(
            owner_user=self.user,
            month="2026-05-01",
            scope="category",
            category="Food and drinks",
            limit_amount="100.00",
        )
        Budget.objects.create(
            owner_user=self.user,
            month="2026-05-01",
            scope="category",
            category="Transport",
            limit_amount="50.00",
        )

        with self.assertNumQueries(1):
            totals = spending_totals_by_month(self.user, [date(2026, 5, 1)])

        overall, categories = totals[date(2026, 5, 1)]
        self.assertEqual(overall, Decimal("100.00"))
        self.assertEqual(categories["Food and drinks"], Decimal("85.00"))
        self.assertEqual(categories["Transport"], Decimal("15.00"))

    def test_budget_owner_isolation(self) -> None:
        Budget.objects.create(
            owner_user=self.other,
            month="2026-05-01",
            scope="overall",
            limit_amount="1.00",
        )
        response = self.client.get("/budgets/?month=2026-05")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

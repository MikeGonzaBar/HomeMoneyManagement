from datetime import date

from django.test import override_settings
from rest_framework.test import APITestCase

from account.models import Account
from transaction.models import Transaction
from users.models import AuthToken, User

from .views import _monthly_category_summary, _monthly_summary, _period_summary


@override_settings(GOOGLE_AI_API_KEY=None)
class ReportsOwnershipTests(APITestCase):
    """Report route ownership tests."""

    def setUp(self) -> None:
        """Create users, auth token, account, and one transaction."""
        self.alice = User.objects.create(username="alice", first_name="Alice", last_name="User")
        self.bob = User.objects.create(username="bob", first_name="Bob", last_name="User")
        self.token = AuthToken.issue_for_user(self.alice)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.account = Account.objects.create(
            owner_user=self.alice,
            account_name="Checking",
            account_type="Checking",
            bank="Bank",
            total="100.00",
        )
        Transaction.objects.create(
            owner_user=self.alice,
            account_fk=self.account,
            transaction_type="Income",
            category="Salary",
            date="2026-05-20",
            title="Paycheck",
            total="100.00",
        )

    def test_reports_require_matching_route_user(self) -> None:
        response = self.client.get("/reports/analytics/bob/")
        self.assertEqual(response.status_code, 403)

    def test_reports_return_authenticated_user_data(self) -> None:
        response = self.client.get("/reports/analytics/alice/?start_date=2026-05-01&end_date=2026-05-31")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["kpis"]["total_income"], 100.0)

    def test_analytics_aggregates_periods_monthly_and_categories(self) -> None:
        Transaction.objects.create(
            owner_user=self.alice,
            account_fk=self.account,
            transaction_type="Expense",
            category="Food",
            date="2026-05-10",
            title="Lunch",
            total="25.00",
        )
        Transaction.objects.create(
            owner_user=self.alice,
            account_fk=self.account,
            transaction_type="Expense",
            category="Transport",
            date="2026-04-20",
            title="Previous month transit",
            total="15.00",
        )
        Transaction.objects.create(
            owner_user=self.alice,
            account_fk=self.account,
            from_account_fk=self.account,
            to_account_fk=self.account,
            transaction_type="Transfer",
            category="Transfer",
            date="2026-05-11",
            title="Excluded transfer",
            total="500.00",
        )

        with self.assertNumQueries(1):
            current = _period_summary(self.alice, date(2026, 5, 1), date(2026, 5, 31))
        with self.assertNumQueries(1):
            previous = _period_summary(self.alice, date(2026, 4, 1), date(2026, 4, 30))
        with self.assertNumQueries(1):
            monthly = _monthly_summary(self.alice, date(2026, 4, 1), date(2026, 5, 31))
        with self.assertNumQueries(1):
            categories = _monthly_category_summary(
                self.alice,
                date(2026, 4, 1),
                date(2026, 5, 31),
            )

        self.assertEqual(current, (100.0, 25.0, {"Food": 25.0}))
        self.assertEqual(previous, (0.0, 15.0, {"Transport": 15.0}))
        self.assertEqual(monthly["2026-05"], {"income": 100.0, "expense": 25.0})
        self.assertEqual(categories["2026-05"], {"Food": 25.0})

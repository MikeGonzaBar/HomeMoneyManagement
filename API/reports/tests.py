from django.test import override_settings
from rest_framework.test import APITestCase

from account.models import Account
from transaction.models import Transaction
from users.models import AuthToken, User


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

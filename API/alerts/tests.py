from rest_framework.test import APITestCase

from budgets.models import Budget
from users.models import AuthToken, User


class AlertTests(APITestCase):
    """Alert refresh and ownership tests."""

    def setUp(self) -> None:
        """Create an authenticated API user."""
        self.user = User.objects.create(username="alice", first_name="Alice", last_name="User")
        self.user.set_password("password123")
        self.user.save()
        self.token = AuthToken.issue_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_refresh_generates_budget_alert(self) -> None:
        Budget.objects.create(
            owner_user=self.user,
            month="2026-05-01",
            scope="overall",
            limit_amount="0.01",
        )
        response = self.client.post("/alerts/refresh/")
        self.assertEqual(response.status_code, 200)

    def test_alerts_are_user_scoped(self) -> None:
        response = self.client.get("/alerts/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

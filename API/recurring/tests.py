from decimal import Decimal

from rest_framework.test import APITestCase

from account.models import Account
from users.models import AuthToken, User


class RecurringTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username="alice", first_name="Alice", last_name="User")
        self.user.set_password("password123")
        self.user.save()
        self.token = AuthToken.issue_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.checking = Account.objects.create(owner_user=self.user, account_name="Checking", account_type="Checking", bank="Bank", total="100.00")
        self.savings = Account.objects.create(owner_user=self.user, account_name="Savings", account_type="Savings", bank="Bank", total="0.00")

    def test_due_occurrence_requires_confirm_before_posting(self):
        created = self.client.post(
            "/recurring-transactions/",
            {
                "title": "Rent",
                "transaction_type": "Expense",
                "category": "Bills and utilities",
                "total": "10.00",
                "account_id": str(self.checking.id),
                "frequency": "monthly",
                "interval": 1,
                "start_date": "2026-05-01",
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        due = self.client.get("/recurring-transactions/due/?through=2026-05-01")
        self.assertEqual(len(due.data), 1)
        self.checking.refresh_from_db()
        self.assertEqual(self.checking.total, Decimal("100.00"))

        posted = self.client.post(f"/recurring-transactions/due/{due.data[0]['occurrence_id']}/post/")
        self.assertEqual(posted.status_code, 200)
        self.checking.refresh_from_db()
        self.assertEqual(self.checking.total, Decimal("90.00"))

    def test_recurring_transfer_posts_once(self):
        created = self.client.post(
            "/recurring-transactions/",
            {
                "title": "Save",
                "transaction_type": "Transfer",
                "category": "Transfer",
                "total": "25.00",
                "from_account_id": str(self.checking.id),
                "to_account_id": str(self.savings.id),
                "frequency": "monthly",
                "start_date": "2026-05-01",
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        due = self.client.get("/recurring-transactions/due/?through=2026-05-01")
        occurrence_id = due.data[0]["occurrence_id"]
        self.client.post(f"/recurring-transactions/due/{occurrence_id}/post/")
        self.client.post(f"/recurring-transactions/due/{occurrence_id}/post/")
        self.checking.refresh_from_db()
        self.savings.refresh_from_db()
        self.assertEqual(self.checking.total, Decimal("75.00"))
        self.assertEqual(self.savings.total, Decimal("25.00"))

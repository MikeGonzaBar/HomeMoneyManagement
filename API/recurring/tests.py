from decimal import Decimal

from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase

from account.models import Account
from transaction.models import Transaction
from users.models import AuthToken, User

from .models import RecurringOccurrence, RecurringTransaction


class RecurringTests(APITestCase):
    """Recurring rule and occurrence posting tests."""

    def setUp(self) -> None:
        """Create user, auth token, and account fixtures."""
        self.user = User.objects.create(username="alice", first_name="Alice", last_name="User")
        self.user.set_password("password123")
        self.user.save()
        self.token = AuthToken.issue_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.checking = Account.objects.create(owner_user=self.user, account_name="Checking", account_type="Checking", bank="Bank", total="100.00")
        self.savings = Account.objects.create(owner_user=self.user, account_name="Savings", account_type="Savings", bank="Bank", total="0.00")

    def test_due_occurrence_requires_confirm_before_posting(self) -> None:
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

    def test_recurring_transfer_posts_once(self) -> None:
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

    def test_due_list_preloads_rules_and_posted_transactions(self) -> None:
        rule = RecurringTransaction.objects.create(
            owner_user=self.user,
            title="Payday",
            transaction_type="Income",
            category="Salary",
            total="100.00",
            account_fk=self.checking,
            frequency="monthly",
            interval=1,
            start_date="2026-01-01",
            next_due_date="2026-06-01",
        )
        first_transaction = Transaction.objects.create(
            owner_user=self.user,
            account_fk=self.checking,
            transaction_type="Income",
            category="Salary",
            date="2026-05-01",
            title="May salary",
            total="100.00",
        )
        second_transaction = Transaction.objects.create(
            owner_user=self.user,
            account_fk=self.checking,
            transaction_type="Income",
            category="Salary",
            date="2026-05-02",
            title="Bonus",
            total="100.00",
        )
        RecurringOccurrence.objects.create(
            recurring_transaction=rule,
            owner_user=self.user,
            due_date="2026-05-01",
            status=RecurringOccurrence.STATUS_POSTED,
            posted_transaction=first_transaction,
        )
        RecurringOccurrence.objects.create(
            recurring_transaction=rule,
            owner_user=self.user,
            due_date="2026-05-02",
            status=RecurringOccurrence.STATUS_POSTED,
            posted_transaction=second_transaction,
        )
        RecurringOccurrence.objects.create(
            recurring_transaction=rule,
            owner_user=self.user,
            due_date="2026-05-03",
            status=RecurringOccurrence.STATUS_DUE,
        )

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get("/recurring-transactions/due/?through=2026-05-31")
        data_queries = [
            query for query in queries.captured_queries
            if "SAVEPOINT" not in query["sql"].upper()
        ]
        self.assertEqual(len(data_queries), 4)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]["posted_transaction"]["id"], first_transaction.id)
        self.assertEqual(response.data[1]["posted_transaction"]["id"], second_transaction.id)
        self.assertIsNone(response.data[2]["posted_transaction"])

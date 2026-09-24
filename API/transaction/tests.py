from decimal import Decimal

from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase

from account.models import Account
from users.models import AuthToken, User
from .models import Transaction
from .services import _apply_delta


class TransactionBalanceTests(APITestCase):
    """Balance and ownership tests for transaction endpoints."""

    def setUp(self) -> None:
        """Create owner, cross-user, and account fixtures."""
        self.alice = User.objects.create(username="alice", first_name="Alice", last_name="User")
        self.alice.set_password("password123")
        self.alice.save()
        self.bob = User.objects.create(username="bob", first_name="Bob", last_name="User")
        self.bob.set_password("password123")
        self.bob.save()
        self.token = AuthToken.issue_for_user(self.alice)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.checking = Account.objects.create(
            owner_user=self.alice,
            account_name="Checking",
            account_type="Checking",
            bank="Bank",
            total="100.00",
        )
        self.savings = Account.objects.create(
            owner_user=self.alice,
            account_name="Savings",
            account_type="Savings",
            bank="Bank",
            total="25.00",
        )
        self.bob_account = Account.objects.create(
            owner_user=self.bob,
            account_name="Bob",
            account_type="Checking",
            bank="Bank",
            total="200.00",
        )

    def test_create_income_and_expense_update_balance(self) -> None:
        income = self.client.post(
            "/transactions/create/",
            {
                "transaction_type": "Income",
                "category": "Salary",
                "date": "2026-05-20",
                "title": "Paycheck",
                "total": "50.00",
                "owner_id": "bob",
                "account_id": str(self.checking.id),
            },
            format="json",
        )
        self.assertEqual(income.status_code, 201)
        self.checking.refresh_from_db()
        self.assertEqual(self.checking.total, Decimal("150.00"))

        expense = self.client.post(
            "/transactions/create/",
            {
                "transaction_type": "Expense",
                "category": "Food",
                "date": "2026-05-20",
                "title": "Lunch",
                "total": "20.00",
                "account_id": str(self.checking.id),
            },
            format="json",
        )
        self.assertEqual(expense.status_code, 201)
        self.checking.refresh_from_db()
        self.assertEqual(self.checking.total, Decimal("130.00"))

    def test_transfer_update_and_delete_reverse_balances(self) -> None:
        created = self.client.post(
            "/transactions/create/",
            {
                "transaction_type": "Transfer",
                "category": "Transfer",
                "date": "2026-05-20",
                "title": "Move money",
                "total": "10.00",
                "from_account_id": str(self.checking.id),
                "to_account_id": str(self.savings.id),
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        self.checking.refresh_from_db()
        self.savings.refresh_from_db()
        self.assertEqual(self.checking.total, Decimal("90.00"))
        self.assertEqual(self.savings.total, Decimal("35.00"))

        updated = self.client.patch(
            f"/transactions/update/{created.data['id']}/",
            {"total": "15.00"},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        self.checking.refresh_from_db()
        self.savings.refresh_from_db()
        self.assertEqual(self.checking.total, Decimal("85.00"))
        self.assertEqual(self.savings.total, Decimal("40.00"))

        deleted = self.client.delete(f"/transactions/delete/{created.data['id']}/")
        self.assertEqual(deleted.status_code, 200)
        self.checking.refresh_from_db()
        self.savings.refresh_from_db()
        self.assertEqual(self.checking.total, Decimal("100.00"))
        self.assertEqual(self.savings.total, Decimal("25.00"))

    def test_rejects_cross_user_account_without_balance_change(self) -> None:
        response = self.client.post(
            "/transactions/create/",
            {
                "transaction_type": "Expense",
                "category": "Food",
                "date": "2026-05-20",
                "title": "Bad",
                "total": "20.00",
                "account_id": str(self.bob_account.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.bob_account.refresh_from_db()
        self.assertEqual(self.bob_account.total, Decimal("200.00"))

    def test_route_username_mismatch_is_forbidden(self) -> None:
        response = self.client.get("/transactions/retrieve/bob/0/0/0/")
        self.assertEqual(response.status_code, 403)

    def test_reverse_direction_transfer_locks_accounts_in_id_order(self) -> None:
        with CaptureQueriesContext(connection) as queries:
            response = self.client.post(
                "/transactions/create/",
                {
                    "transaction_type": "Transfer",
                    "category": "Transfer",
                    "date": "2026-05-20",
                    "title": "Reverse move",
                    "total": "5.00",
                    "from_account_id": str(self.savings.id),
                    "to_account_id": str(self.checking.id),
                },
                format="json",
            )

        lock_queries = [
            query["sql"]
            for query in queries.captured_queries
            if 'FROM "account_account"' in query["sql"] and "FOR UPDATE" in query["sql"]
        ]
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(lock_queries), 1)
        self.assertIn('ORDER BY "account_account"."id" ASC', lock_queries[0])
        self.checking.refresh_from_db()
        self.savings.refresh_from_db()
        self.assertEqual(self.checking.total, Decimal("105.00"))
        self.assertEqual(self.savings.total, Decimal("20.00"))

    def test_transfer_update_locks_old_and_new_accounts_once(self) -> None:
        created = self.client.post(
            "/transactions/create/",
            {
                "transaction_type": "Transfer",
                "category": "Transfer",
                "date": "2026-05-20",
                "title": "Original direction",
                "total": "10.00",
                "from_account_id": str(self.checking.id),
                "to_account_id": str(self.savings.id),
            },
            format="json",
        )

        with CaptureQueriesContext(connection) as queries:
            updated = self.client.patch(
                f"/transactions/update/{created.data['id']}/",
                {
                    "from_account_id": str(self.savings.id),
                    "to_account_id": str(self.checking.id),
                },
                format="json",
            )

        lock_queries = [
            query["sql"]
            for query in queries.captured_queries
            if 'FROM "account_account"' in query["sql"] and "FOR UPDATE" in query["sql"]
        ]
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(len(lock_queries), 1)
        self.assertIn('ORDER BY "account_account"."id" ASC', lock_queries[0])
        self.checking.refresh_from_db()
        self.savings.refresh_from_db()
        self.assertEqual(self.checking.total, Decimal("110.00"))
        self.assertEqual(self.savings.total, Decimal("15.00"))

    def test_apply_delta_uses_database_expression(self) -> None:
        with CaptureQueriesContext(connection) as queries:
            _apply_delta(self.checking, Decimal("2.50"))

        update_queries = [
            query["sql"]
            for query in queries.captured_queries
            if 'UPDATE "account_account"' in query["sql"]
        ]
        self.assertEqual(len(update_queries), 1)
        self.assertIn('"total" + 2.5', update_queries[0])
        self.assertEqual(self.checking.total, Decimal("102.50"))
        self.checking.refresh_from_db()
        self.assertEqual(self.checking.total, Decimal("102.50"))
    def test_transaction_list_is_paginated(self) -> None:
        for index in range(24):
            Transaction.objects.create(
                owner_user=self.alice,
                account_fk=self.checking,
                transaction_type="Expense",
                category="Food",
                date=f"2026-05-{index + 1:02d}",
                title=f"Expense {index}",
                total="1.00",
            )

        response = self.client.get(
            "/transactions/retrieve/alice/0/0/0/?page_size=5&page=2"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 24)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNotNone(response.data["next"])
        self.assertTrue(response.data["next"].startswith("/transactions/retrieve/alice/"))

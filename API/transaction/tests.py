from decimal import Decimal

from rest_framework.test import APITestCase

from account.models import Account
from users.models import AuthToken, User
from .models import Transaction


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

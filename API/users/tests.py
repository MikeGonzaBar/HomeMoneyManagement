from decimal import Decimal

from rest_framework.test import APITestCase

from account.models import Account
from transaction.models import Transaction
from .models import AuthToken, User


class UserTokenAuthTests(APITestCase):
    def test_register_returns_token_and_user_payload(self):
        response = self.client.post(
            "/user/register/",
            {
                "username": "alice",
                "password": "strongpass123",
                "password_confirm": "strongpass123",
                "first_name": "Alice",
                "last_name": "User",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["valid"])
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["username"], "alice")
        self.assertTrue(AuthToken.objects.filter(key=response.data["token"]).exists())

    def test_login_profile_and_logout_token_flow(self):
        user = User(username="alice", first_name="Alice", last_name="User")
        user.set_password("strongpass123")
        user.save()

        login = self.client.post(
            "/user/login/",
            {"username_or_email": "alice", "password": "strongpass123"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)
        token = login.data["token"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        profile = self.client.get("/user/profile/")
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.data["user"]["username"], "alice")

        logout = self.client.post("/user/logout/")
        self.assertEqual(logout.status_code, 200)

        profile_after_logout = self.client.get("/user/profile/")
        self.assertEqual(profile_after_logout.status_code, 401)

    def test_update_info_requires_authenticated_user(self):
        response = self.client.put(
            "/user/update-info/",
            {"new_username": "mallory", "first_name": "Mallory", "last_name": "User"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_update_info_changes_authenticated_user_only(self):
        user = User(username="alice", first_name="Alice", last_name="User")
        user.set_password("strongpass123")
        user.save()
        token = AuthToken.issue_for_user(user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.put(
            "/user/update-info/",
            {"new_username": "alice2", "first_name": "Alicia", "last_name": "Updated"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.username, "alice2")
        self.assertEqual(user.first_name, "Alicia")

    def test_delete_user_removes_owned_accounts_with_transactions(self):
        user = User(username="alice", first_name="Alice", last_name="User")
        user.set_password("strongpass123")
        user.save()
        token = AuthToken.issue_for_user(user)
        account = Account.objects.create(
            account_type="Checking",
            bank="Test Bank",
            total=Decimal("100.00"),
            account_name="Main Checking",
            owner_user=user,
        )
        Transaction.objects.create(
            transaction_type="Expense",
            category="Groceries",
            date="2026-05-20",
            title="Market",
            total=Decimal("12.50"),
            owner_user=user,
            account_fk=account,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.delete(
            "/user/detail/alice/",
            {"password": "strongpass123"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertFalse(User.objects.filter(username="alice").exists())
        self.assertFalse(Account.objects.filter(owner="alice").exists())
        self.assertFalse(Transaction.objects.filter(owner_id="alice").exists())

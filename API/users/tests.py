from decimal import Decimal
import importlib

from django.test import override_settings
from django.urls import clear_url_caches
from rest_framework.test import APITestCase

from account.models import Account
from transaction.models import Transaction
from .models import AuthToken, User


class UserTokenAuthTests(APITestCase):
    """Token authentication and user account workflow tests."""

    def test_register_returns_token_and_user_payload(self) -> None:
        """Registration returns a token and the public user payload."""
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
        self.assertFalse(response.data["user"]["is_admin"])
        self.assertTrue(AuthToken.objects.filter(key=response.data["token"]).exists())

    def test_login_profile_and_logout_token_flow(self) -> None:
        """Login issues a usable token and logout revokes it."""
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
        self.assertFalse(login.data["user"]["is_admin"])

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        profile = self.client.get("/user/profile/")
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.data["user"]["username"], "alice")
        self.assertFalse(profile.data["user"]["is_admin"])

        logout = self.client.post("/user/logout/")
        self.assertEqual(logout.status_code, 200)

        profile_after_logout = self.client.get("/user/profile/")
        self.assertEqual(profile_after_logout.status_code, 401)

    def test_update_info_requires_authenticated_user(self) -> None:
        """Profile updates require token authentication."""
        response = self.client.put(
            "/user/update-info/",
            {"new_username": "mallory", "first_name": "Mallory", "last_name": "User"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_update_info_changes_authenticated_user_only(self) -> None:
        """Profile updates mutate only the token-authenticated user."""
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

    def test_delete_user_removes_owned_accounts_with_transactions(self) -> None:
        """User deletion removes related account and transaction data."""
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


class ApiAdminTests(APITestCase):
    """API admin-mode permission and user-management tests."""

    def setUp(self) -> None:
        """Create an admin user and a regular user with tokens."""
        self.admin = User(username="admin", first_name="Admin", last_name="User", is_admin=True)
        self.admin.set_password("strongpass123")
        self.admin.save()
        self.admin_token = AuthToken.issue_for_user(self.admin)

        self.user = User(username="alice", first_name="Alice", last_name="User")
        self.user.set_password("strongpass123")
        self.user.save()
        self.user_token = AuthToken.issue_for_user(self.user)

    def test_non_admin_token_cannot_access_api_admin(self) -> None:
        """Regular API users receive 403 for admin-mode endpoints."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.user_token.key}")

        response = self.client.get("/api-admin/users/")

        self.assertEqual(response.status_code, 403)

    def test_admin_can_list_and_update_users(self) -> None:
        """API admins can list users and update safe admin-managed fields."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")

        list_response = self.client.get("/api-admin/users/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual({item["username"] for item in list_response.data}, {"admin", "alice"})
        self.assertNotIn("password", list_response.data[0])

        patch_response = self.client.patch(
            f"/api-admin/users/{self.user.id}/",
            {"is_admin": True, "first_name": "Alicia"},
            format="json",
        )

        self.assertEqual(patch_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_admin)
        self.assertEqual(self.user.first_name, "Alicia")

    def test_admin_can_revoke_user_tokens(self) -> None:
        """API admins can revoke every active token for a target user."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")

        response = self.client.post(f"/api-admin/users/{self.user.id}/tokens/revoke/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["revoked_tokens"], 1)
        self.user_token.refresh_from_db()
        self.assertIsNotNone(self.user_token.revoked_at)

    def test_cannot_remove_last_api_admin(self) -> None:
        """The API prevents accidentally removing the final admin user."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")

        response = self.client.patch(
            f"/api-admin/users/{self.admin.id}/",
            {"is_admin": False},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_admin)


class SwaggerSchemaTests(APITestCase):
    """OpenAPI/Swagger availability and auth metadata tests."""

    def test_schema_includes_token_auth_and_core_paths(self) -> None:
        """Generated schema advertises Token auth and core API routes."""
        response = self.client.get("/schema/")

        self.assertEqual(response.status_code, 200)
        schema = response.data
        self.assertIn("TokenAuth", schema["components"]["securitySchemes"])
        self.assertIn("/user/login/", schema["paths"])
        self.assertIn("/api-admin/users/", schema["paths"])

    def test_docs_routes_respect_api_docs_enabled_flag(self) -> None:
        """Docs URLs are removed when API_DOCS_ENABLED is false."""
        import MoneyManagement.urls as urlconf

        try:
            with override_settings(API_DOCS_ENABLED=False):
                clear_url_caches()
                disabled_urlconf = importlib.reload(urlconf)
                names = {getattr(pattern, "name", None) for pattern in disabled_urlconf.urlpatterns}
                self.assertNotIn("schema", names)
                self.assertNotIn("swagger-ui", names)
        finally:
            with override_settings(API_DOCS_ENABLED=True):
                clear_url_caches()
                importlib.reload(urlconf)

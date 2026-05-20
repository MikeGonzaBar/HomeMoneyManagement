from rest_framework.test import APITestCase

from users.models import AuthToken, User
from .models import Account


class AccountOwnershipTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create(username="alice", first_name="Alice", last_name="User")
        self.alice.set_password("password123")
        self.alice.save()
        self.bob = User.objects.create(username="bob", first_name="Bob", last_name="User")
        self.bob.set_password("password123")
        self.bob.save()
        self.alice_token = AuthToken.issue_for_user(self.alice)

    def auth_as_alice(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.alice_token.key}")

    def test_create_account_uses_token_owner_not_body_owner(self):
        self.auth_as_alice()
        response = self.client.post(
            "/accounts/",
            {
                "account_name": "Checking",
                "account_type": "Checking",
                "bank": "Bank",
                "total": "100.00",
                "owner": "bob",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        account = Account.objects.get(id=response.data["id"])
        self.assertEqual(account.owner_user, self.alice)
        self.assertEqual(account.owner, "alice")

    def test_route_username_mismatch_is_forbidden(self):
        self.auth_as_alice()
        response = self.client.get("/accounts/details/bob/0/")
        self.assertEqual(response.status_code, 403)

    def test_cannot_update_another_users_account(self):
        bob_account = Account.objects.create(
            owner_user=self.bob,
            account_name="Bob Checking",
            account_type="Checking",
            bank="Bank",
            total="50.00",
        )

        self.auth_as_alice()
        response = self.client.patch(
            f"/accounts/details/alice/{bob_account.id}/",
            {"total": "999.00"},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        bob_account.refresh_from_db()
        self.assertEqual(str(bob_account.total), "50.00")

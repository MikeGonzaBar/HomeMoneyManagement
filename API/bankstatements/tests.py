from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from unittest.mock import Mock, patch

from users.models import AuthToken, User
from .models import BankStatement


class BankStatementOwnershipTests(APITestCase):
    """Ownership and upload error tests for bank statement endpoints."""

    def setUp(self) -> None:
        """Create two users and one statement for each user."""
        self.alice = User.objects.create(username="alice", first_name="Alice", last_name="User")
        self.bob = User.objects.create(username="bob", first_name="Bob", last_name="User")
        self.token = AuthToken.issue_for_user(self.alice)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.alice_statement = BankStatement.objects.create(
            owner_user=self.alice,
            file=ContentFile(b"%PDF-1.4\n", name="alice.pdf"),
            original_filename="alice.pdf",
            file_size=9,
        )
        self.bob_statement = BankStatement.objects.create(
            owner_user=self.bob,
            file=ContentFile(b"%PDF-1.4\n", name="bob.pdf"),
            original_filename="bob.pdf",
            file_size=9,
        )

    def test_route_username_mismatch_is_forbidden(self) -> None:
        response = self.client.get("/bank-statements/user/bob/")
        self.assertEqual(response.status_code, 403)

    def test_detail_does_not_expose_other_users_statement(self) -> None:
        response = self.client.get(f"/bank-statements/details/{self.bob_statement.id}/")
        self.assertEqual(response.status_code, 404)

    def test_user_list_only_returns_owned_statements(self) -> None:
        response = self.client.get("/bank-statements/user/alice/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["statements"]), 1)
        self.assertEqual(response.data["statements"][0]["id"], self.alice_statement.id)

    @patch("bankstatements.views.extract_transactions_from_pdf")
    def test_upload_surfaces_ai_processing_failure(self, mock_extract: Mock) -> None:
        mock_extract.return_value = {
            "transactions": [],
            "account_name": None,
            "account_type": None,
            "statement_period": None,
            "initial_balance": None,
            "error": "Gemini quota exceeded",
        }
        pdf = SimpleUploadedFile("statement.pdf", b"%PDF-1.4\n%%EOF\n", content_type="application/pdf")

        response = self.client.post("/bank-statements/upload/", {"pdf_file": pdf}, format="multipart")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data["status"], "failed")
        self.assertEqual(response.data["extracted_data"]["processing_error"], "Gemini quota exceeded")
        statement = BankStatement.objects.get(id=response.data["file_details"]["id"])
        self.assertEqual(statement.owner_user, self.alice)
        self.assertEqual(statement.processing_status, "failed")

    @patch("bankstatements.views.extract_transactions_from_pdf")
    def test_upload_reports_missing_ai_key_as_service_unavailable(self, mock_extract: Mock) -> None:
        mock_extract.return_value = {
            "transactions": [],
            "account_name": None,
            "account_type": None,
            "statement_period": None,
            "initial_balance": None,
            "error": "AI API key not configured",
        }
        pdf = SimpleUploadedFile("statement.pdf", b"%PDF-1.4\n%%EOF\n", content_type="application/pdf")

        response = self.client.post("/bank-statements/upload/", {"pdf_file": pdf}, format="multipart")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["status"], "failed")
        self.assertEqual(response.data["message"], "AI API key not configured")

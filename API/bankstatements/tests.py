from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase
from unittest.mock import Mock, patch

from account.models import Account
from transaction.models import Transaction
from users.models import AuthToken, User

from .models import BankStatement, BankStatementImportBatch, BankStatementTransactionCandidate
from .reconciliation import create_import_batch


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

    def test_statement_list_uses_one_annotated_data_query(self) -> None:
        second_statement = BankStatement.objects.create(
            owner_user=self.alice,
            file=ContentFile(b"%PDF-1.4\n", name="alice-second.pdf"),
            original_filename="alice-second.pdf",
            file_size=9,
        )
        first_batch = BankStatementImportBatch.objects.create(
            bank_statement=self.alice_statement,
            owner_user=self.alice,
            status=BankStatementImportBatch.STATUS_COMMITTED,
        )
        latest_batch = BankStatementImportBatch.objects.create(
            bank_statement=self.alice_statement,
            owner_user=self.alice,
            status=BankStatementImportBatch.STATUS_REVIEW,
        )
        for index in range(2):
            BankStatementTransactionCandidate.objects.create(
                import_batch=latest_batch,
                owner_user=self.alice,
                title=f"Candidate {index}",
                transaction_type="Expense",
                category="Food",
                date="2026-05-10",
                amount="10.00",
            )

        with self.assertNumQueries(4):
            response = self.client.get("/bank-statements/user/alice/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        statements = {item["id"]: item for item in response.data["statements"]}
        self.assertEqual(statements[self.alice_statement.id]["review_batch_id"], latest_batch.id)
        self.assertNotEqual(statements[self.alice_statement.id]["review_batch_id"], first_batch.id)
        self.assertEqual(statements[self.alice_statement.id]["review_batch_status"], "review")
        self.assertEqual(statements[self.alice_statement.id]["review_candidate_count"], 2)
        self.assertIsNone(statements[second_statement.id]["review_batch_id"])
        self.assertEqual(statements[second_statement.id]["review_candidate_count"], 0)

    def test_statement_list_is_paginated(self) -> None:
        for index in range(24):
            BankStatement.objects.create(
                owner_user=self.alice,
                file=ContentFile(f"%PDF-1.4\\n{index}".encode(), name=f"page-{index}.pdf"),
                original_filename=f"page-{index}.pdf",
                file_size=9,
            )

        response = self.client.get("/bank-statements/user/alice/?page_size=10&page=2")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(len(response.data["statements"]), 10)
        self.assertIsNotNone(response.data["next"])
        self.assertTrue(response.data["next"].startswith("/bank-statements/user/alice/"))



    def test_statement_detail_uses_one_annotated_data_query(self) -> None:
        batch = BankStatementImportBatch.objects.create(
            bank_statement=self.alice_statement,
            owner_user=self.alice,
            status=BankStatementImportBatch.STATUS_REVIEW,
        )
        BankStatementTransactionCandidate.objects.create(
            import_batch=batch,
            owner_user=self.alice,
            title="Candidate",
            transaction_type="Expense",
            category="Food",
            date="2026-05-10",
            amount="10.00",
        )

        with self.assertNumQueries(3):
            response = self.client.get(f"/bank-statements/details/{self.alice_statement.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["statement"]["review_batch_id"], batch.id)
        self.assertEqual(response.data["statement"]["review_candidate_count"], 1)

    def test_import_batch_preloads_imported_transactions(self) -> None:
        account = Account.objects.create(
            owner_user=self.alice,
            account_name="Checking",
            account_type="Checking",
            bank="Bank",
            total="100.00",
        )
        transaction = Transaction.objects.create(
            owner_user=self.alice,
            account_fk=account,
            transaction_type="Expense",
            category="Food",
            date="2026-05-10",
            title="Imported expense",
            total="10.00",
        )
        batch = BankStatementImportBatch.objects.create(
            bank_statement=self.alice_statement,
            owner_user=self.alice,
            status=BankStatementImportBatch.STATUS_COMMITTED,
        )
        for index in range(2):
            BankStatementTransactionCandidate.objects.create(
                import_batch=batch,
                owner_user=self.alice,
                title=f"Imported {index}",
                transaction_type="Expense",
                category="Food",
                date="2026-05-10",
                amount="10.00",
                imported_transaction=transaction,
                status=BankStatementTransactionCandidate.STATUS_IMPORTED,
            )

        with self.assertNumQueries(4):
            response = self.client.get(f"/bank-statements/import-batches/{batch.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["candidates"]), 2)
        self.assertEqual(
            [item["imported_transaction"]["id"] for item in response.data["candidates"]],
            [transaction.id, transaction.id],
        )

    def test_import_batch_bulk_creates_and_matches_candidates(self) -> None:
        account = Account.objects.create(
            owner_user=self.alice,
            account_name="Checking",
            account_type="Checking",
            bank="Bank",
            total="100.00",
        )
        existing = Transaction.objects.create(
            owner_user=self.alice,
            account_fk=account,
            transaction_type="Expense",
            category="Food",
            date="2026-05-10",
            title="Existing purchase",
            total="10.00",
        )
        transactions = [
            {
                "title": "Existing purchase" if index == 0 else f"Purchase {index}",
                "transaction_type": "Expense",
                "category": "Food",
                "date": "2026-05-10",
                "amount": "10.00",
            }
            for index in range(50)
        ]

        with CaptureQueriesContext(connection) as queries:
            batch = create_import_batch(
                self.alice_statement,
                {"transactions": transactions},
            )
        data_queries = [
            query for query in queries.captured_queries
            if "SAVEPOINT" not in query["sql"].upper()
        ]
        self.assertEqual(len(data_queries), 4)

        candidates = list(batch.candidates.order_by("id"))
        self.assertEqual(len(candidates), 50)
        self.assertEqual(candidates[0].possible_matches[0]["id"], existing.id)
        self.assertTrue(candidates[0].possible_matches[0]["title"] == "Existing purchase")

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

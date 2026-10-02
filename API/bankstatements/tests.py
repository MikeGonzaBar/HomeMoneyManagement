from datetime import date

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext, override_settings
from rest_framework.test import APITestCase
from unittest.mock import Mock, patch

from account.models import Account
from transaction.models import Transaction
from users.models import AuthToken, User

from .models import BankStatement, BankStatementImportBatch, BankStatementImportProduct, BankStatementTransactionCandidate, ProductStatementSnapshot, RetirementStatementSnapshot, CreditCardStatementSnapshot, DeferredPurchase
from .reconciliation import (
    batch_payload,
    commit_batch,
    create_import_batch,
    update_candidate,
    update_deferred_purchases,
    update_import_product,
)
from .tasks import process_bank_statement
from .services import (
    _gemini_models_to_try,
    _is_transient_gemini_error,
    normalize_credit_card_deferred_extraction,
    normalize_multi_product_extraction,
    normalize_nu_cajitas_extraction,
    normalize_retirement_extraction,
)


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

    def test_delete_statement_cascades_its_multi_product_review_data(self) -> None:
        """Deleting a statement must also remove its derived review records."""
        batch = BankStatementImportBatch.objects.create(
            bank_statement=self.alice_statement,
            owner_user=self.alice,
        )
        product = BankStatementImportProduct.objects.create(
            import_batch=batch,
            source_product_id="checking",
            name="Checking",
            product_type="checking",
        )
        candidate = BankStatementTransactionCandidate.objects.create(
            import_batch=batch,
            owner_user=self.alice,
            title="Purchase",
            transaction_type="Expense",
            category="Food",
            date="2026-05-10",
            amount="10.00",
            source_product=product,
        )

        response = self.client.delete(f"/bank-statements/delete/{self.alice_statement.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(BankStatement.objects.filter(id=self.alice_statement.id).exists())
        self.assertFalse(BankStatementImportBatch.objects.filter(id=batch.id).exists())
        self.assertFalse(BankStatementImportProduct.objects.filter(id=product.id).exists())
        self.assertFalse(BankStatementTransactionCandidate.objects.filter(id=candidate.id).exists())

    def test_deleting_account_unlinks_pending_statement_candidate(self) -> None:
        account = Account.objects.create(
            owner_user=self.alice,
            account_name="Temporary account",
            account_type="Checking",
            bank="Bank",
            total="0.00",
        )
        batch = BankStatementImportBatch.objects.create(
            bank_statement=self.alice_statement,
            owner_user=self.alice,
        )
        candidate = BankStatementTransactionCandidate.objects.create(
            import_batch=batch,
            owner_user=self.alice,
            title="Draft transaction",
            transaction_type="Expense",
            category="Food",
            date="2026-05-10",
            amount="10.00",
            account_fk=account,
        )

        response = self.client.delete(f"/accounts/delete/alice/{account.id}/")

        self.assertEqual(response.status_code, 200)
        candidate.refresh_from_db()
        self.assertIsNone(candidate.account_fk)



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

    def test_statement_list_reports_resolved_progress_and_period(self) -> None:
        """The list endpoint must expose per-statement review progress and period."""
        batch = BankStatementImportBatch.objects.create(
            bank_statement=self.alice_statement,
            owner_user=self.alice,
            status=BankStatementImportBatch.STATUS_REVIEW,
            detected_account_name="Chase Checking",
            statement_period_start=date(2026, 5, 1),
            statement_period_end=date(2026, 5, 31),
        )
        resolved_statuses = [
            BankStatementTransactionCandidate.STATUS_IMPORTED,
            BankStatementTransactionCandidate.STATUS_SKIPPED,
            BankStatementTransactionCandidate.STATUS_LINKED,
        ]
        for index, candidate_status in enumerate(resolved_statuses):
            BankStatementTransactionCandidate.objects.create(
                import_batch=batch,
                owner_user=self.alice,
                title=f"Resolved {index}",
                transaction_type="Expense",
                category="Food",
                date="2026-05-10",
                amount="10.00",
                status=candidate_status,
            )
        for index in range(2):
            BankStatementTransactionCandidate.objects.create(
                import_batch=batch,
                owner_user=self.alice,
                title=f"Pending {index}",
                transaction_type="Expense",
                category="Food",
                date="2026-05-11",
                amount="10.00",
            )

        response = self.client.get("/bank-statements/user/alice/")

        self.assertEqual(response.status_code, 200)
        statement = next(
            item for item in response.data["statements"]
            if item["id"] == self.alice_statement.id
        )
        self.assertEqual(statement["review_batch_status"], "review")
        self.assertEqual(statement["review_candidate_count"], 5)
        self.assertEqual(statement["review_resolved_count"], 3)
        self.assertEqual(statement["review_account_name"], "Chase Checking")
        self.assertEqual(statement["review_period_start"], "2026-05-01")
        self.assertEqual(statement["review_period_end"], "2026-05-31")

    def test_failed_statement_can_be_queued_for_retry(self) -> None:
        self.alice_statement.processing_status = "failed"
        self.alice_statement.processed = False
        self.alice_statement.error_message = "Temporary provider timeout"
        self.alice_statement.save(update_fields=["processing_status", "processed", "error_message"])

        response = self.client.post(f"/bank-statements/retry/{self.alice_statement.id}/")

        self.assertEqual(response.status_code, 202)
        self.alice_statement.refresh_from_db()
        self.assertEqual(self.alice_statement.processing_status, "pending")
        self.assertIsNone(self.alice_statement.error_message)

    def test_statement_retry_is_owner_scoped_and_failed_only(self) -> None:
        other_response = self.client.post(f"/bank-statements/retry/{self.bob_statement.id}/")
        active_response = self.client.post(f"/bank-statements/retry/{self.alice_statement.id}/")

        self.assertEqual(other_response.status_code, 404)
        self.assertEqual(active_response.status_code, 409)

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
        # 5 statements: batch INSERT, candidate INSERTs, match SELECT, match UPDATE.
        # The candidate INSERTs split in two because SQLite caps one statement at
        # ~999 bound parameters (20 columns x 49 rows = 980), so the 50th row spills
        # into a second INSERT. Asserted as <= so a different SQLite parameter limit
        # still passes, while a per-candidate N+1 (50+ queries) still fails.
        self.assertLessEqual(
            len(data_queries),
            5,
            "\n".join(q["sql"] for q in data_queries),
        )

        candidates = list(batch.candidates.order_by("id"))
        self.assertEqual(len(candidates), 50)
        self.assertEqual(candidates[0].possible_matches[0]["id"], existing.id)
        self.assertTrue(candidates[0].possible_matches[0]["title"] == "Existing purchase")

    @patch("bankstatements.tasks.extract_transactions_from_pdf")
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

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["status"], "processing")
        process_bank_statement(response.data["file_details"]["id"])
        statement = BankStatement.objects.get(id=response.data["file_details"]["id"])
        self.assertEqual(statement.owner_user, self.alice)
        self.assertEqual(statement.processing_status, "failed")
        self.assertIn("Gemini quota exceeded", statement.error_message)

    @patch("bankstatements.tasks.extract_transactions_from_pdf")
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

        self.assertEqual(response.status_code, 202)
        process_bank_statement(response.data["file_details"]["id"])
        statement = BankStatement.objects.get(id=response.data["file_details"]["id"])
        self.assertEqual(statement.processing_status, "failed")
        self.assertIn("AI API key not configured", statement.error_message)

    @patch("bankstatements.tasks.extract_transactions_from_pdf")
    def test_background_processing_completes_and_creates_review_batch(self, mock_extract: Mock) -> None:
        mock_extract.return_value = {
            "transactions": [],
            "account_name": "Rappi Card",
            "account_type": "Credit Card",
            "statement_period": None,
            "initial_balance": None,
        }
        pdf = SimpleUploadedFile("rappi.pdf", b"%PDF-1.4\n%%EOF\n", content_type="application/pdf")

        response = self.client.post("/bank-statements/upload/", {"pdf_file": pdf}, format="multipart")
        statement_id = response.data["file_details"]["id"]
        process_bank_statement(statement_id)

        statement = BankStatement.objects.get(id=statement_id)
        self.assertEqual(statement.processing_status, "completed")
        self.assertTrue(statement.processed)
        self.assertTrue(statement.import_batches.exists())


class GeminiFallbackTests(APITestCase):
    @override_settings(
        GOOGLE_AI_MODEL="gemini-primary",
        GOOGLE_AI_FALLBACK_MODELS="gemini-backup-a, gemini-primary, gemini-backup-b",
    )
    def test_configured_model_is_followed_by_unique_fallbacks(self) -> None:
        self.assertEqual(
            _gemini_models_to_try(),
            ["gemini-primary", "gemini-backup-a", "gemini-backup-b"],
        )

    def test_503_is_treated_as_a_transient_error(self) -> None:
        self.assertTrue(_is_transient_gemini_error(Exception("503 UNAVAILABLE: high demand")))
        self.assertTrue(_is_transient_gemini_error(Exception("429 RESOURCE_EXHAUSTED")))
        self.assertFalse(_is_transient_gemini_error(Exception("400 invalid argument")))

    @override_settings(GOOGLE_AI_REQUEST_TIMEOUT=20)
    def test_request_timeout_is_configured(self) -> None:
        from django.conf import settings

        self.assertEqual(settings.GOOGLE_AI_REQUEST_TIMEOUT, 20)

    @override_settings(GOOGLE_AI_MODEL="gemini-3.8-flash", GOOGLE_AI_FALLBACK_MODELS="")
    def test_default_fallbacks_only_include_available_models(self) -> None:
        models = _gemini_models_to_try()
        self.assertEqual(models, ["gemini-3.8-flash", "gemini-3.5-flash-lite"])


class RetirementStatementImportTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="retiree")
        self.statement = BankStatement.objects.create(
            owner_user=self.user, file=ContentFile(b"%PDF-1.4\n", name="afore.pdf"),
            original_filename="afore.pdf", file_size=9,
        )

    def retirement_data(self) -> dict:
        return {
            "statement_kind": "retirement", "account_name": "Profuturo AFORE", "account_type": "Retirement",
            "initial_balance": "100.00", "statement_period": {"start": "2026-01-01", "end": "2026-01-31"},
            "balance_period": {"start": "2026-01-01", "end": "2026-01-31"},
            "movements_period": {"start": "2026-01-01", "end": "2026-01-31"},
            "retirement_breakdown": {"institution": "Profuturo", "subaccounts": {"retirement": 133.00, "voluntary_savings": 0, "housing": 0}},
            "reconciliation": {"opening_balance": "100.00", "closing_balance": "133.00", "is_reconciled": True},
            "transactions": [
                {"title": "Employer contribution", "amount": "30.00", "date": "2026-01-20", "transaction_type": "Income", "category": "Retirement contribution"},
                {"title": "Period return", "amount": "5.00", "transaction_type": "Income", "category": "Investment return", "retirement_movement_type": "return"},
                {"title": "Period fee", "amount": "2.00", "transaction_type": "Expense", "category": "Retirement fee", "retirement_movement_type": "fee"},
                {"title": "Days contributed", "amount": "1.00", "importable": False},
            ],
        }

    def test_reconciled_afore_import_updates_account_and_creates_snapshot(self) -> None:
        account = Account.objects.create(owner_user=self.user, account_name="Profuturo AFORE", account_type="Retirement", bank="Profuturo", total="100.00")
        batch = create_import_batch(self.statement, self.retirement_data())
        self.assertEqual(batch.candidates.count(), 3)
        result = commit_batch(self.user, batch.id, {"account_id": account.id})
        self.assertEqual(len(result["failed"]), 0)
        account.refresh_from_db()
        self.assertEqual(str(account.total), "133.00")
        self.assertEqual(account.retirement_metadata["institution"], "Profuturo")
        self.assertTrue(RetirementStatementSnapshot.objects.filter(account=account, import_batch=batch).exists())

    def test_mismatched_retirement_period_is_review_only(self) -> None:
        data = normalize_retirement_extraction({
            "statement_kind": "retirement", "account_type": "AFORE", "initial_balance": 100,
            "balance_period": {"start": "2025-09-01", "end": "2026-08-31"},
            "movements_period": {"start": "2026-05-01", "end": "2026-08-31"},
            "retirement_breakdown": {"institution": "Profuturo"},
            "reconciliation": {"is_reconciled": True, "closing_balance": 133}, "transactions": [],
        })
        self.assertFalse(data["reconciliation"]["is_reconciled"])
        self.assertIsNone(data["initial_balance"])

    def test_unreconciled_retirement_can_import_from_confirmed_opening_balance_only(self) -> None:
        data = self.retirement_data()
        data["reconciliation"] = {
            "opening_balance": "100.00",
            "closing_balance": "999.00",
            "is_reconciled": False,
        }
        batch = create_import_batch(self.statement, data)
        account = Account.objects.create(
            owner_user=self.user,
            account_name="Profuturo AFORE",
            account_type="Retirement",
            bank="Profuturo",
            total="100.00",
        )

        with self.assertRaises(ValidationError):
            commit_batch(self.user, batch.id, {"account_id": account.id})

        result = commit_batch(
            self.user,
            batch.id,
            {"account_id": account.id, "use_retirement_opening_balance_only": True},
        )

        self.assertEqual(len(result["failed"]), 0)
        account.refresh_from_db()
        self.assertEqual(str(account.total), "133.00")
        self.assertEqual(account.retirement_metadata["import_mode"], "opening_balance_only")
        self.assertFalse(RetirementStatementSnapshot.objects.filter(import_batch=batch).exists())


class MultiProductStatementImportTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="multi")
        self.statement = BankStatement.objects.create(owner_user=self.user, file=ContentFile(b"%PDF", name="hey.pdf"), original_filename="hey.pdf", file_size=4)

    def test_gbm_portfolio_summary_is_not_an_account_and_leaf_products_reconcile_with_valuation(self) -> None:
        data = normalize_multi_product_extraction({
            "statement_kind": "multi_product",
            "accounts": [
                {"source_product_id": "portfolio-gbm", "name": "PORTAFOLIO GBM", "product_type": "Investment",
                 "opening_balance": "25221.23", "closing_balance": "25029.11", "is_portfolio_summary": True},
                {"source_product_id": "deuda", "name": "DEUDA", "product_type": "Investment",
                 "opening_balance": "25220.37", "closing_balance": "25028.24",
                 "reconciliation": {"opening_balance": "25220.37", "closing_balance": "25028.24", "cash_movements": "-289.69", "valuation_change": "97.56"}},
                {"source_product_id": "efectivo", "name": "EFECTIVO", "product_type": "Checking",
                 "opening_balance": "0.87", "closing_balance": "0.88",
                 "reconciliation": {"opening_balance": "0.87", "closing_balance": "0.88", "cash_movements": "0.01", "valuation_change": "0.00"}},
            ],
        })

        self.assertEqual([product["source_product_id"] for product in data["accounts"]], ["deuda", "efectivo"])
        self.assertTrue(data["accounts"][0]["reconciliation"]["is_reconciled"])
        self.assertTrue(data["accounts"][1]["reconciliation"]["is_reconciled"])

    def test_nu_cajitas_are_split_from_spendable_account_and_transfers_are_deduplicated(self) -> None:
        extracted = {
            "statement_kind": "bank", "account_name": "Cuenta Nu", "account_type": "Other",
            "statement_period": {"start": "2026-08-01", "end": "2026-08-31"},
            "initial_balance": 149372.92,
            "transactions": [
                {"date": "2026-08-26", "title": "Depósito en Cajita: Cajita para crédito", "amount": 299.88, "transaction_type": "Expense", "category": "Account Transfer"},
                {"date": "2026-08-26", "title": "MIGUEL GONZALEZ BARAJAS MERCADO*PAGO", "amount": 299.88, "transaction_type": "Income", "category": "Money Transfer"},
                {"date": "2026-08-18", "title": "ITESO UNIV Compra", "amount": 8226.72, "transaction_type": "Expense", "category": "Education"},
                {"date": "2026-08-18", "title": "Retiro de Cajita: Cajita para crédito", "amount": 8226.72, "transaction_type": "Income", "category": "Account Transfer"},
                {"date": "2026-08-26", "title": "Depósito en Cajita: Cajita para crédito", "amount": 299.88, "transaction_type": "Income", "category": "Account Transfer"},
            ],
        }
        pdf_text = """
        Cuenta Nu: 00018287118
        Saldo inicial $149,372.92
        Dinero generado este mes $971.21
        Saldo al generar este estado de cuenta $142,417.29
        En su Cuenta $0.00
        Total Cajitas $142,417.29
        Detalle de movimientos de tus cajitas
        """

        data = normalize_multi_product_extraction(normalize_nu_cajitas_extraction(extracted, pdf_text))

        self.assertEqual(data["statement_kind"], "multi_product")
        self.assertIsNone(data["initial_balance"])
        self.assertEqual([product["name"] for product in data["accounts"]], ["Cuenta Nu", "Cajitas Nu"])
        self.assertEqual(data["accounts"][0]["product_type"], "Checking")
        self.assertEqual(data["accounts"][0]["opening_balance"], 0.0)
        self.assertEqual(data["accounts"][0]["closing_balance"], 0.0)
        self.assertEqual(data["accounts"][1]["product_type"], "Investment")
        self.assertEqual(data["accounts"][1]["opening_balance"], 149372.92)
        self.assertEqual(data["accounts"][1]["closing_balance"], 142417.29)
        self.assertTrue(all(product["reconciliation"]["is_reconciled"] for product in data["accounts"]))
        self.assertEqual(len(data["transactions"]), 5)
        transfers = [item for item in data["transactions"] if item["transaction_type"] == "Transfer"]
        self.assertEqual(len(transfers), 2)
        self.assertEqual(transfers[0]["source_product_id"], "nu-main")
        self.assertEqual(transfers[0]["destination_product_id"], "nu-cajitas")
        generated = next(item for item in data["transactions"] if item["title"] == "Dinero generado este mes")
        self.assertEqual(generated["source_product_id"], "nu-cajitas")
        self.assertEqual(generated["category"], "Investments")

        batch = create_import_batch(self.statement, data)
        self.assertEqual(batch.products.count(), 2)
        self.assertEqual(batch.candidates.count(), 5)

    def test_multi_product_transfers_preserve_net_worth_and_create_snapshots(self) -> None:
        data = normalize_multi_product_extraction({
            "statement_kind": "multi_product", "statement_period": {"start": "2026-08-01", "end": "2026-08-31"},
            "accounts": [
                {"source_product_id": "checking", "name": "Hey Smart", "product_type": "Checking", "opening_balance": "100.00", "closing_balance": "50.00", "reconciliation": {"is_reconciled": True}},
                {"source_product_id": "investment", "name": "Hey Pagaré", "product_type": "Investment", "opening_balance": "0.00", "closing_balance": "50.00", "reconciliation": {"is_reconciled": True}, "positions": [{"investment_id": "005", "total": 50}]},
            ],
            "transactions": [{"title": "Open investment", "transaction_type": "Transfer", "category": "Account Transfer", "date": "2026-08-04", "amount": "50.00", "source_product_id": "checking", "destination_product_id": "investment"}],
        })
        batch = create_import_batch(self.statement, data)
        checking = Account.objects.create(owner_user=self.user, account_name="Hey Smart", account_type="Checking", bank="Hey", total="100.00")
        investment = Account.objects.create(owner_user=self.user, account_name="Hey Pagaré", account_type="Investment", bank="Hey", total="0.00")
        result = commit_batch(self.user, batch.id, {"product_account_map": {str(product.id): str(checking.id if product.source_product_id == "checking" else investment.id) for product in batch.products.all()}})
        self.assertEqual(len(result["failed"]), 0)
        checking.refresh_from_db(); investment.refresh_from_db()
        self.assertEqual(str(checking.total), "50.00")
        self.assertEqual(str(investment.total), "50.00")
        self.assertEqual(ProductStatementSnapshot.objects.filter(account=checking).count(), 1)
        self.assertEqual(BankStatementImportProduct.objects.filter(import_batch=batch).count(), 2)

    def test_multi_product_account_details_and_transaction_assignment_are_editable(self) -> None:
        data = normalize_multi_product_extraction({
            "statement_kind": "multi_product", "account_name": "Hey Banco",
            "statement_period": {"start": "2026-08-01", "end": "2026-08-31"},
            "accounts": [
                {"source_product_id": "checking", "name": "Checking", "bank_name": "Hey", "product_type": "Checking", "opening_balance": "100.00", "closing_balance": "50.00", "reconciliation": {"opening_balance": 100, "closing_balance": 50, "cash_movements": -50, "valuation_change": 0}},
                {"source_product_id": "investment", "name": "Investment", "bank_name": "Hey", "product_type": "Investment", "opening_balance": "0.00", "closing_balance": "50.00", "reconciliation": {"opening_balance": 0, "closing_balance": 50, "cash_movements": 50, "valuation_change": 0}},
            ],
            "transactions": [{"title": "Fund investment", "transaction_type": "Transfer", "category": "Account Transfer", "date": "2026-08-04", "amount": "50.00", "source_product_id": "checking", "destination_product_id": "investment"}],
        })
        batch = create_import_batch(self.statement, data)
        checking = batch.products.get(source_product_id="checking")
        investment = batch.products.get(source_product_id="investment")
        candidate = batch.candidates.get()

        update_import_product(self.user, checking.id, {
            "name": "Everyday account", "bank_name": "Hey Banco", "product_type": "Checking",
            "opening_balance": "100.00", "closing_balance": "40.00",
        })
        update_import_product(self.user, investment.id, {
            "name": "Savings investment", "bank_name": "Hey Banco", "product_type": "Investment",
            "opening_balance": "0.00", "closing_balance": "60.00",
        })
        update_candidate(self.user, candidate.id, {
            "amount": "60.00", "source_product_id": "checking", "destination_product_id": "investment",
        })

        payload = batch_payload(batch)
        self.assertEqual(payload["products"][0]["name"], "Everyday account")
        self.assertEqual(payload["products"][0]["bank_name"], "Hey Banco")
        self.assertEqual(payload["products"][0]["calculated_closing_balance"], 40.0)
        self.assertEqual(payload["products"][1]["calculated_closing_balance"], 60.0)
        self.assertTrue(all(product["reconciliation"]["is_reconciled"] for product in payload["products"]))
        self.assertEqual(payload["candidates"][0]["source_product_id"], "checking")
        self.assertEqual(payload["candidates"][0]["destination_product_id"], "investment")

    def test_transfer_candidate_rejects_the_same_source_and_destination_account(self) -> None:
        batch = create_import_batch(self.statement, {
            "account_name": "Checking", "account_type": "Checking",
            "transactions": [{
                "title": "Outgoing transfer", "amount": "50.00", "date": "2026-08-04",
                "transaction_type": "Transfer", "category": "Account Transfer",
            }],
        })
        account = Account.objects.create(
            owner_user=self.user, account_name="Checking", account_type="Checking", bank="Hey", total="100.00"
        )

        with self.assertRaisesMessage(ValidationError, "Transfer source and destination accounts must be different"):
            update_candidate(self.user, batch.candidates.get().id, {
                "from_account_id": str(account.id), "to_account_id": str(account.id),
            })


class CreditCardDeferredPaymentImportTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="cardholder")
        self.statement = BankStatement.objects.create(owner_user=self.user, file=ContentFile(b"%PDF", name="banamex.pdf"), original_filename="banamex.pdf", file_size=4)

    def test_msi_schedule_is_metadata_and_ledger_reaches_verified_available_credit(self) -> None:
        data = normalize_credit_card_deferred_extraction({
            "statement_kind": "credit_card_deferred_payments", "account_name": "Banamex JOY", "account_type": "Credit Card",
            "statement_period": {"start": "2026-08-04", "end": "2026-09-03"},
            "card_summary": {"credit_limit": "49000.00", "available_credit": "29104.00", "opening_total_debt": "9000.00", "total_debt": "19896.00", "regular_debt": "14633.00", "deferred_balance": "5263.00", "statement_date": "2026-09-03"},
            "reconciliation": {"is_reconciled": True},
            "deferred_purchases": [{"merchant": "Liverpool", "original_amount": "1599.00", "remaining_balance": "799.50", "current_installment": "266.50", "installment_number": 3, "installment_count": 6}],
            "transactions": [
                {"title": "Card payment", "amount": "9000.00", "date": "2026-08-10", "transaction_type": "Income", "category": "Account Transfer"},
                {"title": "Purchases including MSI installments", "amount": "19896.00", "date": "2026-08-20", "transaction_type": "Expense", "category": "Shopping"},
            ],
        })
        self.assertTrue(data["reconciliation"]["is_reconciled"])
        self.assertFalse(data["deferred_purchases"][0]["importable"])
        batch = create_import_batch(self.statement, data)
        self.assertEqual(batch.candidates.count(), 2)
        account = Account.objects.create(owner_user=self.user, account_name="Banamex JOY", account_type="Credit Card", bank="Banamex", total="40000.00", credit_limit="49000.00")
        result = commit_batch(self.user, batch.id, {"account_id": account.id})
        self.assertEqual(len(result["failed"]), 0)
        account.refresh_from_db()
        self.assertEqual(str(account.total), "29104.00")
        self.assertEqual(CreditCardStatementSnapshot.objects.filter(account=account, import_batch=batch).count(), 1)
        self.assertEqual(DeferredPurchase.objects.filter(account=account).count(), 1)

    def test_card_with_missing_opening_debt_is_review_only(self) -> None:
        data = normalize_credit_card_deferred_extraction({
            "account_type": "Credit Card", "card_summary": {"credit_limit": 49000, "available_credit": 29104, "total_debt": 19896},
            "reconciliation": {"is_reconciled": True},
        })
        self.assertFalse(data["reconciliation"]["is_reconciled"])
        self.assertIsNone(data["initial_balance"])

    def test_msi_ordinal_is_not_misrepresented_as_a_currency_amount(self) -> None:
        data = normalize_credit_card_deferred_extraction({
            "account_type": "Credit Card",
            "card_summary": {},
            "deferred_purchases": [{"merchant": "Amazon", "current_installment": 6, "installment_count": 12}],
        })
        plan = data["deferred_purchases"][0]
        self.assertIsNone(plan["current_installment"])
        self.assertEqual(plan["installment_number"], 6)

    def test_reviewed_msi_details_can_be_updated_before_import(self) -> None:
        batch = create_import_batch(self.statement, {
            "statement_kind": "credit_card_deferred_payments",
            "deferred_purchases": [{"source_key": "amazon-1", "merchant": "Amazon", "remaining_balance": "600", "current_installment": "100", "installment_number": 2, "installment_count": 6}],
            "transactions": [],
        })
        updated = update_deferred_purchases(self.user, batch.id, [{
            "source_key": "amazon-1", "remaining_balance": "0", "current_installment": "125.50",
            "installment_number": 3, "installment_count": 6,
        }])
        plan = updated.deferred_purchases[0]
        self.assertEqual(plan["remaining_balance"], "0.00")
        self.assertEqual(plan["current_installment"], "125.50")
        self.assertEqual(plan["installment_number"], 3)
        self.assertEqual(plan["installment_count"], 6)

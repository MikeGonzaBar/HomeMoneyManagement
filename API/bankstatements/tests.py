from datetime import date, timedelta
import json
import time
from datetime import timedelta
from decimal import Decimal

import httpx

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import OperationalError, connection
from django.test import SimpleTestCase
from django.test.utils import CaptureQueriesContext, override_settings
from django.utils import timezone
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
    refresh_product_reconciliations,
    update_candidate,
    update_deferred_purchases,
    update_import_product,
)
from .tasks import process_bank_statement
from .management.commands.process_bank_statements import Command as ProcessStatementsCommand
from .services import (
    classify_gemini_error,
    GeminiRequestDeadlineExceeded,
    GeminiRateLimitedError,
    _build_local_analysis,
    _canonical_local_analysis,
    _fail_fast_on_gemini_rate_limit,
    _gemini_models_to_try,
    _is_transient_gemini_error,
    _local_analysis_comparison,
    _local_analysis_prompt_suffix,
    _run_with_gemini_deadline,
    process_bank_statement_with_ai,
    normalize_credit_card_deferred_extraction,
    normalize_multi_product_extraction,
    normalize_nu_cajitas_extraction,
    normalize_retirement_extraction,
)
from .tasks import _retry_delay_seconds


class LocalAnchorsTests(SimpleTestCase):
    clean_text = """
        RappiCard
        Periodo 07-ago-2026 al 06-sept-2026
        Límite de crédito $15,000.00
        Crédito disponible $203.64
        Saldo deudor total $14,796.36
    """

    def inspection(self, text: str, page_count: int = 1) -> dict:
        return {"text": text, "page_count": page_count, "status": "available", "reason_codes": []}

    def test_clean_credit_card_text_builds_bounded_deterministic_anchors(self) -> None:
        analysis = _build_local_analysis(self.inspection(self.clean_text))

        self.assertEqual(analysis["source_quality"]["status"], "usable")
        self.assertEqual(analysis["anchors"]["statement_period"], {"start": "2026-08-07", "end": "2026-09-06"})
        self.assertIn("rappi", analysis["document_markers"])
        self.assertEqual(
            analysis["anchors"]["balances"],
            [
                {"key": "credit_limit", "amount": "15000.00"},
                {"key": "available_credit", "amount": "203.64"},
                {"key": "total_debt", "amount": "14796.36"},
            ],
        )
        self.assertEqual(_canonical_local_analysis(analysis), _canonical_local_analysis(analysis))

    def test_multi_product_text_omits_generic_global_balances_and_keeps_portfolio_cross_check(self) -> None:
        analysis = _build_local_analysis(self.inspection("""
            GBM RESUMEN DEL PORTAFOLIO
            Saldo inicial $25,221.23
            Saldo final $25,029.11
            Valor del portafolio $25,029.11
        """))

        balances = analysis["anchors"].get("balances", [])
        self.assertEqual(balances, [{"key": "portfolio_total", "amount": "25029.11"}])

    def test_english_month_period_is_normalized_without_retaining_raw_text(self) -> None:
        analysis = _build_local_analysis(self.inspection("""
            Banamex statement period 04-Aug-2026 - 03-Sep-2026
            Saldo inicial $100.00
        """))

        self.assertEqual(analysis["anchors"]["statement_period"], {"start": "2026-08-04", "end": "2026-09-03"})

    def test_garbled_text_never_becomes_an_anchor_or_leaks_raw_content(self) -> None:
        secret = "CLABE 646180120620859617 MIGUEL GONZALEZ"
        analysis = _build_local_analysis(self.inspection(("\ufffd" * 300) + secret))

        self.assertEqual(analysis["source_quality"]["status"], "limited")
        self.assertEqual(analysis["anchors"], {})
        serialized = _canonical_local_analysis(analysis)
        self.assertNotIn("646180120620859617", serialized)
        self.assertNotIn("MIGUEL", serialized)

    def test_comparison_uses_only_safe_result_paths(self) -> None:
        analysis = _build_local_analysis(self.inspection(self.clean_text))
        comparison = _local_analysis_comparison(analysis, {
            "statement_period": {"start": "2026-08-07", "end": "2026-09-06"},
            "card_summary": {"credit_limit": 15000, "available_credit": 203.64, "total_debt": 14796.36},
            "reconciliation": {},
        })
        self.assertEqual(comparison, {"matched": 4, "mismatched": 0, "not_comparable": 0})

    def test_prompt_suffix_contains_only_canonical_analysis_and_integrity_rules(self) -> None:
        analysis = _build_local_analysis(self.inspection(self.clean_text))
        suffix = _local_analysis_prompt_suffix(analysis)

        self.assertIn("LOCAL_ANALYSIS", suffix)
        self.assertIn("PDF remains authoritative", suffix)
        self.assertNotIn(self.clean_text.strip(), suffix)
        self.assertIn(_canonical_local_analysis(analysis), suffix)


class LocalAnchorsServiceTests(SimpleTestCase):
    inspection = {
        "text": "RappiCard Periodo 07-ago-2026 al 06-sept-2026 Límite de crédito $15,000.00 Crédito disponible $203.64 Saldo deudor total $14,796.36",
        "page_count": 1,
        "status": "available",
        "reason_codes": [],
    }
    response_payload = {
        "transactions": [], "account_name": "RappiCard", "account_type": "Credit Card",
        "statement_period": {"start": "2026-08-07", "end": "2026-09-06"},
        "card_summary": {"credit_limit": 15000, "available_credit": 203.64, "total_debt": 14796.36},
    }

    def _client(self) -> Mock:
        client = Mock()
        uploaded = Mock(uri="gs://statement", mime_type="application/pdf", state="ACTIVE")
        client.files.upload.return_value = uploaded
        client.interactions.create.return_value = Mock(output_text=json.dumps(self.response_payload))
        return client

    @override_settings(GOOGLE_AI_API_KEY="test-key", GOOGLE_AI_MODEL="test-model", GOOGLE_AI_FALLBACK_MODELS="")
    @patch("bankstatements.services._inspect_local_pdf")
    @patch("bankstatements.services.google_genai.Client")
    def test_observe_mode_does_not_change_gemini_prompt(self, client_factory: Mock, inspect: Mock) -> None:
        inspect.return_value = self.inspection
        client = self._client()
        client_factory.return_value = client
        with self.settings(GOOGLE_AI_LOCAL_ANCHORS_MODE="observe"):
            result = process_bank_statement_with_ai("ignored.pdf")

        prompt = client.interactions.create.call_args.kwargs["input"][1]["text"]
        self.assertNotIn("LOCAL_ANALYSIS", prompt)
        self.assertIn("GBM / BROKERAGE REVIEW REQUIREMENT", prompt)
        self.assertIn("If a counterpart or ownership is unresolved, preserve the movement in", prompt)
        self.assertIsNone(result["error"])
        client.files.delete.assert_called_once()
        client_factory.assert_called_once()
        client_options = client_factory.call_args.kwargs
        self.assertEqual(client_options["api_key"], "test-key")
        self.assertEqual(client_options["http_options"]["timeout"], 120000)
        self.assertEqual(client_options["http_options"]["retry_options"], {"attempts": 1})
        self.assertIsInstance(client_options["http_options"]["httpx_client"], httpx.Client)

    @override_settings(GOOGLE_AI_API_KEY="test-key", GOOGLE_AI_MODEL="test-model", GOOGLE_AI_FALLBACK_MODELS="")
    @patch("bankstatements.services._inspect_local_pdf")
    @patch("bankstatements.services.google_genai.Client")
    def test_send_mode_adds_bounded_analysis_without_changing_document_input(self, client_factory: Mock, inspect: Mock) -> None:
        inspect.return_value = self.inspection
        client = self._client()
        client_factory.return_value = client
        with self.settings(GOOGLE_AI_LOCAL_ANCHORS_MODE="send"):
            process_bank_statement_with_ai("ignored.pdf")

        request_input = client.interactions.create.call_args.kwargs["input"]
        self.assertEqual(request_input[0]["type"], "document")
        self.assertIn("LOCAL_ANALYSIS", request_input[1]["text"])
        self.assertNotIn(self.inspection["text"], request_input[1]["text"])

    @override_settings(GOOGLE_AI_API_KEY="test-key", GOOGLE_AI_MODEL="test-model", GOOGLE_AI_FALLBACK_MODELS="")
    @patch("bankstatements.services._inspect_local_pdf")
    @patch("bankstatements.services.google_genai.Client")
    def test_rate_limit_returns_to_task_retry_path_without_sdk_backoff(self, client_factory: Mock, inspect: Mock) -> None:
        inspect.return_value = self.inspection
        client = self._client()
        client.interactions.create.side_effect = Exception("429 RESOURCE_EXHAUSTED")
        client_factory.return_value = client

        result = process_bank_statement_with_ai("ignored.pdf")

        self.assertEqual(result["failure_class"], "rate_limited")
        self.assertIn("AI processing failed", result["error"])
        self.assertEqual(client.interactions.create.call_count, 2)
        client.files.delete.assert_called_once()


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

    def test_assignment_draft_is_owner_scoped_and_serialized(self) -> None:
        account = Account.objects.create(
            owner_user=self.alice, account_name="MiCuenta", account_type="Checking", bank="Banamex", total="0.00"
        )
        batch = BankStatementImportBatch.objects.create(
            bank_statement=self.alice_statement, owner_user=self.alice,
            detected_account_name="MiCuenta", detected_account_type="Checking",
        )

        response = self.client.patch(
            f"/bank-statements/import-batches/{batch.id}/assignment/", {"account_id": str(account.id)}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        batch.refresh_from_db()
        self.assertEqual(batch.draft_account_id, account.id)
        self.assertEqual(response.data["import_batch"]["draft_assignment"]["account_name"], "MiCuenta")
        list_response = self.client.get("/bank-statements/user/alice/")
        self.assertEqual(list_response.data["statements"][0]["review_draft_assignment"]["account_id"], account.id)

    def test_new_account_draft_can_be_saved_and_cleared_without_creating_account(self) -> None:
        batch = BankStatementImportBatch.objects.create(bank_statement=self.alice_statement, owner_user=self.alice)
        response = self.client.patch(
            f"/bank-statements/import-batches/{batch.id}/assignment/",
            {"new_account": {"name": "Future account", "bank": "Banamex", "account_type": "Checking"}}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Account.objects.filter(owner_user=self.alice).count(), 0)
        self.assertEqual(response.data["import_batch"]["draft_assignment"]["kind"], "new")

        clear_response = self.client.patch(
            f"/bank-statements/import-batches/{batch.id}/assignment/", {"account_id": "", "new_account": None}, format="json"
        )
        self.assertEqual(clear_response.status_code, 200)
        self.assertIsNone(clear_response.data["import_batch"]["draft_assignment"])

    def test_zero_candidate_batch_exposes_safe_scan_summary(self) -> None:
        batch = create_import_batch(self.alice_statement, {
            "transactions": [], "account_name": "MiCuenta", "account_type": "Checking", "statement_period": {},
        })
        response = self.client.get(f"/bank-statements/import-batches/{batch.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["scan_summary"]["importable_candidate_count"], 0)
        self.assertTrue(response.data["scan_summary"]["zero_result_reason"])

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
        self.alice_statement.retry_count = 3
        self.alice_statement.next_retry_at = timezone.now() + timedelta(hours=1)
        self.alice_statement.failure_class = "timeout"
        self.alice_statement.save(update_fields=["processing_status", "processed", "error_message", "retry_count", "next_retry_at", "failure_class"])

        response = self.client.post(f"/bank-statements/retry/{self.alice_statement.id}/")

        self.assertEqual(response.status_code, 202)
        self.alice_statement.refresh_from_db()
        self.assertEqual(self.alice_statement.processing_status, "pending")
        self.assertIsNone(self.alice_statement.error_message)
        self.assertEqual(self.alice_statement.retry_count, 0)
        self.assertIsNone(self.alice_statement.next_retry_at)
        self.assertEqual(self.alice_statement.failure_class, "")

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
        self.assertEqual(statement.processing_status, "pending")
        self.assertEqual(statement.failure_class, "rate_limited")
        self.assertIsNotNone(statement.next_retry_at)

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

    def test_rate_limit_retry_delay_is_parsed(self) -> None:
        failure_class, retry_after = classify_gemini_error(
            "429 rate limit exceeded; please retry in 1h2m3s"
        )
        self.assertEqual(failure_class, "rate_limited")
        self.assertEqual(retry_after, 3723)

    def test_rate_limit_header_fails_fast_and_preserves_retry_after(self) -> None:
        response = httpx.Response(
            429,
            headers={"Retry-After": "180"},
            request=httpx.Request("POST", "https://example.test/interactions"),
        )

        with self.assertRaises(GeminiRateLimitedError) as captured:
            _fail_fast_on_gemini_rate_limit(response)

        self.assertTrue(response.is_closed)
        self.assertEqual(captured.exception.retry_after_seconds, 180)
        self.assertEqual(classify_gemini_error(captured.exception), ("rate_limited", 180))

    def test_timeout_and_invalid_request_are_classified_safely(self) -> None:
        self.assertEqual(classify_gemini_error("Request timed out")[0], "timeout")
        self.assertEqual(classify_gemini_error("400 invalid argument")[0], "permanent")

    def test_deadline_guard_returns_successful_call_result(self) -> None:
        self.assertEqual(_run_with_gemini_deadline(lambda: "ok", 1), "ok")

    def test_deadline_guard_interrupts_a_stalled_call(self) -> None:
        with self.assertRaises(GeminiRequestDeadlineExceeded):
            _run_with_gemini_deadline(lambda: time.sleep(2), 1)

    @override_settings(GOOGLE_AI_REQUEST_TIMEOUT=20)
    def test_request_timeout_is_configured(self) -> None:
        from django.conf import settings

        self.assertEqual(settings.GOOGLE_AI_REQUEST_TIMEOUT, 20)

    @override_settings(GOOGLE_AI_MODEL="gemini-3.8-flash", GOOGLE_AI_FALLBACK_MODELS="")
    def test_default_fallbacks_only_include_available_models(self) -> None:
        models = _gemini_models_to_try()
        self.assertEqual(models, ["gemini-3.8-flash", "gemini-3.5-flash-lite"])


class AutomaticStatementRetryTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="retry-user")
        self.statement = BankStatement.objects.create(
            owner_user=self.user,
            file=ContentFile(b"%PDF-1.4\n", name="retry.pdf"),
            original_filename="retry.pdf",
            file_size=9,
        )

    @override_settings(
        BANK_STATEMENT_MAX_AUTO_RETRIES=3,
        BANK_STATEMENT_RETRY_BASE_SECONDS=60,
        BANK_STATEMENT_RATE_LIMIT_RETRY_BASE_SECONDS=300,
        BANK_STATEMENT_RATE_LIMIT_JITTER_SECONDS=0,
    )
    @patch("bankstatements.tasks.extract_transactions_from_pdf")
    def test_timeout_is_scheduled_with_bounded_automatic_retry(self, mock_extract: Mock) -> None:
        mock_extract.return_value = {
            "error": "AI processing failed: Request timed out",
            "failure_class": "timeout",
        }

        process_bank_statement(self.statement.id)

        self.statement.refresh_from_db()
        self.assertEqual(self.statement.processing_status, "pending")
        self.assertEqual(self.statement.retry_count, 1)
        self.assertEqual(self.statement.failure_class, "timeout")
        self.assertIsNotNone(self.statement.next_retry_at)
        self.assertGreater(self.statement.next_retry_at, timezone.now())

    @override_settings(
        BANK_STATEMENT_MAX_AUTO_RETRIES=3,
        BANK_STATEMENT_RATE_LIMIT_RETRY_BASE_SECONDS=300,
        BANK_STATEMENT_RATE_LIMIT_JITTER_SECONDS=0,
    )
    @patch("bankstatements.tasks.extract_transactions_from_pdf")
    def test_rate_limit_is_scheduled_for_automatic_retry(self, mock_extract: Mock) -> None:
        mock_extract.return_value = {
            "error": "AI processing failed: 429 RESOURCE_EXHAUSTED",
            "failure_class": "rate_limited",
        }

        process_bank_statement(self.statement.id)

        self.statement.refresh_from_db()
        self.assertEqual(self.statement.processing_status, "pending")
        self.assertEqual(self.statement.retry_count, 1)
        self.assertEqual(self.statement.failure_class, "rate_limited")
        self.assertIsNotNone(self.statement.next_retry_at)

    @override_settings(
        BANK_STATEMENT_MAX_AUTO_RETRIES=3,
        BANK_STATEMENT_RATE_LIMIT_RETRY_BASE_SECONDS=300,
        BANK_STATEMENT_RATE_LIMIT_JITTER_SECONDS=0,
    )
    @patch("bankstatements.tasks.extract_transactions_from_pdf")
    def test_rate_limit_pauses_all_pending_statement_jobs(self, mock_extract: Mock) -> None:
        queued = BankStatement.objects.create(
            owner_user=self.user,
            file=ContentFile(b"%PDF-1.4\n", name="queued.pdf"),
            original_filename="queued.pdf",
            file_size=9,
        )
        mock_extract.return_value = {
            "error": "AI processing failed: Gemini rate limited the request (HTTP 429)",
            "failure_class": "rate_limited",
        }

        process_bank_statement(self.statement.id)

        self.statement.refresh_from_db()
        queued.refresh_from_db()
        self.assertEqual(self.statement.processing_status, "pending")
        self.assertEqual(queued.processing_status, "pending")
        self.assertEqual(queued.next_retry_at, self.statement.next_retry_at)
        self.assertGreater(queued.next_retry_at, timezone.now() + timedelta(minutes=4))

    def test_provider_retry_after_is_used_without_jitter(self) -> None:
        self.assertEqual(_retry_delay_seconds(1, 180, "rate_limited"), 180)

    @patch("bankstatements.tasks.extract_transactions_from_pdf")
    def test_deletion_while_processing_discards_extraction_result(self, mock_extract: Mock) -> None:
        def delete_before_result(_file_path: str) -> dict:
            BankStatement.objects.filter(id=self.statement.id).delete()
            return {
                "transactions": [],
                "account_name": "Deleted statement",
                "account_type": "Checking",
                "statement_period": None,
                "initial_balance": None,
            }

        mock_extract.side_effect = delete_before_result

        process_bank_statement(self.statement.id)

        self.assertFalse(BankStatement.objects.filter(id=self.statement.id).exists())
        self.assertFalse(BankStatementImportBatch.objects.filter(bank_statement_id=self.statement.id).exists())

    def test_deleted_pending_statement_is_not_claimed_from_the_queue(self) -> None:
        self.statement.delete()

        self.assertIsNone(ProcessStatementsCommand._claim_next())

    @override_settings(BANK_STATEMENT_MAX_AUTO_RETRIES=3)
    @patch("bankstatements.tasks.extract_transactions_from_pdf")
    def test_non_transient_error_fails_without_automatic_retry(self, mock_extract: Mock) -> None:
        mock_extract.return_value = {
            "error": "AI processing failed: invalid PDF request",
            "failure_class": "permanent",
        }

        process_bank_statement(self.statement.id)

        self.statement.refresh_from_db()
        self.assertEqual(self.statement.processing_status, "failed")
        self.assertEqual(self.statement.retry_count, 0)
        self.assertIsNone(self.statement.next_retry_at)

    @override_settings(BANK_STATEMENT_MAX_AUTO_RETRIES=3)
    @patch("bankstatements.tasks.extract_transactions_from_pdf")
    def test_retry_exhaustion_becomes_terminal_failure(self, mock_extract: Mock) -> None:
        self.statement.retry_count = 3
        self.statement.save(update_fields=["retry_count"])
        mock_extract.return_value = {
            "error": "AI processing failed: service unavailable",
            "failure_class": "provider_unavailable",
        }

        process_bank_statement(self.statement.id)

        self.statement.refresh_from_db()
        self.assertEqual(self.statement.processing_status, "failed")
        self.assertIn("automatic retries", self.statement.error_message)

    def test_claim_skips_future_retry_and_claims_due_statement(self) -> None:
        self.statement.next_retry_at = timezone.now() + timedelta(minutes=5)
        self.statement.save(update_fields=["next_retry_at"])
        due_statement = BankStatement.objects.create(
            owner_user=self.user,
            file=ContentFile(b"%PDF-1.4\n", name="due.pdf"),
            original_filename="due.pdf",
            file_size=9,
            next_retry_at=timezone.now() - timedelta(seconds=1),
        )

        claimed_id = ProcessStatementsCommand._claim_next()

        self.assertEqual(claimed_id, due_statement.id)
        self.statement.refresh_from_db()
        self.assertEqual(self.statement.processing_status, "pending")

    @patch("bankstatements.management.commands.process_bank_statements.close_old_connections")
    @patch("bankstatements.management.commands.process_bank_statements.time.sleep")
    @patch.object(ProcessStatementsCommand, "_claim_next")
    def test_db_outage_waits_and_retries_instead_of_crashing(
        self, mock_claim: Mock, mock_sleep: Mock, mock_close: Mock
    ) -> None:
        """A PostgreSQL DNS outage must not kill the worker loop (regression)."""
        outcomes = iter([
            OperationalError('could not translate host name "postgres" to address'),
            None,
        ])

        def fake_claim() -> int | None:
            outcome = next(outcomes)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        mock_claim.side_effect = fake_claim

        call_command("process_bank_statements", "--once")

        self.assertEqual(mock_claim.call_count, 2)
        mock_sleep.assert_called_once_with(1.0)


class WorkerLoggingTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="worker-log-user")
        self.statement = BankStatement.objects.create(
            owner_user=self.user, file=ContentFile(b"%PDF-1.4\n", name="log.pdf"),
            original_filename="log.pdf", file_size=9,
        )

    @patch.object(ProcessStatementsCommand, "_claim_next", return_value=None)
    def test_worker_startup_is_logged(self, _mock_claim: Mock) -> None:
        """An idle worker must still prove it is alive in `docker compose logs`."""
        with self.assertLogs(
            "bankstatements.management.commands.process_bank_statements", level="INFO"
        ) as captured:
            call_command("process_bank_statements", "--once")
        self.assertTrue(any("started" in message for message in captured.output))

    @patch("bankstatements.tasks.create_import_batch")
    @patch("bankstatements.tasks.extract_transactions_from_pdf", return_value={})
    def test_statement_processing_start_and_completion_are_logged(
        self, _mock_extract: Mock, _mock_create: Mock
    ) -> None:
        with self.assertLogs("bankstatements.tasks", level="INFO") as captured:
            process_bank_statement(self.statement.id)
        output = "\n".join(captured.output)
        self.assertIn("processing started", output)
        self.assertIn("processing completed", output)
        self.statement.refresh_from_db()
        self.assertEqual(self.statement.processing_status, "completed")



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

    def test_product_with_balances_but_no_reconciliation_requires_review(self) -> None:
        data = normalize_multi_product_extraction({
            "statement_kind": "multi_product",
            "extraction_status": "complete",
            "accounts": [
                {
                    "source_product_id": "gbm-cash",
                    "name": "EFECTIVO",
                    "product_type": "Efectivo",
                    "opening_balance": "0.87",
                    "closing_balance": "0.88",
                },
            ],
        })

        product = data["accounts"][0]
        self.assertFalse(product["reconciliation"]["is_reconciled"])
        self.assertIn("no product-level reconciliation", product["reconciliation"]["reason"])
        self.assertEqual(data["extraction_status"], "needs_review")
        self.assertEqual(data["extraction_issues"][0]["type"], "missing_product_reconciliation")

    def test_external_cash_adjustments_reconcile_cash_without_an_invented_counterpart(self) -> None:
        batch = create_import_batch(self.statement, {
            "statement_kind": "multi_product",
            "statement_period": {"start": "2026-08-01", "end": "2026-08-31"},
            "accounts": [
                {"source_product_id": "cash", "name": "Efectivo", "product_type": "Cash", "opening_balance": "0.87", "closing_balance": "0.88"},
                {"source_product_id": "fund", "name": "MPAGORF B1", "product_type": "Investment", "opening_balance": "25220.37", "closing_balance": "25028.24", "reconciliation": {"valuation_change": "97.57"}},
            ],
            "transactions": [
                {"title": "Fund sale", "amount": "299.10", "date": "2026-08-27", "transaction_type": "Transfer", "category": "Account Transfer", "source_product_id": "fund", "destination_product_id": "cash"},
                {"title": "External cash withdrawal", "amount": "299.10", "date": "2026-08-27", "transaction_type": "External Withdrawal", "category": "External cash adjustment", "source_product_id": "cash"},
                {"title": "Fund purchase", "amount": "4.70", "date": "2026-08-28", "transaction_type": "Transfer", "category": "Account Transfer", "source_product_id": "cash", "destination_product_id": "fund"},
                {"title": "External cash deposit", "amount": "4.70", "date": "2026-08-28", "transaction_type": "External Deposit", "category": "External cash adjustment", "source_product_id": "cash"},
                {"title": "Fund purchase", "amount": "4.70", "date": "2026-08-31", "transaction_type": "Transfer", "category": "Account Transfer", "source_product_id": "cash", "destination_product_id": "fund"},
                {"title": "External cash deposit", "amount": "4.71", "date": "2026-08-31", "transaction_type": "External Deposit", "category": "External cash adjustment", "source_product_id": "cash"},
            ],
        })

        refresh_product_reconciliations(batch)
        products = {product.source_product_id: product for product in batch.products.all()}
        products["cash"].refresh_from_db()
        products["fund"].refresh_from_db()
        self.assertTrue(products["cash"].reconciliation["is_reconciled"])
        self.assertTrue(products["fund"].reconciliation["is_reconciled"])
        self.assertEqual(products["cash"].reconciliation["cash_movements"], 0.01)
        self.assertEqual(products["fund"].reconciliation["cash_movements"], -289.7)

    def test_skipped_unresolved_diagnostic_does_not_block_external_cash_deposit_commit(self) -> None:
        """A reviewer can skip an AI diagnostic without blocking valid GBM cash rows."""
        batch = create_import_batch(self.statement, {
            "statement_kind": "multi_product",
            "statement_period": {"start": "2026-08-01", "end": "2026-08-31"},
            "accounts": [
                {"source_product_id": "cash", "name": "Efectivo", "product_type": "Cash", "opening_balance": "0.00", "closing_balance": "4.70", "reconciliation": {"is_reconciled": True}},
                {"source_product_id": "fund", "name": "MPAGORF B1", "product_type": "Investment", "opening_balance": "0.00", "closing_balance": "0.00", "reconciliation": {"is_reconciled": True}},
            ],
            "transactions": [
                {
                    "title": "ABONO DE EFECTIVO", "amount": "4.70", "date": "2026-08-28",
                    "transaction_type": "External Deposit", "category": "External cash adjustment",
                    "destination_product_id": "cash",
                },
            ],
            "unresolved_transfers": [
                {
                    "title": "Unverified external source", "amount": "4.70", "date": "2026-08-28",
                    "source_product_id": None, "destination_product_id": "cash",
                },
            ],
        })
        batch.candidates.filter(raw_data__unresolved_transfer=True).update(
            status=BankStatementTransactionCandidate.STATUS_SKIPPED
        )
        cash = Account.objects.create(owner_user=self.user, account_name="Efectivo", account_type="Cash", bank="GBM", total="0.00")
        fund = Account.objects.create(owner_user=self.user, account_name="MPAGORF B1", account_type="Investment", bank="GBM", total="0.00")

        product_map = {
            str(product.id): str(cash.id if product.source_product_id == "cash" else fund.id)
            for product in batch.products.all()
        }
        result = commit_batch(self.user, batch.id, {"product_account_map": product_map})

        self.assertEqual(result["failed"], [])
        cash.refresh_from_db()
        self.assertEqual(str(cash.total), "4.70")

    def test_multi_product_commit_applies_verified_valuation_without_creating_income(self) -> None:
        batch = create_import_batch(self.statement, {
            "statement_kind": "multi_product",
            "statement_period": {"start": "2026-08-01", "end": "2026-08-31"},
            "accounts": [
                {
                    "source_product_id": "fund", "name": "MPAGORF B1", "product_type": "Investment",
                    "opening_balance": "100.00", "closing_balance": "110.00",
                    "reconciliation": {"is_reconciled": True, "valuation_change": "10.00"},
                },
            ],
            "transactions": [],
        })
        fund = Account.objects.create(
            owner_user=self.user, account_name="MPAGORF B1", account_type="Investment", bank="GBM", total="100.00"
        )
        product = batch.products.get(source_product_id="fund")

        result = commit_batch(self.user, batch.id, {"product_account_map": {str(product.id): str(fund.id)}})

        self.assertEqual(result["failed"], [])
        fund.refresh_from_db()
        self.assertEqual(str(fund.total), "110.00")
        self.assertFalse(Transaction.objects.filter(owner_user=self.user).exists())
        self.assertTrue(ProductStatementSnapshot.objects.filter(import_product=product, closing_balance="110.00").exists())

    def test_multi_product_commit_creates_requested_accounts_atomically(self) -> None:
        """New product accounts are materialized by commit, not by the browser."""
        batch = create_import_batch(self.statement, {
            "statement_kind": "multi_product",
            "statement_period": {"start": "2026-08-01", "end": "2026-08-31"},
            "accounts": [
                {"source_product_id": "cash", "name": "Cash sleeve", "bank_name": "GBM", "product_type": "Cash", "opening_balance": "10.00", "closing_balance": "5.00", "reconciliation": {"is_reconciled": True}},
                {"source_product_id": "fund", "name": "Fund sleeve", "bank_name": "GBM", "product_type": "Investment", "opening_balance": "0.00", "closing_balance": "5.00", "reconciliation": {"is_reconciled": True}},
            ],
            "transactions": [{"title": "Invest", "transaction_type": "Transfer", "category": "Account Transfer", "date": "2026-08-02", "amount": "5.00", "source_product_id": "cash", "destination_product_id": "fund"}],
        })
        product_ids = [product.id for product in batch.products.order_by("id")]

        result = commit_batch(self.user, batch.id, {"new_product_ids": product_ids})

        self.assertEqual(result["failed"], [])
        accounts = Account.objects.filter(owner_user=self.user, bank="GBM").order_by("account_name")
        self.assertEqual([(account.account_name, str(account.total)) for account in accounts], [("Cash sleeve", "5.00"), ("Fund sleeve", "5.00")])
        self.assertEqual(batch.products.filter(linked_account__isnull=True).count(), 0)

    def test_multi_product_transfer_can_use_an_existing_external_account(self) -> None:
        """A statement product can receive a transfer from another owned account."""
        batch = create_import_batch(self.statement, {
            "statement_kind": "multi_product",
            "statement_period": {"start": "2026-08-01", "end": "2026-08-31"},
            "accounts": [{"source_product_id": "nu-main", "name": "Cuenta Nu", "bank_name": "Nu", "product_type": "Checking", "opening_balance": "0.00", "closing_balance": "299.88", "reconciliation": {"is_reconciled": True}}],
            "transactions": [{"title": "Mercado Pago transfer", "transaction_type": "Transfer", "category": "Account Transfer", "date": "2026-08-26", "amount": "299.88", "destination_product_id": "nu-main"}],
        })
        mercado_pago = Account.objects.create(owner_user=self.user, account_name="Mercado Pago", account_type="Checking", bank="Mercado Pago", total="299.88")
        cuenta_nu = Account.objects.create(owner_user=self.user, account_name="Cuenta Nu", account_type="Checking", bank="Nu", total="0.00")
        candidate = batch.candidates.get()

        update_candidate(self.user, candidate.id, {"from_account_id": str(mercado_pago.id)})
        product = batch.products.get(source_product_id="nu-main")
        result = commit_batch(self.user, batch.id, {"product_account_map": {str(product.id): str(cuenta_nu.id)}})

        self.assertEqual(result["failed"], [])
        mercado_pago.refresh_from_db()
        cuenta_nu.refresh_from_db()
        self.assertEqual(str(mercado_pago.total), "0.00")
        self.assertEqual(str(cuenta_nu.total), "299.88")

    def test_multi_product_failed_commit_rolls_back_new_accounts(self) -> None:
        """A failure after account creation cannot leave empty duplicate accounts."""
        batch = create_import_batch(self.statement, {
            "statement_kind": "multi_product",
            "statement_period": {"start": "2026-08-01", "end": "2026-08-31"},
            "accounts": [
                {"source_product_id": "cash", "name": "Rollback cash", "bank_name": "GBM", "product_type": "Cash", "opening_balance": "10.00", "closing_balance": "5.00", "reconciliation": {"is_reconciled": True}},
                {"source_product_id": "fund", "name": "Rollback fund", "bank_name": "GBM", "product_type": "Investment", "opening_balance": "0.00", "closing_balance": "5.00", "reconciliation": {"is_reconciled": True}},
            ],
            "transactions": [{"title": "Broken transfer", "transaction_type": "Transfer", "category": "Account Transfer", "date": "2026-08-02", "amount": "5.00", "source_product_id": "cash", "destination_product_id": "cash"}],
        })
        product_ids = [product.id for product in batch.products.order_by("id")]

        with self.assertRaises(ValidationError):
            commit_batch(self.user, batch.id, {"new_product_ids": product_ids})

        self.assertFalse(Account.objects.filter(owner_user=self.user, account_name__startswith="Rollback ").exists())
        self.assertEqual(batch.products.filter(linked_account__isnull=False).count(), 0)

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


class BatchDraftTransferTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="draft-transfer-user")
        self.statement = BankStatement.objects.create(
            owner_user=self.user, file=ContentFile(b"%PDF", name="statement.pdf"),
            original_filename="statement.pdf", file_size=4,
        )

    def test_transfer_can_use_new_statement_account_as_destination_at_commit(self) -> None:
        source = Account.objects.create(
            owner_user=self.user, account_name="Source", account_type="Checking", bank="Banamex", total="1000.00",
        )
        batch = create_import_batch(self.statement, {
            "account_name": "Future savings", "account_type": "Savings", "initial_balance": "0.00",
            "transactions": [{
                "title": "Fund savings", "amount": "125.00", "date": "2026-08-20",
                "transaction_type": "Transfer", "category": "Account Transfer",
            }],
        })
        batch.draft_new_account = {"name": "Future savings", "bank": "Banamex", "account_type": "Savings"}
        batch.save(update_fields=["draft_new_account", "updated_at"])
        candidate = batch.candidates.get()

        update_candidate(self.user, candidate.id, {
            "from_account_id": str(source.id),
            "to_uses_batch_draft": True,
        })
        candidate.refresh_from_db()
        self.assertTrue(candidate.to_uses_batch_draft)
        self.assertIsNone(candidate.to_account_fk_id)
        self.assertTrue(batch_payload(batch)["candidates"][0]["to_uses_batch_draft"])

        result = commit_batch(self.user, batch.id, {"new_account_initial_balance": "0.00"})

        batch.refresh_from_db()
        candidate.refresh_from_db()
        destination = Account.objects.get(owner_user=self.user, account_name="Future savings")
        self.assertEqual(batch.status, BankStatementImportBatch.STATUS_COMMITTED)
        self.assertEqual(batch.linked_account_id, destination.id)
        self.assertFalse(candidate.to_uses_batch_draft)
        self.assertEqual(candidate.to_account_fk_id, destination.id)
        self.assertEqual(result["failed"], [])
        transaction = Transaction.objects.get(owner_user=self.user, title="Fund savings")
        self.assertEqual(transaction.from_account_fk_id, source.id)
        self.assertEqual(transaction.to_account_fk_id, destination.id)

    def test_same_batch_draft_at_both_transfer_ends_is_rejected(self) -> None:
        batch = create_import_batch(self.statement, {
            "transactions": [{
                "title": "Invalid transfer", "amount": "50.00", "date": "2026-08-20",
                "transaction_type": "Transfer", "category": "Account Transfer",
            }],
        })
        batch.draft_new_account = {"name": "Future account", "bank": "Banamex", "account_type": "Checking"}
        batch.save(update_fields=["draft_new_account", "updated_at"])

        with self.assertRaisesMessage(ValidationError, "Transfer source and destination accounts must be different"):
            update_candidate(self.user, batch.candidates.get().id, {
                "from_uses_batch_draft": True,
                "to_uses_batch_draft": True,
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

    def test_new_reconciled_card_uses_verified_opening_available_credit(self) -> None:
        data = normalize_credit_card_deferred_extraction({
            "statement_kind": "credit_card_deferred_payments", "account_name": "New card", "account_type": "Credit Card",
            "statement_period": {"start": "2026-08-04", "end": "2026-09-03"},
            "card_summary": {"credit_limit": "49000.00", "available_credit": "29104.00", "opening_total_debt": "9000.00", "total_debt": "19896.00", "regular_debt": "14633.00", "deferred_balance": "5263.00", "statement_date": "2026-09-03"},
            "reconciliation": {"is_reconciled": True},
            "transactions": [
                {"title": "Card payment", "amount": "9000.00", "date": "2026-08-10", "transaction_type": "Income", "category": "Account Transfer"},
                {"title": "Purchases", "amount": "19896.00", "date": "2026-08-20", "transaction_type": "Expense", "category": "Shopping"},
            ],
        })
        batch = create_import_batch(self.statement, data)
        batch.draft_new_account = {"name": "New card", "bank": "Banamex", "account_type": "Credit Card"}
        batch.save(update_fields=["draft_new_account", "updated_at"])

        result = commit_batch(self.user, batch.id, {"new_account_initial_balance": "29104.00"})

        self.assertEqual(len(result["failed"]), 0)
        account = Account.objects.get(owner_user=self.user, account_name="New card")
        self.assertEqual(str(account.total), "29104.00")
        self.assertEqual(str(account.credit_limit), "49000.00")

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

    def _unreconciled_joy_batch(self):
        """Build a Banamex JOY card batch like the audited one: four MSI plans,
        an unreconciled card summary, and the four already-posted installments."""
        data = normalize_credit_card_deferred_extraction({
            "statement_kind": "credit_card_deferred_payments", "account_name": "JOY BANAMEX",
            "account_type": "Credit Card",
            "statement_period": {"start": "2026-08-04", "end": "2026-09-03"},
            "card_summary": {"credit_limit": "49000.00", "available_credit": "29104.00",
                             "total_debt": "19896.44", "regular_debt": "14632.87",
                             "deferred_balance": "5263.57", "statement_date": "2026-09-03"},
            "reconciliation": {"is_reconciled": False},
            "deferred_purchases": [
                {"merchant": "LIV GDL GRAN PLAZA", "original_amount": "1599.00", "remaining_balance": "799.50", "current_installment": "266.50", "installment_number": 3, "installment_count": 6},
                {"merchant": "IS PLUS LA PERLA", "original_amount": "2648.00", "remaining_balance": "1765.33", "current_installment": "882.67", "installment_number": 1, "installment_count": 3},
                {"merchant": "FARM GUADALAJARA 19", "original_amount": "1549.36", "remaining_balance": "1032.91", "current_installment": "516.45", "installment_number": 1, "installment_count": 3},
                {"merchant": "MERPAGO*CONVERSE", "original_amount": "1999.00", "remaining_balance": "1665.83", "current_installment": "333.17", "installment_number": 1, "installment_count": 6},
            ],
            "transactions": [
                {"title": "LIV GDL GRAN PLAZA 003 de 006", "amount": "266.50", "date": "2026-08-20", "transaction_type": "Expense", "category": "Shopping"},
                {"title": "IS PLUS LA PERLA 001 de 003", "amount": "882.67", "date": "2026-08-20", "transaction_type": "Expense", "category": "Shopping"},
                {"title": "FARM GUADALAJARA 19 001 de 003", "amount": "516.45", "date": "2026-08-20", "transaction_type": "Expense", "category": "Shopping"},
                {"title": "MERPAGO*CONVERSE 001 de 006", "amount": "333.17", "date": "2026-08-20", "transaction_type": "Expense", "category": "Shopping"},
            ],
        })
        return create_import_batch(self.statement, data)

    def test_import_transactions_only_still_persists_msi_plans(self) -> None:
        # Regression: an unreconciled card imported "transactions only" used to
        # drop the extracted MSI schedule entirely, so JOY showed no plans.
        batch = self._unreconciled_joy_batch()
        account = Account.objects.create(owner_user=self.user, account_name="JOY BANAMEX",
                                         account_type="Credit Card", bank="Banamex",
                                         total="29104.00", credit_limit="49000.00")
        result = commit_batch(self.user, batch.id,
                              {"account_id": account.id, "import_transactions_only": True})
        self.assertEqual(len(result["imported"]), 4)
        # The four plans are recorded even though the balance was not trusted.
        self.assertEqual(CreditCardStatementSnapshot.objects.filter(account=account, import_batch=batch).count(), 1)
        self.assertEqual(DeferredPurchase.objects.filter(account=account).count(), 4)
        remaining = sum((dp.remaining_balance for dp in DeferredPurchase.objects.filter(account=account)), Decimal("0"))
        self.assertEqual(remaining, Decimal("5263.57"))
        # Plan metadata changes nothing beyond the imported ledger rows: the four
        # posted installments (1,998.79) are the only balance movement.
        account.refresh_from_db()
        self.assertEqual(account.total, Decimal("29104.00") - Decimal("1998.79"))
        self.assertEqual(Transaction.objects.filter(owner_user=self.user).count(), 4)

    def test_committed_msi_details_can_be_corrected_after_import(self) -> None:
        batch = self._unreconciled_joy_batch()
        account = Account.objects.create(owner_user=self.user, account_name="JOY BANAMEX",
                                         account_type="Credit Card", bank="Banamex",
                                         total="29104.00", credit_limit="49000.00")
        commit_batch(self.user, batch.id,
                      {"account_id": account.id, "import_transactions_only": True})

        first_key = str(batch.deferred_purchases[0]["source_key"])
        corrections = []
        for plan in batch.deferred_purchases:
            corrected = dict(plan)
            if str(corrected.get("source_key")) == first_key:
                corrected["remaining_balance"] = "700.00"
                corrected["current_installment"] = "250.00"
                corrected["installment_number"] = 4
            corrections.append(corrected)
        updated = update_deferred_purchases(self.user, batch.id, corrections)

        # The batch, the account snapshot and the plan rows all follow.
        self.assertEqual(updated.deferred_purchases[0]["remaining_balance"], "700.00")
        snapshot = CreditCardStatementSnapshot.objects.get(import_batch=batch)
        self.assertEqual(snapshot.deferred_purchases[0]["remaining_balance"], "700.00")
        plan_row = DeferredPurchase.objects.get(account=account, source_key=first_key)
        self.assertEqual(plan_row.remaining_balance, Decimal("700.00"))
        self.assertEqual(plan_row.current_installment, Decimal("250.00"))
        self.assertEqual(plan_row.installment_number, 4)
        self.assertEqual(DeferredPurchase.objects.filter(account=account).count(), 4)
        # Corrections never move money: the four posted installments are
        # still the only balance movement.
        account.refresh_from_db()
        self.assertEqual(account.total, Decimal("29104.00") - Decimal("1998.79"))

    def test_restore_command_recovers_missing_plans_idempotently(self) -> None:
        batch = self._unreconciled_joy_batch()
        # The audited defect only affects batches that were already
        # committed by code that skipped the persist stage. A batch
        # still in review is promoted by its own commit.
        batch.status = BankStatementImportBatch.STATUS_COMMITTED
        batch.save(update_fields=["status"])
        account = Account.objects.create(owner_user=self.user, account_name="JOY BANAMEX",
                                         account_type="Credit Card", bank="Banamex",
                                         total="29104.00", credit_limit="49000.00")
        # Simulate the audited state: plans live on the batch, nothing promoted.
        self.assertEqual(CreditCardStatementSnapshot.objects.count(), 0)
        self.assertEqual(DeferredPurchase.objects.count(), 0)

        # Dry run reports but writes nothing.
        call_command("restore_deferred_purchases", "--batch-id", batch.id, "--account-id", account.id)
        self.assertEqual(CreditCardStatementSnapshot.objects.count(), 0)
        self.assertEqual(DeferredPurchase.objects.count(), 0)

        call_command("restore_deferred_purchases", "--batch-id", batch.id,
                     "--account-id", account.id, "--apply")
        self.assertEqual(CreditCardStatementSnapshot.objects.filter(account=account).count(), 1)
        self.assertEqual(DeferredPurchase.objects.filter(account=account).count(), 4)

        # A second run is idempotent: no duplicate snapshot or plans, and the
        # batch now resolves to its linked account.
        batch.refresh_from_db()
        call_command("restore_deferred_purchases", "--batch-id", batch.id,
                     "--account-id", account.id, "--apply")
        self.assertEqual(CreditCardStatementSnapshot.objects.filter(account=account).count(), 1)
        self.assertEqual(DeferredPurchase.objects.filter(account=account).count(), 4)
        self.assertEqual(batch.linked_account_id, account.id)
        # No transactions invented by the repair.
        self.assertEqual(Transaction.objects.filter(owner_user=self.user).count(), 0)


"""
Service for processing bank statements using Google AI Studio (Gemini API).
"""
import os
import json
import base64
import hashlib
import logging
import re
import time
import io
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.files.base import ContentFile
from google import genai as google_genai

logger = logging.getLogger(__name__)

RETIREMENT_CATEGORIES = {
    "contribution": "Retirement contribution",
    "return": "Investment return",
    "fee": "Retirement fee",
    "interest": "Retirement interest",
}

DEFAULT_GEMINI_FALLBACK_MODELS = (
    "gemini-3.5-flash-lite",
)


def _gemini_models_to_try() -> list[str]:
    """Return the configured model followed by unique fallback models."""
    configured_model = getattr(settings, "GOOGLE_AI_MODEL", None)
    configured_fallbacks = getattr(settings, "GOOGLE_AI_FALLBACK_MODELS", "")
    fallback_models = [name.strip() for name in configured_fallbacks.split(",") if name.strip()]
    fallback_models = fallback_models or list(DEFAULT_GEMINI_FALLBACK_MODELS)
    return list(dict.fromkeys(filter(None, [configured_model, *fallback_models])))


def _is_transient_gemini_error(error: Exception) -> bool:
    """Identify failures that are safe to retry or route to another model."""
    message = str(error).lower()
    return any(marker in message for marker in (
        "429", "500", "502", "503", "504", "quota", "resourceexhausted",
        "unavailable", "high demand", "timeout", "timed out", "rate limit",
    ))


def _money(value: Any) -> Decimal | None:
    """Return a two-decimal amount without accepting invented/invalid values."""
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return None


def normalize_credit_card_deferred_extraction(data: Dict[str, Any]) -> Dict[str, Any]:
    """Make MSI schedules informational unless the card balance is demonstrably safe."""
    kind = str(data.get("statement_kind") or "").lower()
    account_type = str(data.get("account_type") or "").lower()
    summary = data.get("card_summary") or {}
    deferred = data.get("deferred_purchases") or []
    is_card = kind == "credit_card_deferred_payments" or (account_type in {"credit card", "credit", "crédito"} and (summary or deferred))
    if not is_card:
        return data

    data["statement_kind"] = "credit_card_deferred_payments"
    data["account_type"] = "Credit Card"
    data["card_summary"] = summary
    normalized_plans = []
    for plan in deferred:
        merchant = str(plan.get("merchant") or plan.get("title") or "Deferred purchase").strip()
        original = _money(plan.get("original_amount"))
        count = plan.get("installment_count") or plan.get("total_installments") or ""
        plan["source_key"] = str(plan.get("source_key") or f"{merchant}|{original or ''}|{count}")[:180]
        plan["merchant"] = merchant
        # Gemini occasionally puts the ordinal (for example, 6 in "6 of 12")
        # into current_installment. That field is a currency amount, so move a
        # clearly ordinal integer into installment_number instead of displaying
        # it as "$6" in the review UI.
        try:
            count_value = int(count)
            current_value = Decimal(str(plan.get("current_installment")))
            missing_ordinal = plan.get("installment_number") in (None, "")
            if missing_ordinal and current_value == current_value.to_integral_value() and 1 <= int(current_value) <= count_value:
                plan["installment_number"] = int(current_value)
                plan["current_installment"] = None
                logger.warning("Normalized MSI ordinal placed in current_installment for %s", merchant)
        except (InvalidOperation, TypeError, ValueError):
            pass
        # A schedule is never a second expense. The associated current-period
        # ledger charge, if present, is the only importable economic event.
        plan["importable"] = False
        normalized_plans.append(plan)
    data["deferred_purchases"] = normalized_plans

    reconciliation = data.get("reconciliation") or {}
    limit = _money(summary.get("credit_limit"))
    available_closing = _money(summary.get("available_credit"))
    opening_debt = _money(summary.get("opening_total_debt"))
    closing_debt = _money(summary.get("total_debt"))
    regular_debt = _money(summary.get("regular_debt"))
    deferred_debt = _money(summary.get("deferred_balance"))
    valid_limit = limit is not None and available_closing is not None and closing_debt is not None and limit - available_closing == closing_debt
    valid_breakdown = regular_debt is None or deferred_debt is None or regular_debt + deferred_debt == closing_debt
    has_opening = opening_debt is not None and limit is not None
    reconciliation["opening_balance"] = float(limit - opening_debt) if has_opening else None
    reconciliation["closing_balance"] = float(available_closing) if available_closing is not None else None
    reconciliation["is_reconciled"] = reconciliation.get("is_reconciled") is True and valid_limit and valid_breakdown and has_opening
    if not reconciliation["is_reconciled"]:
        reconciliation["reason"] = reconciliation.get("reason") or "Credit limit, available credit, opening debt, and debt breakdown do not safely reconcile. Review only."
    data["reconciliation"] = reconciliation
    data["initial_balance"] = reconciliation["opening_balance"] if reconciliation["is_reconciled"] else None
    return data


def normalize_multi_product_extraction(data: Dict[str, Any]) -> Dict[str, Any]:
    """Make a unified-bank response safe for product-level import review."""
    if str(data.get("statement_kind") or "").lower() != "multi_product":
        return data
    products = data.get("accounts") or []
    seen: set[str] = set()
    normalized = []
    for product in products:
        product_id = str(product.get("source_product_id") or "").strip()
        product_name = str(product.get("name") or "").strip()
        # Portfolio rows are aggregate cross-checks, not balance-bearing
        # accounts. For example, GBM's "PORTAFOLIO GBM" includes DEUDA and
        # EFECTIVO, which must remain the only importable products.
        is_portfolio_summary = (
            product.get("is_portfolio_summary") is True
            or product_name.upper().startswith(("PORTAFOLIO", "PORTFOLIO"))
        )
        if not product_id or product_id in seen or is_portfolio_summary:
            continue
        seen.add(product_id)
        product["product_type"] = product.get("product_type") or product.get("type") or "Other"
        reconciliation = product.get("reconciliation") or {}
        opening = _money(reconciliation.get("opening_balance", product.get("opening_balance")))
        closing = _money(reconciliation.get("closing_balance", product.get("closing_balance")))
        cash_movement = _money(reconciliation.get("cash_movements", reconciliation.get("net_cash_movement")))
        valuation_change = _money(reconciliation.get("valuation_change", reconciliation.get("market_value_change")))
        # Investment statements commonly change value because of market
        # performance, which is not an importable cash transaction. A product
        # can therefore reconcile as opening + cash movement + valuation.
        if opening is not None and closing is not None and cash_movement is not None and valuation_change is not None:
            reconciliation["opening_balance"] = float(opening)
            reconciliation["closing_balance"] = float(closing)
            reconciliation["cash_movements"] = float(cash_movement)
            reconciliation["valuation_change"] = float(valuation_change)
            expected_closing = opening + cash_movement + valuation_change
            reconciliation["is_reconciled"] = expected_closing == closing
            if reconciliation["is_reconciled"]:
                reconciliation["reason"] = ""
            else:
                reconciliation["reason"] = (
                    f"Opening balance plus cash movements and valuation change equals "
                    f"{expected_closing}, not closing balance {closing}."
                )
        product["reconciliation"] = reconciliation
        # A product without a demonstrable balance reconciliation remains visible
        # but cannot silently create an account or affect balances.
        product["review_only"] = reconciliation.get("is_reconciled") is not True
        normalized.append(product)
    data["accounts"] = normalized
    data["transactions"] = [
        item for item in (data.get("transactions") or [])
        if item.get("importable") is not False
    ]
    return data


def _labeled_money(text: str, label_pattern: str) -> Decimal | None:
    """Read one explicitly labelled currency value from extracted PDF text."""
    match = re.search(
        rf"{label_pattern}\s*[+-]?\$?\s*([\d,]+(?:\.\d{{1,2}})?)",
        text,
        flags=re.IGNORECASE,
    )
    return _money(match.group(1).replace(",", "")) if match else None


def normalize_nu_cajitas_extraction(data: Dict[str, Any], pdf_text: str) -> Dict[str, Any]:
    """Split a Nu aggregate statement into its spendable account and Cajitas."""
    lowered_text = pdf_text.lower()
    if "cuenta nu:" not in lowered_text or "total cajitas" not in lowered_text:
        return data

    total_opening = _labeled_money(pdf_text, r"Saldo inicial")
    total_closing = _labeled_money(pdf_text, r"Saldo al generar este estado de cuenta")
    main_closing = _labeled_money(pdf_text, r"En su Cuenta")
    cajitas_closing = _labeled_money(pdf_text, r"Total Cajitas")
    generated = _labeled_money(pdf_text, r"Dinero generado este mes") or Decimal("0.00")
    if None in (total_opening, total_closing, main_closing, cajitas_closing):
        logger.warning("Nu Cajitas statement detected, but its labelled balance split is incomplete")
        return data

    normalized_transactions: list[dict[str, Any]] = []
    seen_movements: set[tuple[str, str, Decimal | None]] = set()
    has_generated_income = False
    for raw in data.get("transactions") or []:
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        title = str(item.get("title") or item.get("description") or "").strip()
        title_lower = title.lower()
        amount = _money(item.get("amount", item.get("total")))
        movement_key = (str(item.get("date") or ""), title_lower, amount)
        if movement_key in seen_movements:
            continue
        seen_movements.add(movement_key)

        if "cajita" in title_lower and "retiro" in title_lower:
            item.update({
                "transaction_type": "Transfer", "category": "Account Transfer",
                "source_product_id": "nu-cajitas", "destination_product_id": "nu-main",
            })
        elif "cajita" in title_lower and ("depósito" in title_lower or "deposito" in title_lower or title_lower.startswith("dep")):
            item.update({
                "transaction_type": "Transfer", "category": "Account Transfer",
                "source_product_id": "nu-main", "destination_product_id": "nu-cajitas",
            })
        elif "dinero generado" in title_lower or "interés" in title_lower or "interes" in title_lower:
            item.update({
                "transaction_type": "Income", "category": "Investments",
                "source_product_id": "nu-cajitas",
            })
            has_generated_income = amount == generated
        else:
            item["source_product_id"] = "nu-main"
        normalized_transactions.append(item)

    if generated and not has_generated_income:
        period = data.get("statement_period") or {}
        if period.get("end"):
            normalized_transactions.append({
                "date": period["end"], "title": "Dinero generado este mes",
                "amount": float(generated), "transaction_type": "Income",
                "category": "Investments", "source_product_id": "nu-cajitas",
            })

    main_net = Decimal("0.00")
    cajitas_net = Decimal("0.00")
    for item in normalized_transactions:
        amount = _money(item.get("amount", item.get("total"))) or Decimal("0.00")
        transaction_type = item.get("transaction_type")
        source = item.get("source_product_id")
        destination = item.get("destination_product_id")
        if transaction_type == "Transfer":
            if source == "nu-main":
                main_net -= amount
            elif source == "nu-cajitas":
                cajitas_net -= amount
            if destination == "nu-main":
                main_net += amount
            elif destination == "nu-cajitas":
                cajitas_net += amount
        else:
            signed = amount if transaction_type == "Income" else -amount
            if source == "nu-cajitas":
                cajitas_net += signed
            else:
                main_net += signed

    main_opening = main_closing - main_net
    cajitas_opening = cajitas_closing - cajitas_net
    products_reconcile = (
        main_opening + cajitas_opening == total_opening
        and main_closing + cajitas_closing == total_closing
    )
    if not products_reconcile:
        logger.warning(
            "Nu product split does not reconcile opening=%s/%s closing=%s/%s",
            main_opening + cajitas_opening, total_opening,
            main_closing + cajitas_closing, total_closing,
        )
    reason = "" if products_reconcile else "The Nu product split does not match the aggregate statement balances."
    data.update({
        "statement_kind": "multi_product", "account_name": "Nu", "account_type": "Other",
        "initial_balance": None, "transactions": normalized_transactions,
        "accounts": [
            {
                "source_product_id": "nu-main", "name": "Cuenta Nu", "bank_name": "Nu", "product_type": "Checking",
                "opening_balance": float(main_opening), "closing_balance": float(main_closing),
                "reconciliation": {
                    "opening_balance": float(main_opening), "closing_balance": float(main_closing),
                    "cash_movements": float(main_net), "valuation_change": 0.0,
                    "is_reconciled": products_reconcile, "reason": reason,
                },
            },
            {
                "source_product_id": "nu-cajitas", "name": "Cajitas Nu", "bank_name": "Nu", "product_type": "Investment",
                "opening_balance": float(cajitas_opening), "closing_balance": float(cajitas_closing),
                "reconciliation": {
                    "opening_balance": float(cajitas_opening), "closing_balance": float(cajitas_closing),
                    "cash_movements": float(cajitas_net), "valuation_change": 0.0,
                    "is_reconciled": products_reconcile, "reason": reason,
                },
            },
        ],
        "portfolio_summary": {
            "opening_balance": float(total_opening), "closing_balance": float(total_closing),
            "net_cash_movements": float(total_closing - total_opening), "valuation_change": 0.0,
        },
        "reconciliation": {
            "opening_balance": float(total_opening), "closing_balance": float(total_closing),
            "is_reconciled": products_reconcile, "reason": reason,
        },
    })
    logger.info(
        "Normalized Nu statement into Cuenta Nu and Cajitas Nu products; transactions=%s reconciled=%s",
        len(normalized_transactions), products_reconcile,
    )
    return data


def normalize_retirement_extraction(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize retirement-specific AI output and make unsafe imports review-only."""
    kind = str(data.get("statement_kind") or "").lower()
    account_type = str(data.get("account_type") or "").lower()
    breakdown = data.get("retirement_breakdown") or {}
    is_retirement = kind == "retirement" or account_type in {"retirement", "pension", "afore"} or bool(breakdown)
    if not is_retirement:
        return data

    data["statement_kind"] = "retirement"
    data["account_type"] = "Retirement"
    data["retirement_breakdown"] = breakdown
    if not data.get("account_name"):
        data["account_name"] = f"{breakdown.get('institution') or 'Retirement'} AFORE"
    data["balance_period"] = data.get("balance_period") or data.get("statement_period") or {}
    data["movements_period"] = data.get("movements_period") or data.get("statement_period") or {}
    data["statement_period"] = data["balance_period"]
    reconciliation = data.get("reconciliation") or {}
    opening = reconciliation.get("opening_balance", data.get("initial_balance"))
    closing = reconciliation.get("closing_balance", breakdown.get("total_closing_balance"))
    reconciliation["opening_balance"] = opening
    reconciliation["closing_balance"] = closing
    same_period = data["balance_period"] == data["movements_period"]
    reconciliation["is_reconciled"] = reconciliation.get("is_reconciled") is True and same_period and opening is not None and closing is not None
    if not reconciliation["is_reconciled"]:
        reconciliation["reason"] = reconciliation.get("reason") or "Balance and movement periods do not safely reconcile. Review only."
    data["reconciliation"] = reconciliation
    data["initial_balance"] = opening if reconciliation["is_reconciled"] else None

    for item in data.get("transactions") or []:
        movement_type = str(item.get("retirement_movement_type") or "").lower()
        if movement_type in RETIREMENT_CATEGORIES:
            item["category"] = RETIREMENT_CATEGORIES[movement_type]
            item["transaction_type"] = "Expense" if movement_type == "fee" else "Income"
        if not item.get("date"):
            item["date"] = data["movements_period"].get("end")
            item["date_source"] = "movement_period_end"
        if item.get("date") is None:
            item["importable"] = False
    return data


def _uploaded_file_state_name(uploaded_file: Any) -> str:
    """Return a normalized file state name across google-genai package versions."""
    state = getattr(uploaded_file, 'state', None)
    return str(getattr(state, 'name', state or '')).upper()

# Try to import PDF libraries for password-protected PDF support
try:
    from pypdf import PdfReader, PdfWriter
    PDF_LIBRARY_AVAILABLE = True
    PYPDF2_AVAILABLE = False
    logger.info("pypdf library available for PDF decryption")
except ImportError:
    try:
        from PyPDF2 import PdfFileReader, PdfFileWriter
        PDF_LIBRARY_AVAILABLE = True
        PYPDF2_AVAILABLE = True
        logger.info("PyPDF2 library available for PDF decryption")
    except ImportError:
        PDF_LIBRARY_AVAILABLE = False
        PYPDF2_AVAILABLE = False
        logger.warning("PDF libraries (pypdf/PyPDF2) not available. Password-protected PDFs cannot be processed.")


def _extract_pdf_text(pdf_file_path: str) -> str:
    """Extract text for deterministic, institution-specific safety checks."""
    if not PDF_LIBRARY_AVAILABLE:
        return ""
    try:
        reader = PdfReader(pdf_file_path)
        pages = getattr(reader, "pages", [])
        return "\n".join((page.extract_text() or "") for page in pages)
    except Exception as exc:
        logger.warning("Could not extract PDF text for deterministic normalization: %s", exc)
        return ""


def process_bank_statement_with_ai(pdf_file_path: str) -> Dict[str, Any]:
    """
    Process a bank statement PDF using Google AI Studio (Gemini API) to extract transactions.
    
    Args:
        pdf_file_path: Path to the uploaded PDF file
        
    Returns:
        Dictionary containing:
        - transactions: List of extracted transactions
        - account_name: Detected account name (if any)
        - account_type: Account type (Credit Card, Debit Card, Checking Account, Savings Account, or Other)
        - statement_period: Dictionary with start and end dates
        - raw_response: Raw AI response for debugging
    """
    api_key = getattr(settings, 'GOOGLE_AI_API_KEY', None)
    
    if not api_key:
        logger.warning("GOOGLE_AI_API_KEY not configured. Skipping AI processing.")
        return {
            'transactions': [],
            'account_name': None,
            'account_type': None,
            'statement_period': None,
            'initial_balance': None,  # Add this
            'raw_response': None,
            'error': 'AI API key not configured'
        }
    
    try:
        # Use the supported Google GenAI SDK and its current Interactions API.
        client = google_genai.Client(api_key=api_key)
        logger.info("Using google-genai SDK for bank statement processing")

        # Prioritize current, file-capable Gemini model IDs. The old code used
        # aliases such as gemini-flash-latest; the legacy SDK constructor does
        # not validate model IDs, so those aliases can fail later at generation
        # time with confusing endpoint/model errors.
        model_name = None
        
        # Canonical categories (single source of truth; must match BankStatementReview.vue and TableData.vue)
        # Order: income-related, then expense, then transfer-related, then other
        available_categories = [
            'Salary',
            'Awards',
            'Investments',
            'Gifts',
            'Account Transfer',
            'Balance Transfer',
            'Money Transfer',
            'Transfer',
            'Bills and utilities',
            'Education',
            'Entertainment',
            'Food and drinks',
            'Insurance',
            'Loans',
            'Medical',
            'Shopping',
            'Transportation',
            'Others',
            'Retirement contribution',
            'Investment return',
            'Retirement fee',
            'Retirement interest',
        ]
        
        # Create the prompt for transaction extraction
        prompt = f"""Analyze this bank statement PDF and extract all transactions.

FIRST classify the document. For ordinary bank/card statements use statement_kind "bank".
For retirement, pension, AFORE, SIEFORE, or Mexican retirement-subaccount statements use statement_kind "retirement" and account_type "Retirement".
For a unified statement that contains more than one balance-bearing product (for example checking plus term investments), use statement_kind "multi_product".
For a credit-card statement with "Meses sin intereses", "MSI", deferred purchases, or installment schedules, use statement_kind "credit_card_deferred_payments" and account_type "Credit Card".

CREDIT-CARD / MSI RULES:
- This is ONE credit-card liability, not a new account or loan for each deferred purchase.
- Return card_summary with credit_limit, available_credit, opening_total_debt, total_debt, regular_debt, deferred_balance, payment_due, and statement_date when explicitly shown.
- Return deferred_purchases[] with merchant, original_amount, remaining_balance, current_installment, installment_number, installment_count, and source_key when shown. These rows are informational and MUST NOT also appear as transactions.
- Extract the posted current-period ledger row for each installment as the only expense. If a schedule and ledger row clearly match, put deferred_purchase_source_key on the ledger row; do not duplicate it.
- A card payment is a Transfer only if both source and destination accounts are known. Otherwise return it in unresolved_transfers[] and do not create a funding account.
- Reconcile only when credit_limit - available_credit equals total_debt, the stated regular_debt + deferred_balance (when both disclosed) equals total_debt, and opening_total_debt is explicit. Never invent card balances, installment dates, or matches.

MULTI-PRODUCT RULES:
- Return accounts[] for LEAF, balance-bearing products only. Each product needs source_product_id, name, bank_name, product_type, opening_balance, closing_balance, positions, and reconciliation. Never create an account for a portfolio/parent/summary row such as "PORTAFOLIO GBM", "Resumen del portafolio", or a total. These values belong in portfolio_summary and are only a cross-check.
- For broker investment statements, extract the exact leaf rows from the detailed portfolio breakdown (for example GBM "DEUDA" and "EFECTIVO"). Each entry needs source_product_id, name, product_type, opening_balance, closing_balance, positions, and reconciliation.
- The only valid product types are Checking, Savings, Credit Card, Débito, Investment, Loan, Mortgage, Business, Other, or Retirement.
- A term-investment opening is a Transfer from checking to investment. A principal payout is a Transfer from investment to checking. Interest is Income on the investment and tax withholding is Expense on the investment.
- Every transaction needs source_product_id. Transfers also need destination_product_id. A credit-card payment with no actual card statement/balance must be returned in unresolved_transfers[], not turned into a new Credit Card account.
- Do not extract projected maturity values, portfolio totals, rate tables, generic credit disclosures, or informational messages as balances or transactions.
- For investments, extract reconciliation.cash_movements and reconciliation.valuation_change separately. Market performance, plus/minusvalia, unrealized gain/loss, and portfolio yield are valuation_change, never a cash transaction. Set reconciliation.is_reconciled=true only when opening_balance + cash_movements + valuation_change equals closing_balance within 0.01.
- Return portfolio_summary separately with opening_balance, closing_balance, net_cash_movements, and valuation_change. It is verification data only and MUST NOT appear in accounts[] or transactions[].

NU / CAJITAS RULES:
- A Cuenta Nu statement that shows both "En su Cuenta" and "Total Cajitas" is multi_product, even when its graph presents one aggregate opening and closing balance.
- Return "Cuenta Nu" as a Checking product and "Cajitas Nu" as an Investment product. Never assign the aggregate capital to Cuenta Nu.
- "Depósito en Cajita" is a Transfer from Cuenta Nu to Cajitas Nu. "Retiro de Cajita" is a Transfer from Cajitas Nu to Cuenta Nu. The mirrored Cajitas-detail row is the same transfer and MUST NOT be duplicated.
- "Dinero generado este mes" is Income in Cajitas Nu and must be included once at the statement period end.
- Use the explicit "En su Cuenta" and "Total Cajitas" closing values. Derive each opening product balance only when their movements reconcile exactly to those closing values and their sum matches the aggregate opening balance.

RETIREMENT/AFORE RULES:
- This is ONE aggregate retirement asset, never separate bank accounts for "Ahorro para el retiro", voluntary savings, or "Ahorro para la vivienda".
- Return balance_period (the summary period) separately from movements_period (the detailed-movement period). Never claim they reconcile if their dates differ.
- Return retirement_breakdown with institution, subtype "AFORE", opening/closing totals, and labeled retirement, voluntary_savings, and housing values where shown.
- Only economic rows are transactions. Mark salary base, days contributed, indicators, performance tables, and other informational rows importable=false.
- Use retirement_movement_type: contribution, return, fee, or interest. Dated contributions retain their date. An undated aggregate return/fee/interest must have date null; the application will use movements_period.end only when it exists.
- Never invent a date, opening balance, or total. "Saldo anterior" for one subaccount is NOT the aggregate account opening balance.
- reconciliation must include opening_balance, closing_balance, is_reconciled, and reason. Set is_reconciled=true ONLY if the same-period opening balance plus signed economic movements exactly reaches closing balance.

For each transaction, extract:
- date (format: YYYY-MM-DD)
- title/description (transaction description)
- amount (as a positive number)
- transaction_type (either "Income", "Expense", or "Transfer")
- category: MUST be one of these exact categories: {', '.join(available_categories)}

Also extract:
- account_name: The name of the bank account
- account_type: Use exactly one of: "Checking", "Savings", "Credit Card", "Débito", "Efectivo", "Investment", "Loan", "Mortgage", "Business", "Other". Use "Débito" for debit cards, "Credit Card" for credit cards, "Efectivo" for cash.
- statement_period: The start and end dates of the statement period (format: YYYY-MM-DD)
- initial_balance: The initial balance at the start of the statement period. This is CRITICAL for new accounts. Look for terms like "Saldo Inicial", "Saldo Anterior", "Previous Balance", "Opening Balance", "Balance Inicial", "Saldo Previo", or similar in:
  * Summary tables (tablas de resumen)
  * Transaction graphs (gráficos transaccionales)
  * Statement headers
  * Balance summary sections
  This is the balance BEFORE any transactions in this statement period. Extract this as a number (can be positive or negative). If you see a value like 232902.12 in a summary table labeled "Saldo Inicial" or "Saldo Anterior", that is the initial_balance. If not found, use null.

Return the data as a JSON object with this exact structure:
{{
  "transactions": [
    {{
      "date": "2024-01-15",
      "title": "Transaction description",
      "amount": 100.50,
      "transaction_type": "Expense",
      "category": "Food and drinks"
    }}
  ],
  "account_name": "Account Name",
  "account_type": "Credit Card",
  "statement_period": {{
    "start": "2024-01-01",
    "end": "2024-01-31"
  }},
  "initial_balance": 232902.12,
  "statement_kind": "bank",
  "balance_period": {{"start": "2024-01-01", "end": "2024-01-31"}},
  "movements_period": {{"start": "2024-01-01", "end": "2024-01-31"}},
  "retirement_breakdown": {{}},
  "card_summary": {{}},
  "deferred_purchases": [],
  "reconciliation": {{"opening_balance": 232902.12, "closing_balance": 0, "is_reconciled": false, "reason": ""}},
  "accounts": [],
  "portfolio_summary": {{"opening_balance": null, "closing_balance": null, "net_cash_movements": null, "valuation_change": null}},
  "unresolved_transfers": []
}}

CRITICAL CATEGORY RULES:
- The category field MUST be one of these exact values (case-sensitive): {', '.join(available_categories)}
- Do NOT create new categories or use variations
- Category mapping guide:
  * Food, groceries, restaurants, cafes → "Food and drinks"
  * Gas, taxi, Uber, public transport, parking → "Transportation"
  * Rent, electricity, water, internet, phone bills → "Bills and utilities"
  * Clothing, electronics, general purchases → "Shopping"
  * Movies, games, subscriptions, hobbies → "Entertainment"
  * Doctor, pharmacy, hospital → "Medical"
  * School, tuition, courses, books → "Education"
  * Salary, wages, paycheck → "Salary"
  * Bank transfers, wire transfers → "Transfer" or "Money Transfer"
  * Credit card payments, account transfers → "Account Transfer" or "Balance Transfer"
  * Gifts, donations → "Gifts"
  * Insurance payments → "Insurance"
  * Loan payments → "Loans"
  * Investment transactions → "Investments"
  * Awards, bonuses, prizes → "Awards"
  * If unsure or doesn't fit any category → "Others"

Important:
- Only return valid JSON, no additional text
- Amounts should be positive numbers (use transaction_type to indicate Income/Expense)
- Dates must be in YYYY-MM-DD format
- If you cannot determine a category, use "Others" (not "Other")
- If you cannot determine transaction_type, infer from context (positive amounts are usually Income, negative are Expense)
- For account_type, look for explicit mentions of credit/debit/checking/savings in the statement header, account name, or document title
- Common indicators: "Tarjeta de Crédito" or "Credit Card" = Credit Card, "Tarjeta de Débito" or "Debit Card" = Debit Card, "Cuenta" or "Account" without card mention = Checking/Savings
- For initial_balance: This is VERY IMPORTANT. Look carefully for "Saldo Inicial", "Saldo Anterior", "Previous Balance", "Opening Balance", "Balance Inicial", "Saldo Previo" in:
  * Summary tables (often labeled "Resumen Transaccional" or "Grafico Transaccional")
  * Balance tables showing "Saldo Anterior" vs "Saldo Actual"
  * Statement headers or account information sections
  * Any table or section that shows balances at the start of the period
  This should be the balance at the START of the statement period, before any transactions are applied. It is often displayed in a summary table with columns like "Saldo Anterior", "Intereses", "Saldo Actual". The "Saldo Anterior" value is the initial_balance. Extract the exact numeric value you see, even if it's a large number like 232902.12.
"""
        
        # For PDF processing, try file upload API
        # If we hit quota errors, try the next model in the list
        uploaded_file = None
        last_error = None
        response = None
        
        try:
            # Try processing with an explicitly configured model first, then the
            # known current Gemini model IDs. This avoids the previous behavior
            # of trying a None/invalid model before falling back.
            models_to_retry = _gemini_models_to_try()
            transient_retries = max(0, int(getattr(settings, "GOOGLE_AI_TRANSIENT_RETRIES", 1)))
            request_timeout = max(1, int(getattr(settings, "GOOGLE_AI_REQUEST_TIMEOUT", 45)))
            
            for retry_model_name in models_to_retry:
                for attempt in range(transient_retries + 1):
                    try:
                        logger.info(
                            "Attempting bank-statement processing with model %s (attempt %s/%s)",
                            retry_model_name, attempt + 1, transient_retries + 1,
                        )

                        if uploaded_file is None:
                            uploaded_file = client.files.upload(file=pdf_file_path)

                            while _uploaded_file_state_name(uploaded_file) == "PROCESSING":
                                time.sleep(2)
                                uploaded_file = client.files.get(name=uploaded_file.name)

                            if _uploaded_file_state_name(uploaded_file) == "FAILED":
                                raise Exception(f"File upload failed: {_uploaded_file_state_name(uploaded_file)}")

                        response = client.interactions.create(
                            model=retry_model_name,
                            input=[
                                {
                                    "type": "document",
                                    "uri": uploaded_file.uri,
                                    "mime_type": uploaded_file.mime_type,
                                },
                                {"type": "text", "text": prompt},
                            ],
                            store=False,
                            timeout=request_timeout,
                        )

                        model_name = retry_model_name
                        break
                    
                    except Exception as e:
                        last_error = e
                        if _is_transient_gemini_error(e):
                            if attempt < transient_retries:
                                delay = 2 ** attempt
                                logger.warning("Transient Gemini error from %s; retrying in %ss: %s", retry_model_name, delay, e)
                                time.sleep(delay)
                                continue
                            logger.warning("Transient Gemini error from %s after %s attempts; trying fallback: %s", retry_model_name, attempt + 1, e)
                            break
                        logger.error("Non-transient Gemini error from %s: %s", retry_model_name, e)
                        if retry_model_name == models_to_retry[-1]:
                            raise Exception(f"Failed to process PDF: {str(e)}")
                        break

                if response is not None:
                    break
            
            # If we exhausted all models due to quota, raise a helpful error
            if response is None and last_error and _is_transient_gemini_error(last_error):
                raise Exception(
                    "All configured Gemini models were temporarily unavailable or rate limited. "
                    "Please retry shortly or configure GOOGLE_AI_FALLBACK_MODELS. "
                    f"Last error: {str(last_error)}"
                )
            
            if response is None:
                raise Exception("Failed to process PDF with any available model.")
                
        finally:
            # Clean up the uploaded file if it was created
            if uploaded_file:
                try:
                    client.files.delete(name=uploaded_file.name)
                except Exception:
                    pass  # Ignore cleanup errors
        
        # Extract the text response
        response_text = (
            getattr(response, "output_text", None)
            or getattr(response, "text", None)
            or ""
        ).strip()
        if not response_text:
            raise Exception(f"Gemini returned an empty response using model {model_name}")

        response_digest = hashlib.sha256(response_text.encode("utf-8")).hexdigest()[:16]
        logger.info(
            "Gemini response received model=%s chars=%s sha256_prefix=%s",
            model_name, len(response_text), response_digest,
        )
        
        # Try to parse JSON from the response
        # Sometimes the AI wraps JSON in markdown code blocks
        fenced_json = '```json' in response_text
        fenced_code = not fenced_json and '```' in response_text
        if fenced_json:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif fenced_code:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        # Parse the JSON response
        try:
            extracted_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(
                "Gemini JSON parse failed model=%s chars=%s sha256_prefix=%s fenced_json=%s fenced_code=%s line=%s column=%s error=%s",
                model_name, len(response_text), response_digest, fenced_json, fenced_code,
                e.lineno, e.colno, e.msg,
            )
            return {
                'transactions': [],
                'account_name': None,
                'account_type': None,
                'statement_period': None,
                'initial_balance': None,  # Add this
                'raw_response': response_text,
                'error': f'Failed to parse AI response: {str(e)}'
            }

        if not isinstance(extracted_data, dict):
            logger.error(
                "Gemini JSON has invalid top-level type model=%s sha256_prefix=%s type=%s",
                model_name, response_digest, type(extracted_data).__name__,
            )
            return {
                'transactions': [], 'account_name': None, 'account_type': None,
                'statement_period': None, 'initial_balance': None,
                'raw_response': response_text,
                'error': 'Failed to parse AI response: top-level JSON value must be an object',
            }

        logger.info(
            "Gemini JSON parsed model=%s sha256_prefix=%s keys=%s transactions_type=%s transactions_count=%s",
            model_name, response_digest, sorted(extracted_data.keys()),
            type(extracted_data.get("transactions")).__name__,
            len(extracted_data.get("transactions", [])) if isinstance(extracted_data.get("transactions"), list) else None,
        )

        extracted_data = normalize_nu_cajitas_extraction(extracted_data, _extract_pdf_text(pdf_file_path))
        extracted_data = normalize_multi_product_extraction(extracted_data)
        extracted_data = normalize_credit_card_deferred_extraction(extracted_data)
        extracted_data = normalize_retirement_extraction(extracted_data)
        
        # Use the same categories list defined earlier
        valid_categories = available_categories
        
        # Category mapping for common variations
        category_mapping = {
            'Food': 'Food and drinks',
            'Food & Drinks': 'Food and drinks',
            'Restaurant': 'Food and drinks',
            'Groceries': 'Food and drinks',
            'Transport': 'Transportation',
            'Transportation': 'Transportation',
            'Bills': 'Bills and utilities',
            'Utilities': 'Bills and utilities',
            'Other': 'Others',
            'Misc': 'Others',
            'Miscellaneous': 'Others',
            'General': 'Others',
            'Shopping': 'Shopping',
            'Entertainment': 'Entertainment',
            'Medical': 'Medical',
            'Healthcare': 'Medical',
            'Education': 'Education',
            'Salary': 'Salary',
            'Income': 'Salary',
            'Wages': 'Salary',
            'Transfer': 'Transfer',
            'Money Transfer': 'Money Transfer',
            'Account Transfer': 'Account Transfer',
            'Balance Transfer': 'Balance Transfer',
            'Gifts': 'Gifts',
            'Insurance': 'Insurance',
            'Loans': 'Loans',
            'Investments': 'Investments',
            'Awards': 'Awards'
        }
        
        def normalize_category(category: str) -> str:
            """Normalize category to match valid categories."""
            if not category:
                return 'Others'
            
            category = category.strip()
            
            # Check if it's already valid
            if category in valid_categories:
                return category
            
            # Try mapping
            if category in category_mapping:
                return category_mapping[category]
            
            # Try case-insensitive match
            category_lower = category.lower()
            for valid_cat in valid_categories:
                if valid_cat.lower() == category_lower:
                    return valid_cat
            
            # Try partial match
            for valid_cat in valid_categories:
                if category_lower in valid_cat.lower() or valid_cat.lower() in category_lower:
                    return valid_cat
            
            # Default to Others
            logger.warning(f"Category '{category}' not found in valid categories, using 'Others'")
            return 'Others'
        
        # Normalize account type
        def normalize_account_type(account_type: str) -> str:
            """Normalize account type to match UI expectations."""
            if not account_type:
                return 'Other'
            
            account_type = account_type.strip()
            account_type_lower = account_type.lower()
            
            # Canonical account types (match AccountsCarousel.vue / BankStatementReview.vue)
            # Use Débito (not "Debit Card") and Credit Card / Crédito for consistency
            account_type_mapping = {
                'savings account': 'Savings',
                'checking account': 'Checking',
                'credit card': 'Credit Card',
                'debit card': 'Débito',
                'checking': 'Checking',
                'savings': 'Savings',
                'credit': 'Credit Card',
                'crédito': 'Crédito',
                'debit': 'Débito',
                'cash': 'Efectivo',
                'efectivo': 'Efectivo',
                'investment': 'Investment',
                'retirement': 'Retirement',
                'pension': 'Retirement',
                'afore': 'Retirement',
                'loan': 'Loan',
                'mortgage': 'Mortgage',
                'business': 'Business',
                'other': 'Other',
            }

            if account_type_lower in account_type_mapping:
                return account_type_mapping[account_type_lower]

            for key, value in account_type_mapping.items():
                if key in account_type_lower or account_type_lower in key:
                    return value

            if 'savings' in account_type_lower:
                return 'Savings'
            if 'checking' in account_type_lower:
                return 'Checking'
            if 'credit' in account_type_lower or 'crédito' in account_type_lower:
                return 'Credit Card'
            if 'debit' in account_type_lower:
                return 'Débito'
            if 'cash' in account_type_lower or 'efectivo' in account_type_lower:
                return 'Efectivo'
            if any(value in account_type_lower for value in ('retirement', 'pension', 'afore', 'siefore')):
                return 'Retirement'

            return 'Other'
        
        # Validate and normalize the response structure
        raw_account_type = extracted_data.get('account_type', 'Other')
        normalized_account_type = normalize_account_type(raw_account_type)
        
        result = {
            'transactions': extracted_data.get('transactions', []),
            'account_name': extracted_data.get('account_name'),
            'account_type': normalized_account_type,  # Normalized account type
            'statement_period': extracted_data.get('statement_period'),
            'initial_balance': extracted_data.get('initial_balance'),  # Add this line
            'statement_kind': extracted_data.get('statement_kind', 'bank'),
            'balance_period': extracted_data.get('balance_period'),
            'movements_period': extracted_data.get('movements_period'),
            'retirement_breakdown': extracted_data.get('retirement_breakdown') or {},
            'card_summary': extracted_data.get('card_summary') or {},
            'deferred_purchases': extracted_data.get('deferred_purchases') or [],
            'reconciliation': extracted_data.get('reconciliation') or {},
            'accounts': extracted_data.get('accounts') or [],
            'unresolved_transfers': extracted_data.get('unresolved_transfers') or [],
            'raw_response': response_text,
            'error': None
        }
        
        # Validate initial_balance if present
        if result['initial_balance'] is not None:
            try:
                result['initial_balance'] = float(result['initial_balance'])
            except (ValueError, TypeError):
                logger.warning(f"Invalid initial_balance value: {result['initial_balance']}, setting to None")
                result['initial_balance'] = None

        # Validate transaction structure and normalize categories
        if not isinstance(result['transactions'], list):
            logger.warning(
                "Gemini response transactions is not a list model=%s sha256_prefix=%s type=%s; ignoring it",
                model_name, response_digest, type(result['transactions']).__name__,
            )
            result['transactions'] = []

        validated_transactions = []
        rejected_transactions = 0
        for transaction in result['transactions']:
            if not isinstance(transaction, dict):
                rejected_transactions += 1
                continue
            if all(key in transaction for key in ['date', 'title', 'amount', 'transaction_type']):
                # Ensure amount is a float
                try:
                    transaction['amount'] = float(transaction['amount'])
                    
                    # Normalize category to match UI categories
                    if 'category' in transaction:
                        transaction['category'] = normalize_category(transaction['category'])
                    else:
                        transaction['category'] = 'Others'
                    
                    validated_transactions.append(transaction)
                except (ValueError, TypeError):
                    rejected_transactions += 1
                    logger.warning("Gemini transaction has an invalid amount model=%s sha256_prefix=%s", model_name, response_digest)
            else:
                rejected_transactions += 1
        
        result['transactions'] = validated_transactions
        logger.info(
            "Gemini response validation complete model=%s sha256_prefix=%s accepted_transactions=%s rejected_transactions=%s statement_kind=%s",
            model_name, response_digest, len(validated_transactions), rejected_transactions,
            result['statement_kind'],
        )
        
        return result
        
    except FileNotFoundError:
        logger.error(f"PDF file not found: {pdf_file_path}")
        return {
            'transactions': [],
            'account_name': None,
            'account_type': None,
            'statement_period': None,
            'initial_balance': None,  # Add this
            'raw_response': None,
            'error': 'PDF file not found'
        }
    except Exception as e:
        logger.error(f"Error processing bank statement with AI: {str(e)}", exc_info=True)
        return {
            'transactions': [],
            'account_name': None,
            'account_type': None,
            'statement_period': None,
            'initial_balance': None,  # Add this
            'raw_response': None,
            'error': f'AI processing failed: {str(e)}'
        }


def is_pdf_password_protected(pdf_file: Any) -> bool:
    """
    Check if a PDF file is password-protected.
    
    Args:
        pdf_file: Django UploadedFile object or file path string
        
    Returns:
        bool: True if PDF is password-protected, False otherwise
    """
    if not PDF_LIBRARY_AVAILABLE:
        return False
    
    try:
        # Handle both file objects and file paths
        if hasattr(pdf_file, 'read'):
            # It's a file object
            pdf_file.seek(0)
            file_content = pdf_file.read()
            pdf_file.seek(0)
        else:
            # It's a file path
            with open(pdf_file, 'rb') as f:
                file_content = f.read()
        
        if PYPDF2_AVAILABLE:
            # Using PyPDF2
            from PyPDF2 import PdfFileReader
            pdf_reader = PdfFileReader(io.BytesIO(file_content))
            return pdf_reader.isEncrypted
        else:
            # Using pypdf (newer library)
            pdf_reader = PdfReader(io.BytesIO(file_content))
            return pdf_reader.is_encrypted
    except Exception as e:
        logger.warning(f"Error checking PDF encryption: {str(e)}")
        return False


def decrypt_pdf_file(pdf_file: Any, password: str) -> ContentFile:
    """
    Decrypt a password-protected PDF file.
    
    Args:
        pdf_file: Django UploadedFile object or file path string
        password: Password to decrypt the PDF
        
    Returns:
        ContentFile: Decrypted PDF file as ContentFile object
        
    Raises:
        ValueError: If password is incorrect or decryption fails
    """
    if not PDF_LIBRARY_AVAILABLE:
        raise ValueError("PDF decryption libraries not available. Please install pypdf or PyPDF2.")
    
    try:
        # Handle both file objects and file paths
        original_filename = None
        if hasattr(pdf_file, 'read'):
            # It's a file object
            pdf_file.seek(0)
            file_content = pdf_file.read()
            pdf_file.seek(0)
            original_filename = getattr(pdf_file, 'name', 'decrypted.pdf')
        else:
            # It's a file path
            original_filename = os.path.basename(pdf_file)
            with open(pdf_file, 'rb') as f:
                file_content = f.read()
        
        if PYPDF2_AVAILABLE:
            # Using PyPDF2
            from PyPDF2 import PdfFileReader, PdfFileWriter
            pdf_reader = PdfFileReader(io.BytesIO(file_content))
            
            if not pdf_reader.isEncrypted:
                # Not encrypted, return original content
                return ContentFile(file_content, name=original_filename)
            
            # Try to decrypt
            if not pdf_reader.decrypt(password):
                raise ValueError("Incorrect password or decryption failed")
            
            # Create decrypted PDF
            pdf_writer = PdfFileWriter()
            for page_num in range(pdf_reader.numPages):
                pdf_writer.addPage(pdf_reader.getPage(page_num))
            
            decrypted_pdf = io.BytesIO()
            pdf_writer.write(decrypted_pdf)
            decrypted_pdf.seek(0)
            
            return ContentFile(decrypted_pdf.read(), name=original_filename)
        else:
            # Using pypdf (newer library)
            pdf_reader = PdfReader(io.BytesIO(file_content))
            
            if not pdf_reader.is_encrypted:
                # Not encrypted, return original content
                return ContentFile(file_content, name=original_filename)
            
            # Try to decrypt
            if not pdf_reader.decrypt(password):
                raise ValueError("Incorrect password or decryption failed")
            
            # Create decrypted PDF
            pdf_writer = PdfWriter()
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            decrypted_pdf = io.BytesIO()
            pdf_writer.write(decrypted_pdf)
            decrypted_pdf.seek(0)
            
            return ContentFile(decrypted_pdf.read(), name=original_filename)
            
    except ValueError:
        raise  # Re-raise password errors
    except Exception as e:
        logger.error(f"Error decrypting PDF: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to decrypt PDF: {str(e)}")


def extract_transactions_from_pdf(pdf_file_path: str) -> Dict[str, Any]:
    """
    Wrapper function to extract transactions from a PDF file.
    This is the main function to be called from views.
    
    Args:
        pdf_file_path: Path to the PDF file
        
    Returns:
        Dictionary with extracted transaction data
    """
    return process_bank_statement_with_ai(pdf_file_path)


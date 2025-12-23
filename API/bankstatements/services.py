"""
Service for processing bank statements using Google AI Studio (Gemini API).
"""
import os
import json
import base64
import logging
import time
import io
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.files.base import ContentFile
import google.generativeai as genai

logger = logging.getLogger(__name__)

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
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Try to find an available model that supports file uploads
        # Prioritize free-tier friendly models first (Flash models have better free tier limits)
        model_names_to_try = [
            'gemini-flash-latest',            # Free-tier friendly, good balance of performance and cost
            'gemini-flash-lite-latest',       # Most cost-effective, best free tier limits
            'gemini-2.5-flash-preview-09-2025',  # What gemini-flash-latest points to
            'gemini-2.5-flash-lite-preview-09-2025',  # What gemini-flash-lite-latest points to
            # Fallback to older model names in case newer ones aren't available
            'gemini-1.5-pro',
            'gemini-1.5-pro-latest', 
            'gemini-pro',
            'gemini-3-pro-preview',           # Premium model (may have quota limits on free tier)
            'models/gemini-flash-latest',      # Try with models/ prefix
            'models/gemini-flash-lite-latest',
            'models/gemini-3-pro-preview',
            'models/gemini-pro'
        ]
        
        model = None
        model_name = None
        
        for name in model_names_to_try:
            try:
                model = genai.GenerativeModel(name)
                model_name = name
                logger.info(f"Successfully loaded model: {model_name}")
                break
            except Exception as e:
                logger.debug(f"Failed to load model {name}: {str(e)}")
                continue
        
        if model is None:
            # Last resort: try to list available models
            try:
                available_models = genai.list_models()
                logger.info("Attempting to find available models...")
                for m in available_models:
                    model_display_name = m.display_name or m.name
                    if 'gemini' in model_display_name.lower():
                        # Extract model name (remove 'models/' prefix if present)
                        model_id = m.name.replace('models/', '')
                        try:
                            model = genai.GenerativeModel(model_id)
                            model_name = model_id
                            logger.info(f"Found and using model: {model_name}")
                            break
                        except Exception:
                            continue
            except Exception as list_error:
                logger.warning(f"Could not list models: {str(list_error)}")
        
        if model is None:
            raise Exception(
                "No suitable Gemini model found. "
                "Please check your API key and ensure you have access to Gemini models. "
                "Try visiting https://aistudio.google.com/ to verify your API key and available models."
            )
        
        # Define the exact categories available in the UI (must match BankStatementReview.vue)
        available_categories = [
            'Awards',
            'Bills and utilities',
            'Education',
            'Entertainment',
            'Food and drinks',
            'Gifts',
            'Insurance',
            'Investments',
            'Loans',
            'Medical',
            'Others',
            'Salary',
            'Shopping',
            'Transportation',
            'Transfer',
            'Account Transfer',
            'Money Transfer',
            'Balance Transfer'
        ]
        
        # Create the prompt for transaction extraction
        prompt = f"""Analyze this bank statement PDF and extract all transactions.

For each transaction, extract:
- date (format: YYYY-MM-DD)
- title/description (transaction description)
- amount (as a positive number)
- transaction_type (either "Income", "Expense", or "Transfer")
- category: MUST be one of these exact categories: {', '.join(available_categories)}

Also extract:
- account_name: The name of the bank account
- account_type: Determine if this is a "Credit Card", "Debit Card", "Checking Account", "Savings Account", or "Other". Look for keywords like "Tarjeta de Crédito", "Credit Card", "Tarjeta de Débito", "Debit Card", "Cuenta de Cheques", "Checking", "Ahorros", "Savings", or similar indicators in the statement.
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
  "initial_balance": 232902.12
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
            # Try processing with the selected model, and if quota error, try other models
            models_to_retry = [model_name] + [name for name in model_names_to_try if name != model_name]
            
            for retry_model_name in models_to_retry:
                try:
                    # Create model instance for this retry
                    retry_model = genai.GenerativeModel(retry_model_name)
                    logger.info(f"Attempting to process with model: {retry_model_name}")
                    
                    # Upload the file to Gemini
                    if uploaded_file is None:
                        uploaded_file = genai.upload_file(path=pdf_file_path, mime_type='application/pdf')
                        
                        # Wait for file to be processed
                        while uploaded_file.state.name == "PROCESSING":
                            time.sleep(2)
                            uploaded_file = genai.get_file(uploaded_file.name)
                        
                        if uploaded_file.state.name == "FAILED":
                            raise Exception(f"File upload failed: {uploaded_file.state.name}")
                    
                    # Generate content with the uploaded file
                    response = retry_model.generate_content([prompt, uploaded_file])
                    model_name = retry_model_name  # Update to the model that worked
                    break  # Success! Exit the retry loop
                    
                except Exception as e:
                    error_str = str(e)
                    # Check if it's a quota/rate limit error
                    if '429' in error_str or 'quota' in error_str.lower() or 'ResourceExhausted' in error_str:
                        logger.warning(f"Quota exceeded for model {retry_model_name}, trying next model...")
                        last_error = e
                        continue  # Try next model
                    else:
                        # For other errors, log and re-raise
                        logger.error(f"Error with model {retry_model_name}: {str(e)}")
                        last_error = e
                        if retry_model_name == models_to_retry[-1]:
                            # Last model failed, raise the error
                            raise Exception(f"Failed to process PDF: {str(e)}")
                        continue
            
            # If we exhausted all models due to quota, raise a helpful error
            if response is None and last_error and ('429' in str(last_error) or 'quota' in str(last_error).lower()):
                raise Exception(
                    f"All models exceeded quota limits. Please check your Google AI Studio quota at "
                    f"https://ai.dev/usage?tab=rate-limit. "
                    f"Last error: {str(last_error)}"
                )
            
            if response is None:
                raise Exception("Failed to process PDF with any available model.")
                
        finally:
            # Clean up the uploaded file if it was created
            if uploaded_file:
                try:
                    genai.delete_file(uploaded_file.name)
                except Exception:
                    pass  # Ignore cleanup errors
        
        # Extract the text response
        response_text = response.text.strip()
        
        # Try to parse JSON from the response
        # Sometimes the AI wraps JSON in markdown code blocks
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        # Parse the JSON response
        try:
            extracted_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response text: {response_text}")
            return {
                'transactions': [],
                'account_name': None,
                'account_type': None,
                'statement_period': None,
                'initial_balance': None,  # Add this
                'raw_response': response_text,
                'error': f'Failed to parse AI response: {str(e)}'
            }
        
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
            
            # Mapping for common variations
            account_type_mapping = {
                'savings account': 'Savings',
                'checking account': 'Checking',
                'credit card': 'Credit Card',
                'debit card': 'Debit Card',
                'checking': 'Checking',
                'savings': 'Savings',
                'credit': 'Credit Card',
                'debit': 'Débito',
                'cash': 'Efectivo',
                'investment': 'Investment',
                'loan': 'Loan',
                'mortgage': 'Mortgage',
                'business': 'Business',
                'other': 'Other'
            }
            
            # Check exact match first
            if account_type_lower in account_type_mapping:
                return account_type_mapping[account_type_lower]
            
            # Check partial matches
            for key, value in account_type_mapping.items():
                if key in account_type_lower or account_type_lower in key:
                    return value
            
            # If it contains "savings", normalize to "Savings"
            if 'savings' in account_type_lower:
                return 'Savings'
            # If it contains "checking", normalize to "Checking"
            if 'checking' in account_type_lower:
                return 'Checking'
            # If it contains "credit", normalize to "Credit Card"
            if 'credit' in account_type_lower and 'card' in account_type_lower:
                return 'Credit Card'
            # If it contains "debit", normalize to "Débito"
            if 'debit' in account_type_lower and 'card' in account_type_lower:
                return 'Débito'
            
            # Return original if no match found
            return account_type
        
        # Validate and normalize the response structure
        raw_account_type = extracted_data.get('account_type', 'Other')
        normalized_account_type = normalize_account_type(raw_account_type)
        
        result = {
            'transactions': extracted_data.get('transactions', []),
            'account_name': extracted_data.get('account_name'),
            'account_type': normalized_account_type,  # Normalized account type
            'statement_period': extracted_data.get('statement_period'),
            'initial_balance': extracted_data.get('initial_balance'),  # Add this line
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
        validated_transactions = []
        for transaction in result['transactions']:
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
                    logger.warning(f"Invalid amount in transaction: {transaction}")
        
        result['transactions'] = validated_transactions
        
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


def is_pdf_password_protected(pdf_file) -> bool:
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


def decrypt_pdf_file(pdf_file, password: str) -> ContentFile:
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


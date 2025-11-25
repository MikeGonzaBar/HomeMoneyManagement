# MoneyManagement Backend

This Django project serves as the backend for the MoneyManagement application, handling various aspects of user management, accounts, and transactions.

## Requirements

In the `requirements.txt` file, specify the required Django and Django REST framework versions:

```text
Django == 4.2.5
djangorestframework == 3.14.0
```

## Settings

The project's settings are configured in the `settings.py` file. Key settings include:

- **SECRET_KEY**: A secret key used for cryptographic operations. Ensure it's kept confidential in production.

- **DEBUG**: Set to `True` for development. Disable in production for security.

- **INSTALLED_APPS**: List of installed Django applications, including `rest_framework`, `users`, `account`, `transaction`, etc.

- **DATABASES**: Configuration for the default SQLite database.

- **AUTH_PASSWORD_VALIDATORS**: Password validation rules for user passwords.

- **LANGUAGE_CODE**, **TIME_ZONE**, **USE_I18N**, **USE_L10N**, **USE_TZ**: Internationalization and timezone settings.

- **STATIC_URL**: URL prefix for static files.

- **DEFAULT_AUTO_FIELD**: Default primary key field type.

## Endpoints

This backend provides the following API endpoints:

- `/user/`: User-related endpoints for authentication and user profile management.

- `/accounts/`: Endpoints for managing user accounts and account information.

- `/transactions/`: Endpoints for managing transactions done by the user.

- `/bank-statements/`: Endpoints for uploading and managing bank statement PDFs with AI-powered transaction extraction.

Each endpoint offers specific functionalities related to the respective domain, facilitating efficient interaction with the frontend application.

### Users Endpoint

The Users endpoint provides functionalities related to user management, including user creation, login, and deletion.

#### Users Models

In the `models.py` file, the `User` model is defined with the following fields:

- `id`: Auto-incremented primary key.
- `username`: Unique username for the user.
- `password`: Password for the user.
- `first_name`: First name of the user.
- `last_name`: Last name of the user.

The `User` model also includes various methods for handling user data, such as checking for missing data, creating a new user, login authentication, and deleting a user.

#### Users Views

In the `views.py` file, the following views are defined for handling user-related requests:

- `UserPostGet`:
  - URL: `POST /user/`
  - Description: Creates a new user with the provided data.
  - Method: `POST`
  - Response:
    - Status 201 (Created)

      ```json
      {
        "id": 1,
        "username": "john_doe",
        "password": "********",  # Masked password for security
        "first_name": "John",
        "last_name": "Doe",
        "status": "User saved"
      }
      ```

    - Status 400 (Bad Request)

      ```json
      {
        "error": "data incomplete",
        "missing_args": ["password"]
      }
      ```

- `UserDetail`:
  - URL: `GET /user/<username>/`, `POST /user/<username>/`, `DELETE /user/<username>/`
  - Description: Provides user details, authenticates user login, and deletes a user.
  - Methods: `GET`, `POST`, `DELETE`
  - Response:
    - Status 200 (OK) - Login Successful

      ```json
      {
        "valid": true,
        "id": 1
      }
      ```

    - Status 400 (Bad Request) - Invalid Password

      ```json
      {
        "error": "Password incorrect"
      }
      ```

    - Status 403 (Forbidden) - Invalid Method (for `GET`)

      ```json
      {
        "error": "GET method not valid"
      }
      ```

#### Users URLs

In the `urls.py` file, the URLs for the Users endpoint are configured:

- `POST /user/`: Creates a new user.
- `GET /user/<username>/`: Retrieves user details (Not implemented).
- `POST /user/<username>/`: Authenticates user login.
- `DELETE /user/<username>/`: Deletes a user.

### Accounts Endpoint

The Accounts endpoint provides functionalities related to account management, including account creation, retrieval, updating, and deletion.

#### Accounts Models

In the `models.py` file, the `Account` model is defined with the following fields:

- `id`: Auto-incremented primary key.
- `account_type`: Type of the account.
- `bank`: Bank associated with the account.
- `total`: Total balance in the account.
- `account_name`: Name of the account.
- `owner`: Username of the account owner.

The `Account` model also includes various methods for handling account data, such as checking for missing data, creating a new account, retrieving user accounts, updating account details, and deleting an account.

#### Accounts Views

In the `views.py` file, the following views are defined for handling account-related requests:

- `AccountCreate`:
  - URL: `POST /accounts/`
  - Description: Creates a new account with the provided data.
  - Method: `POST`
  - Response:
    - Status 201 (Created)

      ```json
      {
        "id": 1,
        "account_type": "Savings",
        "bank": "Example Bank",
        "total": 5000.0,
        "account_name": "My Savings Account",
        "owner": "john_doe",
        "status": "Account saved"
      }
      ```

    - Status 400 (Bad Request)

      ```json
      {
        "error": "data incomplete",
        "missing_args": ["total"]
      }
      ```

- `AccountOps`:
  - URL: `GET /accounts/details/<username>/`, `PATCH /accounts/details/<username>/`
  - Description: Provides account details and allows updating the account balance.
  - Methods: `GET`, `PATCH`
  - Response:
    - Status 200 (OK) - Request successful

      ```json
      [
        {
          "id": 1,
          "account_type": "Savings",
          "bank": "Example Bank",
          "total": 5000.0,
          "account_name": "My Savings Account",
          "owner": "john_doe"
        },
        {
          "id": 2,
          "account_type": "Checking",
          "bank": "Another Bank",
          "total": 2500.0,
          "account_name": "My Checking Account",
          "owner": "john_doe"
        }
      ]
      ```

    - Status 400 (Bad Request) - Invalid request or missing data

      ```json
      {
        "error": "Account not found"
      }
      ```

- `AccountDelete`:
  - URL: `DELETE /accounts/delete/<username>/<id>/`
  - Description: Deletes an account for the specified user with the given ID.
  - Method: `DELETE`
  - Response:
    - Status 200 (OK) - Account deleted successfully

      ```json
      {
        "success": "Account deleted successfully"
      }
      ```

    - Status 400 (Bad Request) - Invalid request or account not found

      ```json
      {
        "error": "Account not found"
      }
      ```

#### Accounts URLs

In the `urls.py` file, the URLs for the Accounts endpoint are configured:

- `POST /accounts/`: Creates a new account.
- `GET /accounts/details/<username>/`: Retrieves account details for the specified user.
- `PATCH /accounts/details/<username>/`: Updates the account balance for the specified user.
- `DELETE /accounts/delete/<username>/<id>/`: Deletes an account for the specified user with the given ID.

### Transactions Endpoint

The Transactions endpoint provides functionalities related to managing financial transactions, including creating, retrieving, updating, and deleting transactions.

#### Transactions Models

In the `models.py` file, the `Transaction` model is defined with the following fields:

- `id`: Auto-incremented primary key.
- `transaction_type`: Type of the transaction.
- `category`: Category of the transaction.
- `date`: Date of the transaction.
- `title`: Title or description of the transaction.
- `total`: Total amount of the transaction.
- `owner_id`: Username of the transaction owner.
- `account_id`: Account ID associated with the transaction.

The `Transaction` model also includes various methods for handling transaction data, such as creating a new transaction, retrieving transactions, updating transaction details, and deleting a transaction.

#### Transactions Views

In the `views.py` file, the following views are defined for handling transaction-related requests:

- `TransactionCreate`:
  - URL: `POST /transactions/create/`
  - Description: Creates a new transaction with the provided data.
  - Method: `POST`
  - Response:
    - Status 201 (Created)

      ```json
      {
        "id": 1,
        "transaction_type": "Expense",
        "category": "Groceries",
        "date": "2023-09-30",
        "title": "Grocery shopping",
        "total": 50.0,
        "owner_id": "john_doe",
        "account_id": "1234",
        "status": "transaction saved"
      }
      ```

    - Status 400 (Bad Request)

      ```json
      {
        "error": "data incomplete",
        "missing_args": ["total"]
      }
      ```

- `TransactionRetrieve`:
  - URL: `GET /transactions/retrieve/<username>/<account_id>/<month>/<year>/`
  - Description: Retrieves transactions based on the provided parameters.
  - Method: `GET`
  - Response:
    - Status 200 (OK) - Request successful

      ```json
      [
        {
          "id": 1,
          "transaction_type": "Expense",
          "category": "Groceries",
          "date": "2023-09-30",
          "title": "Grocery shopping",
          "total": 50.0,
          "owner_id": "john_doe",
          "account_id": "1234"
        },
        {
          "id": 2,
          "transaction_type": "Income",
          "category": "Salary",
          "date": "2023-09-15",
          "title": "Monthly salary",
          "total": 3000.0,
          "owner_id": "john_doe",
          "account_id": "5678"
        }
      ]
      ```

    - Status 400 (Bad Request) - Invalid request or missing data

      ```json
      {
        "error": "Account not found"
      }
      ```

- `TransactionUpdate`:
  - URL: `PATCH /transactions/update/<transaction_id>/`
  - Description: Updates an existing transaction based on the provided data.
  - Method: `PATCH`
  - Response:
    - Status 200 (OK) - Transaction updated successfully

      ```json
      {
        "success": "Transaction updated successfully",
        "updated_transaction": {
          "id": 1,
          "transaction_type": "Expense",
          "category": "Groceries",
          "date": "2023-09-30",
          "title": "Grocery shopping",
          "total": 40.0,
          "owner_id": "john_doe",
          "account_id": "1234"
        }
      }
      ```

    - Status 400 (Bad Request) - Invalid request or transaction not found

      ```json
      {
        "error": "Transaction not found"
      }
      ```

- `TransactionDelete`:
  - URL: `DELETE /transactions/delete/<transaction_id>/`
  - Description: Deletes a transaction based on the provided transaction ID.
  - Method: `DELETE`
  - Response:
    - Status 200 (OK) - Transaction deleted successfully

      ```json
      {
        "success": "Transaction deleted successfully"
      }
      ```

    - Status 400 (Bad Request) - Invalid request or transaction not found

      ```json
      {
        "error": "Transaction not found"
      }
      ```

#### Transactions URLs

In the `urls.py` file, the URLs for the Transactions endpoint are configured:

- `POST /transactions/create/`: Creates a new transaction.
- `GET /transactions/retrieve/<username>/<account_id>/<month>/<year>/`: Retrieves transactions based on provided parameters.
- `PATCH /transactions/update/<transaction_id>/`: Updates an existing transaction.
- `DELETE /transactions/delete/<transaction_id>/`: Deletes a transaction.

### Bank Statements Endpoint

The Bank Statements endpoint provides functionalities for uploading PDF bank statements and automatically extracting transaction data using Google AI Studio (Gemini API).

#### Bank Statements Views

- `upload_bank_statement`:
  - URL: `POST /bank-statements/upload/`
  - Description: Uploads a bank statement PDF and processes it with AI to extract transactions.
  - Method: `POST`
  - Request: Form data with `pdf_file` (PDF file) and `user_id` (username)
  - Response:
    - Status 200 (OK) - Upload successful with extracted data

      ```json
      {
        "message": "Bank statement uploaded successfully",
        "file_details": {
          "id": 1,
          "filename": "statement.pdf",
          "file_size": 123456,
          "file_size_display": "120.6 KB",
          "upload_date": "2024-01-15T10:30:00Z",
          "processing_status": "completed"
        },
        "status": "success",
        "extracted_data": {
          "transactions": [
            {
              "date": "2024-01-15",
              "title": "Grocery Store Purchase",
              "amount": 125.50,
              "transaction_type": "Expense",
              "category": "Food and drinks"
            }
          ],
          "account_name": "Checking Account",
          "account_type": "Credit Card",
          "statement_period": {
            "start": "2024-01-01",
            "end": "2024-01-31"
          },
          "processing_error": null
        }
      }
      ```

    - Status 400 (Bad Request) - Invalid file or missing data

- `get_user_bank_statements`:
  - URL: `GET /bank-statements/user/<user_id>/`
  - Description: Retrieves all bank statements for a specific user.
  - Method: `GET`
  - Response: List of bank statements with metadata

- `get_bank_statement_details`:
  - URL: `GET /bank-statements/details/<statement_id>/`
  - Description: Retrieves details of a specific bank statement.
  - Method: `GET`
  - Response: Bank statement details including file information and processing status

- `delete_bank_statement`:
  - URL: `DELETE /bank-statements/delete/<statement_id>/`
  - Description: Deletes a bank statement and its associated file.
  - Method: `DELETE`
  - Response: Success message

#### Bank Statements URLs

In the `urls.py` file, the URLs for the Bank Statements endpoint are configured:

- `POST /bank-statements/upload/`: Uploads and processes a bank statement PDF.
- `GET /bank-statements/user/<user_id>/`: Retrieves all bank statements for a user.
- `GET /bank-statements/details/<statement_id>/`: Retrieves details of a specific statement.
- `DELETE /bank-statements/delete/<statement_id>/`: Deletes a bank statement.

**Note**: Bank statement processing requires Google AI Studio API key configuration. See [GOOGLE_AI_SETUP.md](GOOGLE_AI_SETUP.md) for setup instructions.

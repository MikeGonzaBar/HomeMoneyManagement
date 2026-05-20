# MoneyManagement Backend

This Django REST API powers Budget Buddy's users, accounts, transactions, bank statements, and reports. All application data endpoints require DRF-style opaque token authentication.

## Requirements

```text
Django == 4.2.24
djangorestframework == 3.15.2
django-cors-headers == 4.2.0
psycopg2-binary == 2.9.9
google-genai >= 1.0.0
python-dotenv >= 1.0.0
pypdf >= 3.0.0
gunicorn >= 22.0.0
```

## Local Setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py test
python manage.py runserver
```

Migrations are committed to the repo. Do not run `makemigrations` at container startup.

## Authentication

Register and login return the same response shape:

```json
{
  "valid": true,
  "token": "<opaque-token>",
  "user": {
    "id": 1,
    "username": "john_doe",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

Use the token on every authenticated request:

```http
Authorization: Token <opaque-token>
```

Unauthenticated requests return `401`. Routes that still include a username are compatibility routes; the server derives the effective user from the token. If a route username does not match the token user, the API returns `403`.

## Configuration

Development defaults are intentionally convenient. Production must be explicit:

- `SECRET_KEY`: required and must not use the development fallback when `DEBUG=False`.
- `DEBUG`: set to `False` in production.
- `ALLOWED_HOSTS`: required when `DEBUG=False`; wildcard hosts are rejected.
- `CORS_ALLOWED_ORIGINS`: required when `DEBUG=False`.
- `CORS_ALLOW_ALL_ORIGINS`: must be `False` when `DEBUG=False`.
- `DATABASE_URL` or `USE_POSTGRES=true`: enables PostgreSQL. Otherwise local SQLite is used.
- `GOOGLE_AI_API_KEY`: enables Gemini-powered statement extraction and report insights. `GOOGLE_API_KEY` and `GEMINI_API_KEY` are accepted as aliases for local compatibility.
- `GOOGLE_AI_MODEL`: optional Gemini model override; defaults to `gemini-2.5-flash`.
- `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and `SECURE_HSTS_SECONDS`: default to secure production values when `DEBUG=False`; override only if a trusted proxy handles the behavior.
- `SECURE_HSTS_PRELOAD`: defaults to `False`; set to `True` only when the production domain and subdomains are ready for HSTS preload behavior.

Production checks:

```bash
DEBUG=False \
SECRET_KEY=replace-me-with-a-long-secret \
ALLOWED_HOSTS=example.com \
CORS_ALLOWED_ORIGINS=https://example.com \
CORS_ALLOW_ALL_ORIGINS=False \
SECURE_SSL_REDIRECT=True \
SESSION_COOKIE_SECURE=True \
CSRF_COOKIE_SECURE=True \
SECURE_HSTS_SECONDS=31536000 \
SECURE_HSTS_PRELOAD=True \
python manage.py check --deploy
```

Production serving should run migrations once and serve with Gunicorn:

```bash
python manage.py migrate
gunicorn --bind 0.0.0.0:8000 --workers=4 MoneyManagement.wsgi:application
```

## Ownership And Money Rules

- Accounts are created for `request.user`; request body `owner` is ignored.
- Transactions and bank statements are created for `request.user`; request body ownership fields are compatibility-only.
- Account and transaction lookups are scoped by authenticated owner.
- Cross-user account references are rejected with `400`; another user's object ID is not exposed.
- Account totals, credit limits, and transaction totals are stored as decimals.
- Transaction create, update, and delete adjust balances inside a database transaction.
- Income increases the selected account balance.
- Expense decreases the selected account balance.
- Transfer decreases the source account and increases the destination account.
- Credit-card balances use the same signed movement semantics as the UI's available-credit model.

Legacy string fields such as `owner`, `owner_id`, `account_id`, `from_account_id`, `to_account_id`, and `user_id` are still populated for compatibility, but new integrity is anchored by foreign keys.

## Endpoints

### Users

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `POST` | `/user/register/` | No | Register and receive a token. |
| `POST` | `/user/login/` | No | Login with `username_or_email` and `password`. |
| `POST` | `/user/logout/` | Yes | Revoke the current token. |
| `GET` | `/user/profile/` | Yes | Return the authenticated user profile. |
| `PUT` | `/user/update-info/` | Yes | Update the authenticated user's username/name. |
| `PUT` | `/user/change-password/` | Yes | Change the authenticated user's password. |
| `GET` | `/user/detail/<username>/` | Yes | Return details only for the token user. |
| `DELETE` | `/user/detail/<username>/` | Yes | Delete only the token user's account after password confirmation. |

Legacy `POST /user/` and `POST /user/<username>/` remain available for register/login compatibility.

### Accounts

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/accounts/` | Create an account for the token user. |
| `GET` | `/accounts/details/<username>/<id>/` | List all accounts for the token user; `<id>` is ignored for compatibility. |
| `PATCH` | `/accounts/details/<username>/<id>/` | Update one owned account. |
| `DELETE` | `/accounts/delete/<username>/<id>/` | Delete one owned account unless protected by transactions. |

Example create payload:

```json
{
  "account_name": "Checking",
  "account_type": "Debit",
  "bank": "Example Bank",
  "total": 5000,
  "credit_limit": null
}
```

### Transactions

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/transactions/create/` | Create a transaction and apply its balance effect. |
| `GET` | `/transactions/retrieve/<username>/<account_id>/<month>/<year>/` | Retrieve owned transactions. Use `0` as a wildcard for account/month/year. |
| `PATCH` | `/transactions/update/<transaction_id>/` | Reverse the old effect, apply the new effect, and save. |
| `DELETE` | `/transactions/delete/<transaction_id>/` | Reverse the stored effect and delete. |

Income or expense payload:

```json
{
  "transaction_type": "Expense",
  "category": "Groceries",
  "date": "2026-05-20",
  "title": "Market",
  "total": 50.25,
  "account_id": "1"
}
```

Transfer payload:

```json
{
  "transaction_type": "Transfer",
  "category": "Transfer",
  "date": "2026-05-20",
  "title": "Move to savings",
  "total": 200,
  "from_account_id": "1",
  "to_account_id": "2"
}
```

### Bank Statements

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/bank-statements/upload/` | Upload a PDF statement for the token user. |
| `GET` | `/bank-statements/user/<user_id>/` | List statements for the token user. |
| `GET` | `/bank-statements/details/<statement_id>/` | Get one owned statement. |
| `DELETE` | `/bank-statements/delete/<statement_id>/` | Delete one owned statement. |

Upload form data accepts `pdf_file` and optional `password`. Any submitted `user_id` is ignored as authority.

### Reports

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/reports/analytics/<username>/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` | KPIs, chart data, net worth, categories, and insights for the token user. |
| `GET` | `/reports/insights/<username>/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` | Smart insight payload for the token user. |

If `GOOGLE_AI_API_KEY` is configured, report insights use Gemini. Otherwise the API returns deterministic data-driven fallback insights.

## Regression Commands

```bash
python manage.py test
python manage.py check --deploy
```

In Docker:

```bash
docker compose run --rm money-management-api python /HomeMoneyManagement/manage.py test
docker compose run --rm \
  -e DEBUG=False \
  -e SECRET_KEY=replace-me-with-a-long-secret \
  -e ALLOWED_HOSTS=localhost,127.0.0.1 \
  -e CORS_ALLOWED_ORIGINS=http://localhost:8080 \
  -e CORS_ALLOW_ALL_ORIGINS=False \
  -e SECURE_HSTS_PRELOAD=True \
  money-management-api python /HomeMoneyManagement/manage.py check --deploy
```

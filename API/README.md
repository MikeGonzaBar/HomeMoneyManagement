# MoneyManagement Backend

This Django REST API powers Budget Buddy's users, accounts, transactions, budgets, recurring transactions, bank statements, reports, and in-app alerts. All application data endpoints require DRF-style opaque token authentication.

**Current API version:** v1.1.1

## Release Highlights

- v1.1.1 aligns API schema metadata with the app release; no API contract changes are required for the phone UI fix
- API admin mode at `/api-admin/` for safe user management and token revocation
- OpenAPI schema at `/schema/` and Swagger UI at `/docs/` when `API_DOCS_ENABLED=True`
- `is_admin` is included in authenticated user payloads and can be managed by existing API admins
- Docker keeps raw API, admin, and docs access private on `127.0.0.1` by default

## Requirements

```text
Django == 4.2.30
djangorestframework == 3.15.2
django-cors-headers == 4.2.0
psycopg2-binary == 2.9.9
setuptools >= 75.0.0
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
    "last_name": "Doe",
    "theme_preference": "system",
    "is_admin": false
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
- `API_DOCS_ENABLED`: enables `/schema/` and `/docs/`; defaults to the value of `DEBUG`.
- `GOOGLE_AI_API_KEY`: enables Gemini-powered statement extraction and report insights. `GOOGLE_API_KEY` and `GEMINI_API_KEY` are accepted as aliases for local compatibility.
- `GOOGLE_AI_MODEL`: optional Gemini model override; defaults to `gemini-3.8-flash`.
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

Docker binds the API to `127.0.0.1:${API_HOST_PORT:-8000}` by default so raw API, Django admin, and Swagger access stay private on a VM. The UI remains public on `${UI_HOST_PORT:-8080}` and proxies `/api/` and `/media/` to the API container over the Docker network. PostgreSQL is internal-only unless you intentionally add a host port. The API container uses Gunicorn with configurable workers/threads, and `DB_CONN_MAX_AGE` defaults to 60 seconds.

PostgreSQL query metrics are enabled through `pg_stat_statements`. Inspect them with:

```sql
SELECT calls, total_exec_time, query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```

Use an SSH tunnel for remote admin/API/docs access:

```bash
ssh -L 8000:127.0.0.1:8000 user@vm
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
- Transfer transactions require different source and destination accounts.
- Transfers are not counted as income or expense in reports.
- Credit-card balances use the same signed movement semantics as the UI's available-credit model.
- Budgets are monthly and scoped to the authenticated user.
- Recurring rules generate due occurrences; real transactions are created only when an occurrence is posted.
- Import review candidates can be imported, skipped, or linked to an existing transaction.
- Import batch commits are idempotent; already processed candidates are ignored on repeat commits.
- Alerts are owner-scoped and in-app only.
- User preferences currently include `theme_preference`: `system`, `light`, or `dark`.

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
| `GET` | `/user/preferences/` | Yes | Return persisted user preferences. |
| `PUT` | `/user/preferences/` | Yes | Update persisted preferences such as `theme_preference`. |
| `GET` | `/user/detail/<username>/` | Yes | Return details only for the token user. |
| `DELETE` | `/user/detail/<username>/` | Yes | Delete only the token user's account after password confirmation. |

Legacy `POST /user/` and `POST /user/<username>/` remain available for register/login compatibility.

### API Admin

API admin endpoints use the same `Authorization: Token <opaque-token>` header, but require the token user to have `is_admin=True`. Promote or demote users with:

```bash
python manage.py set_api_admin <username> --enabled true
python manage.py set_api_admin <username> --enabled false
```

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api-admin/users/` | List API users without passwords or token values. |
| `PATCH` | `/api-admin/users/<id>/` | Update safe fields including `first_name`, `last_name`, `theme_preference`, and `is_admin`. |
| `POST` | `/api-admin/users/<id>/tokens/revoke/` | Revoke all active API tokens for a user. |

### OpenAPI Docs

When `API_DOCS_ENABLED=True`, the OpenAPI schema is available at `/schema/` and Swagger UI is available at `/docs/`. In Docker these routes are private by default because the API host port binds to `127.0.0.1`.

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

### Budgets

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/budgets/?month=YYYY-MM` | List budgets for the token user and month. |
| `POST` | `/budgets/` | Create an owned monthly budget. |
| `GET` | `/budgets/<id>/` | Retrieve one owned budget. |
| `PATCH` | `/budgets/<id>/` | Update one owned budget. |
| `DELETE` | `/budgets/<id>/` | Delete one owned budget. |
| `GET` | `/budgets/summary/?month=YYYY-MM` | Return summary rows with calculated spend, remaining, percent used, and status. |

Budget payload:

```json
{
  "month": "2026-05",
  "scope": "category",
  "category": "Groceries",
  "limit_amount": 450
}
```

Use `"scope": "overall"` with `"category": null` for an overall monthly budget.

### Recurring Transactions

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/recurring-transactions/` | List recurring rules for the token user. |
| `POST` | `/recurring-transactions/` | Create a recurring income, expense, or transfer rule. |
| `GET` | `/recurring-transactions/<id>/` | Retrieve one owned recurring rule. |
| `PATCH` | `/recurring-transactions/<id>/` | Update one owned recurring rule. |
| `DELETE` | `/recurring-transactions/<id>/` | Delete one owned recurring rule. |
| `GET` | `/recurring-transactions/due/?through=YYYY-MM-DD` | Generate/list due occurrences through a date. |
| `POST` | `/recurring-transactions/due/<occurrence_id>/post/` | Confirm and post a due occurrence as a real transaction. |
| `POST` | `/recurring-transactions/due/<occurrence_id>/skip/` | Skip a due occurrence. |

Recurring rules use the same transaction template fields as manual transactions plus:

```json
{
  "frequency": "monthly",
  "interval": 1,
  "start_date": "2026-05-01",
  "next_due_date": "2026-06-01",
  "end_date": null,
  "active": true
}
```

### Bank Statements

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/bank-statements/upload/` | Upload a PDF statement for the token user. |
| `GET` | `/bank-statements/user/<user_id>/` | List statements for the token user. |
| `GET` | `/bank-statements/details/<statement_id>/` | Get one owned statement. |
| `DELETE` | `/bank-statements/delete/<statement_id>/` | Delete one owned statement. |
| `GET` | `/bank-statements/import-batches/<id>/` | Retrieve an owned persisted import review batch. |
| `PATCH` | `/bank-statements/import-candidates/<id>/` | Set a candidate decision: import, skip, or link to an existing transaction. |
| `POST` | `/bank-statements/import-batches/<id>/commit/` | Idempotently commit candidate decisions. |

Upload form data accepts `pdf_file` and optional `password`. Any submitted `user_id` is ignored as authority. Upload responses still include extracted data for compatibility and also return a `review_batch_id` for reconciliation.

Candidate matching detects possible duplicates by owner, account, date, amount, normalized title, and transaction type. The client can import new transactions, skip rows, or link candidates to existing transactions.

### Reports

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/reports/analytics/<username>/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` | KPIs, chart data, net worth, categories, and insights for the token user. |
| `GET` | `/reports/insights/<username>/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` | Smart insight payload for the token user. |
| `GET` | `/reports/forecast/<username>/?months=6` | Cashflow forecast for up to 12 months. |

If `GOOGLE_AI_API_KEY` is configured, report insights use Gemini. Otherwise the API returns deterministic data-driven fallback insights.

Forecasting uses current balances, confirmed real transactions through today, active recurring transactions for future known items, monthly category budgets where configured, and trailing 3-month category averages where no budget or recurring data exists.

### Alerts

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/alerts/` | List non-dismissed alerts for the token user. |
| `POST` | `/alerts/refresh/` | Regenerate budget, recurring, forecast, and import-review alerts. |
| `PATCH` | `/alerts/<id>/read/` | Mark an owned alert as read. |
| `PATCH` | `/alerts/<id>/dismiss/` | Dismiss an owned alert. |

V1 alert types cover budget 80%/100% thresholds, recurring due/overdue items, forecasted negative balances within 30 days, and import candidates with possible duplicate matches.

## Container And Dependency Security

The current Docker stack uses Alpine 3.23-based runtime images:

- API: `python:3.12.13-alpine3.23`
- UI builder: `node:lts-alpine3.23`
- UI runtime: `nginx:stable-alpine3.23`
- Database: `postgres:15.18-alpine3.23` with locally built `gosu`

Before broad testing or release, run:

```bash
docker compose build
docker run --rm -v "${PWD}:/repo" -w /repo/UI/home-money-management node:lts-alpine3.23 npm audit --audit-level=high
```

The latest hardening pass verified 0 high/critical findings for the API image, UI image, Postgres image, API `requirements.txt`, and UI `package-lock.json` via Trivy.

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

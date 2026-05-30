# Home Money Management - Frontend

Vue 3 + Vuetify frontend for Budget Buddy. The app covers dashboard analytics, transactions and transfers, monthly budgets, recurring due-item confirmation, statement import reconciliation, reports/forecasting, in-app alerts, and persisted light/dark/system theme preferences.

**Current frontend version:** v1.1.1

## Release Notes

- Adds phone-only authenticated layout fixes below the existing `sm` breakpoint.
- Keeps logo, notification, theme toggle, avatar, and navigation reachable on phone widths.
- Moves the Transactions export action into page content on phone so it no longer overlaps the header.
- Adds contained horizontal scrolling for mobile transaction, budget, and recurring tables.
- Aligns the frontend package release with the v1.1.1 app tag.
- Continues to use token-based sessions that include the backend `is_admin` flag in the stored user payload.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Technology Stack

- **Vue.js 3** - Progressive JavaScript framework
- **TypeScript** - Type-safe JavaScript
- **Vuetify 3** - Material Design component framework
- **Chart.js** - Data visualization library
- **Vite** - Build tool and development server
- **Vue Router** - Client-side routing

## Main Screens

- **Dashboard**: Account carousel, budget snapshot, recurring due-soon panel, transaction history, projections, and category charts.
- **Transactions**: Income, expense, and first-class transfer flows. Transfers use separate source/destination accounts and are excluded from income/expense totals.
- **Budgets**: Overall and category monthly budgets with limit, spent, remaining, progress, and status.
- **Recurring**: Rule management for income, expense, and transfer templates. Due occurrences must be posted or skipped by the user.
- **Reports**: KPIs, cashflow forecast, income/expense charts, net worth growth, and category trends.
- **Profile**: User details, uploaded bank statements, unfinished import review batches, and theme preference.
- **Alert Center**: Bell popover for budget thresholds, due/overdue recurring items, negative-balance forecasts, and import duplicate-review alerts.

## Development

The Vite development server runs on `http://localhost:3000` and proxies `/api` requests to the Django API at `http://localhost:8000`.

Docker serves the production build through Nginx on `http://localhost:8080`.

### Project Layout

```text
src/
├── components/      # Reusable UI such as AlertCenter, ThemeToggle, BankStatementReview
├── views/           # Route screens: Home, Transactions, Budgets, Recurring, Reports, Profile
├── layouts/         # App shell and navigation
├── router/          # Vue Router route definitions
├── plugins/         # Vuetify registration
├── services/        # API client, session helpers, money formatting, theme persistence
├── styles/          # Shared SCSS settings
└── App.vue          # Global app shell and theme-aware CSS
```

### API Configuration

- `VITE_API_BASE_URL` controls the browser-facing API base URL. It defaults to `/api`.
- `VITE_API_PROXY_TARGET` controls the Vite dev proxy target. It defaults to `http://localhost:8000`.

### Authentication

- Login and registration store only `{ token, user }` under `money_management_user`.
- API requests automatically send `Authorization: Token <token>`.
- A `401` response clears the saved session so stale or revoked tokens do not linger.
- Legacy localStorage shapes are treated as invalid and cleared.

### Theme Behavior

- Theme preference is persisted on the backend through `GET/PUT /user/preferences/`.
- Supported values are `system`, `light`, and `dark`.
- `src/services/theme.ts` applies the active mode on login/app load and keeps the quick header toggle in sync.
- Dark-mode route/page overrides should live under the global `.app-dark .v-application ...` selectors in `App.vue`. Avoid scoped `:global(.app-dark)` page rules because they can compile into broad selectors and leak styles after route navigation.

### Feature Notes

- Budgets and recurring pages call owner-scoped APIs and expect token-based auth.
- Recurring transactions use confirm-due behavior: listing due occurrences does not create real transactions until the user posts one.
- Bank statement uploads still expose extracted rows, but review batches are persisted so users can return later from Profile/My Files.
- Import reconciliation supports import, skip, and link-to-existing decisions. Commits are idempotent.
- Alert refresh is in-app only; browser notifications and email are intentionally out of scope.

### Validation

```bash
npm run build
```

`npm run build` runs `vue-tsc --noEmit` before `vite build`.

For the production container:

```bash
docker compose build money-management-ui
```

For dependency auditing before broad testing:

```bash
docker run --rm -v "${PWD}:/repo" -w /repo/UI/home-money-management node:lts-alpine3.23 npm audit --audit-level=high
```

The current high/critical audit baseline passes. The remaining npm advisory is moderate and tied to the Vite/esbuild development server path.

### Dependency Notes

- The frontend Docker build uses `node:lts-alpine3.23`; the runtime image uses `nginx:stable-alpine3.23`.
- `axios` is pinned to the hardened `^1.16.1` range.
- Legacy Vue CLI-era dependencies were removed because this app builds with Vite.

For detailed project documentation, see the [main README.md](../../README.md).

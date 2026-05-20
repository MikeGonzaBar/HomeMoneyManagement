# Home Money Management - Frontend

Vue.js 3 frontend application for the Home Money Management system.

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

## Development

The Vite development server runs on `http://localhost:3000` and proxies `/api` requests to the Django API at `http://localhost:8000`.

Docker serves the production build through Nginx on `http://localhost:8080`.

### API Configuration

- `VITE_API_BASE_URL` controls the browser-facing API base URL. It defaults to `/api`.
- `VITE_API_PROXY_TARGET` controls the Vite dev proxy target. It defaults to `http://localhost:8000`.

### Authentication

- Login and registration store only `{ token, user }` under `money_management_user`.
- API requests automatically send `Authorization: Token <token>`.
- A `401` response clears the saved session so stale or revoked tokens do not linger.
- Legacy localStorage shapes are treated as invalid and cleared.

### Validation

```bash
npx vue-tsc --noEmit
npm run build
```

For detailed project documentation, see the [main README.md](../../README.md).

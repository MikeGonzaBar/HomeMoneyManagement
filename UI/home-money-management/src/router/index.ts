// Composables
import { createRouter, createWebHistory } from 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    /** Page title fragment, rendered as "<fragment> | Budget Buddy". */
    title?: string
    /** Per-route <meta name="description">; falls back to the index.html default. */
    description?: string
  }
}

const routes = [
  {
    path: '/',
    name: 'Home',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "home" */ '@/views/Home.vue'),
    // No meta on purpose: Home keeps the index.html title/description.
  },
  {
    path: '/profile',
    name: 'Profile',
    meta: {
      title: 'Profile',
      description: 'Manage your Budget Buddy account, security settings and preferences.',
    },
    component: () => import(/* webpackChunkName: "profile" */ '@/views/Profile.vue'),
  },
  {
    path: '/transactions',
    name: 'Transactions',
    meta: {
      title: 'Transactions',
      description: 'Review, filter and categorise transactions across all of your accounts.',
    },
    component: () => import(/* webpackChunkName: "transactions" */ '@/views/Transactions.vue'),
  },
  {
    path: '/budgets',
    name: 'Budgets',
    meta: {
      title: 'Budgets',
      description: 'Set monthly category budgets and track spending against them.',
    },
    component: () => import(/* webpackChunkName: "budgets" */ '@/views/Budgets.vue'),
  },
  {
    path: '/recurring',
    name: 'Recurring',
    meta: {
      title: 'Recurring',
      description: 'Manage recurring income, bills and subscriptions in Budget Buddy.',
    },
    component: () => import(/* webpackChunkName: "recurring" */ '@/views/Recurring.vue'),
  },
  {
    path: '/reports',
    name: 'Reports',
    meta: {
      title: 'Reports',
      description: 'Financial analytics, cashflow forecasts and spending reports.',
    },
    component: () => import(/* webpackChunkName: "reports" */ '@/views/Reports.vue'),
  },
  {
    path: '/statements',
    name: 'Statements',
    meta: {
      title: 'Statements',
      description: 'Upload and import bank statements to reconcile your accounts.',
    },
    component: () => import(/* webpackChunkName: "statements" */ '@/views/Statements.vue'),
  },
  {
    path: '/statements/:batchId/review',
    name: 'ImportReview',
    meta: {
      title: 'Review Import',
      description: 'Review and confirm the transactions detected in an imported statement.',
    },
    component: () => import(/* webpackChunkName: "import-review" */ '@/views/ImportReview.vue'),
  },
  {
    path: '/statements/:batchId/scan-result',
    name: 'StatementScanResult',
    meta: { title: 'Statement Scan Result', description: 'Review an AI statement scan with no importable transactions.' },
    component: () => import(/* webpackChunkName: "statement-scan-result" */ '@/views/StatementScanResult.vue'),
  },
  {
    path: '/accounts',
    name: 'Accounts',
    meta: {
      title: 'Accounts',
      description: 'Track balances across your bank, credit and investment accounts.',
    },
    component: () => import(/* webpackChunkName: "accounts" */ '@/views/Accounts.vue'),
  },
  {
    path: '/privacy-policy',
    name: 'PrivacyPolicy',
    meta: {
      title: 'Privacy Policy',
      description: 'How Budget Buddy collects, uses and protects your financial data.',
    },
    component: () => import(/* webpackChunkName: "privacy-policy" */ '@/views/PrivacyPolicy.vue'),
  },
  {
    path: '/terms-of-service',
    name: 'TermsOfService',
    meta: {
      title: 'Terms of Service',
      description: 'Terms and conditions for using the Budget Buddy application.',
    },
    component: () => import(/* webpackChunkName: "terms-of-service" */ '@/views/TermsOfService.vue'),
  },
  {
    path: '/help',
    name: 'HelpCenter',
    meta: {
      title: 'Help Center',
      description: 'Guides and answers for getting the most out of Budget Buddy.',
    },
    component: () => import(/* webpackChunkName: "help-center" */ '@/views/HelpCenter.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
})

/**
 * Per-route document metadata. The server only ever sends index.html (SPA), so
 * the title/description have to be swapped on navigation here. Both defaults
 * are captured from index.html once so routes without meta fall back cleanly.
 */
const DEFAULT_TITLE = document.title
const DEFAULT_DESCRIPTION =
  document.querySelector<HTMLMetaElement>('meta[name="description"]')?.content ?? ''

router.afterEach(to => {
  document.title = to.meta.title ? `${to.meta.title} | Budget Buddy` : DEFAULT_TITLE

  document
    .querySelector<HTMLMetaElement>('meta[name="description"]')
    ?.setAttribute('content', to.meta.description || DEFAULT_DESCRIPTION)
})

// A deploy replaces hashed asset filenames. A tab left open across a deploy can
// request a lazy chunk (route JS or its CSS) that no longer exists, so the
// dynamic import rejects and navigation silently dies. Detect that specific
// failure and offer a one-click reload that preserves uploads/drafts (they live
// server-side), instead of leaving a dead navigation control.
const CHUNK_ERROR_MARKERS = [
  'Failed to fetch dynamically imported module',
  'Unable to preload CSS',
  'error loading dynamically imported module',
  'Importing a module script failed',
  'Unable to preload',
]

function isChunkLoadError(error: unknown): boolean {
  if (!error) return false
  const message = typeof error === 'string' ? error : (error as { message?: string })?.message || String(error)
  return CHUNK_ERROR_MARKERS.some(marker => message.includes(marker))
}

// Guard against a reload loop if the reloaded bundle is itself stale.
const RELOAD_GUARD_KEY = 'bb-chunk-reload-at'

function offerReloadForStaleAssets(): void {
  const lastReload = Number(sessionStorage.getItem(RELOAD_GUARD_KEY) || '0')
  const now = Date.now()
  if (now - lastReload < 10_000) {
    // Already reloaded moments ago and still failing: do not loop. Surface a
    // manual control so the user is never left with a dead page.
    renderStaleAssetBanner(true)
    return
  }
  sessionStorage.setItem(RELOAD_GUARD_KEY, String(now))
  renderStaleAssetBanner(false, () => window.location.reload())
}

function renderStaleAssetBanner(manualOnly: boolean, onReload?: () => void): void {
  if (document.getElementById('bb-stale-asset-banner')) return
  const banner = document.createElement('div')
  banner.id = 'bb-stale-asset-banner'
  banner.setAttribute('role', 'alert')
  banner.style.cssText = [
    'position:fixed', 'left:50%', 'bottom:24px', 'transform:translateX(-50%)',
    'z-index:9999', 'display:flex', 'gap:12px', 'align-items:center',
    'background:#111827', 'color:#f9fafb', 'padding:12px 16px',
    'border-radius:12px', 'box-shadow:0 8px 24px rgba(0,0,0,0.25)',
    'font:500 14px system-ui, sans-serif', 'max-width:92vw',
  ].join(';')
  const text = document.createElement('span')
  text.textContent = manualOnly
    ? 'A new version is available but could not load automatically. Reload to continue.'
    : 'A new version of Budget Buddy is available. Reload to load it — your uploads and drafts are saved.'
  banner.appendChild(text)
  const button = document.createElement('button')
  button.type = 'button'
  button.textContent = 'Reload'
  button.style.cssText = [
    'background:#4f46e5', 'color:#fff', 'border:0', 'padding:6px 14px',
    'border-radius:8px', 'cursor:pointer', 'font:600 14px system-ui, sans-serif',
  ].join(';')
  button.addEventListener('click', () => (onReload ? onReload() : window.location.reload()))
  banner.appendChild(button)
  document.body.appendChild(banner)
}

router.onError(error => {
  if (isChunkLoadError(error)) {
    offerReloadForStaleAssets()
  } else {
    console.error('Router navigation error:', error)
  }
})

export default router

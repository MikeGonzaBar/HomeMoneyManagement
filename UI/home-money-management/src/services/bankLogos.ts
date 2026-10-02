/**
 * Bank logos via the Brandfetch Logo API.
 * https://docs.brandfetch.com/logo-api/overview
 *
 * Two constraints from Brandfetch drive the whole design:
 *
 * 1. The Logo API is a **CDN URL meant for an `<img src>`**, not a JSON
 *    endpoint. Fetching it with XHR/`fetch` is treated as automated traffic and
 *    redirected (302 `automated_traffic`), so this module only ever *builds* a
 *    URL - the browser loads the image itself. See `BankLogo.vue`.
 * 2. It identifies a brand by **domain** (or ticker/ISIN/crypto), never by a
 *    display name. Our `Account.bank` is free text ("Banamex", "Chase"), so it
 *    has to be mapped to a domain first.
 *
 * The client ID is read from `VITE_BRANDFETCH_CLIENT_ID`. Brandfetch's docs
 * have you embed it in pages, so it is not a server secret - but it is still a
 * credential with a monthly allowance, so it is env-driven and never hardcoded.
 * With no client ID the app is unchanged: callers fall back to their own avatar.
 */

/** Curated name -> domain map for banks we actually see in the data. */
const BANK_DOMAINS: Readonly<Record<string, string>> = {
  // Mexico
  bbva: 'bbva.com',
  banorte: 'banorte.com',
  banamex: 'banamex.com',
  profuturo: 'profuturo.mx',
  hey: 'hey.com',
  'pagare hey': 'hey.com',
  santander: 'santander.com.mx',
  hsbc: 'hsbc.com.mx',
  scotiabank: 'scotiabank.com.mx',
  citibanamex: 'citibanamex.com',
  inmBanco: 'inmBanco.com',
  // United States
  chase: 'chase.com',
  boa: 'bankofamerica.com',
  'bank of america': 'bankofamerica.com',
  wellsfargo: 'wellsfargo.com',
  citibank: 'citi.com',
  usbank: 'usbank.com',
  pnc: 'pnc.com',
  capitalone: 'capitalone.com',
  discover: 'discover.com',
  americanexpress: 'americanexpress.com',
};

/** Cash-like "banks" that have no brand to look up. */
const NOT_A_BANK = new Set(['bank', 'efectivo', 'cash', 'efectivo en efectivo', 'other', 'desconocido', 'unknown']);

/** Lowercase, strip accents and punctuation, collapse whitespace. */
export const normalizeBankName = (bank?: string | null): string =>
  (bank ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

/**
 * Best-effort domain for a bank name, or null when we should not ask
 * Brandfetch at all. A miss is expected and cheap: the URL is built with
 * `fallback/404` so an unknown brand 404s instead of returning a placeholder
 * logo, and the caller keeps its own avatar.
 */
export const resolveBankDomain = (bank?: string | null): string | null => {
  const name = normalizeBankName(bank);
  if (!name || NOT_A_BANK.has(name)) return null;
  if (BANK_DOMAINS[name]) return BANK_DOMAINS[name];

  // "Chase Checking", "BOA Savings" -> try the leading words.
  const words = name.split(' ');
  for (let take = words.length; take > 0; take -= 1) {
    const candidate = BANK_DOMAINS[words.slice(0, take).join(' ')];
    if (candidate) return candidate;
  }

  // Last resort: guess the domain. Usually wrong, and `fallback/404` makes
  // being wrong invisible.
  const slug = name.replace(/\s+/g, '');
  return slug ? `${slug}.com` : null;
};

/** True when a client ID is configured; otherwise callers skip the network. */
export const brandfetchEnabled = (clientId?: string | null): boolean =>
  Boolean((clientId ?? '').trim());

export interface BankLogoOptions {
  /** `light` | `dark` logo variant. Omit to let Brandfetch choose. */
  theme?: 'light' | 'dark'
  /** Square edge in pixels (16..2048). */
  size?: number
}

const CDN = 'https://cdn.brandfetch.io';

/**
 * Build the `<img src>` for a bank. Returns null when there is no client ID
 * or no usable domain, so the caller can render its own avatar instead.
 *
 * `fallback/404` is deliberate: a missing logo should 404 quietly so the
 * caller can swap in an initial, rather than showing the Brandfetch wordmark
 * as if it were the bank's.
 */
export const bankLogoUrl = (
  bank: string | null | undefined,
  clientId: string | null | undefined,
  options: BankLogoOptions = {},
): string | null => {
  if (!brandfetchEnabled(clientId)) return null;
  const domain = resolveBankDomain(bank);
  if (!domain) return null;

  const size = Math.min(2048, Math.max(16, Math.round(options.size ?? 64)));
  const parts = [
    `domain/${encodeURIComponent(domain)}`,
    `w/${size}`,
    `h/${size}`,
    'fallback/404',
    'type/icon',
  ];
  if (options.theme) parts.splice(3, 0, `theme/${options.theme}`);
  return `${CDN}/${parts.join('/')}?c=${encodeURIComponent((clientId ?? '').trim())}`;
};

/** First letter, for the avatar shown when no logo loads. */
export const bankInitial = (bank?: string | null): string => {
  const name = normalizeBankName(bank);
  return name ? name.charAt(0).toUpperCase() : '?';
};

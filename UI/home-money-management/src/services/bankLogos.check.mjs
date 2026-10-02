// Runnable check for the bank-logo URL builder.
//   node --experimental-strip-types src/services/bankLogos.check.mjs
// Two things break silently if these drift: a wrong URL means no logo at all,
// and a missing `fallback/404` means the Brandfetch wordmark gets shown to the
// user as if it were their bank.
import assert from 'node:assert/strict';
import { bankInitial, bankLogoUrl, brandfetchEnabled, normalizeBankName, resolveBankDomain } from './bankLogos.ts';

const KEY = 'test-client-id';

// --- name normalisation -------------------------------------------------
assert.equal(normalizeBankName('  Banamex  '), 'banamex');
assert.equal(normalizeBankName('Banco de Santander'), 'banco de santander');
assert.equal(normalizeBankName('Pagaré Hey'), 'pagare hey', 'accents are stripped, not dropped');
assert.equal(normalizeBankName('BBVA México'), 'bbva mexico');
assert.equal(normalizeBankName(undefined), '');
assert.equal(normalizeBankName(null), '');
assert.equal(normalizeBankName(''), '');

// --- domain resolution --------------------------------------------------
assert.equal(resolveBankDomain('Banamex'), 'banamex.com');
assert.equal(resolveBankDomain('BBVA'), 'bbva.com');
assert.equal(resolveBankDomain('Chase Checking'), 'chase.com', 'leading words match');
assert.equal(resolveBankDomain('BOA Savings'), 'bankofamerica.com', 'BOA is the alias');
assert.equal(resolveBankDomain('  banorte  '), 'banorte.com', 'case and padding are irrelevant');
assert.equal(resolveBankDomain('Profuturo'), 'profuturo.mx');
assert.equal(resolveBankDomain('Pagaré Hey'), 'hey.com', 'accented name still hits the map');

// Cash and placeholders are not brands: asking costs a request and can only miss.
assert.equal(resolveBankDomain('Efectivo'), null);
assert.equal(resolveBankDomain('Cash'), null);
assert.equal(resolveBankDomain('Bank'), null);
assert.equal(resolveBankDomain('Unknown'), null);
assert.equal(resolveBankDomain(''), null);
assert.equal(resolveBankDomain(undefined), null);

// Unknown but plausible: a guess, so the URL is still well-formed.
assert.equal(resolveBankDomain('Fidelity Investments'), 'fidelityinvestments.com');

// --- feature gate -------------------------------------------------------
assert.equal(brandfetchEnabled(KEY), true);
assert.equal(brandfetchEnabled(''), false);
assert.equal(brandfetchEnabled('   '), false);
assert.equal(brandfetchEnabled(null), false);

// No client ID means no network call at all, whatever the bank.
assert.equal(bankLogoUrl('Banamex', null), null);
assert.equal(bankLogoUrl('Banamex', ''), null);
assert.equal(bankLogoUrl('Efectivo', KEY), null, 'no domain, no URL');

// --- URL shape ----------------------------------------------------------
const url = bankLogoUrl('Banamex', KEY);
assert.ok(url.startsWith('https://cdn.brandfetch.io/domain/banamex.com/'), url);
assert.ok(url.includes('fallback/404'), 'a miss must 404, not show the Brandfetch wordmark');
assert.ok(url.includes('type/icon'), url);
assert.ok(url.includes(`?c=${KEY}`), url);
assert.ok(!url.includes('undefined'), url);

// Size is clamped to what the CDN accepts (16..2048) and always integral.
// The rounding mode is deliberately not asserted - Brandfetch truncates a
// decimal server-side anyway, so round-vs-trunc has no user-visible effect.
for (const size of [8, 0, -5, 12.6, 9999, 16, 2048, 64]) {
  const sized = bankLogoUrl('Banamex', KEY, { size });
  const w = Number(sized.match(/\/w\/(\d+)\//)[1]);
  const h = Number(sized.match(/\/h\/(\d+)\//)[1]);
  assert.ok(Number.isInteger(w) && w >= 16 && w <= 2048, `w for size ${size}: ${w}`);
  assert.equal(w, h, 'square request keeps w and h equal');
}

// Theme variant is opt-in and lands in the path, before fallback.
assert.ok(bankLogoUrl('Banamex', KEY, { theme: 'dark' }).includes('/theme/dark/'));
assert.ok(!bankLogoUrl('Banamex', KEY).includes('/theme/'));

// The client ID is query-escaped so it cannot break out of the URL.
const odd = bankLogoUrl('Banamex', 'a b&c=d');
assert.ok(!odd.slice(odd.indexOf('?c=')).includes('&c='), odd);
assert.ok(odd.includes('c=a%20b%26c%3Dd'), odd);

// --- initials for the fallback avatar ------------------------------------
assert.equal(bankInitial('banamex'), 'B');
assert.equal(bankInitial('BBVA'), 'B');
assert.equal(bankInitial('Pagaré Hey'), 'P');
assert.equal(bankInitial(''), '?');
assert.equal(bankInitial(null), '?');

console.log('bankLogos: all checks passed');

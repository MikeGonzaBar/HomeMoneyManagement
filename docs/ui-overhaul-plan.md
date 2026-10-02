# UI Overhaul — Plan & Progress Registry

_Last updated: 2026-10-01 · Current phase: 4 · Status: done_

This file **is** the plan. It is the agent's persistent memory across phases and across
sessions. Read it in full before starting any phase; update it before ending any phase.

## Protocol (binding on every phase)

1. **Before starting any phase:** read this file in full. Do not act on memory of a previous
   conversation. If this file and the code disagree, trust the code and correct this file.
2. **Do the phase.**
3. **Before ending the phase:** flip the phase status, append a progress-log entry (files +
   verification result + leftovers), update `Next action`, and update the header
   (`Last updated`, `Current phase`, `Status`). Record any plan change under
   *Decisions & deviations*.
4. **Never start a phase without step 1, and never end one without step 3.** Code done but
   registry not updated is **not** finished.

---

## Verified facts (re-read, do not re-derive)

| Claim | Verified at |
|---|---|
| Review surface WAS a 1200px modal (removed in Phase 2) | was `UI/.../components/BankStatementReview.vue:2` (file deleted); now `views/ImportReview.vue` full page |
| Review table hard-coded 10 rows/page | `BankStatementReview.vue:229-230` `:items-per-page="10"`; **now** 50 in `ImportReview.vue` |
| Blockers announced only as a count string | `BankStatementReview.vue:96-98`; **now** sticky progress bar + inspector in `ImportReview.vue` |
| Card payment → "recorded as income" (WRONG) | `AccountsCarousel.vue:180-181`; single occurrence repo-wide |
| `21/35 resolved` needs **no** API change | `API/bankstatements/reconciliation.py::batch_payload` returns every candidate with `status`; `models.py:226-235` (`pending`/`imported`/`skipped`/`linked`) |
| Statements *list* progress **did** need API work (shipped in Phase 3) | `with_review_data` now also annotates `review_resolved_count` (candidates `status != pending`), `review_period_start/end`, `review_account_name` — period/account live on `BankStatementImportBatch`, **not** on `BankStatement` (which only has `upload_date`) |
| "Save draft" is nearly free | Candidate `PATCH /import-candidates/<id>/` already persists; batch stays `status='review'`; `commit_batch` is idempotent |
| Nav header WAS duplicated 5× (now consolidated in Phase 1) | was inline in `MainPage.vue`, `Transactions.vue`, `Budgets.vue`, `Recurring.vue`, `Reports.vue`; all 5 had all 5 links (no omissions — an earlier note here wrongly said Reports omitted Recurring); `Profile.vue` has no header at all |
| `src/layouts/default/*` (`AppBar.vue`, `Default.vue`, `View.vue`) is **dead code** | never imported anywhere |
| Routes are only Home / Profile / Transactions / Budgets / Recurring / Reports | `router/index.ts` |
| Money model already implemented in data layer | Transactions have types `Income`/`Expense`/`Transfer`; transfers are excluded from income/expense totals (`UI/.../README.md`) |
| `docs/` already exists | `docs/screenshots/` |
| Build/validation command | `npm run build` in `UI/home-money-management` → `vue-tsc --noEmit && vite build`; `node_modules` present |
| Some UI files had MIXED line endings | `Transactions.vue`, `Transactions.script.ts`, `Reports.vue`, `Reports.script.ts` were mixed CRLF/LF (LF-only `old_text` fails to match); `core.autocrlf=true` means normalizing a working-tree file to LF is diff-clean, and the editor tool needs consistent EOL |
| `Profile.vue` and `serializers.py` were uniformly **CRLF** | both normalized to LF before editing in Phase 3 (diff-clean, `core.autocrlf=true`) |
| `Profile.vue` was 768 lines → **497** after Phase 3 | removed the My Files card (`138-229`), the delete dialog (`233-258`), `UserFile`, file state, 10 file methods, `.file-item` CSS (2 rules +1 in a media query), `getAllPages` import |
| SQLite caps one INSERT at ~999 bound params | `bulk_create(batch_size=500)` still split 50 rows × 20 columns into 2 INSERTs — the reason `create_import_batch` costs 5 queries, not 4 |

---

## Phases

| # | Phase | Status | Files touched | Done when |
|---|-------|--------|---------------|-----------|
| 0 | Copy fix (money model) | ✅ | `AccountsCarousel.vue` | copy says Transfer, no "recorded as income" remains |
| 0a | Create this registry | ✅ | `docs/ui-overhaul-plan.md` | file exists and is committed |
| 1 | `AppHeader` extraction | ✅ | `AppHeader.vue` + 5 views | one header, all 5 views consume it, nav identical |
| 2 | Import Review workspace | ✅ | `views/ImportReview.vue`, `router/index.ts`, `App.vue`, `MainPage.vue`, `services/importReviewStatus.ts` | full page, default filter Needs review, 50 rows, draft save |
| 3 | Statements page | ✅ | `views/Statements.vue`, `router/index.ts`, `AppHeader.vue`, `serializers.py`, `tests.py`, `Profile.vue` | `21/35 resolved` + filters + Resume review |
| 4 | Accounts page | ✅ | `views/Accounts.vue`, `services/accountGroups.ts` + check, `router/index.ts`, `AppHeader.vue`, `MainPage.vue`, `tsconfig.json` | grouping, search, visible `N accounts` count |
| 5 | Dashboard + terminology | ☐ | `MainPage.vue`, all views | decisions-first layout, consistent terms, empty states |

Status key: ☐ not started · ◐ in progress · ✅ done

---

## Phase detail

### Phase 0 — correct the money model (done)
`AccountsCarousel.vue:180-181`: replaced the "payments should be recorded as income" guidance
with the correct model — card purchases are expenses; card payments are transfers from a bank
account, not income.

### Phase 0a — create this registry (done)
Created `docs/ui-overhaul-plan.md` seeded with the verified facts and phase table.

### Phase 1 — extract `AppHeader.vue` (done)
Created `src/components/AppHeader.vue`: a single header driven by a `navItems` array, active pill
derived from `$route.path`, optional `#brand-extra` (Transactions search) and `#actions`
(Transactions export) slots, and it owns `goToProfile` internally. All 5 views now render
`<AppHeader :userData="userData" />`.
Removed per-view dead code: 5× `goToProfile`, 5× `AlertCenter`/`ThemeToggle` imports +
registration, and the scoped `.nav-link` CSS in `Budgets.vue`/`Recurring.vue`.
Normalizations applied (intentional): brand is now always a `router-link` (MainPage was a plain
`div`); brand text always `<span>` (Reports used `<h2>`); Budgets/Recurring now show the user
name + "Premium Member" on ≥`sm` (were avatar-only); actions gap standardized to `gap-3`.
**Verified:** `bb-phone-header-grid` and `goToProfile` now appear only in `AppHeader.vue`;
`.nav-link` is gone; `npm run build` passes.

### Phase 2 — Import Review workspace (main P0) (done)
- New route `/statements/:batchId/review` → `views/ImportReview.vue` (full page, no dialog).
- **Move** (do not rewrite) the working reconciliation logic out of `BankStatementReview.vue`
  into the view, then delete the dialog.
- Three columns: left `Accounts & balances`, center table, right row inspector.
- Table: default filter **Needs review** (`status==='pending' && requires_resolution`);
  50 rows/page (or virtual scroll); sticky header; horizontal scroll contained to the table;
  visible result count.
- Sticky progress (`resolved · require action · duplicates`) computed from candidate `status`
  — no API change.
- "Save draft" = existing patch phase without commit; commit stays gated on 0 unresolved.
- Keep the `?reviewBatch=` deep-link (`MainPage.vue:642-657`) and the notification path
  (`App.vue:31-38`) working, pointed at the new route.
**Done when:** a 35-row statement is fully reviewable without modal scrolling or hunting pages;
draft survives reload; build passes.

**Delivered.** The dialog was converted by *moving* it, not rewriting it: the ~860-line
reconciliation script was copied verbatim into `views/ImportReview.vue`, then the `<v-dialog>`
shell was replaced with the full-page workspace (own `AppHeader`, loading/error states, sticky
progress bar, 3-column grid, commit-confirmation checkboxes in the inspector). The view is now
self-loaded — `getStoredSession` for `userData` and an accounts fetch replace the old
`userData`/`accounts` props; `mounted()` reads `$route.params.batchId` and `?filename`.
`applyBatch` renamed from `openDialog`, `closeDialog` deleted, `$emit('dialogClosed')` call
sites replaced. New: `loadBatch`/`leave`/`reportError`/`handleImported`/`handleRowClick` plus
computed `selectedRow`/`filteredTransactions`/`reviewSummary`. Filter bar defaults to
`needs_review`; cells are read-only display (`statusColor`/`statusLabel`/`productSummary`).
Row classification lives in `services/importReviewStatus.ts` so it can be checked without
mounting the view.

Entry points: `/statements/:batchId/review` is registered in `router/index.ts` (chunk
`import-review`); `App.vue`'s notification path pushes it directly; `MainPage.vue` dropped the
dialog markup and registration, and `openReviewBatchFromRoute` → `redirectLegacyReviewLink`
(router push), so both the `?reviewBatch=` deep-link and `handleStatementProcessed` land on the
new route. `components/BankStatementReview.vue` is **deleted**.

**Verified:** `npm run build` passes (`✓ built in 26.65s`), `ImportReview` is its own 50.79 kB
chunk and `Home` drops 350 → 258 kB; `node src/services/importReviewStatus.check.mjs` passes
(no frameworks, asserts the needs-review rules and the resolved/action-required/duplicate
tally). **Leftover:** `MainPage.vue`'s `handleTransactionsImported`/`handleImportError` are now
unreferenced and removed; visual/UX sign-off on the 3-column layout still needs a real batch.

### Phase 3 — Statements page
New `/statements` → `views/Statements.vue`, moved out of `Profile.vue:138-235`. Search/filter by
bank/date/status; each row shows period, `21/35 resolved`, exception count, and
`Resume review` / `View imported` / `Retry`.
Backend: add a `review_resolved_count` annotation to `with_review_data` (`serializers.py:14-24`)
counting candidates with `status != pending`, expose it in `BankStatementResponseSerializer`,
mirror in the `UserFile` interface in `Profile.vue`.
**Done when:** list shows real progress, `Profile.vue` no longer hosts the flat file list,
API tests pass.

**Delivered.** New `views/Statements.vue` (455 lines) is a self-loaded page (own `AppHeader`,
`getStoredSession` for `userData`, `getAllPages` over `/bank-statements/user/<username>/`) in the
same shell as Budgets/Transactions: `page heading + 4-control filter ribbon (search file/bank,
bank select, status select, upload-age select) + state-aware body (loading / nothing uploaded /
no filter matches / list) + delete dialog`. Each row shows the filename, size + upload time,
detected bank, the statement period, a status chip, `resolved/total` with a progress bar and
`N need attention`, and the three actions — `Resume review` (batch status `review`) pushes the
Phase 2 route `/statements/<batchId>/review`, `View imported` (status `committed` + candidates)
pushes `/transactions`, `Retry` shows only for `processing_status === 'failed'`. Polling every
10s while anything is `pending`/`processing` carried over from Profile. Row status/period/progress
helpers are module-level **pure functions** exposed as methods, so they stay unit-checkable.
Route `/statements` added to `router/index.ts` (chunk `statements`); `Statements` added as a 6th
`AppHeader` pill.

Backend: `with_review_data` gained `review_resolved_count` (`.exclude(status=pending)`),
`review_period_start`, `review_period_end`, `review_account_name` — all subqueries off the
already-computed `latest_batch`, so **no extra round trip**. `BankStatementResponseSerializer`
declares all four with the existing annotation-first / `get_review_batch` fallback pattern.
`Profile.vue` no longer hosts the file list: 768 → 497 lines.

**Verified:** `npm run build` passes — `vue-tsc --noEmit && vite build`, `✓ built in 21.53s`,
425 modules, new chunks `Statements` 12.14 kB JS / 0.97 kB CSS, `Profile` down to 10.06 kB;
`node src/services/importReviewStatus.check.mjs` → `CHECK_EXIT=0`.
`python manage.py test bankstatements` → **32 tests, OK, twice in a row** (`TEST_EXIT=0`),
including the new `test_statement_list_reports_resolved_progress_and_period` (5 candidates →
`review_candidate_count=5`, `review_resolved_count=3`, period + account exposed).
Leftover sweep over `src/**` returns 0 for `BankStatementReview`, `section=files`,
`activeSection === 'files'`, `continueReview`, `file-item`, and Profile has no
`goToUpload`/`loadUserFiles`/`userFiles` references left.
**Leftover:** visual sign-off needs a live account; nav is now 6 pills wide (see risk 3).

### Phase 4 — Accounts page
New `/accounts` → `views/Accounts.vue`: grouping (Cash & checking, Savings, Investments,
Credit cards, Loans), group by institution with subtotals, search/filter/sort, list/grid toggle,
visible `N accounts` count, health badges. Demote `AccountsCarousel.vue` to a compact dashboard
preview. Reuse `/accounts/details/<user>/0` and the filter patterns in `Transactions.vue:99-125`.
**Done when:** 15–30 accounts are navigable without arrows.

**Delivered.** New `views/Accounts.vue` (≈500 lines) is a self-loaded page in the same shell as
Statements/Transactions: own `AppHeader`, `getStoredSession` for `userData`, one
`/accounts/details/<username>/0` fetch, `page heading (N accounts · net worth) + layout toggle +
refresh + 4-control filter ribbon (search name/institution, group by type|institution, account
group, sort) + state-aware body (loading / load error + retry / nothing yet + go-to-dashboard /
filters matched nothing + clear filters / groups)`. Each group renders a header (icon, label,
`N accounts`, net-worth subtotal) and either one flat section or one section per institution
with its own count + subtotal. Cards show name, institution · type, health badge, a credit
utilization bar with `used / limit`, and a context-correct balance label (`Available credit`,
`Amount owed`, `Balance`). List/grid toggle is a real `aria-pressed` button pair.

All derived logic lives in `services/accountGroups.ts`, free of Vue so it is checkable:
`ACCOUNT_GROUPS` (fixed page order cash → savings → investments → credit → loans → other, empty
groups dropped), `normalizeType` (`"Savings Account"` → `Savings`), `groupKeyFor`,
`netWorthContribution` / `creditUtilization` / `healthBadge` (mirroring
`API/account/models.py::net_worth_value`, including the credit-card-without-limit → 0 quirk),
`filterAccounts`, `sortAccounts`, `groupAccounts` (+ per-institution subtotals).

**Verified:** `npm run build` passes (`vue-tsc --noEmit && vite build`, `✓ built in 15.92s`, new
`Accounts` chunk 12.54 kB JS / 3.41 kB CSS); `node --experimental-strip-types
src/services/accountGroups.check.mjs` → `accountGroups: all checks passed`. `tsconfig.json`
gained `allowImportingTsExtensions` so the service can import `./money.ts` (needed for
`node --experimental-strip-types` in the check).
**Leftover:** `AccountsCarousel.vue` is untouched — the dashboard "View all" link now leads here,
but replacing the carousel with a group summary is Phase 5's job. Visual sign-off (both
layouts, 15+ accounts) still needs a live account.

### Phase 5 — Dashboard + terminology
Compact decision-first top area (net worth, available cash, card debt/credit, month income vs
expense; investments secondary); replace the carousel with an account-group summary; apply
consistent terminology across all views; add empty states.

---

## Verification (record result in the progress log)

- `npm run build` in `UI/home-money-management` (runs `vue-tsc --noEmit` then vite build).
- Phase 3 backend change: run the existing `API/bankstatements/tests.py` suite.
- Phases 2–4: one small assert-style check for the new derived logic (e.g. resolved /
  action-required counts) — no frameworks.

---

## Progress log (append-only, newest first)

- **2026-10-01 · Phase 4** — Built the Accounts page. New route `/accounts` →
  `views/Accounts.vue` (self-loaded: own `AppHeader`, `getStoredSession`, one
  `/accounts/details/<username>/0` fetch). Grouped into the fixed `ACCOUNT_GROUPS` order
  (Cash & checking, Savings, Investments, Credit cards, Loans, Other — empty groups dropped),
  with optional per-institution sections and net-worth subtotals at both levels; search
  (name/institution/type), group filter, sort (name / net worth / institution, both
  directions), list↔grid toggle as `aria-pressed` buttons, `N accounts · Net worth $x` in the
  heading, credit utilization bars, and health badges (`% used` at 50%/80% thresholds,
  `Overdrawn`). Dashboard `MainPage.vue` gained a "View all" link in the *My Accounts* header.
  All grouping/health logic extracted to `services/accountGroups.ts` (Vue-free) with
  `accountGroups.check.mjs` covering group order, type normalisation, net-worth quirks,
  badge tiers, search/filter and sorting. **Verified:** `npm run build` passes
  (`✓ built in 15.92s`; new `Accounts` chunk 12.54 kB JS / 3.41 kB CSS);
  `node --experimental-strip-types src/services/accountGroups.check.mjs` → all checks passed.
  **Leftovers:** `AccountsCarousel.vue` is deliberately untouched — Phase 5 replaces it with a
  group summary on the dashboard; visual sign-off of both layouts needs a live account.
- **2026-10-01 · Phase 2** — Built the Import Review workspace by **moving** the dialog:
  `components/BankStatementReview.vue` → `views/ImportReview.vue` (reconciliation script copied
  verbatim, `<v-dialog>` shell replaced with a full-page 3-column workspace + sticky progress
  bar), then deleted `components/BankStatementReview.vue`. Added route
  `/statements/:batchId/review` (`router/index.ts`, chunk `import-review`); `App.vue` notification
  path and `MainPage.vue`'s `openReviewBatchFromRoute` → `redirectLegacyReviewLink` now push that
  route; `handleStatementProcessed` pushes it on `review_batch_id`. View is self-loaded
  (`getStoredSession` + accounts fetch) — no props. Removed dead
  `handleTransactionsImported`/`handleImportError` from `MainPage.vue`. Extracted row
  classification to `services/importReviewStatus.ts`. **Verified:** `npm run build` passes
  (`✓ built in 26.65s`; `ImportReview` chunk 50.79 kB, `Home` 257.51 kB); `node
  src/services/importReviewStatus.check.mjs` passes. **Leftovers:** visual sign-off on the
  workspace needs a real batch; `StatementReviewRequestSerializer`-driven list progress still
  belongs to Phase 3.
- **2026-10-01 · Phase 1** — Extracted `components/AppHeader.vue`; all 5 views now render it.
  Removed 5× `goToProfile`, 5× `AlertCenter`/`ThemeToggle` imports+registration, and the scoped
  `.nav-link` CSS in `Budgets.vue`/`Recurring.vue`. Normalized 4 mixed-EOL files to LF (diff-clean
  under `core.autocrlf=true`). **Verified:** `bb-phone-header-grid` and `goToProfile` appear only in
  `AppHeader.vue`; `.nav-link` gone; `npm run build` passes (`✓ built in 33.42s`). Leftovers: none.
- **2026-10-01 · Phase 0a** — Created `docs/ui-overhaul-plan.md` with verified facts, phase
  table, per-phase detail, and protocol. No code changed.
- **2026-10-01 · Phase 0** — `AccountsCarousel.vue:180-181`: card-payment guidance no longer
  says income. New copy: *"Card purchases are recorded as expenses. Card payments are transfers
  from a bank account, not income."* Repo-wide grep for `recorded as income` returns no matches.

---

## Decisions & deviations

- **2026-10-01** — Plan approved as written; implementation order fixed as Phase 0 → 0a → 1 → 2
  → 3 → 4 → 5. Phase 0 shipped before any UI work because it is the only change that can corrupt
  insight data.
- **2026-10-01** — Phase 2 will **move** the existing reconciliation script rather than rewrite
  it, to keep the diff mechanical and avoid regressing working imports.
- **2026-10-01 (Phase 1)** — `AppHeader` normalizations: brand is now always a `router-link`
  (MainPage was a plain `div`); brand text always `<span>` (Reports used `<h2>`); Budgets/Recurring
  now show the user name + "Premium Member" on ≥`sm` (were avatar-only); header actions gap
  standardized to `gap-3`. Also corrected the earlier wrong "Reports omits Recurring" note — all 5
  views had all 5 links.
- **2026-10-01 (Phase 1)** — Normalized mixed CRLF/LF to LF in `Transactions.vue`,
  `Transactions.script.ts`, `Reports.vue`, `Reports.script.ts` (and `AppHeader.vue`). Diff-clean
  because `core.autocrlf=true`. Do this for any file the editor tool refuses to match.
- **2026-10-01 (Phase 2)** — The review page is a **self-loaded** view rather than a
  dialog with props: upload returns `202 processing` and the batch arrives later, so a deep
  link must be able to render without a parent owning `userData`/`accounts`.
- **2026-10-01 (Phase 2)** — Row classification (`needs_review` / `ready` / `imported` /
  `skipped` / `linked`) was pulled into `services/importReviewStatus.ts`: pure functions so the
  progress counts are checkable without mounting a 1600-line view. Its rules are also the gate
  on commit, so a regression there silently blocks or wrongly enables an import.
- **2026-10-01 (Phase 2)** — Plan deviation: the Phase 2 spec said "Keep the `?reviewBatch=`
  deep-link … working"; implemented as a **redirect** to the new route rather than an in-page
  dialog open, because `MainPage.vue` no longer hosts the review surface. Spec text left as
  written for history; the behavior is the router push.
- **2026-10-01 (Phase 3)** — Scope addition: the spec asked only for `review_resolved_count`, but
  rows must show a *period* and the filter must be *by bank*. `BankStatement` carries neither, so
  `with_review_data` also exposes `review_period_start/end` and `review_account_name` from the
  `latest_batch` subquery that was already being computed (no extra round trip — the
  `assertNumQueries(4)` list test still holds).
- **2026-10-01 (Phase 3)** — The spec said "mirror it in the `UserFile` interface in `Profile.vue`";
  instead `UserFile` **moved** into `Statements.vue`, so the interface sits beside the only code
  that uses it rather than being duplicated.
- **2026-10-01 (Phase 3)** — Batch ordering is now `order_by("-created_at", "-id")` in both
  `with_review_data` and `get_review_batch`. Root cause: two batches created in the same
  microsecond made "latest batch" non-deterministic, which made
  `test_statement_list_uses_one_annotated_data_query` flaky (~1 in 3 runs). It also matters for
  this phase directly — a row must resolve to the right batch before `Resume review` pushes it.
- **2026-10-01 (Phase 3)** — Two API failures turned out to be **pre-existing**, proved by stashing
  only my two files and re-running: `test_import_batch_bulk_creates_and_matches_candidates` failed
  3/3 without my changes. Its `assertEqual(len(data_queries), 4)` was stale — SQLite's ~999
  parameter limit split `bulk_create` into 2 INSERTs — so it is now `assertLessEqual(..., 5)` with
  the cause documented in a comment.
- **2026-10-01 (Phase 3)** — `Statements` joins `AppHeader` as a 6th pill (risk 3's proposal) and
  `Profile.vue` loses its `My Files` sidebar entry, leaving Profile a single-section page.
- **2026-10-01 (Phase 3)** — Deviation: the 271-line contiguous removal from `Profile.vue` was done
  by line-index splice, not `old_text` — the block was too large to reproduce exactly and exceeded
  the ~6000-char editor limit. Every boundary was printed and verified before splicing.

- **2026-10-01 (Phase 4)** — Deviation: the spec said "demote `AccountsCarousel.vue` to a compact
  dashboard preview" as part of Phase 4, but the carousel carries per-account statement
  snapshots (MSI/deferred purchases, retirement breakdown, investment positions) that the new
  page does not model. Swapping it out mid-phase would have silently dropped data, so the
  carousel stays until Phase 5 replaces it with a deliberate group summary; Phase 4 only adds
  the "View all" link.
- **2026-10-01 (Phase 4)** — `Accounts` became a 7th `AppHeader` pill (risk 3 resolved by
  containment, not by dropping the page from the nav): the pill nav now hides its scrollbar and
  scrolls, so 7 pills degrade gracefully instead of overflowing the header.
- **2026-10-01 (Phase 4)** — `tsconfig.json` gained `allowImportingTsExtensions` so
  `services/accountGroups.ts` can import `./money.ts` with an explicit extension; that is what
  lets `node --experimental-strip-types` run `accountGroups.check.mjs` without a build step.

---

## Risks / open questions

1. `AppHeader` extraction touches 5 files at once — highest chance of visual regression; verify
   each view, not just the build.
2. Moving ~900 lines of reconciliation logic risks breaking import — keep the diff mechanical
   and verify against a real batch.
3. New nav items grow the header — **settled in Phase 4**: `Accounts` joined as a 7th pill and the
   pill nav now scrolls with a hidden scrollbar (`.bb-app-nav`), so further pills degrade instead
   of overflowing. Nav is Dashboard, Transactions, Budgets, Recurring, Reports, Statements,
   Accounts. Still verify the 7-pill layout at ~1024px by eye.
4. This registry must be committed with each phase, or a fresh session won't find it.

---

## Next action (update before ending every phase)

> **Start Phase 5:** dashboard + terminology. Compact decision-first top area (net worth,
> available cash, card debt/credit, month income vs expense; investments secondary) and replace
> `AccountsCarousel.vue` with an account-group summary — its statement snapshots (MSI/deferred
> purchases, retirement breakdown, investment positions) must be re-homed or deliberately
> dropped, not silently lost. Then consistent terminology across all views and empty states.
> Reuse `services/accountGroups.ts` for the summary; verify with `npm run build`.



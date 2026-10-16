/**
 * Build budget check - fails `npm run build` when a shipped asset outgrows its
 * budget, so bundle-size regressions are caught in the same place they are
 * introduced.
 *
 * Text assets (.js/.css/.html) are measured gzipped, because nginx.conf ships
 * them with `gzip on` - that is what actually goes over the wire. Binary assets
 * are measured raw. Raising a budget is legitimate when the growth is
 * intentional: edit BUDGETS below in the same commit so the change is visible
 * in review.
 */
import { readdirSync, readFileSync } from 'node:fs'
import { extname, join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'
import { gzipSync } from 'node:zlib'

const DIST = fileURLToPath(new URL('../dist', import.meta.url))
const KB = 1024

/** Per-extension budgets in bytes. */
const BUDGETS = {
  '.js': 150 * KB, // gzipped
  '.css': 100 * KB, // gzipped
  '.html': 10 * KB, // gzipped
  '.png': 64 * KB, // raw
  '.jpg': 64 * KB,
  '.jpeg': 64 * KB,
  '.webp': 64 * KB,
  '.gif': 64 * KB,
  '.svg': 16 * KB,
  // PNG-in-ICO wrapper around the 192px logo; see scripts/make-favicons.mjs.
  '.ico': 32 * KB,
  '.woff2': 400 * KB, // already compressed; measure raw
}
const GZIPPED = new Set(['.js', '.css', '.html'])

const walk = dir =>
  readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const path = join(dir, entry.name)
    return entry.isDirectory() ? walk(path) : [path]
  })

const fmt = bytes => `${(bytes / KB).toFixed(1)} KB`
const failures = []
const rows = []

for (const file of walk(DIST)) {
  const ext = extname(file).toLowerCase()
  const budget = BUDGETS[ext]
  if (!budget) continue

  const buf = readFileSync(file)
  const size = GZIPPED.has(ext) ? gzipSync(buf, { level: 6 }).length : buf.length
  rows.push({ name: relative(DIST, file), size, budget, gz: GZIPPED.has(ext) })
  if (size > budget) failures.push(rows[rows.length - 1])
}

rows.sort((a, b) => b.size - a.size)
for (const { name, size, budget, gz } of rows) {
  const flag = size > budget ? 'FAIL' : ' ok '
  console.log(`[${flag}] ${name}: ${fmt(size)} / ${fmt(budget)}${gz ? ' (gz)' : ''}`)
}

if (rows.length === 0) {
  console.error('No budgeted assets found in dist/ - did `vite build` run?')
  process.exit(1)
}

if (failures.length > 0) {
  console.error(
    `\n${failures.length} asset(s) over budget: ` +
      failures.map(f => `${f.name} (${fmt(f.size)} > ${fmt(f.budget)})`).join(', ') +
      '\nEither shrink the asset or raise its budget in scripts/check-build-budget.mjs.',
  )
  process.exit(1)
}

console.log(`\nAll ${rows.length} budgeted assets within budget.`)
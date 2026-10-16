// Django DateField values (financial posting dates, statement periods, matched
// transaction dates) are calendar dates, not UTC instants. `new Date("2026-09-17")`
// parses the bare date as midnight UTC, which then renders as the *previous* day
// for any viewer west of UTC (for example America/Mexico_City, UTC-6). Parse the
// YYYY-MM-DD components into a local Date so the same calendar day is shown for
// display, filtering, sorting and CSV export. Real timestamps (upload times) are
// intentionally left to plain `new Date(...)` and must not go through here.
const DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/;

/**
 * Parse a backend calendar-date string into a local-time Date, preserving the
 * day regardless of the viewer's UTC offset. Returns null for empty/invalid
 * input so callers can skip it instead of rendering "Invalid Date".
 */
export function parseCalendarDate(value: string | null | undefined): Date | null {
  if (!value) return null;
  const match = DATE_ONLY.exec(value);
  if (match) {
    return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

/** Format a backend calendar-date string for en-US display without day drift. */
export function formatCalendarDate(value: string | null | undefined): string {
  const date = parseCalendarDate(value);
  if (!date) return '';
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

/**
 * The local calendar date as YYYY-MM-DD. Use for "today" defaults in
 * query parameters and form placeholders: `new Date().toISOString()`
 * is UTC, which drifts to the adjacent day for viewers away from UTC.
 */
export function todayLocalISO(at: Date = new Date()): string {
  const month = String(at.getMonth() + 1).padStart(2, '0');
  const day = String(at.getDate()).padStart(2, '0');
  return `${at.getFullYear()}-${month}-${day}`;
}

/** The local calendar month as YYYY-MM for month-scoped queries. */
export function monthLocalKey(at: Date = new Date()): string {
  return todayLocalISO(at).slice(0, 7);
}

// Runnable check for the calendar-date contract.
//   node src/services/calendarDate.check.mjs
// Fails loudly if a backend YYYY-MM-DD date is allowed to drift a day for a
// viewer west of UTC (the reported bug: 2026-09-17 rendered as Sep 16 in
// America/Mexico_City). Run it under several timezones to prove the contract.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { parseCalendarDate, formatCalendarDate } from './calendarDate.ts';

// A bare date must parse to a *local* Date whose components match the input,
// independent of the host timezone. This is the invariant that kills the drift.
const known = parseCalendarDate('2026-09-17');
assert.equal(known.getFullYear(), 2026);
assert.equal(known.getMonth(), 8); // September, zero-based
assert.equal(known.getDate(), 17);

// The two audited records must keep their statement posting dates.
assert.equal(formatCalendarDate('2026-09-17'), 'Sep 17, 2026');
assert.equal(formatCalendarDate('2026-08-31'), 'Aug 31, 2026');

// Month/year boundaries and a leap day must not shift.
assert.equal(formatCalendarDate('2026-01-01'), 'Jan 1, 2026');
assert.equal(formatCalendarDate('2026-12-31'), 'Dec 31, 2026');
assert.equal(formatCalendarDate('2024-02-29'), 'Feb 29, 2024'); // leap day
assert.equal(formatCalendarDate('2026-03-01'), 'Mar 1, 2026'); // day after a leap day

// Inclusive range endpoints stay put.
assert.equal(parseCalendarDate('2026-08-04').getDate(), 4);

// Empty and malformed input must not render "Invalid Date" or throw.
assert.equal(parseCalendarDate(''), null);
assert.equal(parseCalendarDate(null), null);
assert.equal(parseCalendarDate(undefined), null);
assert.equal(parseCalendarDate('not-a-date'), null);
assert.equal(formatCalendarDate(''), '');
assert.equal(formatCalendarDate('garbage'), '');

// A real timestamp (upload time) still parses; it is not a calendar date but
// must remain usable rather than null.
const stamp = parseCalendarDate('2026-09-17T18:30:00Z');
assert.ok(stamp instanceof Date);

// The display helper must render the same calendar day under negative-offset,
// UTC and positive-offset zones. Spawn a fresh node with TZ forced so the
// assertion exercises Intl under each zone.
const probe = "import {formatCalendarDate} from './calendarDate.ts';"
  + "process.stdout.write(formatCalendarDate(process.argv[1]));";
for (const [tz, expected] of [
  ['America/Mexico_City', 'Sep 17, 2026'], // UTC-6, the reported regression zone
  ['UTC', 'Sep 17, 2026'],
  ['Asia/Tokyo', 'Sep 17, 2026'], // UTC+9, guards against an opposite drift
]) {
  const out = execFileSync(process.execPath, ['-e', probe, '2026-09-17'], {
    cwd: import.meta.dirname,
    env: { ...process.env, TZ: tz },
    encoding: 'utf8',
  });
  assert.equal(out, expected, `TZ=${tz} drifted the calendar date`);
}

// "Today" defaults keep the viewer's local calendar day, not the UTC day.
// 2026-10-02T05:30Z is Oct 1 23:30 in Mexico City but Oct 2 in UTC/Tokyo.
const localProbe = "import {todayLocalISO, monthLocalKey} from './calendarDate.ts';"
  + "const at = new Date(process.argv[1]);"
  + "process.stdout.write(todayLocalISO(at) + '|' + monthLocalKey(at));";
for (const [tz, instant, expected] of [
  ['America/Mexico_City', '2026-10-02T05:30:00Z', '2026-10-01|2026-10'],
  ['UTC', '2026-10-02T05:30:00Z', '2026-10-02|2026-10'],
  ['Asia/Tokyo', '2026-10-02T05:30:00Z', '2026-10-02|2026-10'],
]) {
  const out = execFileSync(process.execPath, ['-e', localProbe, instant], {
    cwd: import.meta.dirname,
    env: { ...process.env, TZ: tz },
    encoding: 'utf8',
  });
  assert.equal(out, expected, `TZ=${tz} drifted the local today/month default`);
}

console.log('calendarDate: all checks passed');

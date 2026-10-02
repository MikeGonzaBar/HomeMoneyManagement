// Runnable check for the canvas theming helper.
//   node --experimental-strip-types src/services/chartTheme.check.mjs
// A chart cannot read var(--token), so a wrong fallback here means invisible
// axis text on the dark surface - exactly the bug this helper exists to stop.
import assert from 'node:assert/strict';
import { axisInk, chartInk, cssVar, legendInk, tooltipInk } from './chartTheme.ts';

// No DOM (SSR / node): fall back rather than throwing.
assert.equal(cssVar('--bb-text-muted', '#6b7280'), '#6b7280', 'no getComputedStyle -> fallback');
assert.equal(chartInk().text, '#6b7280');
assert.equal(chartInk().surface, '#ffffff');
assert.equal(tooltipInk().backgroundColor, '#ffffff');
assert.equal(tooltipInk().titleColor, '#1f2937');

// With a DOM, the *computed* token wins - this is what makes dark mode work.
globalThis.document = { documentElement: {} };
globalThis.getComputedStyle = () => ({
  getPropertyValue: (name) => ({ '--bb-text-muted': ' #cbd5e1 ', '--bb-border-soft': '#1f2937', '--bb-surface': '#111827', '--bb-text-strong': '#f8fafc' })[name] ?? '',
});
globalThis.window = {};
assert.equal(cssVar('--bb-text-muted', '#6b7280'), '#cbd5e1', 'value is trimmed');
assert.equal(chartInk().text, '#cbd5e1');
assert.equal(chartInk().grid, '#1f2937');
assert.equal(chartInk().surface, '#111827');
assert.equal(tooltipInk().titleColor, '#f8fafc', 'tooltip text follows the strong token');
assert.equal(tooltipInk().backgroundColor, '#111827');

// Axes and legends must never be left on chart.js defaults.
assert.equal(axisInk().color, '#cbd5e1');
assert.equal(axisInk().grid.color, '#1f2937');
assert.equal(axisInk().border.color, '#1f2937');
assert.equal(legendInk().color, '#cbd5e1');
assert.equal(legendInk().font.size, 10);
assert.equal(legendInk(12).font.size, 12);

// An undefined token still yields a usable colour, never ''.
globalThis.getComputedStyle = () => ({ getPropertyValue: () => '' });
assert.equal(cssVar('--nope', '#abc'), '#abc');
assert.equal(chartInk().text, '#6b7280');

console.log('chartTheme: all checks passed');
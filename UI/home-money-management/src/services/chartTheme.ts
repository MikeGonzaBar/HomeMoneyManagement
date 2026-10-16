/**
 * Chart theming.
 *
 * Chart.js draws to a <canvas>, so it cannot use the `var(--token)` values the
 * rest of the UI uses — the token has to be resolved to a real colour string
 * before it reaches the options object. Every chart asks for its ink here
 * rather than taking chart.js's light-mode defaults, which are near-invisible
 * on the dark surface.
 */

/** Resolve a CSS custom property to its computed value, with a fallback. */
export const cssVar = (name: string, fallback: string): string => {
  // Guard on `document`, which is what we actually dereference below — a
  // `window` check passes in environments that have no document and then throws.
  if (typeof document === 'undefined' || typeof getComputedStyle === 'undefined') return fallback;
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
};

export interface ChartInk {
  /** Axis ticks, legend labels, tooltip text. */
  text: string
  /** Grid lines and axis borders. */
  grid: string
  /** Opaque box drawn over the canvas (tooltip background). */
  surface: string
}

/**
 * Chart colours for the current theme. Call at render time, not at module
 * load, so it picks up the `app-dark` class ThemeToggle puts on <html>.
 */
export const chartInk = (): ChartInk => ({
  text: cssVar('--bb-text-muted', '#6b7280'),
  grid: cssVar('--bb-border-soft', '#f3f4f6'),
  surface: cssVar('--bb-surface', '#ffffff'),
});

/** The tick/grid styling every cartesian axis in the app shares. */
export const axisInk = () => {
  const ink = chartInk();
  return {
    color: ink.text,
    border: { color: ink.grid },
    grid: { color: ink.grid, drawTicks: false },
  };
};

/** Legend label styling; keeps the existing point-style look. */
export const legendInk = (fontSize = 10) => {
  const ink = chartInk();
  return {
    color: ink.text,
    padding: 10,
    usePointStyle: true,
    font: { size: fontSize },
  };
};

/** Tooltip body/box, which chart.js draws opaque over the canvas. */
export const tooltipInk = () => {
  const ink = chartInk();
  return {
    backgroundColor: ink.surface,
    titleColor: cssVar('--bb-text-strong', '#1f2937'),
    bodyColor: ink.text,
    borderColor: ink.grid,
    borderWidth: 1,
  };
};

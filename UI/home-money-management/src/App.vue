<template>
  <v-app>
    <router-view />
  </v-app>
</template>

<script lang="ts" setup>
import { onMounted } from 'vue'
import { getStoredSession } from '@/services/session'
import { applyDocumentTheme } from '@/services/theme'

onMounted(() => {
  applyDocumentTheme(getStoredSession()?.user.theme_preference ?? 'system')
})
</script>

<style>
/* Global Styles for Budget Buddy */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
  font-family: 'Inter', sans-serif;
}

:root {
  --bb-text-strong: #1f2937;
  --bb-text-muted: #6b7280;
  --bb-surface: #ffffff;
  --bb-surface-soft: #f9fafb;
  --bb-border-soft: #f3f4f6;
  --bb-row-hover: #f9fafb;
  --bb-metric-limit: #111827;
  --bb-metric-spent: #be123c;
  --bb-metric-positive: #047857;
  --bb-metric-negative: #dc2626;
  --bb-metric-card-bg: #ffffff;
}

.app-dark {
  --bb-text-strong: #f8fafc;
  --bb-text-muted: #cbd5e1;
  --bb-surface: #111827;
  --bb-surface-soft: #172033;
  --bb-border-soft: #1f2937;
  --bb-row-hover: #1f2937;
  --bb-metric-limit: #f8fafc;
  --bb-metric-spent: #fda4af;
  --bb-metric-positive: #86efac;
  --bb-metric-negative: #fca5a5;
  --bb-metric-card-bg: linear-gradient(180deg, rgba(23, 32, 51, 0.96), rgba(17, 24, 39, 0.96));
}

.v-application {
  background: #f9fafb !important;
}

.app-dark .v-application,
.app-dark body {
  background: #0f172a !important;
  color: #e5e7eb;
}

.app-dark .bg-white,
.app-dark .bg-white\/95,
.app-dark .glass-card,
.app-dark .dashboard-panel,
.app-dark .dashboard-summary-card,
.app-dark .reports-card,
.app-dark .transactions-filter-panel,
.app-dark .transactions-total-card,
.app-dark .v-card {
  background-color: #111827 !important;
  border-color: #1f2937 !important;
  color: #f8fafc !important;
}

.app-dark .bg-gray-50 {
  background-color: #0f172a !important;
}

.app-dark .border-gray-100,
.app-dark .border-gray-200 {
  border-color: #1f2937 !important;
}

.app-dark .text-gray-900,
.app-dark .text-gray-800,
.app-dark .text-gray-700 {
  color: #f8fafc !important;
}

.app-dark .text-gray-600,
.app-dark .text-gray-500,
.app-dark .text-gray-400,
.app-dark .text-grey-darken-1,
.app-dark .text-grey-darken-2 {
  color: #cbd5e1 !important;
}

.app-dark .bb-input-shell,
.app-dark .bb-button-muted,
.app-dark .bb-button-secondary,
.app-dark .bb-icon-button,
.app-dark .bb-phone-nav-button,
.app-dark .bb-phone-nav-panel,
.app-dark .bb-phone-nav-link,
.app-dark .bb-page-button,
.app-dark .v-field {
  background: #1f2937 !important;
  border-color: #334155 !important;
  color: #f8fafc !important;
}

.app-dark .bb-input-control,
.app-dark .v-field__input,
.app-dark input {
  color: #f8fafc !important;
}

.app-dark .v-overlay-container .v-list,
.app-dark .table-header,
.app-dark thead tr,
.app-dark tbody tr:hover,
.app-dark .transactions-total-footer,
.app-dark footer {
  background: #111827 !important;
  border-color: #1f2937 !important;
}

.app-dark .v-application .budget-widget-row {
  border-top-color: #1f2937;
}

.app-dark .v-application .budget-progress-track {
  background: #1f2937;
}

.app-dark .v-application .budget-empty-state {
  background: linear-gradient(135deg, rgba(20, 83, 45, 0.28), rgba(31, 41, 55, 0.64));
  border-color: rgba(74, 222, 128, 0.22);
}

.app-dark .v-application .budget-empty-icon {
  background: #1f2937;
  border-color: rgba(74, 222, 128, 0.24);
  color: #86efac;
}

.app-dark .v-application .due-empty-state {
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.26), rgba(31, 41, 55, 0.64));
  border-color: rgba(96, 165, 250, 0.24);
}

.app-dark .v-application .due-empty-icon {
  background: #1f2937;
  border-color: rgba(96, 165, 250, 0.26);
  color: #93c5fd;
}

.app-dark .v-application .budget-month-shell {
  background: #1f2937;
  border-color: #334155;
}

.app-dark .v-application .budget-month-input {
  color-scheme: dark;
}

.app-dark .v-application .budget-month-input::-webkit-calendar-picker-indicator {
  filter: invert(1);
  opacity: 0.75;
}

.app-dark .v-application .metric-card {
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
}

.app-dark .v-application .reports-stacked-chart {
  background: linear-gradient(180deg, rgba(23, 32, 51, 0.96), rgba(17, 24, 39, 0.96));
  border-color: #1f2937;
}

.app-dark .v-application .forecast-month {
  background: rgba(23, 32, 51, 0.72);
  border-color: #1f2937;
  box-shadow: inset 0 1px rgba(255, 255, 255, 0.04), 0 8px 18px rgba(0, 0, 0, 0.12);
}

.app-dark .v-application .reports-stacked-chart::before {
  background-image: linear-gradient(to top, rgba(203, 213, 225, 0.08) 1px, transparent 1px);
}

.app-dark .v-application .reports-stacked-segment {
  box-shadow: inset 0 1px rgba(255, 255, 255, 0.18), 0 1px 0 rgba(15, 23, 42, 0.2);
}

.app-dark .v-application .reports-legend-dot {
  box-shadow: 0 0 0 1px rgba(248, 250, 252, 0.16) !important;
}

.app-dark .v-application .due-panel {
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
}

.app-dark .v-application .due-panel .empty-state,
.app-dark .v-application .due-item {
  background: rgba(23, 32, 51, 0.72);
}

.app-dark .v-application .projection-refresh-button,
.app-dark .v-application .due-refresh-button {
  background: #172033 !important;
  border-color: rgba(134, 239, 172, 0.28) !important;
  color: #86efac !important;
}

.app-dark .v-application .alert-title,
.app-dark .v-application .alert-item-title {
  color: #f8fafc;
}

.app-dark .v-application .alert-subtitle,
.app-dark .v-application .alert-item-message,
.app-dark .v-application .alert-empty {
  color: #cbd5e1;
}

.app-dark .v-application .alert-item {
  background: #111827;
  border-color: #1f2937;
}

.app-dark .v-application .v-btn.due-refresh-button.v-btn--variant-outlined {
  background: #172033 !important;
  border-color: rgba(134, 239, 172, 0.28) !important;
  color: #86efac !important;
}

.app-dark .v-application .projection-refresh-button .v-icon,
.app-dark .v-application .projection-refresh-button .v-btn__content,
.app-dark .v-application .due-refresh-button .v-icon,
.app-dark .v-application .due-refresh-button .v-btn__content {
  color: inherit !important;
}

.app-dark .v-application .account-card {
  --account-accent-blue: #93c5fd;
  --account-accent-orange: #fdba74;
  --account-accent-green: #86efac;
  --account-amount-positive: #86efac;
  --account-amount-negative: #fca5a5;
  --account-amount-warning: #fdba74;
}

.app-dark .v-application .account-card.selected {
  border-color: #86efac !important;
  box-shadow: 0 8px 30px rgba(74, 222, 128, 0.18) !important;
}

.app-dark .v-application .account-balance-label--asset,
.app-dark .v-application .account-type-chip.text-blue {
  color: #93c5fd !important;
}

.app-dark .v-application .account-balance-label--credit,
.app-dark .v-application .account-type-chip.text-orange {
  color: #fdba74 !important;
}

.app-dark .v-application .account-balance-label--cash,
.app-dark .v-application .account-type-chip.text-green,
.app-dark .v-application .account-amount-positive {
  color: #86efac !important;
}

.app-dark .v-application .account-amount-negative {
  color: #fca5a5 !important;
}

.app-dark .v-application .account-amount-warning {
  color: #fdba74 !important;
}

.app-dark .v-application .account-type-chip {
  background: rgba(15, 23, 42, 0.28) !important;
  border-color: color-mix(in srgb, currentColor 34%, transparent);
}

.app-dark .v-application .account-type-chip.text-purple {
  color: #d8b4fe !important;
}

.app-dark .v-application .account-type-chip.text-amber,
.app-dark .v-application .account-type-chip.text-brown {
  color: #fde68a !important;
}

.app-dark .v-application .account-type-chip.text-teal {
  color: #5eead4 !important;
}

.app-dark .v-application .account-type-chip.text-grey {
  color: #cbd5e1 !important;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #4CAF50;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #2E7D32;
}

/* App surfaces */
.glass-card {
  background: #ffffff;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
}

/* Modern shadows */
.shadow-soft {
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
}

.shadow-medium {
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}

.shadow-strong {
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.10);
}

/* Smooth transitions */
.smooth-transition {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Hover effects */
.hover-lift:hover {
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
  transform: translateY(-1px);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

/* Budget Buddy specific styles */
.budget-gradient {
  background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 50%, #8BC34A 100%);
}

.budget-text-gradient {
  background: none;
  color: var(--bb-text-strong, #1f2937);
  -webkit-background-clip: text;
  -webkit-text-fill-color: currentColor;
  background-clip: text;
}

/* Shared native controls */
.bb-button,
.bb-icon-button,
.bb-input-shell {
  transition: background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, color 0.2s ease;
}

.bb-button {
  align-items: center;
  border: 1px solid transparent;
  border-radius: 0.75rem;
  cursor: pointer;
  display: inline-flex;
  font-size: 0.875rem;
  font-weight: 700;
  gap: 0.5rem;
  height: 2.75rem;
  justify-content: center;
  letter-spacing: 0;
  padding: 0 1rem;
  white-space: nowrap;
}

.bb-button-primary {
  background: #2E7D32;
  color: #ffffff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
}

.bb-button-primary:hover {
  background: #276b2b;
}

.bb-button-secondary {
  background: #ffffff;
  border-color: rgba(76, 175, 80, 0.35);
  color: #2E7D32;
}

.bb-button-secondary:hover {
  background: #f0fdf4;
  border-color: #4CAF50;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
}

.bb-button-muted {
  background: #ffffff;
  border-color: #e5e7eb;
  color: #374151;
}

.bb-button-muted:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.bb-icon-button {
  align-items: center;
  background: #ffffff;
  border: 1px solid transparent;
  border-radius: 9999px;
  color: #4b5563;
  cursor: pointer;
  display: inline-flex;
  height: 2.5rem;
  justify-content: center;
  width: 2.5rem;
}

.bb-icon-button:hover {
  background: #f9fafb;
  border-color: #f3f4f6;
  color: #111827;
}

.bb-phone-nav,
.transactions-phone-export {
  display: none;
}

.bb-phone-nav {
  position: relative;
}

.bb-phone-nav > summary {
  list-style: none;
}

.bb-phone-nav > summary::-webkit-details-marker {
  display: none;
}

.bb-phone-nav-button {
  align-items: center;
  background: #ffffff;
  border: 1px solid #f3f4f6;
  border-radius: 9999px;
  color: #4b5563;
  cursor: pointer;
  display: inline-flex;
  height: 2.5rem;
  justify-content: center;
  width: 2.5rem;
}

.bb-phone-nav-button:hover {
  background: #f9fafb;
  color: #111827;
}

.bb-phone-nav-panel {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 0.875rem;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.14);
  display: none;
  gap: 0.25rem;
  min-width: 11rem;
  padding: 0.5rem;
  position: absolute;
  right: 0;
  top: calc(100% + 0.625rem);
  z-index: 80;
}

.bb-phone-nav[open] .bb-phone-nav-panel {
  display: grid;
}

.bb-phone-nav-link {
  background: transparent;
  border: 0;
  border-radius: 0.625rem;
  color: #4b5563;
  cursor: pointer;
  display: block;
  font-size: 0.9rem;
  font-weight: 700;
  padding: 0.65rem 0.75rem;
  text-align: left;
  text-decoration: none;
  width: 100%;
}

.bb-phone-nav-link:hover,
.bb-phone-nav-link.router-link-exact-active {
  background: #f0fdf4;
  color: #2e7d32;
}

.bb-input-shell {
  align-items: center;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  display: flex;
  min-height: 2.75rem;
  overflow: hidden;
}

.bb-input-shell:focus-within {
  border-color: #4CAF50;
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.12);
}

.bb-input-control {
  background: transparent;
  border: 0;
  color: #111827;
  flex: 1 1 auto;
  font-size: 0.875rem;
  min-width: 0;
  outline: 0;
  padding: 0 1rem 0 0.5rem;
}

.bb-input-control::placeholder {
  color: #9ca3af;
}

.bb-input-control.with-leading-icon {
  padding-left: 2rem;
}

.bb-page-button {
  align-items: center;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  color: #374151;
  display: inline-flex;
  font-size: 0.875rem;
  font-weight: 700;
  height: 2.25rem;
  justify-content: center;
  min-width: 2.25rem;
  padding: 0 0.625rem;
}

.bb-page-button:hover {
  background: #f9fafb;
  border-color: rgba(76, 175, 80, 0.35);
  color: #2E7D32;
}

.bb-page-button.active {
  background: #2E7D32;
  border-color: #2E7D32;
  color: #ffffff;
}

.bb-button:focus-visible,
.bb-icon-button:focus-visible,
.bb-page-button:focus-visible {
  outline: 3px solid rgba(76, 175, 80, 0.28);
  outline-offset: 2px;
}

/* Vuetify controls, aligned to the native controls above */
.v-application .v-btn {
  border-radius: 0.75rem !important;
  box-shadow: none !important;
  font-weight: 700 !important;
  letter-spacing: 0 !important;
  text-transform: none !important;
}

.v-application .v-card {
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05) !important;
}

.v-application .v-btn:not(.v-btn--icon) {
  min-height: 2.5rem;
  padding-inline: 1rem;
}

.v-application .v-btn--variant-outlined:not(.text-error):not(.text-red):not([class*="text-red"]) {
  background: #ffffff;
  border-color: rgba(76, 175, 80, 0.35) !important;
  color: #2E7D32;
}

.v-application .v-btn--variant-outlined:not(.text-error):not(.text-red):not([class*="text-red"]):hover {
  background: #f0fdf4;
  border-color: #4CAF50 !important;
}

.app-dark .v-application .v-btn.due-refresh-button.v-btn--variant-outlined:not(.text-error):not(.text-red):not([class*="text-red"]) {
  background: #172033 !important;
  border-color: rgba(134, 239, 172, 0.28) !important;
  color: #86efac !important;
}

.app-dark .v-application .v-btn.due-refresh-button.v-btn--variant-outlined:not(.text-error):not(.text-red):not([class*="text-red"]):hover {
  background: #1f2937 !important;
  border-color: rgba(134, 239, 172, 0.44) !important;
}

.v-application .v-btn--variant-outlined.text-error,
.v-application .v-btn--variant-outlined.text-red,
.v-application .v-btn--variant-outlined[class*="text-red"] {
  background: #ffffff;
  border-color: #fecaca !important;
}

.v-application .v-btn--variant-text {
  color: #374151;
}

.v-application .v-field {
  background: #ffffff;
  border-radius: 0.75rem !important;
  transform: none !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.v-application .v-field:hover {
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06) !important;
  transform: none !important;
}

.v-application .v-field--focused {
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.12) !important;
  transform: none !important;
}

.v-application .v-field__outline,
.v-application .v-field__outline__start,
.v-application .v-field__outline__notch,
.v-application .v-field__outline__end {
  border-radius: 0.75rem !important;
}

.v-application .v-field__outline {
  color: #e5e7eb !important;
}

.v-application .v-field--focused .v-field__outline {
  color: #4CAF50 !important;
}

.v-application .v-field--error .v-field__outline {
  color: #ef4444 !important;
}

.v-application .v-field__input {
  color: #111827;
  font-size: 0.875rem;
  font-weight: 600;
}

.v-application .v-label.v-field-label {
  color: #6b7280 !important;
  opacity: 1 !important;
}

.v-application .v-field--focused .v-label.v-field-label {
  color: #2E7D32 !important;
}

.v-application .v-field--variant-outlined .v-field-label--floating {
  background: #ffffff;
  padding: 0 0.375rem;
  z-index: 2;
}

.v-application .v-field--variant-outlined .v-field__outline__notch::before {
  border-top: 0 !important;
}

.v-overlay-container .v-list {
  border: 1px solid #f3f4f6;
  border-radius: 0.875rem !important;
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.12);
}

@media (max-width: 640px) {
  .bb-phone-header-grid {
    display: flex;
    gap: 0.5rem;
    height: 4rem;
    justify-content: space-between;
  }

  .bb-phone-brand {
    flex: 0 0 auto;
    min-width: 0;
  }

  .bb-phone-brand-text {
    display: none !important;
  }

  .bb-phone-actions {
    flex: 0 0 auto;
    gap: 0.4rem !important;
    min-width: 0;
  }

  .bb-phone-actions .bb-icon-button,
  .bb-phone-nav-button {
    height: 2.35rem;
    width: 2.35rem;
  }

  .bb-phone-user-shell {
    gap: 0;
    padding: 0.25rem !important;
  }

  .bb-phone-user-shell > .hidden {
    display: none !important;
  }

  .bb-phone-nav {
    display: block;
  }

  .transactions-header-export {
    display: none !important;
  }

  .transactions-phone-export {
    display: inline-flex;
    margin-top: 0.75rem;
    width: 100%;
  }

  .bb-phone-table-scroll {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .bb-phone-min-table {
    min-width: 42rem;
  }

  .bb-phone-min-table-compact {
    min-width: 36rem;
  }
}
</style>

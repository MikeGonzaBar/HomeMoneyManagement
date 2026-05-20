<template>
  <v-app>
    <router-view />
  </v-app>
</template>

<script lang="ts" setup>
//
</script>

<style>
/* Global Styles for Budget Buddy */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
  font-family: 'Inter', sans-serif;
}

.v-application {
  background: #f9fafb !important;
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
  color: #1f2937;
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
</style>

/// <reference types="vite/client" />

/**
 * Brandfetch Logo API client ID (https://developers.brandfetch.com/register).
 *
 * Optional: with it unset, bank logos are skipped entirely and the UI falls
 * back to its own initial avatars. It is embedded in <img src> by design, so it
 * is not a server secret - but it carries a monthly allowance, so it is never
 * hardcoded in the source.
 */
interface ImportMetaEnv {
  readonly VITE_BRANDFETCH_CLIENT_ID?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// Global type declarations
declare global {
  interface Window {
    // Add any global window properties here if needed
  }
}
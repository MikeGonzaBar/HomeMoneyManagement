<template>
  <!--
    Bank logo via the Brandfetch Logo API.

    The API is a CDN URL designed for an <img src>; requesting it with fetch()
    is treated as automated traffic and redirected, so this component never
    calls the API itself - the browser loads the image. `fallback/404` means a
    miss is a clean 404 and we keep our own initial avatar, rather than showing
    the Brandfetch wordmark as if it were the bank.
  -->
  <img
    v-if="src && !failed"
    :src="src"
    :alt="`${bank || 'Bank'} logo`"
    class="bank-logo"
    loading="lazy"
    decoding="async"
    @error="failed = true"
  />
  <span v-else class="bank-logo__initial" :style="initialStyle" role="img" :aria-label="`${bank || 'Unknown bank'}`">
    {{ initial }}
  </span>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { bankInitial, bankLogoUrl } from '@/services/bankLogos';

/**
 * Read once at module scope: the client ID is a build-time value, so it cannot
 * change at runtime and re-reading it per account would be wasted work.
 */
const CLIENT_ID = import.meta.env.VITE_BRANDFETCH_CLIENT_ID ?? '';

export default defineComponent({
  name: 'BankLogo',
  props: {
    bank: { type: String, default: '' },
    /** Rendered edge in px; keep it >= 2x the display size for retina. */
    size: { type: Number, default: 64 },
    /** `light` | `dark` logo variant. */
    theme: { type: String as () => 'light' | 'dark' | undefined, default: undefined },
  },
  data() {
    return {
      failed: false,
      // Precomputed once per (bank, size, theme) so the template stays cheap.
      src: bankLogoUrl(this.bank, CLIENT_ID, { size: this.size, theme: this.theme }),
      initial: bankInitial(this.bank),
    };
  },
  computed: {
    initialStyle(): Record<string, string> {
      return { fontSize: `${Math.max(10, Math.round(this.size / 2.6))}px` };
    },
  },
  watch: {
    // A recycled row (v-for keys) can change which bank it shows.
    bank() {
      this.src = bankLogoUrl(this.bank, CLIENT_ID, { size: this.size, theme: this.theme });
      this.initial = bankInitial(this.bank);
      this.failed = false;
    },
  },
});
</script>

<style scoped>
.bank-logo {
  border-radius: 6px;
  display: block;
  height: 100%;
  object-fit: contain;
  width: 100%;
}

.bank-logo__initial {
  align-items: center;
  background: var(--bb-surface-soft, #f3f4f6);
  border-radius: 6px;
  color: var(--bb-text-muted, #6b7280);
  display: flex;
  font-weight: 600;
  height: 100%;
  justify-content: center;
  line-height: 1;
  user-select: none;
  width: 100%;
}
</style>

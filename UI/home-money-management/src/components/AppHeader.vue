<template>
  <header class="bg-white/95 backdrop-blur border-b border-gray-200 sticky top-0 z-50">
    <div class="w-full px-4 sm:px-6 lg:px-10">
      <div class="bb-phone-header-grid grid grid-cols-[minmax(0,1fr)_minmax(0,auto)_minmax(0,1fr)] items-center gap-6 h-[72px]">
        <!-- Logo and Brand -->
        <div class="bb-phone-brand flex items-center gap-3 min-w-0">
          <router-link to="/" class="flex items-center gap-3 shrink-0">
            <img src="@/assets/logo-192.png" alt="Budget Buddy" class="w-10 h-10 rounded-lg object-contain" />
            <span class="bb-phone-brand-text text-xl font-bold text-gray-900 tracking-tight whitespace-nowrap">Budget Buddy</span>
          </router-link>
          <!-- Page-specific brand content (e.g. Transactions search) -->
          <slot name="brand-extra" />
        </div>

        <!-- Desktop Navigation -->
        <nav class="bb-app-nav hidden md:flex items-center gap-1 rounded-full border border-gray-100 bg-gray-50 p-1 shadow-sm">
          <router-link v-for="item in navItems" :key="item.to" :to="item.to"
            :class="isActive(item.to) ? navActiveClass : navInactiveClass">
            {{ item.label }}
          </router-link>
        </nav>

        <!-- User Profile -->
        <div class="bb-phone-actions flex items-center justify-end gap-3 min-w-0">
          <details class="bb-phone-nav">
            <summary class="bb-phone-nav-button" aria-label="Open navigation">
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7h16M4 12h16M4 17h16"></path>
              </svg>
            </summary>
            <nav class="bb-phone-nav-panel" aria-label="Phone navigation">
              <router-link v-for="item in navItems" :key="item.to" :to="item.to" class="bb-phone-nav-link">{{ item.label }}</router-link>
              <button type="button" class="bb-phone-nav-link" @click="goToProfile">Profile</button>
            </nav>
          </details>
          <!-- Page-specific header actions (e.g. Transactions export) -->
          <slot name="actions" />
          <AlertCenter />
          <ThemeToggle />
          <div class="bb-phone-user-shell flex items-center gap-3 rounded-full border border-gray-100 bg-gray-50 py-1 pl-4 pr-1.5">
            <div class="text-right hidden sm:block">
              <p class="text-sm font-semibold text-gray-900 leading-none">{{ userData?.user?.first_name }} {{
                userData?.user?.last_name }}</p>
              <p class="text-xs text-gray-500 mt-1">Premium Member</p>
            </div>
            <div
              class="h-9 w-9 rounded-full bg-brand-primary flex items-center justify-center text-white font-semibold cursor-pointer shadow-sm"
              @click="goToProfile">
              {{ userData?.user?.first_name?.charAt(0) }}{{ userData?.user?.last_name?.charAt(0) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script lang="ts">
import AlertCenter from '@/components/AlertCenter.vue';
import ThemeToggle from '@/components/ThemeToggle.vue';

const NAV_ITEMS = [
  { label: 'Dashboard', to: '/' },
  { label: 'Transactions', to: '/transactions' },
  { label: 'Budgets', to: '/budgets' },
  { label: 'Recurring', to: '/recurring' },
  { label: 'Reports', to: '/reports' },
  { label: 'Statements', to: '/statements' },
  { label: 'Accounts', to: '/accounts' },
];

export default {
  name: 'AppHeader',
  components: {
    AlertCenter,
    ThemeToggle,
  },
  props: {
    userData: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      navItems: NAV_ITEMS,
      navActiveClass: 'rounded-full bg-white px-4 py-2 text-sm font-semibold text-brand-primary shadow-sm',
      navInactiveClass: 'rounded-full px-4 py-2 text-sm font-medium text-gray-500 transition-colors hover:bg-white hover:text-gray-700',
    };
  },
  methods: {
    isActive(path: string): boolean {
      return (this as any).$route.path === path;
    },
    goToProfile() {
      (this as any).$router.push('/profile');
    },
  },
};
</script>

<style scoped>
/* The pill nav shrinks and scrolls instead of overflowing the header once the
   viewport is too narrow for every pill (7 since Phase 4 — see the overhaul
   plan's risk 3). Focus scrolling still reveals off-screen pills. */
.bb-app-nav {
  scrollbar-width: none;
}

.bb-app-nav::-webkit-scrollbar {
  display: none;
}
</style>

<template>
  <footer class="mt-auto border-t border-gray-200 py-8 px-6 bg-white">
    <div class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
      <div class="flex items-center gap-2 opacity-70">
        <img src="@/assets/logo-192.png" alt="" class="w-5 h-5 rounded object-contain" />
        <span class="text-sm font-bold">Budget Buddy © {{ currentYear }}</span>
      </div>
      <div class="flex gap-6 md:gap-8 text-sm font-medium text-gray-500 flex-wrap justify-center">
        <router-link to="/privacy-policy" class="py-1 hover:text-brand-primary transition-colors">
          Privacy Policy
        </router-link>
        <router-link to="/terms-of-service" class="py-1 hover:text-brand-primary transition-colors">
          Terms of Service
        </router-link>
        <router-link to="/help" class="py-1 hover:text-brand-primary transition-colors">
          Help Center
        </router-link>
        <a href="https://github.com/gonzales-juan/HomeMoneyManagement/issues" target="_blank" rel="noopener noreferrer" class="py-1 hover:text-brand-primary transition-colors">
          Report Issue
        </a>
      </div>
    </div>
  </footer>
</template>

<script lang="ts">
export default {
  name: 'AppFooter',
  computed: {
    currentYear() {
      return new Date().getFullYear()
    }
  }
}
</script>
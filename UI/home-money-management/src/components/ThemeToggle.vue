<template>
  <button class="bb-icon-button" :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'" @click="toggleTheme">
    <v-icon :icon="isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'" size="20"></v-icon>
  </button>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { useTheme } from 'vuetify'
import axios from '@/services/api'
import { getStoredSession, setStoredSession } from '@/services/session'
import { applyDocumentTheme, type ThemePreference } from '@/services/theme'

export default defineComponent({
  name: 'ThemeToggle',
  setup() {
    const theme = useTheme()
    return { theme }
  },
  data() {
    return {
      preference: 'system' as ThemePreference,
      resolved: 'light' as 'light' | 'dark',
    }
  },
  computed: {
    isDark(): boolean {
      return this.resolved === 'dark'
    },
  },
  mounted() {
    const session = getStoredSession()
    this.preference = session?.user.theme_preference ?? 'system'
    this.applyTheme()
  },
  methods: {
    applyTheme() {
      this.resolved = applyDocumentTheme(this.preference)
      this.theme.global.name.value = this.resolved
    },
    async toggleTheme() {
      this.preference = this.isDark ? 'light' : 'dark'
      this.applyTheme()
      try {
        const response = await axios.put('/user/preferences/', { theme_preference: this.preference })
        const session = getStoredSession()
        if (session && response.data?.user) {
          setStoredSession({ token: session.token, user: response.data.user })
        }
      } catch (error) {
        console.error('Failed to save theme preference:', error)
      }
    },
  },
})
</script>

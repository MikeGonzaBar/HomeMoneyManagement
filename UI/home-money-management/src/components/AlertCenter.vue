<template>
  <v-menu v-model="open" location="bottom end" :close-on-content-click="false" offset="8" max-width="420">
    <template v-slot:activator="{ props }">
      <button v-bind="props" class="bb-icon-button relative" aria-label="Notifications" @click="refreshAlerts">
        <v-icon icon="mdi-bell-outline" size="21"></v-icon>
        <span v-if="unreadCount" class="alert-badge">{{ unreadCount }}</span>
      </button>
    </template>
    <v-card class="alert-menu" rounded="lg">
      <div class="alert-menu-header">
        <div>
          <p class="alert-title">Alerts</p>
          <p class="alert-subtitle">{{ alerts.length }} active item{{ alerts.length === 1 ? '' : 's' }}</p>
        </div>
        <v-btn size="small" variant="text" :loading="loading" @click="refreshAlerts">Refresh</v-btn>
      </div>
      <v-divider></v-divider>
      <div v-if="alerts.length" class="alert-list">
        <article v-for="alert in alerts" :key="alert.id" class="alert-item" :class="alert.severity">
          <div class="alert-item-body">
            <p class="alert-item-title">{{ alert.title }}</p>
            <p class="alert-item-message">{{ alert.message }}</p>
          </div>
          <div class="alert-actions">
            <v-btn icon="mdi-check" size="x-small" variant="text" @click="markRead(alert)"></v-btn>
            <v-btn icon="mdi-close" size="x-small" variant="text" @click="dismiss(alert)"></v-btn>
          </div>
        </article>
      </div>
      <div v-else class="alert-empty">
        <v-icon icon="mdi-check-circle-outline" size="28"></v-icon>
        <p>No active alerts</p>
      </div>
    </v-card>
  </v-menu>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import axios from '@/services/api'

interface AlertItem {
  id: number
  alert_type: string
  severity: 'info' | 'warning' | 'critical'
  title: string
  message: string
  read: boolean
}

export default defineComponent({
  name: 'AlertCenter',
  data() {
    return {
      open: false,
      loading: false,
      alerts: [] as AlertItem[],
    }
  },
  computed: {
    unreadCount(): number {
      return this.alerts.filter((item) => !item.read).length
    },
  },
  mounted() {
    this.loadAlerts()
  },
  methods: {
    normalizeAlerts(payload: unknown): AlertItem[] {
      if (Array.isArray(payload)) return payload as AlertItem[]
      if (payload && typeof payload === 'object' && Array.isArray((payload as any).alerts)) {
        return (payload as any).alerts
      }
      return []
    },
    async loadAlerts() {
      try {
        const response = await axios.get('/alerts/')
        this.alerts = this.normalizeAlerts(response.data)
      } catch (error) {
        console.error('Failed to load alerts:', error)
        this.alerts = []
      }
    },
    async refreshAlerts() {
      this.loading = true
      try {
        const response = await axios.post('/alerts/refresh/')
        this.alerts = this.normalizeAlerts(response.data)
      } catch (error) {
        console.error('Failed to refresh alerts:', error)
        this.alerts = []
      } finally {
        this.loading = false
      }
    },
    async markRead(alert: AlertItem) {
      const response = await axios.patch(`/alerts/${alert.id}/read/`)
      Object.assign(alert, response.data)
    },
    async dismiss(alert: AlertItem) {
      await axios.patch(`/alerts/${alert.id}/dismiss/`)
      this.alerts = this.alerts.filter((item) => item.id !== alert.id)
    },
  },
})
</script>

<style scoped>
.alert-badge {
  align-items: center;
  background: #ef4444;
  border: 2px solid #ffffff;
  border-radius: 999px;
  color: #ffffff;
  display: inline-flex;
  font-size: 0.625rem;
  font-weight: 800;
  height: 1.1rem;
  justify-content: center;
  min-width: 1.1rem;
  padding: 0 0.25rem;
  position: absolute;
  right: -0.1rem;
  top: -0.1rem;
}

.alert-menu {
  width: min(420px, calc(100vw - 24px));
}

.alert-menu-header {
  align-items: center;
  display: flex;
  justify-content: space-between;
  padding: 1rem;
}

.alert-title {
  color: #111827;
  font-weight: 800;
  margin: 0;
}

.alert-subtitle,
.alert-item-message {
  color: #6b7280;
  font-size: 0.8rem;
  margin: 0;
}

.alert-list {
  max-height: 360px;
  overflow: auto;
  padding: 0.5rem;
}

.alert-item {
  border: 1px solid #f3f4f6;
  border-left: 4px solid #3b82f6;
  border-radius: 0.75rem;
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
  padding: 0.75rem;
}

.alert-item.warning {
  border-left-color: #f59e0b;
}

.alert-item.critical {
  border-left-color: #ef4444;
}

.alert-item-body {
  flex: 1;
  min-width: 0;
}

.alert-item-title {
  color: #111827;
  font-size: 0.9rem;
  font-weight: 800;
  margin: 0 0 0.25rem;
}

.alert-actions {
  display: flex;
  flex: 0 0 auto;
}

.alert-empty {
  align-items: center;
  color: #6b7280;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 2rem;
}

</style>

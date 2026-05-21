<template>
  <div class="bg-gray-50 text-gray-900 font-sans antialiased min-h-screen">
    <header class="bg-white/95 backdrop-blur border-b border-gray-200 sticky top-0 z-50">
      <div class="w-full px-4 sm:px-6 lg:px-10">
        <div class="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-6 h-[72px]">
          <router-link to="/" class="flex items-center gap-3 min-w-0">
            <img src="@/assets/logo-192.png" alt="Budget Buddy" class="w-10 h-10 rounded-lg object-contain" />
            <span class="text-xl font-bold text-gray-900 tracking-tight whitespace-nowrap">Budget Buddy</span>
          </router-link>
          <nav class="hidden md:flex items-center gap-1 rounded-full border border-gray-100 bg-gray-50 p-1 shadow-sm">
            <router-link to="/" class="nav-link">Dashboard</router-link>
            <router-link to="/transactions" class="nav-link">Transactions</router-link>
            <router-link to="/budgets" class="nav-link active">Budgets</router-link>
            <router-link to="/recurring" class="nav-link">Recurring</router-link>
            <router-link to="/reports" class="nav-link">Reports</router-link>
          </nav>
          <div class="flex items-center justify-end gap-2 min-w-0">
            <AlertCenter />
            <ThemeToggle />
            <div class="h-9 w-9 rounded-full bg-brand-primary flex items-center justify-center text-white font-semibold cursor-pointer shadow-sm"
              @click="goToProfile">
              {{ userData.user?.first_name?.charAt(0) }}{{ userData.user?.last_name?.charAt(0) }}
            </div>
          </div>
        </div>
      </div>
    </header>

    <main class="w-full px-4 sm:px-6 py-6">
      <div class="page-heading">
        <div>
          <h1 class="text-gray-900 text-3xl font-bold tracking-tight">Budgets</h1>
          <p class="text-gray-500">Plan monthly category spending and track what is left.</p>
        </div>
        <div class="budget-controls">
          <label class="budget-month-shell" for="budget-month-input">
            <span class="budget-month-label">Month</span>
            <input
              id="budget-month-input"
              v-model="selectedMonth"
              aria-label="Budget month"
              class="budget-month-input"
              type="month"
              @change="loadBudgets"
            />
          </label>
          <v-btn color="primary" @click="dialog = true">New Budget</v-btn>
        </div>
      </div>

      <section class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <article class="metric-card metric-card--limit">
          <p class="metric-label">Overall Limit</p>
          <p class="metric-value">${{ totalLimit.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</p>
        </article>
        <article class="metric-card metric-card--spent">
          <p class="metric-label">Spent</p>
          <p class="metric-value">${{ totalSpent.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</p>
        </article>
        <article class="metric-card metric-card--remaining">
          <p class="metric-label">Remaining</p>
          <p class="metric-value" :class="totalRemaining < 0 ? 'metric-value--negative' : 'metric-value--positive'">
            ${{ totalRemaining.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}
          </p>
        </article>
      </section>

      <section class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-5 py-4 text-xs font-bold uppercase text-gray-500">Budget</th>
              <th class="px-5 py-4 text-xs font-bold uppercase text-gray-500">Limit</th>
              <th class="px-5 py-4 text-xs font-bold uppercase text-gray-500">Spent</th>
              <th class="px-5 py-4 text-xs font-bold uppercase text-gray-500">Progress</th>
              <th class="px-5 py-4 text-xs font-bold uppercase text-gray-500 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="budget in budgets" :key="budget.id">
              <td class="px-5 py-4 font-semibold">{{ budget.scope === 'overall' ? 'Overall budget' : budget.category }}</td>
              <td class="px-5 py-4">${{ budget.limit_amount.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</td>
              <td class="px-5 py-4">${{ budget.spent_amount.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</td>
              <td class="px-5 py-4 min-w-[220px]">
                <div class="progress-track">
                  <div class="progress-bar" :class="budget.status" :style="{ width: Math.min(100, budget.percent_used) + '%' }"></div>
                </div>
                <p class="text-xs text-gray-500 mt-1">{{ budget.percent_used }}% used</p>
              </td>
              <td class="px-5 py-4 text-right">
                <v-btn icon="mdi-pencil" size="small" variant="text" @click="editBudget(budget)"></v-btn>
                <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="deleteBudget(budget)"></v-btn>
              </td>
            </tr>
            <tr v-if="budgets.length === 0">
              <td colspan="5" class="px-5 py-12 text-center text-gray-500">No budgets for this month yet.</td>
            </tr>
          </tbody>
        </table>
      </section>
    </main>

    <v-dialog v-model="dialog" max-width="520">
      <v-card rounded="lg">
        <v-card-title class="pa-5">{{ editingId ? 'Edit Budget' : 'New Budget' }}</v-card-title>
        <v-card-text class="pa-5 pt-0">
          <v-select v-model="form.scope" :items="scopeOptions" label="Scope" class="mb-3"></v-select>
          <v-select v-if="form.scope === 'category'" v-model="form.category" :items="categories" label="Category" class="mb-3"></v-select>
          <v-text-field v-model="form.limit_amount" type="number" step="0.01" label="Monthly limit"></v-text-field>
        </v-card-text>
        <v-card-actions class="pa-5 pt-0">
          <v-spacer></v-spacer>
          <v-btn variant="outlined" @click="closeDialog">Cancel</v-btn>
          <v-btn color="primary" :disabled="!isFormValid" @click="saveBudget">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import axios from '@/services/api'
import { getStoredSession } from '@/services/session'
import AlertCenter from '@/components/AlertCenter.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'

interface Budget {
  id: number
  month: string
  scope: 'overall' | 'category'
  category: string | null
  limit_amount: number
  spent_amount: number
  remaining_amount: number
  percent_used: number
  status: string
}

export default defineComponent({
  name: 'Budgets',
  components: { AlertCenter, ThemeToggle },
  data() {
    return {
      userData: { user: {} } as any,
      selectedMonth: new Date().toISOString().slice(0, 7),
      budgets: [] as Budget[],
      dialog: false,
      editingId: null as number | null,
      form: {
        scope: 'category',
        category: '',
        limit_amount: 0,
      },
      scopeOptions: [
        { title: 'Category', value: 'category' },
        { title: 'Overall', value: 'overall' },
      ],
      categories: [
        'Bills and utilities',
        'Education',
        'Entertainment',
        'Food and drinks',
        'Insurance',
        'Investments',
        'Loans',
        'Medical',
        'Others',
        'Shopping',
        'Transportation',
      ],
    }
  },
  computed: {
    isFormValid(): boolean {
      return Number(this.form.limit_amount) >= 0 && (this.form.scope === 'overall' || !!this.form.category)
    },
    totalLimit(): number {
      const overall = this.budgets.find((item) => item.scope === 'overall')
      return overall?.limit_amount ?? this.budgets.reduce((sum, item) => sum + item.limit_amount, 0)
    },
    totalSpent(): number {
      const overall = this.budgets.find((item) => item.scope === 'overall')
      return overall?.spent_amount ?? this.budgets.reduce((sum, item) => sum + item.spent_amount, 0)
    },
    totalRemaining(): number {
      return this.totalLimit - this.totalSpent
    },
  },
  mounted() {
    const session = getStoredSession()
    if (session) this.userData.user = session.user
    if (!this.userData.user?.username) {
      this.$router.replace('/')
      return
    }
    this.loadBudgets()
  },
  methods: {
    async loadBudgets() {
      const response = await axios.get('/budgets/', { params: { month: this.selectedMonth } })
      this.budgets = response.data || []
    },
    editBudget(budget: Budget) {
      this.editingId = budget.id
      this.form = {
        scope: budget.scope,
        category: budget.category || '',
        limit_amount: budget.limit_amount,
      }
      this.dialog = true
    },
    closeDialog() {
      this.dialog = false
      this.editingId = null
      this.form = { scope: 'category', category: '', limit_amount: 0 }
    },
    async saveBudget() {
      const payload = {
        month: this.selectedMonth,
        scope: this.form.scope,
        category: this.form.scope === 'category' ? this.form.category : null,
        limit_amount: this.form.limit_amount,
      }
      if (this.editingId) {
        await axios.patch(`/budgets/${this.editingId}/`, payload)
      } else {
        await axios.post('/budgets/', payload)
      }
      this.closeDialog()
      this.loadBudgets()
    },
    async deleteBudget(budget: Budget) {
      await axios.delete(`/budgets/${budget.id}/`)
      this.loadBudgets()
    },
    goToProfile() {
      this.$router.push('/profile')
    },
  },
})
</script>

<style scoped>
.nav-link {
  border-radius: 999px;
  color: #6b7280;
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.5rem 1rem;
}

.nav-link.active {
  background: #ffffff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  color: #4caf50;
}

.page-heading {
  align-items: flex-start;
  display: flex;
  gap: 1rem;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.budget-controls {
  align-items: center;
  display: flex;
  gap: 0.75rem;
}

.budget-month-shell {
  align-items: center;
  background: var(--bb-surface, #ffffff);
  border: 1px solid var(--bb-border-soft, #e5e7eb);
  border-radius: 0.75rem;
  color: var(--bb-text-strong, #111827);
  display: inline-flex;
  gap: 0.75rem;
  height: 2.75rem;
  min-width: 12rem;
  padding: 0 0.875rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
}

.budget-month-shell:focus-within {
  border-color: #4caf50;
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.12);
}

.budget-month-label {
  color: var(--bb-text-muted, #6b7280);
  flex: 0 0 auto;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0;
}

.budget-month-input {
  background: transparent;
  border: 0;
  color: var(--bb-text-strong, #111827);
  color-scheme: light;
  flex: 1 1 auto;
  font-size: 0.875rem;
  font-weight: 800;
  min-width: 0;
  outline: 0;
}

.budget-month-input::-webkit-calendar-picker-indicator {
  cursor: pointer;
  opacity: 0.7;
}

.metric-card {
  background: var(--bb-metric-card-bg, var(--bb-surface, #ffffff));
  border: 1px solid var(--bb-border-soft, #f3f4f6);
  border-radius: 0.75rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  padding: 1.25rem;
  position: relative;
  overflow: hidden;
}

.metric-card::before {
  background: var(--metric-accent, #4caf50);
  content: '';
  display: block;
  height: 100%;
  left: 0;
  opacity: 0.72;
  position: absolute;
  top: 0;
  width: 4px;
}

.metric-card--limit {
  --metric-accent: #60a5fa;
  --metric-value: var(--bb-metric-limit, var(--bb-text-strong, #111827));
}

.metric-card--spent {
  --metric-accent: #fb7185;
  --metric-value: var(--bb-metric-spent, #be123c);
}

.metric-card--remaining {
  --metric-accent: #34d399;
  --metric-value: var(--bb-metric-positive, #047857);
}

.metric-label {
  color: var(--bb-text-muted, #6b7280);
  font-size: 0.85rem;
  font-weight: 700;
  margin: 0 0 0.5rem;
  position: relative;
}

.metric-value {
  color: var(--metric-value, var(--bb-text-strong, #111827));
  font-size: 1.75rem;
  font-weight: 900;
  margin: 0;
  position: relative;
}

.metric-value--positive {
  color: var(--bb-metric-positive, #047857);
}

.metric-value--negative {
  color: var(--bb-metric-negative, #dc2626);
}

.progress-track {
  background: var(--bb-border-soft, #f3f4f6);
  border-radius: 999px;
  height: 0.55rem;
  overflow: hidden;
}

.progress-bar {
  background: #4caf50;
  height: 100%;
}

.progress-bar.warning {
  background: #f59e0b;
}

.progress-bar.exceeded {
  background: #ef4444;
}

@media (max-width: 768px) {
  .page-heading,
  .budget-controls {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>

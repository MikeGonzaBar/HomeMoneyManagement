<template>
  <div class="bg-gray-50 text-gray-900 font-sans antialiased min-h-screen">
    <AppHeader :userData="userData" />

    <main class="w-full px-4 sm:px-6 py-6">
      <div class="page-heading">
        <div>
          <h1 class="text-gray-900 text-3xl font-bold tracking-tight">Recurring Transactions</h1>
          <p class="text-gray-500">Confirm due bills, income, transfers, and subscriptions before they affect balances.</p>
        </div>
        <v-btn color="primary" @click="dialog = true">New Rule</v-btn>
      </div>

      <section class="due-panel">
        <div class="panel-header">
          <div>
            <h2>Due Soon</h2>
            <p>Generated through {{ throughDate }}</p>
          </div>
          <v-btn class="due-refresh-button" variant="outlined" :loading="loadingDue" @click="loadDue">Refresh</v-btn>
        </div>
        <div v-if="dueItems.length" class="due-list">
          <article v-for="item in dueItems" :key="item.occurrence_id" class="due-item">
            <div>
              <p class="due-title">{{ item.title }}</p>
              <p class="due-meta">{{ item.due_date }} · {{ item.transaction_type }} · ${{ item.total.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</p>
            </div>
            <div class="due-actions">
              <v-btn color="primary" size="small" :disabled="item.status !== 'due'" @click="postDue(item)">Post</v-btn>
              <v-btn variant="outlined" size="small" :disabled="item.status !== 'due'" @click="skipDue(item)">Skip</v-btn>
            </div>
          </article>
        </div>
        <div v-else class="empty-state">
          <p class="empty-title">Nothing due</p>
          <p class="empty-text">Nothing due in the next few days.</p>
        </div>
      </section>

      <section class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden mt-6">
        <div class="bb-phone-table-scroll">
        <table class="bb-phone-min-table-compact w-full text-left border-collapse">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-5 py-4 text-xs font-bold uppercase text-gray-500">Rule</th>
              <th class="px-5 py-4 text-xs font-bold uppercase text-gray-500">Schedule</th>
              <th class="px-5 py-4 text-xs font-bold uppercase text-gray-500">Next Due</th>
              <th class="px-5 py-4 text-xs font-bold uppercase text-gray-500 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="rule in rules" :key="rule.id">
              <td class="px-5 py-4">
                <p class="font-semibold">{{ rule.title }}</p>
                <p class="text-sm text-gray-500">{{ rule.transaction_type }} · {{ rule.category }} · ${{ rule.total.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</p>
              </td>
              <td class="px-5 py-4 capitalize">Every {{ rule.interval }} {{ rule.frequency }}</td>
              <td class="px-5 py-4">{{ rule.next_due_date }}</td>
              <td class="px-5 py-4 text-right">
                <v-btn icon="mdi-pencil" size="small" variant="text" @click="editRule(rule)"></v-btn>
                <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="deleteRule(rule)"></v-btn>
              </td>
            </tr>
            <tr v-if="rules.length === 0">
              <td colspan="4" class="px-5 py-12 text-center text-gray-500">No recurring rules yet.</td>
            </tr>
          </tbody>
        </table>
        </div>
      </section>
    </main>

    <v-dialog v-model="dialog" max-width="660">
      <v-card rounded="lg">
        <v-card-title class="pa-5">{{ editingId ? 'Edit Rule' : 'New Rule' }}</v-card-title>
        <v-card-text class="pa-5 pt-0">
          <v-row>
            <v-col cols="12" md="6">
              <v-select v-model="form.transaction_type" :items="transactionTypes" label="Type"></v-select>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="form.start_date" type="date" label="Start date"></v-text-field>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12" md="8">
              <v-text-field v-model="form.title" label="Title"></v-text-field>
            </v-col>
            <v-col cols="12" md="4">
              <v-text-field v-model="form.total" type="number" step="0.01" label="Amount"></v-text-field>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12" md="6">
              <v-select v-model="form.category" :items="categories" label="Category"></v-select>
            </v-col>
            <v-col cols="12" md="3">
              <v-select v-model="form.frequency" :items="frequencies" label="Frequency"></v-select>
            </v-col>
            <v-col cols="12" md="3">
              <v-text-field v-model="form.interval" type="number" min="1" label="Interval"></v-text-field>
            </v-col>
          </v-row>
          <v-row v-if="form.transaction_type === 'Transfer'">
            <v-col cols="12" md="6">
              <v-select v-model="form.from_account_id" :items="accountOptions" item-title="title" item-value="value" label="From account"></v-select>
            </v-col>
            <v-col cols="12" md="6">
              <v-select v-model="form.to_account_id" :items="accountOptions" item-title="title" item-value="value" label="To account"></v-select>
            </v-col>
          </v-row>
          <v-select v-else v-model="form.account_id" :items="accountOptions" item-title="title" item-value="value" label="Account"></v-select>
        </v-card-text>
        <v-card-actions class="pa-5 pt-0">
          <v-spacer></v-spacer>
          <v-btn variant="outlined" @click="closeDialog">Cancel</v-btn>
          <v-btn color="primary" :disabled="!isFormValid" @click="saveRule">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import axios from '@/services/api'
import { getStoredSession } from '@/services/session'
import AppHeader from '@/components/AppHeader.vue'

interface Account {
  id: number
  account_name: string
}

interface RecurringRule {
  id: number
  title: string
  transaction_type: string
  category: string
  total: number
  account_id?: string | null
  from_account_id?: string | null
  to_account_id?: string | null
  frequency: string
  interval: number
  start_date: string
  next_due_date: string
  active: boolean
}

interface DueItem extends RecurringRule {
  occurrence_id: number
  due_date: string
  status: string
}

const blankForm = () => ({
  title: '',
  transaction_type: 'Expense',
  category: 'Bills and utilities',
  total: 0,
  account_id: '',
  from_account_id: '',
  to_account_id: '',
  frequency: 'monthly',
  interval: 1,
  start_date: new Date().toISOString().slice(0, 10),
  active: true,
})

export default defineComponent({
  name: 'Recurring',
  components: { AppHeader },
  data() {
    const through = new Date()
    through.setDate(through.getDate() + 3)
    return {
      userData: { user: {} } as any,
      accounts: [] as Account[],
      rules: [] as RecurringRule[],
      dueItems: [] as DueItem[],
      throughDate: through.toISOString().slice(0, 10),
      loadingDue: false,
      dialog: false,
      editingId: null as number | null,
      form: blankForm(),
      transactionTypes: ['Income', 'Expense', 'Transfer'],
      frequencies: ['daily', 'weekly', 'monthly', 'yearly'],
      categories: [
        'Bills and utilities',
        'Entertainment',
        'Food and drinks',
        'Insurance',
        'Investments',
        'Loans',
        'Money Transfer',
        'Others',
        'Salary',
        'Transportation',
        'Transfer',
      ],
    }
  },
  computed: {
    accountOptions(): Array<{ title: string; value: string }> {
      return this.accounts.map((account) => ({ title: account.account_name, value: String(account.id) }))
    },
    isFormValid(): boolean {
      const base = !!this.form.title && !!this.form.category && Number(this.form.total) > 0 && !!this.form.start_date
      if (this.form.transaction_type === 'Transfer') {
        return base && !!this.form.from_account_id && !!this.form.to_account_id && this.form.from_account_id !== this.form.to_account_id
      }
      return base && !!this.form.account_id
    },
  },
  mounted() {
    const session = getStoredSession()
    if (session) this.userData.user = session.user
    if (!this.userData.user?.username) {
      this.$router.replace('/')
      return
    }
    this.loadAccounts()
    this.loadRules()
    this.loadDue()
  },
  methods: {
    async loadAccounts() {
      const username = this.userData.user.username
      const response = await axios.get(`/accounts/details/${username}/0`)
      this.accounts = response.data || []
    },
    async loadRules() {
      const response = await axios.get('/recurring-transactions/')
      this.rules = response.data || []
    },
    async loadDue() {
      this.loadingDue = true
      try {
        const response = await axios.get('/recurring-transactions/due/', { params: { through: this.throughDate } })
        this.dueItems = (response.data || []).filter((item: DueItem) => item.status === 'due')
      } finally {
        this.loadingDue = false
      }
    },
    editRule(rule: RecurringRule) {
      this.editingId = rule.id
      this.form = {
        title: rule.title,
        transaction_type: rule.transaction_type,
        category: rule.category,
        total: rule.total,
        account_id: rule.account_id || '',
        from_account_id: rule.from_account_id || '',
        to_account_id: rule.to_account_id || '',
        frequency: rule.frequency,
        interval: rule.interval,
        start_date: rule.start_date,
        active: rule.active,
      }
      this.dialog = true
    },
    closeDialog() {
      this.dialog = false
      this.editingId = null
      this.form = blankForm()
    },
    rulePayload() {
      const payload: any = { ...this.form, total: Number(this.form.total), interval: Number(this.form.interval) || 1 }
      if (payload.transaction_type === 'Transfer') {
        delete payload.account_id
      } else {
        delete payload.from_account_id
        delete payload.to_account_id
      }
      return payload
    },
    async saveRule() {
      if (this.editingId) {
        await axios.patch(`/recurring-transactions/${this.editingId}/`, this.rulePayload())
      } else {
        await axios.post('/recurring-transactions/', this.rulePayload())
      }
      this.closeDialog()
      this.loadRules()
      this.loadDue()
    },
    async deleteRule(rule: RecurringRule) {
      await axios.delete(`/recurring-transactions/${rule.id}/`)
      this.loadRules()
      this.loadDue()
    },
    async postDue(item: DueItem) {
      await axios.post(`/recurring-transactions/due/${item.occurrence_id}/post/`)
      this.loadDue()
    },
    async skipDue(item: DueItem) {
      await axios.post(`/recurring-transactions/due/${item.occurrence_id}/skip/`)
      this.loadDue()
    },
  },
})
</script>

<style scoped>
.page-heading,
.panel-header,
.due-item,
.due-actions {
  align-items: center;
  display: flex;
}

.page-heading,
.panel-header {
  gap: 1rem;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.due-panel {
  background: var(--bb-metric-card-bg, var(--bb-surface, #ffffff));
  border: 1px solid var(--bb-border-soft, #f3f4f6);
  border-radius: 0.75rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  padding: 1.25rem;
  position: relative;
  overflow: hidden;
}

.due-panel::before {
  background: #60a5fa;
  content: '';
  display: block;
  height: 100%;
  left: 0;
  opacity: 0.72;
  position: absolute;
  top: 0;
  width: 4px;
}

.panel-header,
.due-list,
.empty-state {
  position: relative;
}

.panel-header h2,
.due-title {
  color: var(--bb-text-strong, #111827);
  font-weight: 800;
  margin: 0;
}

.panel-header p,
.due-meta,
.empty-text {
  color: var(--bb-text-muted, #6b7280);
  font-size: 0.875rem;
  margin: 0;
}

.due-list {
  display: grid;
  gap: 0.75rem;
}

.due-item {
  background: var(--bb-surface-soft, #f9fafb);
  border: 1px solid var(--bb-border-soft, #f3f4f6);
  border-radius: 0.75rem;
  justify-content: space-between;
  padding: 1rem;
}

.due-actions {
  gap: 0.5rem;
}

.due-refresh-button {
  background: var(--bb-surface, #ffffff) !important;
  border-color: rgba(76, 175, 80, 0.35) !important;
  color: #2e7d32 !important;
}

.due-refresh-button :deep(.v-btn__content),
.due-refresh-button :deep(.v-icon) {
  color: inherit !important;
}

.empty-state {
  align-items: center;
  background: var(--bb-surface-soft, #f9fafb);
  border: 1px solid var(--bb-border-soft, #f3f4f6);
  border-radius: 0.75rem;
  display: flex;
  justify-content: space-between;
  padding: 1rem;
}

.empty-title {
  color: var(--bb-text-strong, #111827);
  font-size: 0.95rem;
  font-weight: 800;
  margin: 0;
}

@media (max-width: 768px) {
  .page-heading,
  .panel-header,
  .due-item {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>

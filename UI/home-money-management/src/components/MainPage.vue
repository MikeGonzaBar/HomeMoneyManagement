<template>
  <div class="bg-gray-50 text-gray-900 font-sans antialiased min-h-screen">
    <AppHeader :userData="userData" />

    <main class="w-full">
      <div class="px-4 sm:px-6 py-6">
        <!-- Decision-first summary: what you have, what you owe, what moved this
             month. Investments are secondary and live in the account summary. -->
        <section class="dashboard-top-area">
          <div class="dashboard-top-primary">
            <div class="dashboard-hero">
              <p class="dashboard-metric-label">Net worth</p>
              <p class="dashboard-hero__value" :class="snapshot.netWorth >= 0 ? 'text-income' : 'text-expense'">
                {{ formatMoney(snapshot.netWorth) }}
              </p>
              <p class="dashboard-hero__hint">
                Assets minus card debt and what you owe. See
                <router-link to="/accounts" class="dashboard-hero__link">all accounts</router-link>.
              </p>
            </div>
            <div class="dashboard-hero">
              <p class="dashboard-metric-label">Available cash</p>
              <p class="dashboard-hero__value">{{ formatMoney(snapshot.availableCash) }}</p>
              <p class="dashboard-hero__hint">Checking, savings and cash on hand.</p>
            </div>
            <div class="dashboard-hero">
              <p class="dashboard-metric-label">
                Card debt<span v-if="snapshot.card.cards"> ({{ snapshot.card.cards }})</span>
              </p>
              <p class="dashboard-hero__value" :class="snapshot.card.used > 0 ? 'text-expense' : ''">
                {{ formatMoney(snapshot.card.used) }}
              </p>
              <p class="dashboard-hero__hint">
                <template v-if="snapshot.card.limit">
                  of {{ formatMoney(snapshot.card.limit) }} limit
                </template>
                <template v-else>No card limit recorded yet.</template>
              </p>
            </div>
          </div>

          <div class="dashboard-top-flow">
            <div>
              <p class="dashboard-metric-label">{{ monthLabel }} income</p>
              <p class="dashboard-flow__value text-income">{{ formatMoney(snapshot.flow.income) }}</p>
            </div>
            <div>
              <p class="dashboard-metric-label">{{ monthLabel }} spending</p>
              <p class="dashboard-flow__value text-expense">{{ formatMoney(snapshot.flow.expense) }}</p>
            </div>
            <div>
              <p class="dashboard-metric-label">Left this month</p>
              <p class="dashboard-flow__value" :class="snapshot.flow.net >= 0 ? 'text-income' : 'text-expense'">
                {{ formatMoney(snapshot.flow.net) }}
              </p>
            </div>
            <div class="dashboard-top-flow__actions">
              <router-link to="/transactions" class="bb-button bb-button-secondary">Transactions</router-link>
            </div>
          </div>
        </section>

        <section class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <article class="dashboard-panel dashboard-budget-panel p-5">
            <div class="dashboard-panel-header compact">
              <div>
                <h2 class="dashboard-section-title">Budget Snapshot</h2>
                <p class="text-sm text-gray-500">Current month progress</p>
              </div>
              <router-link to="/budgets" class="bb-button bb-button-secondary">Manage</router-link>
            </div>
            <div class="budget-snapshot-body">
              <div v-if="budgetSummary.overall" class="budget-overall-summary">
                <div class="budget-widget-row">
                  <div>
                    <p class="text-sm font-semibold text-gray-700">Overall budget</p>
                    <p class="text-xs text-gray-500">{{ budgetSummary.overall.percent_used }}% used</p>
                  </div>
                  <strong :class="budgetSummary.overall.remaining_amount < 0 ? 'text-expense' : 'text-income'">
                    ${{ budgetSummary.overall.remaining_amount.toLocaleString('en-US', { minimumFractionDigits: 2 }) }} left
                  </strong>
                </div>
                <div class="budget-progress-track" aria-hidden="true">
                  <div
                    class="budget-progress-fill"
                    :class="{ warning: budgetSummary.overall.status === 'warning', exceeded: budgetSummary.overall.status === 'exceeded' }"
                    :style="{ width: `${Math.min(Number(budgetSummary.overall.percent_used) || 0, 100)}%` }"
                  ></div>
                </div>
              </div>
              <div v-for="item in budgetSummary.over_budget" :key="item.id" class="budget-widget-row warning">
                <span>{{ item.category || 'Overall' }}</span>
                <strong>{{ item.percent_used }}%</strong>
              </div>
              <div v-if="!budgetSummary.overall && budgetSummary.over_budget.length === 0" class="budget-empty-state">
                <div class="budget-empty-icon">
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M12 8c-2.8 0-5 1.12-5 2.5S9.2 13 12 13s5-1.12 5-2.5S14.8 8 12 8z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                    <path d="M7 10.5v4C7 15.88 9.2 17 12 17s5-1.12 5-2.5v-4" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                    <path d="M7 14.5v2C7 17.88 9.2 19 12 19s5-1.12 5-2.5v-2" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                  </svg>
                </div>
                <div class="budget-empty-copy">
                  <p class="budget-empty-title">No budget set for this month</p>
                  <p class="budget-empty-text">Create an overall or category budget to track monthly spending.</p>
                </div>
                <router-link to="/budgets" class="bb-button bb-button-primary budget-empty-action">Create Budget</router-link>
              </div>
            </div>
          </article>

          <article class="dashboard-panel dashboard-due-panel p-5">
            <div class="dashboard-panel-header compact">
              <div>
                <h2 class="dashboard-section-title">Due Soon</h2>
                <p class="text-sm text-gray-500">Recurring items awaiting confirmation</p>
              </div>
              <router-link to="/recurring" class="bb-button bb-button-secondary">Review</router-link>
            </div>
            <div class="due-soon-body">
              <div v-for="item in dueSoon.slice(0, 3)" :key="item.occurrence_id" class="budget-widget-row">
                <div>
                  <p class="text-sm font-semibold text-gray-700">{{ item.title }}</p>
                  <p class="text-xs text-gray-500">{{ item.due_date }} · {{ item.transaction_type }}</p>
                </div>
                <strong>${{ item.total.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</strong>
              </div>
              <div v-if="dueSoon.length === 0" class="due-empty-state">
                <div class="due-empty-icon">
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M8 7V3m8 4V3M5 11h14" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                    <path d="M6 5h12a2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V7a2 2 0 012-2z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                    <path d="M9 15l2 2 4-5" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                  </svg>
                </div>
                <div class="due-empty-copy">
                  <p class="due-empty-title">No recurring items due</p>
                  <p class="due-empty-text">Upcoming bills, income, and transfers will appear here when they need confirmation.</p>
                </div>
                <router-link to="/recurring" class="bb-button bb-button-primary due-empty-action">Create Recurring</router-link>
              </div>
            </div>
          </article>
        </section>

        <!-- Main Layout -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <!-- Left Column: Accounts and Transactions -->
          <div class="lg:col-span-8 space-y-8">
            <!-- Accounts Section -->
            <section>
              <div class="dashboard-section-header px-1">
                <h2 class="dashboard-section-title">My Accounts</h2>
                <div class="flex items-center gap-2">
                  <router-link to="/accounts" class="bb-button bb-button-secondary">
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                      xmlns="http://www.w3.org/2000/svg">
                      <path d="M4 6h16M4 12h16M4 18h10" stroke-linecap="round" stroke-linejoin="round"
                        stroke-width="2"></path>
                    </svg>
                    View all
                  </router-link>
                  <button class="bb-button bb-button-secondary"
                    @click="openAddAccount">
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                      xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 4v16m8-8H4" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                    </svg>
                    Add Account
                  </button>
                </div>
              </div>
              <div class="custom-scrollbar">
                <AccountSummary ref="accountSummary" :userData="userData" @accountSelected="handleAccountSelected"
                  @allAccountSelected="handleAllAccountSelected" @accountsModified="handleAccountsModified" />
              </div>
            </section>

            <!-- Transaction History Section -->
            <section class="dashboard-panel overflow-hidden">
              <div class="dashboard-panel-header">
                <h2 class="dashboard-section-title">Transaction History</h2>
                <div class="flex items-center gap-3">
                  <div class="bb-input-shell relative">
                    <input v-model="searchQuery"
                      class="bb-input-control with-leading-icon h-11 w-40 md:w-64"
                      placeholder="Search..." type="text" />
                    <svg class="h-4 w-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" fill="none"
                      stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" stroke-linecap="round"
                        stroke-linejoin="round" stroke-width="2"></path>
                    </svg>
                  </div>
                </div>
              </div>
              <div class="p-4">
                <TableData ref="tableData" :transactions="filteredTransactions" :userData="userData"
                  :accounts="accounts" @updateAccounts="handleUpdateAccountsMethod"
                  @updateIncomeExpense="handleUpdateIncomeExpense" />
              </div>
            </section>
          </div>

          <!-- Right Column: Analytics & Widget -->
          <aside class="lg:col-span-4 space-y-8">
            <!-- Spending Analysis Widget -->
            <section class="dashboard-panel dashboard-analysis-panel">
              <div class="dashboard-analysis-header">
                <h2 class="dashboard-section-title">Spending Analysis</h2>
              </div>
              <div class="dashboard-analysis-body">
                <PieChart :transactions="transactions" />
              </div>
            </section>

            <!-- Bank Statement Upload Widget -->
            <section class="dashboard-panel dashboard-upload-panel">
              <div class="dashboard-upload-header">
                <div class="dashboard-widget-header">
                  <div
                    class="w-12 h-12 bg-brand-light rounded-xl flex items-center justify-center text-brand-primary shrink-0">
                    <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                        stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                    </svg>
                  </div>
                  <div>
                    <h3 class="text-base font-semibold text-gray-800">Bank Statement Upload</h3>
                    <p class="text-sm text-gray-500">Automatically detect transactions from your PDF files</p>
                  </div>
                </div>
              </div>
              <div class="dashboard-upload-body">
                <BankStatementUpload :userData="userData" @statementProcessed="handleStatementProcessed"
                  @uploadError="handleUploadError" />
              </div>
            </section>
          </aside>
        </div>

        <!-- Financial Performance Chart -->
        <section class="dashboard-panel financial-performance-panel mt-8 w-full">
          <div class="dashboard-panel-header compact financial-performance-header">
            <div>
              <h2 class="dashboard-section-title">Income and spending</h2>
              <p class="text-sm text-gray-500">Where your money came from and where it went</p>
            </div>
            <v-select v-model="chartPeriod" :items="chartPeriodOptions" density="compact" variant="outlined"
              rounded="lg" hide-details class="chart-period-select financial-period-select shrink-0 text-sm"></v-select>
          </div>
          <Projections :transactions="transactions" :accounts="accounts" />
        </section>
      </div>
    </main>
  </div>
</template>

<script lang="ts">
import AccountSummary from '@/components/AccountSummary.vue'
import TableData from '@/components/TableData.vue'
import PieChart from '@/components/PieChart.vue'
import Projections from '@/components/Projections.vue'
import BankStatementUpload from '@/components/BankStatementUpload.vue'
import AppHeader from '@/components/AppHeader.vue'
import axios, { getAllPages } from '@/services/api'
import { trackBankStatement } from '@/services/bankStatementTracking'
import { dashboardSnapshot } from '@/services/accountGroups'
import type { DashboardSnapshot, FlowTransaction, SnapshotAccount } from '@/services/accountGroups'

interface AccountSummaryRef {
  accountTotalUpdated: () => void;
  openNewAccountModal: () => void;
}

interface Account {
  id: number;
  account_type: string;
  bank: string;
  total: number;
  account_name: string;
}

interface Transaction {
  id: number;
  transaction_type: string;
  category: string;
  date: string;
  title: string;
  total: number;
  owner_id: string;
  account_id: string;
}

interface Data {
  accountSelected: null | Account;
  transactions: Transaction[];
  accounts: Account[];
  searchQuery: string;
  chartPeriod: string;
  chartPeriodOptions: Array<{ title: string; value: string }>;
  budgetSummary: any;
  dueSoon: any[];
  openedReviewBatchId: string | null;
}

export default {
  name: 'MainPage',
  components: {
    AccountSummary,
    TableData,
    PieChart,
    Projections,
    BankStatementUpload,
    AppHeader
  },
  props: {
    userData: {
      type: Object,
      required: true
    }
  },
  data(): Data {
    return {
      accountSelected: null,
      transactions: [],
      accounts: [],
      searchQuery: '',
      chartPeriod: '12',
      chartPeriodOptions: [
        { title: 'Last 12 Months', value: '12' },
        { title: 'Last 6 Months', value: '6' },
        { title: 'Year to Date', value: 'ytd' }
      ],
      budgetSummary: { overall: null, over_budget: [], warnings: [], categories: [] },
      dueSoon: [],
      openedReviewBatchId: null
    }
  },
  computed: {
    /**
     * The top area's numbers. One call into the shared, tested rules so the
     * dashboard can never disagree with the Accounts page about net worth.
     */
    snapshot(): DashboardSnapshot {
      return dashboardSnapshot(
        (this as any).accounts as SnapshotAccount[],
        (this as any).transactions as FlowTransaction[],
      );
    },
    monthLabel(): string {
      return new Date().toLocaleDateString('en-US', { month: 'long' });
    },
    filteredTransactions(): Transaction[] {
      if (!(this as any).searchQuery) {
        return (this as any).transactions;
      }
      const query = (this as any).searchQuery.toLowerCase();
      return (this as any).transactions.filter((t: Transaction) =>
        t.title.toLowerCase().includes(query) ||
        t.category.toLowerCase().includes(query)
      );
    }
  },
  mounted() {
    (this as any).getAccounts();
    (this as any).getTransactions();
    (this as any).getBudgetSummary();
    (this as any).getDueSoon();
  },
  methods: {
    handleUpdateIncomeExpense() {
      (this as any).getTransactions();
    },
    handleUpdateAccountsMethod() {
      ((this as any).$refs.accountSummary as AccountSummaryRef).accountTotalUpdated();
    },
    openAddAccount() {
      ((this as any).$refs.accountSummary as AccountSummaryRef).openNewAccountModal();
    },
    handleAllAccountSelected() {
      (this as any).accountSelected = null;
      (this as any).getTransactions();
    },
    handleAccountSelected(acc: Account) {
      (this as any).accountSelected = acc;
      (this as any).getTransactions();
    },
    handleAccountsModified(accs: Array<Account>) {
      (this as any).accounts = accs;
    },
    formatMoney(value: number): string {
      const amount = Number(value || 0);
      return `${amount < 0 ? '-' : ''}$${Math.abs(amount).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`;
    },
    getTransactions() {
      const accountId = (this as any).accountSelected === null
        ? '0'
        : (this as any).accountSelected.id;
      getAllPages<Transaction>(
        `/transactions/retrieve/${(this as any).userData.user.username}/${accountId}/0/0`,
        (data) => data.results,
      )
        .then((transactions) => {
          (this as any).transactions = transactions;
        })
        .catch((error) => {
          console.log('ERROR', error);
        });
      // Also fetch accounts
      (this as any).getAccounts();
    },
    getAccounts() {
      axios.get(`/accounts/details/${(this as any).userData.user.username}/0`)
        .then((response) => {
          (this as any).accounts = response.data;
          (this as any).redirectLegacyReviewLink();
        })
        .catch((error) => {
          console.log('ERROR fetching accounts:', error);
        });
    },
    redirectLegacyReviewLink() {
      const reviewBatch = (this as any).$route?.query?.reviewBatch;
      if (!reviewBatch || (this as any).openedReviewBatchId === reviewBatch) return;
      (this as any).openedReviewBatchId = reviewBatch;
      (this as any).$router.push({ path: `/statements/${reviewBatch}/review` });
    },
    getBudgetSummary() {
      const month = new Date().toISOString().slice(0, 7);
      axios.get('/budgets/summary/', { params: { month } })
        .then((response) => {
          (this as any).budgetSummary = response.data;
        })
        .catch((error) => console.log('ERROR fetching budget summary:', error));
    },
    getDueSoon() {
      const through = new Date();
      through.setDate(through.getDate() + 3);
      axios.get('/recurring-transactions/due/', { params: { through: through.toISOString().slice(0, 10) } })
        .then((response) => {
          (this as any).dueSoon = (response.data || []).filter((item: any) => item.status === 'due');
        })
        .catch((error) => console.log('ERROR fetching due recurring transactions:', error));
    },
    handleStatementProcessed(bankStatementData: any) {
      if (bankStatementData.status === 'uploaded') {
        trackBankStatement({
          id: bankStatementData.file_details.id,
          filename: bankStatementData.file_details.filename,
        });
      } else if (bankStatementData.review_batch_id) {
        (this as any).$router.push({ path: `/statements/${bankStatementData.review_batch_id}/review` });
      }
    },
    handleUploadError(errorMessage: string) {
      console.error('Upload error:', errorMessage);
      alert(`Upload Error: ${errorMessage}`);
    }
  }
}
</script>

<style scoped>
.dashboard-panel {
  background: var(--bb-surface, #ffffff);
  border: 1px solid var(--bb-border-soft, #f3f4f6);
  border-radius: 1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
}

/* Decision-first top area. Net worth and cash lead; the month flow sits
   beside them. Investments deliberately have no card here — the account
   summary below carries them, so the top stays scannable. */
.dashboard-top-area {
  align-items: stretch;
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 1fr);
  margin-bottom: 2rem;
}

@media (min-width: 1024px) {
  .dashboard-top-area {
    grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  }
}

.dashboard-top-primary {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.dashboard-hero {
  background: var(--bb-surface, #ffffff);
  border: 1px solid var(--bb-border-soft, #f3f4f6);
  border-radius: 1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 7rem;
  padding: 1.25rem;
}

.dashboard-hero__value {
  font-size: 1.875rem;
  font-weight: 700;
  line-height: 1.2;
  margin: 0.25rem 0 0;
}

.dashboard-hero__hint {
  color: var(--bb-text-muted, #6b7280);
  font-size: 0.8125rem;
  margin: 0.375rem 0 0;
}

.dashboard-hero__link {
  color: #16a34a;
  font-weight: 600;
  text-decoration: none;
}

.dashboard-hero__link:hover {
  text-decoration: underline;
}

.dashboard-top-flow {
  align-items: center;
  background: var(--bb-surface, #ffffff);
  border: 1px solid var(--bb-border-soft, #f3f4f6);
  border-radius: 1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  padding: 1.25rem;
}

.dashboard-flow__value {
  font-size: 1.375rem;
  font-weight: 700;
  line-height: 1.2;
  margin: 0.25rem 0 0;
}

.dashboard-top-flow__actions {
  align-items: center;
  display: flex;
}

@media (max-width: 640px) {
  .dashboard-hero,
  .dashboard-top-flow {
    padding: 1rem;
  }

  .dashboard-top-flow__actions {
    grid-column: 1 / -1;
  }
}
.dashboard-budget-panel {
  min-height: 12rem;
  padding: 1.5rem !important;
}

.dashboard-due-panel {
  min-height: 12rem;
  padding: 1.5rem !important;
}

.dashboard-budget-panel .dashboard-panel-header.compact,
.dashboard-due-panel .dashboard-panel-header.compact {
  margin-bottom: 1.25rem;
  padding: 0.25rem 0.25rem 0;
}

.budget-snapshot-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 0.25rem;
}

.due-soon-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 0.25rem;
}

.budget-overall-summary {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.budget-widget-row {
  align-items: center;
  border-top: 1px solid var(--bb-border-soft, #f3f4f6);
  display: flex;
  gap: 1rem;
  justify-content: space-between;
  padding: 0.85rem 0;
}

.budget-widget-row:first-of-type {
  border-top: 0;
}

.budget-widget-row.warning {
  color: #ef4444;
}

.budget-progress-track {
  background: #e5e7eb;
  border-radius: 9999px;
  height: 0.55rem;
  overflow: hidden;
}

.budget-progress-fill {
  background: #10b981;
  border-radius: inherit;
  height: 100%;
  min-width: 0.35rem;
}

.budget-progress-fill.warning {
  background: #f59e0b;
}

.budget-progress-fill.exceeded {
  background: #ef4444;
}

.budget-empty-state {
  align-items: center;
  background: linear-gradient(135deg, rgba(232, 245, 233, 0.92), rgba(240, 253, 244, 0.56));
  border: 1px solid rgba(76, 175, 80, 0.24);
  border-radius: 0.875rem;
  display: grid;
  gap: 1.25rem;
  grid-template-columns: auto minmax(0, 1fr) auto;
  min-height: 7rem;
  padding: 1.25rem;
}

.budget-empty-icon {
  align-items: center;
  background: var(--bb-surface, #ffffff);
  border: 1px solid rgba(76, 175, 80, 0.24);
  border-radius: 0.75rem;
  color: #2e7d32;
  display: flex;
  height: 2.75rem;
  justify-content: center;
  width: 2.75rem;
}

.budget-empty-title {
  color: var(--bb-text-strong, #1f2937);
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1.25rem;
  margin: 0 0 0.2rem;
}

.budget-empty-text {
  color: var(--bb-text-muted, #6b7280);
  font-size: 0.875rem;
  line-height: 1.35rem;
  margin: 0;
}

.budget-empty-action {
  justify-self: end;
}

.due-empty-state {
  align-items: center;
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.94), rgba(219, 234, 254, 0.58));
  border: 1px solid rgba(59, 130, 246, 0.22);
  border-radius: 0.875rem;
  display: grid;
  gap: 1.25rem;
  grid-template-columns: auto minmax(0, 1fr) auto;
  min-height: 7rem;
  padding: 1.25rem;
}

.due-empty-icon {
  align-items: center;
  background: var(--bb-surface, #ffffff);
  border: 1px solid rgba(59, 130, 246, 0.22);
  border-radius: 0.75rem;
  color: #2563eb;
  display: flex;
  height: 2.75rem;
  justify-content: center;
  width: 2.75rem;
}

.due-empty-title {
  color: var(--bb-text-strong, #1f2937);
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1.25rem;
  margin: 0 0 0.2rem;
}

.due-empty-text {
  color: var(--bb-text-muted, #6b7280);
  font-size: 0.875rem;
  line-height: 1.35rem;
  margin: 0;
}

.due-empty-action {
  justify-self: end;
}

.dashboard-section-header,
.dashboard-panel-header,
.dashboard-widget-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.dashboard-panel-header {
  flex-wrap: wrap;
  border-bottom: 1px solid var(--bb-border-soft, #f3f4f6);
  margin-bottom: 0;
  padding: 1.5rem;
}

.dashboard-panel-header.compact {
  border-bottom: 0;
  margin-bottom: 1.5rem;
  padding: 0;
}

.dashboard-widget-header {
  justify-content: flex-start;
  margin-bottom: 1.5rem;
}

.dashboard-analysis-panel {
  padding: 1rem;
}

.dashboard-analysis-header {
  padding: 0.5rem 0.5rem 1rem;
}

.dashboard-analysis-body {
  padding: 0.25rem;
}

.dashboard-analysis-body :deep(.chart-container) {
  gap: 1rem;
}

.dashboard-analysis-body :deep(.chart-section) {
  flex: 1 1 0;
  min-width: 0;
}

.dashboard-upload-panel {
  border-color: #dcfce7;
  margin-top: 1rem;
  padding: 1rem;
}

.dashboard-upload-header {
  padding: 0.5rem 0.5rem 1rem;
}

.dashboard-upload-header .dashboard-widget-header {
  margin-bottom: 0;
}

.dashboard-upload-body {
  background: var(--bb-surface-soft, #f9fafb);
  border: 1px solid var(--bb-border-soft, #f3f4f6);
  border-radius: 0.875rem;
  padding: 0.75rem;
}

.financial-performance-panel {
  padding: 1.5rem;
}

.dashboard-panel-header.compact.financial-performance-header {
  align-items: flex-start;
  gap: 1.5rem;
  padding: 0.25rem 0.25rem 1.25rem;
}

.financial-period-select {
  margin-top: 0.125rem;
}

.financial-period-select :deep(.v-field) {
  background: var(--bb-surface, #ffffff);
  border-radius: 0.75rem;
  min-height: 2.75rem;
}

.financial-period-select :deep(.v-field__input) {
  font-size: 0.875rem;
  font-weight: 600;
  min-height: 2.75rem;
  padding-bottom: 0;
  padding-left: 1rem;
  padding-top: 0;
}

.financial-period-select :deep(.v-field__append-inner) {
  padding-top: 0.625rem;
}

@media (min-width: 1024px) {
  .dashboard-analysis-panel {
    padding: 1.25rem;
  }

  .dashboard-analysis-header {
    padding: 0.75rem 0.75rem 1.25rem;
  }

  .dashboard-analysis-body {
    padding: 0.25rem;
  }

  .dashboard-upload-panel {
    margin-top: 1.5rem;
    padding: 1.25rem;
  }

  .dashboard-upload-header {
    padding: 0.75rem 0.75rem 1.25rem;
  }

  .dashboard-upload-body {
    padding: 1rem;
  }

  .financial-performance-panel {
    padding: 2rem;
  }

  .dashboard-panel-header.compact.financial-performance-header {
    padding: 0.25rem 0.5rem 1.5rem;
  }
}

.dashboard-section-title {
  color: var(--bb-text-strong, #1f2937);
  font-size: 1.125rem;
  font-weight: 600;
  line-height: 1.5rem;
  margin: 0;
}

.dashboard-metric-label {
  color: var(--bb-text-muted, #6b7280);
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.25rem;
  margin-bottom: 0.5rem;
}

.chart-period-select {
  width: fit-content;
  max-width: 180px;
}

.chart-period-select :deep(.v-field) {
  min-width: 0;
}

@media (max-width: 640px) {
  .dashboard-analysis-body :deep(.chart-container) {
    flex-direction: column;
  }

  .dashboard-analysis-body :deep(.chart-section) {
    min-width: 100%;
  }

  .financial-period-select {
    margin-top: 0;
    max-width: none;
    width: 100%;
  }


  .budget-empty-state {
    align-items: flex-start;
    grid-template-columns: auto minmax(0, 1fr);
  }

  .budget-empty-action {
    grid-column: 1 / -1;
    justify-self: stretch;
    width: 100%;
  }

  .due-empty-state {
    align-items: flex-start;
    grid-template-columns: auto minmax(0, 1fr);
  }

  .due-empty-action {
    grid-column: 1 / -1;
    justify-self: stretch;
    width: 100%;
  }
}
</style>

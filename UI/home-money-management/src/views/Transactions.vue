<template>
  <div class="bg-gray-50 text-gray-900 font-sans antialiased min-h-screen">
    <AppHeader :userData="userData">
      <template #brand-extra>
        <label class="hidden md:flex flex-col min-w-40 max-w-64 h-10">
          <div class="bb-input-shell w-full flex-1 h-full">
            <span class="text-gray-400 flex items-center justify-center pl-4">
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </span>
            <input v-model="searchQuery" type="text"
              class="bb-input-control flex w-full min-w-0 flex-1 resize-none overflow-hidden px-4 pl-2"
              placeholder="Search transactions..." />
          </div>
        </label>
      </template>
      <template #actions>
        <button class="transactions-header-export bb-button bb-button-primary min-w-[100px]"
          @click="exportTransactions">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
          </svg>
          <span>Export</span>
        </button>
      </template>
    </AppHeader>

    <main class="w-full">
      <div class="px-4 sm:px-6 py-6">
        <!-- Page Title -->
        <div class="flex flex-col gap-1 mb-6">
          <h1 class="text-gray-900 text-3xl font-bold tracking-tight">Transactions</h1>
          <p class="text-gray-500 text-base">Keep track of your spending and earnings across all connected accounts.</p>
          <button class="transactions-phone-export bb-button bb-button-primary"
            @click="exportTransactions">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
            </svg>
            <span>Export</span>
          </button>
        </div>

        <!-- Filter Ribbon -->
        <div class="transactions-filter-panel mb-6">
          <div class="filter-heading">
            <span class="filter-heading-icon">
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"></path>
              </svg>
            </span>
            <span class="text-sm font-semibold uppercase tracking-wider">Filters</span>
          </div>
          <div class="filter-controls">
            <v-select v-model="filterAccount" :items="accountFilterOptions" item-title="title" item-value="value"
              density="compact" variant="outlined" rounded="lg" hide-details class="filter-select"
              placeholder="All Accounts"></v-select>
            <v-select v-model="filterCategory" :items="categoryFilterOptions" item-title="title" item-value="value"
              density="compact" variant="outlined" rounded="lg" hide-details class="filter-select"
              placeholder="All Categories"></v-select>
            <v-select v-model="filterPeriod" :items="periodOptions" item-title="title" item-value="value"
              density="compact" variant="outlined" rounded="lg" hide-details class="filter-select"></v-select>
          </div>
          <button class="bb-button bb-button-secondary filter-reset-button" @click="resetFilters">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            <span>Reset Filters</span>
          </button>
        </div>

        <!-- Transactions Table -->
        <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden mb-6">
          <div class="bb-phone-table-scroll overflow-x-auto">
            <table class="bb-phone-min-table w-full text-left border-collapse">
              <thead>
                <tr class="bg-gray-50 border-b border-gray-100">
                  <th
                    class="px-6 py-4 text-gray-500 text-xs font-bold uppercase tracking-widest cursor-pointer hover:text-brand-primary"
                    @click="sortBy = sortBy === 'date' ? '-date' : 'date'">Date</th>
                  <th
                    class="px-6 py-4 text-gray-500 text-xs font-bold uppercase tracking-widest cursor-pointer hover:text-brand-primary"
                    @click="sortBy = sortBy === 'title' ? '-title' : 'title'">Description</th>
                  <th class="px-6 py-4 text-gray-500 text-xs font-bold uppercase tracking-widest">Category</th>
                  <th class="px-6 py-4 text-gray-500 text-xs font-bold uppercase tracking-widest">Account</th>
                  <th
                    class="px-6 py-4 text-right text-gray-500 text-xs font-bold uppercase tracking-widest cursor-pointer hover:text-brand-primary"
                    @click="sortBy = sortBy === 'total' ? '-total' : 'total'">Amount</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="t in paginatedTransactions" :key="t.id"
                  class="hover:bg-gray-50 transition-colors">
                  <td class="px-6 py-5 text-sm text-gray-500">{{ formatDate(t.date) }}</td>
                  <td class="px-6 py-5">
                    <div class="flex items-center gap-3">
                      <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                        :style="{ backgroundColor: getCategoryStyle(t.category).color + '20' }">
                        <v-icon :icon="getCategoryStyle(t.category).icon" size="18"
                          :style="{ color: getCategoryStyle(t.category).color }"></v-icon>
                      </div>
                      <span class="font-semibold text-gray-900">{{ t.title }}</span>
                    </div>
                  </td>
                  <td class="px-6 py-5">
                    <span class="px-3 py-1 rounded-full text-xs font-bold"
                      :style="{ backgroundColor: getCategoryStyle(t.category).color + '20', color: getCategoryStyle(t.category).color }">
                      {{ t.category }}
                    </span>
                  </td>
                  <td class="px-6 py-5 text-sm text-gray-500 italic">{{ getAccountName(t) }}</td>
                  <td class="px-6 py-5 text-right font-bold"
                    :class="t.transaction_type === 'Income' ? 'text-income' : t.transaction_type === 'Expense' ? 'text-expense' : 'text-gray-700'">
                    {{ t.transaction_type === 'Income' ? '+' : t.transaction_type === 'Expense' ? '-' : '' }}${{ Math.abs(t.total).toLocaleString('en-US', { minimumFractionDigits: 2 }) }}
                  </td>
                </tr>
                <tr v-if="paginatedTransactions.length === 0">
                  <td colspan="5" class="px-6 py-12 text-center text-gray-500">No transactions found</td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- Pagination -->
          <div
            class="flex flex-col sm:flex-row items-center justify-between px-6 py-4 bg-gray-50 border-t border-gray-100 gap-4">
            <div class="text-sm text-gray-500">
              Showing <span class="font-bold text-gray-900">{{ pageStart }}</span> to
              <span class="font-bold text-gray-900">{{ pageEnd }}</span> of
              <span class="font-bold text-gray-900">{{ filteredTransactions.length }}</span> results
            </div>
            <div class="flex items-center gap-2">
              <button
                class="bb-page-button disabled:opacity-50"
                :disabled="currentPage === 1" @click="currentPage = Math.max(1, currentPage - 1)">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
                </svg>
              </button>
              <button v-for="p in visiblePages" :key="p"
                class="bb-page-button"
                :class="p === currentPage ? 'active' : ''"
                @click="currentPage = p">{{ p }}</button>
              <button
                class="bb-page-button disabled:opacity-50"
                :disabled="currentPage >= totalPages" @click="currentPage = Math.min(totalPages, currentPage + 1)">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Totals Footer -->
        <section class="transactions-total-footer" aria-label="Transaction totals">
          <article class="transactions-total-card">
            <div class="transactions-total-card-header">
              <span class="transactions-total-icon expense">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M17 13l-5 5m0 0l-5-5m5 5V6"></path>
                </svg>
              </span>
              <div>
                <p class="transactions-total-label">Expenses this period</p>
                <p class="transactions-total-meta">Last {{ filterPeriod }} days</p>
              </div>
            </div>
            <p class="transactions-total-value">${{ filteredExpenseTotal.toLocaleString('en-US', {
              minimumFractionDigits: 2
            }) }}</p>
          </article>

          <article class="transactions-total-card">
            <div class="transactions-total-card-header">
              <span class="transactions-total-icon income">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M7 11l5-5m0 0l5 5m-5-5v12"></path>
                </svg>
              </span>
              <div>
                <p class="transactions-total-label">Income this period</p>
                <p class="transactions-total-meta">Last {{ filterPeriod }} days</p>
              </div>
            </div>
            <p class="transactions-total-value">${{ filteredIncomeTotal.toLocaleString('en-US', {
              minimumFractionDigits: 2
            }) }}</p>
          </article>

          <article class="transactions-total-card">
            <div class="transactions-total-card-header">
              <span class="transactions-total-icon net">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
              </span>
              <div>
                <p class="transactions-total-label">Net savings</p>
                <p class="transactions-total-meta">Income minus expenses</p>
              </div>
            </div>
            <p class="transactions-total-value net" :class="filteredNet < 0 ? 'negative' : ''">
              {{ filteredNet >= 0 ? '+' : '' }}${{ filteredNet.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}
            </p>
          </article>
        </section>
      </div>
    </main>
  </div>
</template>

<script lang="ts" src="./Transactions.script.ts"></script>

<style scoped>
.transactions-filter-panel {
  align-items: center;
  background: #ffffff;
  border: 1px solid #f3f4f6;
  border-radius: 1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 1rem 1.25rem;
}

.filter-heading {
  align-items: center;
  color: #6b7280;
  display: flex;
  flex: 0 0 auto;
  gap: 0.75rem;
  min-height: 2.75rem;
}

.filter-heading-icon {
  align-items: center;
  background: #f0fdf4;
  border-radius: 0.75rem;
  color: #4CAF50;
  display: flex;
  height: 2.5rem;
  justify-content: center;
  width: 2.5rem;
}

.filter-controls {
  align-items: center;
  display: flex;
  flex: 1 1 auto;
  flex-wrap: wrap;
  gap: 0.75rem;
  min-width: min(100%, 28rem);
}

.filter-select {
  flex: 1 1 11rem;
  max-width: 14rem;
  min-width: 11rem;
}

.filter-reset-button {
  background: #ffffff;
  border: 1px solid rgba(76, 175, 80, 0.35);
  border-radius: 0.75rem;
  color: #2E7D32;
  flex: 0 0 auto;
}

.filter-reset-button:hover {
  background: #f0fdf4;
  border-color: #4CAF50;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
}

:deep(.filter-select .v-field) {
  background: #f9fafb;
  border-radius: 0.75rem;
  color: #374151;
  min-height: 2.5rem;
}

:deep(.filter-select .v-field__outline) {
  color: #e5e7eb;
}

:deep(.filter-select .v-field--focused .v-field__outline) {
  color: #4CAF50;
}

:deep(.filter-select .v-field__input) {
  font-size: 0.875rem;
  font-weight: 600;
  min-height: 2.5rem;
  padding-bottom: 0;
  padding-top: 0;
}

.transactions-total-footer {
  background: #ffffff;
  border: 1px solid #f3f4f6;
  border-radius: 1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding: 0.75rem;
}

.transactions-total-card {
  background: #f9fafb;
  border: 1px solid #f3f4f6;
  border-radius: 0.875rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  justify-content: space-between;
  min-width: 0;
  padding: 1rem;
}

.transactions-total-card-header {
  align-items: center;
  display: flex;
  gap: 0.75rem;
  min-width: 0;
}

.transactions-total-icon {
  align-items: center;
  border-radius: 0.75rem;
  display: flex;
  flex: 0 0 auto;
  height: 2.5rem;
  justify-content: center;
  width: 2.5rem;
}

.transactions-total-icon.expense {
  background: #fef2f2;
  color: #ef4444;
}

.transactions-total-icon.income {
  background: #f0fdf4;
  color: #22c55e;
}

.transactions-total-icon.net {
  background: #eff6ff;
  color: #3b82f6;
}

.transactions-total-label {
  color: #374151;
  font-size: 0.875rem;
  font-weight: 700;
  line-height: 1.25rem;
  margin: 0;
}

.transactions-total-meta {
  color: #9ca3af;
  font-size: 0.75rem;
  font-weight: 500;
  line-height: 1rem;
  margin: 0.125rem 0 0;
}

.transactions-total-value {
  color: #111827;
  font-size: 1.75rem;
  font-weight: 800;
  line-height: 1;
  margin: 0;
  overflow-wrap: anywhere;
}

.transactions-total-value.net {
  color: #2563eb;
}

.transactions-total-value.net.negative {
  color: #dc2626;
}

@media (max-width: 900px) {
  .transactions-total-footer {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .transactions-filter-panel,
  .filter-controls,
  .filter-reset-button {
    align-items: stretch;
    width: 100%;
  }

  .filter-heading {
    width: 100%;
  }

  .filter-select {
    max-width: none;
    min-width: 100%;
  }

  .transactions-total-value {
    font-size: 1.5rem;
  }
}
</style>

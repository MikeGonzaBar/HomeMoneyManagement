<template>
  <div class="bg-gray-50 text-gray-900 font-sans antialiased min-h-screen flex flex-col">
    <!-- Header -->
    <header class="bg-white/95 backdrop-blur border-b border-gray-200 sticky top-0 z-50">
      <div class="w-full px-4 sm:px-6 lg:px-10">
        <div class="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-6 h-[72px]">
          <router-link to="/" class="flex items-center gap-3 min-w-0">
            <img src="@/assets/logo-192.png" alt="Budget Buddy" class="w-10 h-10 rounded-lg object-contain" />
            <h2 class="text-xl font-bold tracking-tight text-gray-900 whitespace-nowrap">Budget Buddy</h2>
          </router-link>
          <nav class="hidden md:flex items-center gap-1 rounded-full border border-gray-100 bg-gray-50 p-1 shadow-sm">
            <router-link to="/" class="rounded-full px-4 py-2 text-sm font-medium text-gray-500 transition-colors hover:bg-white hover:text-gray-700">
            Dashboard
          </router-link>
            <router-link to="/transactions" class="rounded-full px-4 py-2 text-sm font-medium text-gray-500 transition-colors hover:bg-white hover:text-gray-700">
            Transactions
          </router-link>
            <router-link to="/budgets" class="rounded-full px-4 py-2 text-sm font-medium text-gray-500 transition-colors hover:bg-white hover:text-gray-700">
            Budgets
          </router-link>
            <router-link to="/recurring" class="rounded-full px-4 py-2 text-sm font-medium text-gray-500 transition-colors hover:bg-white hover:text-gray-700">
            Recurring
          </router-link>
            <router-link to="/reports" class="rounded-full bg-white px-4 py-2 text-sm font-semibold text-brand-primary shadow-sm">
            Reports
          </router-link>
          </nav>
          <div class="flex items-center justify-end gap-3 min-w-0">
            <AlertCenter />
            <ThemeToggle />
            <div class="flex items-center gap-3 rounded-full border border-gray-100 bg-gray-50 py-1 pl-4 pr-1.5">
              <div class="text-right hidden sm:block">
                <p class="text-sm font-semibold text-gray-900 leading-none">{{ userData.user?.first_name }} {{ userData.user?.last_name }}</p>
                <p class="text-xs text-gray-500 mt-1">Premium Member</p>
              </div>
              <div
                class="h-9 w-9 rounded-full bg-brand-primary flex items-center justify-center text-white font-semibold cursor-pointer shadow-sm"
                @click="goToProfile">
                {{ userData.user?.first_name?.charAt(0) }}{{ userData.user?.last_name?.charAt(0) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <main class="reports-main flex-1 w-full max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-10">
      <!-- Page Heading & Controls -->
      <div class="reports-page-header">
        <div class="min-w-0">
          <h1 class="text-3xl font-black tracking-tight mb-2 text-gray-900">Financial Analytics</h1>
          <p class="text-gray-500">Comprehensive overview of your financial health and performance trends.</p>
        </div>
        <div class="reports-controls">
          <v-menu v-model="showDateMenu" :close-on-content-click="false" location="bottom" offset="8">
            <template v-slot:activator="{ props }">
              <div
                v-bind="props"
                class="bb-button bb-button-muted">
                <svg class="h-5 w-5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                </svg>
                <span class="text-sm font-bold">{{ dateRangeLabel }}</span>
                <svg class="h-5 w-5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
              </div>
            </template>
            <v-card min-width="320" class="pa-4" rounded="xl">
              <p class="text-sm font-semibold text-gray-700 mb-3">Select date range</p>
              <div class="flex flex-col gap-3 mb-4">
                <v-text-field v-model="dateStart" label="Start date" type="date" variant="outlined" density="compact"
                  hide-details class="date-field"></v-text-field>
                <v-text-field v-model="dateEnd" label="End date" type="date" variant="outlined" density="compact"
                  hide-details class="date-field"></v-text-field>
              </div>
              <div class="flex justify-end gap-2">
                <v-btn variant="outlined" size="small" @click="showDateMenu = false">Cancel</v-btn>
                <v-btn color="primary" size="small" @click="applyDateRange">Apply</v-btn>
              </div>
            </v-card>
          </v-menu>
          <button
            class="bb-button bb-button-primary"
            @click="exportReport">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
            </svg>
            Export
          </button>
        </div>
      </div>

      <!-- KPI Cards -->
      <div v-if="kpiCards.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 lg:gap-6 mb-8">
        <div
          v-for="kpi in kpiCards"
          :key="kpi.key"
          class="reports-card reports-kpi-card">
          <div class="flex items-center justify-between mb-4">
            <span class="text-sm font-medium text-gray-500">{{ kpi.label }}</span>
            <span
              class="text-xs font-bold px-2 py-1 rounded-full"
              :class="kpi.pct >= 0 ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'">
              {{ kpi.pct >= 0 ? '+' : '' }}{{ kpi.pct }}%
            </span>
          </div>
          <div class="text-3xl font-black mb-1 text-gray-900">{{ kpi.display }}</div>
          <div class="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
            <div class="h-full rounded-full transition-all" :class="kpi.barClass" :style="{ width: kpi.barWidth }"></div>
          </div>
        </div>
      </div>

      <!-- Main Grid -->
      <div class="reports-main-grid">
        <div class="reports-card reports-chart-card lg:col-span-3">
          <div class="reports-card-header">
            <div>
              <h3 class="text-lg font-bold text-gray-900">Cashflow Forecast</h3>
              <p class="text-sm text-gray-500">Next {{ forecast?.months || 6 }} months using recurring items, budgets, and history</p>
            </div>
          </div>
          <div class="forecast-strip">
            <article v-for="month in forecastMonths" :key="month.month" class="forecast-month">
              <p class="forecast-label">{{ month.month }}</p>
              <p class="forecast-net" :class="month.expected_net < 0 ? 'negative' : ''">
                {{ month.expected_net >= 0 ? '+' : '' }}${{ month.expected_net.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}
              </p>
              <p class="forecast-meta">In ${{ month.expected_income.toLocaleString('en-US', { maximumFractionDigits: 0 }) }} · Out ${{ month.expected_expenses.toLocaleString('en-US', { maximumFractionDigits: 0 }) }}</p>
            </article>
          </div>
        </div>

        <!-- Income vs Expenses Bar Chart -->
        <div class="reports-card reports-chart-card lg:col-span-2">
          <div class="reports-card-header">
            <div>
              <h3 class="text-lg font-bold text-gray-900">Monthly Income vs. Expenses</h3>
              <p class="text-sm text-gray-500">Overview of the last 6 months</p>
            </div>
            <div class="flex items-center gap-4 text-xs font-bold">
              <div class="flex items-center gap-1.5">
                <span class="w-3 h-3 rounded-full bg-brand-primary"></span>
                <span>Income</span>
              </div>
              <div class="flex items-center gap-1.5">
                <span class="w-3 h-3 rounded-full bg-gray-300"></span>
                <span>Expenses</span>
              </div>
            </div>
          </div>
          <div class="reports-bar-chart">
            <div
              v-for="m in monthlyData"
              :key="m.month"
              class="flex-1 flex flex-col items-center gap-2 h-full justify-end group">
              <div class="relative w-full flex justify-center gap-1 h-full items-end">
                <div
                  class="w-4 bg-gray-300 rounded-t-sm transition-all group-hover:opacity-80"
                  :style="{ height: barHeight(m.expense) }"></div>
                <div
                  class="w-4 bg-brand-primary rounded-t-sm transition-all group-hover:brightness-110"
                  :style="{ height: barHeight(m.income) }"></div>
              </div>
              <span class="text-xs font-medium text-gray-400">{{ m.label }}</span>
            </div>
          </div>
        </div>

        <!-- Net Worth Growth -->
        <div class="reports-card reports-chart-card">
          <div class="mb-6">
            <h3 class="text-lg font-bold text-gray-900">Net Worth Growth</h3>
            <p class="text-sm text-gray-500">Cumulative performance</p>
          </div>
          <div class="mb-8">
            <div class="text-4xl font-black text-brand-primary">${{ netWorth.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) }}</div>
            <p class="text-xs font-medium mt-1 flex items-center gap-1"
              :class="netWorthChange >= 0 ? 'text-green-500' : 'text-red-500'">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  :d="netWorthChange >= 0 ? 'M7 11l5-5m0 0l5 5m-5-5v12' : 'M7 13l5 5m0 0l5-5m-5 5V6'"></path>
              </svg>
              {{ netWorthChange >= 0 ? '+' : '' }}${{ Math.abs(netWorthChange).toLocaleString('en-US', { minimumFractionDigits: 0 }) }} this period
            </p>
          </div>
          <div class="reports-net-worth-chart">
            <svg class="w-full h-full" viewBox="0 0 100 40" preserveAspectRatio="none">
              <path :d="netWorthAreaPath" fill="currentColor" class="text-brand-primary/20"></path>
              <path :d="netWorthPath" fill="none" stroke="currentColor" stroke-width="2" class="text-brand-primary"></path>
            </svg>
          </div>
        </div>

        <!-- Spending by Category Over Time -->
        <div class="reports-card reports-chart-card lg:col-span-3">
          <div class="reports-card-header">
            <div>
              <h3 class="text-lg font-bold text-gray-900">Spending by Category Over Time</h3>
              <p class="text-sm text-gray-500">Variable costs trend analysis</p>
            </div>
            <div class="flex flex-wrap items-center gap-4 text-xs font-bold">
              <div v-for="c in categoryLegend" :key="c" class="flex items-center gap-1.5">
                <span class="w-2.5 h-2.5 rounded-full reports-legend-dot" :style="{ backgroundColor: getReportCategoryColor(c) }"></span>
                <span class="reports-legend-text">{{ c }}</span>
              </div>
            </div>
          </div>
          <div class="reports-stacked-chart">
            <div class="flex-1 flex items-end gap-1 px-2 pt-2">
              <div
                v-for="m in spendingByCategory"
                :key="m.month"
                class="flex-1 flex flex-col justify-end min-h-0"
                :title="m.label">
                <div
                  v-for="(amt, cat) in m.categories"
                  :key="cat"
                  class="w-full min-h-[2px] rounded-t transition-all hover:opacity-90 reports-stacked-segment"
                  :style="{ height: categoryBarHeight(m, cat), backgroundColor: getReportCategoryColor(cat) }"></div>
              </div>
            </div>
            <div class="flex px-2 pb-1 gap-1">
              <span v-for="m in spendingByCategory" :key="m.month" class="flex-1 reports-chart-month-label text-center">{{ m.label }}</span>
            </div>
          </div>
        </div>

        <!-- Top Categories -->
        <div class="reports-card lg:col-span-1">
          <h3 class="text-lg font-bold text-gray-900 mb-6">Top Categories</h3>
          <div class="space-y-5">
            <div v-for="(tc, i) in topCategories" :key="tc.category" class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="font-medium text-gray-900">{{ tc.category }}</span>
                <span class="font-bold text-gray-900">${{ tc.amount.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</span>
              </div>
              <div class="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all"
                  :style="{ width: topCategoryWidth(tc), backgroundColor: getReportCategoryColor(tc.category) }"></div>
              </div>
            </div>
            <p v-if="topCategories.length === 0" class="text-sm text-gray-500">No expense data for this period.</p>
          </div>
          <button
            class="bb-button bb-button-secondary w-full mt-8"
            @click="$router.push('/')">
            View Category Breakdown
          </button>
        </div>

        <!-- Smart Insights -->
        <div class="reports-card reports-insights-card lg:col-span-2">
          <div class="flex-shrink-0 w-32 h-32 bg-brand-primary rounded-full flex items-center justify-center text-white shadow-xl">
            <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
            </svg>
          </div>
          <div class="flex-1">
            <h4 class="text-xl font-black text-gray-900 mb-2">Smart Insights</h4>
            <p class="text-gray-600 text-sm leading-relaxed mb-4">
              {{ smartInsights.message }}
            </p>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="tag in smartInsights.tags"
                :key="tag"
                class="px-3 py-1 bg-white rounded-lg text-xs font-bold border border-gray-200">
                {{ tag }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <footer class="mt-auto border-t border-gray-200 py-8 px-6 bg-white">
      <div class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
        <div class="flex items-center gap-2 opacity-50">
          <img src="@/assets/logo-192.png" alt="" class="w-5 h-5 rounded object-contain" />
          <span class="text-sm font-bold">Budget Buddy © {{ new Date().getFullYear() }}</span>
        </div>
        <div class="flex gap-8 text-sm font-medium text-gray-500">
          <a href="#" class="hover:text-brand-primary transition-colors">Privacy Policy</a>
          <a href="#" class="hover:text-brand-primary transition-colors">Terms of Service</a>
          <a href="#" class="hover:text-brand-primary transition-colors">Help Center</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<script lang="ts" src="./Reports.script.ts"></script>

<style scoped>
.reports-main {
  display: flex;
  flex-direction: column;
}

.reports-page-header {
  align-items: flex-start;
  display: flex;
  gap: 1.5rem;
  justify-content: space-between;
  margin-bottom: 2rem;
}

.reports-controls {
  align-items: center;
  display: flex;
  flex: 0 0 auto;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: flex-end;
}

.reports-main-grid {
  display: grid;
  gap: 2rem;
  grid-template-columns: minmax(0, 1fr);
}

.forecast-strip {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
}

.forecast-month {
  background: var(--bb-surface-soft, #f9fafb);
  border: 1px solid var(--bb-border-soft, #f3f4f6);
  border-radius: 0.75rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  padding: 1rem;
  position: relative;
  overflow: hidden;
}

.forecast-month::before {
  background: var(--bb-metric-positive, #10b981);
  content: '';
  display: block;
  height: 100%;
  left: 0;
  opacity: 0.72;
  position: absolute;
  top: 0;
  width: 3px;
}

.forecast-month > * {
  position: relative;
}

.forecast-label,
.forecast-meta {
  color: var(--bb-text-muted, #6b7280);
  font-size: 0.8rem;
  margin: 0;
}

.forecast-net {
  color: var(--bb-metric-positive, #10b981);
  font-size: 1.2rem;
  font-weight: 900;
  margin: 0.35rem 0;
}

.forecast-net.negative {
  color: var(--bb-metric-negative, #ef4444);
}

.forecast-month:has(.forecast-net.negative)::before {
  background: var(--bb-metric-negative, #ef4444);
}

.reports-card {
  background: #ffffff;
  border: 1px solid #f3f4f6;
  border-radius: 1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  min-width: 0;
  padding: 1.5rem;
}

.reports-kpi-card {
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.reports-kpi-card:hover {
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
  transform: translateY(-1px);
}

.reports-chart-card {
  display: flex;
  flex-direction: column;
}

.reports-card-header {
  align-items: flex-start;
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: space-between;
  margin-bottom: 2rem;
}

.reports-bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  height: 18rem;
  justify-content: space-between;
  padding: 0 0.5rem;
}

.reports-net-worth-chart {
  flex: 1;
  min-height: 11rem;
  position: relative;
}

.reports-stacked-chart {
  background: var(--bb-surface-soft, #f9fafb);
  border: 1px solid var(--bb-border-soft, #f3f4f6);
  border-radius: 0.875rem;
  display: flex;
  flex-direction: column;
  min-height: 20rem;
  overflow: hidden;
  position: relative;
  width: 100%;
}

.reports-stacked-chart::before {
  background-image: linear-gradient(to top, rgba(148, 163, 184, 0.12) 1px, transparent 1px);
  background-size: 100% 25%;
  content: '';
  inset: 0 0 1.5rem;
  pointer-events: none;
  position: absolute;
}

.reports-stacked-segment {
  box-shadow: inset 0 1px rgba(255, 255, 255, 0.14);
  position: relative;
  z-index: 1;
}

.reports-legend-dot {
  box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.08);
}

.reports-legend-text,
.reports-chart-month-label {
  color: var(--bb-text-muted, #9ca3af);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0;
}

.reports-chart-month-label {
  font-size: 0.625rem;
  line-height: 1rem;
}

.reports-insights-card {
  align-items: center;
  background: #f0fdf4;
  border-color: #dcfce7;
  display: flex;
  flex-direction: row;
  gap: 2rem;
}

@media (min-width: 1024px) {
  .reports-main-grid {
    gap: 2.5rem;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .reports-card {
    padding: 2rem;
  }
}

@media (max-width: 768px) {
  .reports-page-header {
    flex-direction: column;
  }

  .reports-controls {
    justify-content: flex-start;
    width: 100%;
  }

  .reports-bar-chart {
    gap: 0.75rem;
    height: 16rem;
  }

  .reports-insights-card {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (max-width: 640px) {
  .reports-card {
    padding: 1.25rem;
  }

  .reports-card-header {
    margin-bottom: 1.5rem;
  }
}
</style>

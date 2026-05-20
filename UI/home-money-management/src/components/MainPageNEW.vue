<template>
  <div class="bg-gray-50 text-gray-900 font-sans antialiased min-h-screen">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div class="w-full px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <!-- Logo and Brand -->
          <div class="flex items-center gap-2">
            <img src="@/assets/logo-192.png" alt="Budget Buddy" class="w-10 h-10 rounded-lg object-contain" />
            <span class="text-xl font-bold text-gray-900 tracking-tight">Budget Buddy</span>
          </div>
          <!-- Desktop Navigation -->
          <nav class="hidden md:flex space-x-8">
            <router-link to="/" class="text-brand-primary border-b-2 border-brand-primary px-1 pt-1 text-sm font-medium">
              Dashboard
            </router-link>
            <router-link to="/transactions"
              class="text-gray-500 hover:text-gray-700 hover:border-gray-300 px-1 pt-1 border-b-2 border-transparent text-sm font-medium">
              Transactions
            </router-link>
            <router-link to="/reports"
              class="text-gray-500 hover:text-gray-700 hover:border-gray-300 px-1 pt-1 border-b-2 border-transparent text-sm font-medium">
              Reports
            </router-link>
          </nav>
          <!-- User Profile -->
          <div class="flex items-center gap-4">
            <button class="p-2 text-gray-400 hover:text-gray-600">
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg">
                <path
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
              </svg>
            </button>
            <div class="flex items-center gap-3 pl-4 border-l border-gray-200">
              <div class="text-right hidden sm:block">
                <p class="text-sm font-semibold text-gray-900 leading-none">{{ userData.user.first_name }} {{
                  userData.user.last_name }}</p>
                <p class="text-xs text-gray-500 mt-1">Premium Member</p>
              </div>
              <div
                class="h-9 w-9 rounded-full bg-brand-primary flex items-center justify-center text-white font-semibold cursor-pointer"
                @click="goToProfile">
                {{ userData.user.first_name.charAt(0) }}{{ userData.user.last_name.charAt(0) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <main class="w-full">
      <div class="px-4 sm:px-6 py-6">
        <!-- Summary Cards -->
        <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <!-- Income Card -->
          <div class="dashboard-summary-card">
            <div class="dashboard-summary-content">
              <p class="dashboard-metric-label">Total Income</p>
              <h3 class="text-3xl font-bold text-income leading-tight mb-2">${{ income.toLocaleString('en-US', {
                minimumFractionDigits: 2, maximumFractionDigits: 2
              }) }}</h3>
              <span class="text-sm text-green-600 font-medium flex items-center" v-if="incomeChange !== 0">
                <svg class="w-4 h-4 mr-1.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path clip-rule="evenodd"
                    d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L10 10.586 13.586 7H12z"
                    fill-rule="evenodd"></path>
                </svg>
                {{ incomeChange > 0 ? '+' : '' }}{{ incomeChange.toFixed(1) }}% from last month
              </span>
            </div>
            <div class="dashboard-summary-icon bg-green-50 text-income">
              <svg class="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg">
                <path d="M7 11l5-5m0 0l5 5m-5-5v12" stroke-linecap="round" stroke-linejoin="round" stroke-width="2">
                </path>
              </svg>
            </div>
          </div>

          <!-- Expense Card -->
          <div class="dashboard-summary-card">
            <div class="dashboard-summary-content">
              <p class="dashboard-metric-label">Total Expenses</p>
              <h3 class="text-3xl font-bold text-expense leading-tight mb-2">${{ expense.toLocaleString('en-US', {
                minimumFractionDigits: 2, maximumFractionDigits: 2
              }) }}</h3>
              <span class="text-sm text-red-600 font-medium flex items-center" v-if="expenseChange !== 0">
                <svg class="w-4 h-4 mr-1.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path clip-rule="evenodd"
                    d="M12 13a1 1 0 100 2h5a1 1 0 001-1V9a1 1 0 10-2 0v2.586l-4.293-4.293a1 1 0 00-1.414 0L8 9.586 3.707 5.293a1 1 0 00-1.414 1.414l5 5a1 1 0 001.414 0L10 9.414 13.586 13H12z"
                    fill-rule="evenodd"></path>
                </svg>
                {{ expenseChange > 0 ? '+' : '' }}{{ expenseChange.toFixed(1) }}% from last month
              </span>
            </div>
            <div class="dashboard-summary-icon bg-red-50 text-expense">
              <svg class="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg">
                <path d="M17 13l-5 5m0 0l-5-5m5 5V6" stroke-linecap="round" stroke-linejoin="round" stroke-width="2">
                </path>
              </svg>
            </div>
          </div>

          <!-- Net Balance Card -->
          <div class="dashboard-summary-card">
            <div class="dashboard-summary-content">
              <p class="dashboard-metric-label">Net Balance</p>
              <h3 class="text-3xl font-bold leading-tight mb-2"
                :class="netBalance >= 0 ? 'text-balance' : 'text-expense'">
                {{ netBalance >= 0 ? '+' : '' }}${{ Math.abs(netBalance).toLocaleString('en-US', {
                  minimumFractionDigits:
                    2, maximumFractionDigits: 2
                }) }}
              </h3>
              <span class="text-sm text-blue-600 font-medium block" v-if="netBalance > 0">Keep it up! Your savings are
                growing.</span>
              <span class="text-sm text-gray-500 block" v-else-if="netBalance === 0">Track your expenses to see your
                balance grow.</span>
              <span class="text-sm text-red-600 font-medium block" v-else>Consider reducing expenses to improve your
                balance.</span>
            </div>
            <div class="dashboard-summary-icon bg-blue-50 text-balance">
              <svg class="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg">
                <path
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
              </svg>
            </div>
          </div>
        </section>

        <!-- Main Layout -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <!-- Left Column: Accounts and Transactions -->
          <div class="lg:col-span-8 space-y-8">
            <!-- Accounts Section -->
            <section>
              <div class="dashboard-section-header px-1">
                <h2 class="dashboard-section-title">My Accounts</h2>
                <button class="text-sm font-semibold flex items-center transition-colors text-[#4CAF50]"
                  @click="openAddAccount">
                  <svg class="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 4v16m8-8H4" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                  </svg>
                  Add Account
                </button>
              </div>
              <div class="custom-scrollbar">
                <AccountsCarousel ref="accountsCarousel" :userData="userData" @accountSelected="handleAccountSelected"
                  @allAccountSelected="handleAllAccountSelected" @accountsModified="handleAccountsModified" />
              </div>
            </section>

            <!-- Transaction History Section -->
            <section class="dashboard-panel overflow-hidden">
              <div class="dashboard-panel-header">
                <h2 class="dashboard-section-title">Transaction History</h2>
                <div class="flex items-center gap-3">
                  <div class="relative">
                    <input v-model="searchQuery"
                      class="pl-8 pr-4 py-2 bg-gray-50 border-none rounded-lg text-sm focus:ring-2 focus:ring-brand-primary w-40 md:w-64"
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
            <section class="dashboard-panel p-6">
              <h2 class="dashboard-section-title mb-6">Spending Analysis</h2>
              <PieChart :transactions="transactions" />
            </section>

            <!-- Bank Statement Upload Widget -->
            <section class="dashboard-panel overflow-hidden">
              <div class="p-6 pb-4">
                <div class="dashboard-widget-header">
                  <div
                    class="w-12 h-12 bg-brand-light rounded-xl flex items-center justify-center text-[#4CAF50] shrink-0">
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
              <div class="px-6 pb-6 pt-2">
                <BankStatementUpload :userData="userData" @statementProcessed="handleStatementProcessed"
                  @uploadError="handleUploadError" />
              </div>
            </section>
          </aside>
        </div>

        <!-- Financial Performance Chart -->
        <section class="dashboard-panel mt-8 p-6 w-full">
          <div class="dashboard-panel-header compact">
            <div>
              <h2 class="dashboard-section-title">Financial Performance</h2>
              <p class="text-sm text-gray-500">Track your income and balance over the past year</p>
            </div>
            <v-select v-model="chartPeriod" :items="chartPeriodOptions" density="compact" variant="outlined"
              rounded="lg" hide-details class="chart-period-select shrink-0 text-sm"></v-select>
          </div>
          <Projections :transactions="transactions" :accounts="accounts" />
        </section>
      </div>
    </main>

    <!-- Bank Statement Review Dialog -->
    <BankStatementReview ref="bankStatementReview" :userData="userData" :accounts="accounts"
      @transactionsImported="handleTransactionsImported" @importError="handleImportError" />
  </div>
</template>

<script lang="ts">
import AccountsCarousel from '@/components/AccountsCarousel.vue'
import TableData from '@/components/TableData.vue'
import PieChart from '@/components/PieChart.vue'
import Projections from '@/components/Projections.vue'
import BankStatementUpload from '@/components/BankStatementUpload.vue'
import BankStatementReview from '@/components/BankStatementReview.vue'
import axios from '@/services/api'

interface AccountsCarousel {
  accountTotalUpdated: () => void;
  openNewAccountModal: () => void;
}

interface DateObject {
  month: number;
  year: number;
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
  month: number;
  year: number;
  transactions: Transaction[];
  accounts: Account[];
  income: number;
  expense: number;
  incomeChange: number;
  expenseChange: number;
  searchQuery: string;
  chartPeriod: string;
  chartPeriodOptions: Array<{ title: string; value: string }>;
  showAddAccountDialog: boolean;
  showNewTransactionDialog: boolean;
}

export default {
  name: 'MainPage',
  components: {
    AccountsCarousel,
    TableData,
    PieChart,
    Projections,
    BankStatementUpload,
    BankStatementReview
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
      month: 0,
      year: 0,
      transactions: [],
      accounts: [],
      income: 0,
      expense: 0,
      incomeChange: 0,
      expenseChange: 0,
      searchQuery: '',
      chartPeriod: '12',
      chartPeriodOptions: [
        { title: 'Last 12 Months', value: '12' },
        { title: 'Last 6 Months', value: '6' },
        { title: 'Year to Date', value: 'ytd' }
      ],
      showAddAccountDialog: false,
      showNewTransactionDialog: false
    }
  },
  computed: {
    netBalance(): number {
      return (this as any).income - (this as any).expense;
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
    const currentDate = new Date();
    (this as any).month = currentDate.getMonth() + 1;
    (this as any).year = currentDate.getFullYear();
    (this as any).getAccounts();
    (this as any).getTransactions();
  },
  methods: {
    goToProfile() {
      (this as any).$router.push('/profile');
    },
    handleUpdateIncomeExpense() {
      (this as any).getTransactions();
    },
    handleUpdateAccountsMethod() {
      ((this as any).$refs.accountsCarousel as AccountsCarousel).accountTotalUpdated();
    },
    openAddAccount() {
      ((this as any).$refs.accountsCarousel as AccountsCarousel).openNewAccountModal();
    },
    handleDatePicked(date: DateObject) {
      (this as any).month = date.month;
      (this as any).year = date.year;
      (this as any).getTransactions();
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
    calculateIncomeAndExpense() {
      if (!(this as any).transactions || (this as any).transactions.length === 0) {
        (this as any).income = 0;
        (this as any).expense = 0;
        (this as any).incomeChange = 0;
        (this as any).expenseChange = 0;
        return;
      }

      const currentDate = new Date();
      const currentMonth = currentDate.getMonth(); // 0-11
      const currentYear = currentDate.getFullYear();
      const lastMonth = currentMonth === 0 ? 11 : currentMonth - 1;
      const lastMonthYear = currentMonth === 0 ? currentYear - 1 : currentYear;

      // Current month transactions - properly parse dates
      const currentTransactions = (this as any).transactions.filter((t: Transaction) => {
        if (!t.date) return false;
        const tDate = new Date(t.date);
        // Check if date is valid
        if (isNaN(tDate.getTime())) return false;
        return tDate.getMonth() === currentMonth && tDate.getFullYear() === currentYear;
      });

      // Last month transactions
      const lastMonthTransactions = (this as any).transactions.filter((t: Transaction) => {
        if (!t.date) return false;
        const tDate = new Date(t.date);
        if (isNaN(tDate.getTime())) return false;
        return tDate.getMonth() === lastMonth && tDate.getFullYear() === lastMonthYear;
      });

      // Calculate current month - sum all income transactions
      (this as any).income = currentTransactions
        .filter((t: Transaction) => t.transaction_type === 'Income')
        .reduce((acc: number, t: Transaction) => acc + (Number(t.total) || 0), 0);

      // Calculate current month expenses - use absolute value
      (this as any).expense = currentTransactions
        .filter((t: Transaction) => t.transaction_type === 'Expense')
        .reduce((acc: number, t: Transaction) => acc + Math.abs(Number(t.total) || 0), 0);

      // Calculate last month for comparison
      const lastMonthIncome = lastMonthTransactions
        .filter((t: Transaction) => t.transaction_type === 'Income')
        .reduce((acc: number, t: Transaction) => acc + (Number(t.total) || 0), 0);

      const lastMonthExpense = lastMonthTransactions
        .filter((t: Transaction) => t.transaction_type === 'Expense')
        .reduce((acc: number, t: Transaction) => acc + Math.abs(Number(t.total) || 0), 0);

      // Calculate percentage changes
      (this as any).incomeChange = lastMonthIncome > 0
        ? (((this as any).income - lastMonthIncome) / lastMonthIncome) * 100
        : ((this as any).income > 0 && lastMonthIncome === 0) ? 100 : 0;

      (this as any).expenseChange = lastMonthExpense > 0
        ? (((this as any).expense - lastMonthExpense) / lastMonthExpense) * 100
        : ((this as any).expense > 0 && lastMonthExpense === 0) ? 100 : 0;
    },
    getTransactions() {
      // Fetch all transactions (month=0, year=0) so the chart has access to last 12 months of data
      if ((this as any).accountSelected === null) {
        axios.get(`/transactions/retrieve/${(this as any).userData.user.username}/0/0/0`)
          .then((response) => {
            (this as any).transactions = response.data;
            (this as any).calculateIncomeAndExpense();
          })
          .catch((error) => {
            console.log('ERROR', error);
          });
      } else {
        axios.get(`/transactions/retrieve/${(this as any).userData.user.username}/${(this as any).accountSelected.id}/0/0`)
          .then((response) => {
            (this as any).transactions = response.data;
            (this as any).calculateIncomeAndExpense();
          })
          .catch((error) => {
            console.log('ERROR', error);
          });
      }
      // Also fetch accounts
      (this as any).getAccounts();
    },
    getAccounts() {
      axios.get(`/accounts/details/${(this as any).userData.user.username}/0`)
        .then((response) => {
          (this as any).accounts = response.data;
        })
        .catch((error) => {
          console.log('ERROR fetching accounts:', error);
        });
    },
    handleStatementProcessed(bankStatementData: any) {
      if (bankStatementData.status === 'uploaded') {
        console.log('Bank statement uploaded successfully:', bankStatementData.file_details);
        if (bankStatementData.file_details.processing_status === 'failed') {
          alert(`Bank statement "${bankStatementData.file_details.filename}" uploaded but processing failed.\n\nPlease try again or process manually.`);
        } else {
          alert(`Bank statement "${bankStatementData.file_details.filename}" uploaded successfully!\n\nFile size: ${bankStatementData.file_details.file_size_display}\nStatus: ${bankStatementData.file_details.processing_status}`);
        }
      } else if (bankStatementData.status === 'processed' && bankStatementData.extracted_data) {
        (this as any).$refs.bankStatementReview.openDialog(bankStatementData);
      } else {
        (this as any).$refs.bankStatementReview.openDialog(bankStatementData);
      }
    },
    handleUploadError(errorMessage: string) {
      console.error('Upload error:', errorMessage);
      alert(`Upload Error: ${errorMessage}`);
    },
    handleTransactionsImported(data: any) {
      (this as any).getTransactions();
      (this as any).handleUpdateAccountsMethod();
      console.log(`Successfully imported ${data.importedCount} transactions`);
    },
    handleImportError(errorMessage: string) {
      console.error('Import error:', errorMessage);
    }
  }
}
</script>

<style scoped>
.dashboard-panel,
.dashboard-summary-card {
  background: #ffffff;
  border: 1px solid #f3f4f6;
  border-radius: 1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
}

.dashboard-summary-card {
  display: flex;
  align-items: stretch;
  gap: 1.5rem;
  justify-content: space-between;
  min-height: 9rem;
  padding: 1.5rem;
}

.dashboard-summary-content {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
}

.dashboard-summary-icon {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  align-self: center;
  border-radius: 0.75rem;
  height: 4rem;
  padding: 1rem;
  width: 4rem;
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
  border-bottom: 1px solid #f3f4f6;
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

.dashboard-section-title {
  color: #1f2937;
  font-size: 1.125rem;
  font-weight: 600;
  line-height: 1.5rem;
  margin: 0;
}

.dashboard-metric-label {
  color: #6b7280;
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
  .dashboard-summary-card {
    gap: 1rem;
    min-height: auto;
    padding: 1.25rem;
  }

  .dashboard-summary-icon {
    height: 3.5rem;
    padding: 0.875rem;
    width: 3.5rem;
  }
}
</style>

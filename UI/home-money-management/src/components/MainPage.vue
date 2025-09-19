<template>
    <v-container fluid class="pa-0">
        <!-- Modern Header with Budget Buddy Branding -->
        <v-app-bar class="budget-header shadow-strong" elevation="0" height="80" fixed>
            <v-container class="d-flex align-center">
                <!-- Budget Buddy Logo and Brand -->
                <div class="d-flex align-center">
                    <v-avatar size="48" class="me-3">
                        <v-img src="@/assets/logo.png" alt="Budget Buddy" />
                    </v-avatar>
                    <div>
                        <h2 class="header-title font-weight-bold mb-0">Budget Buddy</h2>
                        <p class="header-subtitle text-caption mb-0 opacity-90">Smart Money Management</p>
                    </div>
                </div>

                <v-spacer></v-spacer>

                <!-- Welcome Message -->
                <div class="text-center me-8 d-none d-md-block">
                    <h3 class="welcome-title font-weight-medium mb-0">Welcome back, {{ (this as
                        any).userData.user.first_name }}!</h3>
                    <p class="welcome-subtitle text-caption mb-0 opacity-90">Ready to manage your finances?</p>
                </div>

                <!-- User Menu -->
                <v-menu>
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" variant="outlined" class="user-menu-btn smooth-transition hover-lift"
                            size="large">
                            <v-icon left class="me-2">mdi-account-circle</v-icon>
                            {{ (this as any).userData.user.first_name }}
                            <v-icon right class="ms-2">mdi-chevron-down</v-icon>
                        </v-btn>
                    </template>
                    <v-list class="modern-menu" rounded="lg">
                        <v-list-item class="user-profile-section">
                            <template v-slot:prepend>
                                <v-avatar size="40" class="budget-gradient me-3">
                                    <v-icon color="white" size="20">mdi-account</v-icon>
                                </v-avatar>
                            </template>
                            <v-list-item-title class="text-h6 font-weight-bold text-grey-darken-3">
                                {{ (this as any).userData.user.first_name }} {{ (this as any).userData.user.last_name }}
                            </v-list-item-title>
                            <v-list-item-subtitle class="text-grey-darken-1">{{ (this as any).userData.user.username
                            }}</v-list-item-subtitle>
                        </v-list-item>
                        <v-divider class="my-2 bg-grey-lighten-2"></v-divider>
                        <v-list-item @click="(this as any).triggerLogOut" class="logout-item">
                            <template v-slot:prepend>
                                <v-avatar size="32" class="bg-red-lighten-4 me-3">
                                    <v-icon color="red-darken-2" size="18">mdi-logout</v-icon>
                                </v-avatar>
                            </template>
                            <v-list-item-title class="text-red-darken-2 font-weight-medium">Logout</v-list-item-title>
                        </v-list-item>
                    </v-list>
                </v-menu>
            </v-container>
        </v-app-bar>

        <!-- Main Content with proper spacing for fixed header -->
        <div class="main-content" style="margin-top: 80px;">
            <v-container fluid class="pa-6">
                <!-- Account Cards Section -->
                <v-card class="mb-6 glass-card shadow-medium" rounded="xl">
                    <v-card-title class="pa-6 pb-2">
                        <h3 class="budget-text-gradient font-weight-bold">Your Accounts</h3>
                        <p class="text-grey-darken-1 mb-0">Manage and track all your financial accounts</p>
                    </v-card-title>
                    <v-card-text class="pa-6 pt-2">
                        <AccountsCarousel ref="accountsCarousel" :userData="(this as any).userData"
                            @accountSelected="(this as any).handleAccountSelected"
                            @allAccountSelected="(this as any).handleAllAccountSelected"
                            @accountsModified="(this as any).handleAccountsModified" />
                    </v-card-text>
                </v-card>

                <!-- Date Picker and Income/Expense Overview -->
                <v-row class="mb-6">
                    <v-col cols="12" lg="3">
                        <v-card class="glass-card shadow-medium h-100" rounded="xl">
                            <v-card-title class="pa-6 pb-2">
                                <h4 class="budget-text-gradient font-weight-bold">Time Period</h4>
                                <p class="text-grey-darken-1 mb-0 text-caption">Select your analysis period</p>
                            </v-card-title>
                            <v-card-text class="pa-6 pt-2">
                                <DatePicker :userData="(this as any).userData"
                                    @dateSelected="(this as any).handleDatePicked" />
                            </v-card-text>
                        </v-card>
                    </v-col>
                    <v-col cols="12" lg="9">
                        <v-card class="glass-card shadow-medium h-100" rounded="xl">
                            <v-card-title class="pa-6 pb-2">
                                <h4 class="budget-text-gradient font-weight-bold">Financial Overview</h4>
                                <p class="text-grey-darken-1 mb-0 text-caption">Your income and expenses summary</p>
                            </v-card-title>
                            <v-card-text class="pa-6 pt-2">
                                <IncomeExpense :transactions="(this as any).transactions" />
                            </v-card-text>
                        </v-card>
                    </v-col>
                </v-row>

                <!-- Transactions and Analytics -->
                <v-row class="mb-6">
                    <v-col cols="12" lg="8">
                        <v-card class="glass-card shadow-medium h-100" rounded="xl">
                            <v-card-title class="pa-6 pb-2">
                                <h4 class="budget-text-gradient font-weight-bold">Transaction History</h4>
                                <p class="text-grey-darken-1 mb-0 text-caption">Track and manage your financial
                                    transactions</p>
                            </v-card-title>
                            <v-card-text class="pa-6 pt-2">
                                <TableData :transactions="(this as any).transactions" :userData="(this as any).userData"
                                    :accounts="(this as any).accounts"
                                    @updateAccounts="(this as any).handleUpdateAccountsMethod"
                                    @updateIncomeExpense="(this as any).handleUpdateIncomeExpense" />
                            </v-card-text>
                        </v-card>
                    </v-col>
                    <v-col cols="12" lg="4">
                        <v-card class="glass-card shadow-medium h-100" rounded="xl">
                            <v-card-title class="pa-6 pb-2">
                                <h4 class="budget-text-gradient font-weight-bold">Spending Analysis</h4>
                                <p class="text-grey-darken-1 mb-0 text-caption">Visual breakdown of your expenses</p>
                            </v-card-title>
                            <v-card-text class="pa-6 pt-2">
                                <PieChart :transactions="(this as any).transactions" />
                            </v-card-text>
                        </v-card>
                    </v-col>
                </v-row>

                <!-- Bank Statement Upload Section -->
                <v-row class="mb-6">
                    <v-col cols="12">
                        <BankStatementUpload :userData="(this as any).userData"
                            @statementProcessed="(this as any).handleStatementProcessed"
                            @uploadError="(this as any).handleUploadError" />
                    </v-col>
                </v-row>

                <!-- Financial Projections Section -->
                <v-row>
                    <v-col cols="12">
                        <Projections :transactions="(this as any).transactions" :accounts="(this as any).accounts" />
                    </v-col>
                </v-row>
            </v-container>
        </div>

        <!-- Bank Statement Review Dialog -->
        <BankStatementReview ref="bankStatementReview" :userData="(this as any).userData"
            :accounts="(this as any).accounts" @transactionsImported="(this as any).handleTransactionsImported"
            @importError="(this as any).handleImportError" />
    </v-container>
</template>

<script lang="ts">

import AccountsCarousel from '@/components/AccountsCarousel.vue'
import DatePicker from '@/components/DatePicker.vue';
import IncomeExpense from '@/components/IncomeExpense.vue';
import TableData from '@/components/TableData.vue';
import PieChart from '@/components/PieChart.vue';
import Projections from '@/components/Projections.vue';
import BankStatementUpload from '@/components/BankStatementUpload.vue';
import BankStatementReview from '@/components/BankStatementReview.vue';
import axios from 'axios';
// import * as Vue from 'vue';
interface AccountsCarousel {
    accountTotalUpdated: () => void;
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
    transaction_type: string,
    category: string,
    date: string,
    title: string,
    total: number,
    owner_id: string,
    account_id: string,
}
interface Data {
    accountSelected: null | Account;
    month: number;
    year: number;
    transactions: Transaction[];
    accounts: Account[];
}
export default {
    name: 'MainPage',
    props: {
        userData: {
            type: Object,
            required: true
        }
    },
    data: (): Data => ({
        accountSelected: null,
        month: 0,
        year: 0,
        transactions: [],
        accounts: []

    }),
    mounted() {
        const currentDate = new Date();
        (this as any).month = currentDate.getMonth();
        (this as any).year = currentDate.getFullYear();
        (this as any).getTransactions();
    },
    components: { AccountsCarousel, DatePicker, IncomeExpense, TableData, PieChart, Projections, BankStatementUpload, BankStatementReview },
    methods: {
        triggerLogOut() {
            localStorage.removeItem('money_management_user');
            location.reload();
        },
        handleUpdateIncomeExpense() {
            (this as any).getTransactions();
        },
        handleUpdateAccountsMethod() {
            ((this as any).$refs.accountsCarousel as AccountsCarousel).accountTotalUpdated();
        },
        handleDatePicked(date: DateObject) {
            (this as any).month = date.month;
            (this as any).year = date.year;
            (this as any).getTransactions();
        },
        handleAllAccountSelected(acc: Object) {
            (this as any).accountSelected = null;
        },
        handleAccountSelected(acc: Account) {
            (this as any).accountSelected = acc;
            (this as any).getTransactions();
        },
        handleAccountsModified(accs: Array<Account>) {
            (this as any).accounts = accs;
        },
        getTransactions() {
            if ((this as any).accountSelected === null) {
                axios.get(`http://localhost:8000/transactions/retrieve/${(this as any).userData.user.username}/0/${(this as any).month + 1}/${(this as any).year}`)
                    .then((response) => {
                        (this as any).transactions = response.data;
                    })
                    .catch((error) => {
                        console.log('ERROR', error);
                    })
            }
            else {
                axios.get(`http://localhost:8000/transactions/retrieve/${(this as any).userData.user.username}/${(this as any).accountSelected.id}/${(this as any).month + 1}/${(this as any).year}`)
                    .then((response) => {
                        (this as any).transactions = response.data;
                    })
                    .catch((error) => {
                        console.log('ERROR', error);
                    })
            }

        },
        handleStatementProcessed(bankStatementData: any) {
            // Open the review dialog with the processed data
            (this as any).$refs.bankStatementReview.openDialog(bankStatementData);
        },
        handleUploadError(errorMessage: string) {
            // Handle upload errors - you can add a snackbar or alert here
            console.error('Upload error:', errorMessage);
            // For now, just log the error. You can add a toast notification later
        },
        handleTransactionsImported(data: any) {
            // Refresh transactions and accounts after import
            (this as any).getTransactions();
            (this as any).handleUpdateAccountsMethod();
            console.log(`Successfully imported ${data.importedCount} transactions`);
        },
        handleImportError(errorMessage: string) {
            // Handle import errors
            console.error('Import error:', errorMessage);
        }
    }
}
</script>

<style scoped>
/* Modern Main Page Styles */
.main-content {
    min-height: calc(100vh - 80px);
    background: transparent;
}

/* Custom card hover effects */
.glass-card:hover {
    transform: translateY(-2px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .main-content {
        margin-top: 70px !important;
    }

    .v-app-bar {
        height: 70px !important;
    }
}

/* Animation for smooth page transitions */
.main-content {
    animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Custom gradient text for better readability */
.budget-text-gradient {
    background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 600;
}

/* Enhanced glassmorphism for cards */
.glass-card {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow:
        0 8px 32px rgba(0, 0, 0, 0.1),
        inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

/* Budget gradient for header */
.budget-gradient {
    background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 50%, #8BC34A 100%);
    position: relative;
    overflow: hidden;
}

/* Header background */
.budget-header {
    background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 50%, #8BC34A 100%) !important;
    position: relative;
    overflow: hidden;
}


.budget-gradient::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.1) 50%, transparent 70%);
    animation: shimmer 3s infinite;
}

@keyframes shimmer {
    0% {
        transform: translateX(-100%);
    }

    100% {
        transform: translateX(100%);
    }
}

/* Modern User Menu */
.modern-menu {
    background: rgba(255, 255, 255, 0.98);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(76, 175, 80, 0.2);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    min-width: 240px;
    padding: 8px 0;
}

.modern-menu .v-list-item {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: 8px;
    margin: 4px 8px;
}

.modern-menu .user-profile-section {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.05) 0%, rgba(139, 195, 74, 0.05) 100%);
    border: 1px solid rgba(76, 175, 80, 0.1);
}

.modern-menu .user-profile-section:hover {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(139, 195, 74, 0.1) 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
}

.modern-menu .logout-item:hover {
    background: rgba(244, 67, 54, 0.1);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(244, 67, 54, 0.2);
}

.modern-menu .logout-item:active {
    background: rgba(244, 67, 54, 0.2);
    transform: translateY(0);
}

/* Enhanced divider */
.modern-menu .v-divider {
    border-color: rgba(76, 175, 80, 0.2);
    margin: 12px 16px;
}

/* Avatar styling */
.modern-menu .v-avatar {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Text styling */
.modern-menu .v-list-item-title {
    font-weight: 600;
    letter-spacing: 0.3px;
}

.modern-menu .v-list-item-subtitle {
    font-size: 0.8rem;
    opacity: 0.8;
}

/* User Menu Button Styling */
.user-menu-btn {
    border: 2px solid rgba(255, 255, 255, 0.3) !important;
    background: rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(10px);
    font-weight: 500;
    letter-spacing: 0.5px;
    color: white !important;
}

.user-menu-btn .v-btn__content {
    color: white !important;
}

.user-menu-btn .v-icon {
    color: white !important;
}

.user-menu-btn:hover {
    border-color: rgba(255, 255, 255, 0.6) !important;
    background: rgba(255, 255, 255, 0.2) !important;
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    color: white !important;
}

.user-menu-btn:hover .v-btn__content {
    color: white !important;
}

.user-menu-btn:hover .v-icon {
    color: white !important;
}

.user-menu-btn:active {
    transform: translateY(0);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

/* Header Text Styling */
.header-title {
    color: white !important;
    font-size: 1.5rem;
    font-weight: 700;
}

.header-subtitle {
    color: rgba(255, 255, 255, 0.9) !important;
}

.welcome-title {
    color: white !important;
    font-size: 1.1rem;
    font-weight: 500;
}

.welcome-subtitle {
    color: rgba(255, 255, 255, 0.9) !important;
}
</style>
<template>
    <div class="income-expense-container">
        <!-- Income Card -->
        <v-card class="income-card smooth-transition hover-lift" elevation="2" rounded="xl">
            <v-card-text class="pa-6 text-center">
                <v-avatar size="60" class="mb-4 income-avatar">
                    <v-icon color="white" size="32">mdi-trending-up</v-icon>
                </v-avatar>
                <h3 class="text-h6 font-weight-bold mb-2 text-success">Income</h3>
                <h2 class="text-h4 font-weight-bold text-success mb-1">${{ (this as any).income.toLocaleString() }}</h2>
                <p class="text-caption text-grey-darken-1 mb-0">Total earnings</p>
            </v-card-text>
        </v-card>

        <!-- Expense Card -->
        <v-card class="expense-card smooth-transition hover-lift" elevation="2" rounded="xl">
            <v-card-text class="pa-6 text-center">
                <v-avatar size="60" class="mb-4 expense-avatar">
                    <v-icon color="white" size="32">mdi-trending-down</v-icon>
                </v-avatar>
                <h3 class="text-h6 font-weight-bold mb-2 text-error">Expenses</h3>
                <h2 class="text-h4 font-weight-bold text-error mb-1">${{ (this as any).expense.toLocaleString() }}</h2>
                <p class="text-caption text-grey-darken-1 mb-0">Total spending</p>
            </v-card-text>
        </v-card>

        <!-- Net Balance Card -->
        <v-card class="balance-card smooth-transition hover-lift" elevation="2" rounded="xl"
            :class="(this as any).getBalanceCardClass()">
            <v-card-text class="pa-6 text-center">
                <v-avatar size="60" class="mb-4 balance-avatar">
                    <v-icon color="white" size="32">mdi-scale-balance</v-icon>
                </v-avatar>
                <h3 class="text-h6 font-weight-bold mb-2" :class="(this as any).getBalanceTextClass()">Net Balance</h3>
                <h2 class="text-h4 font-weight-bold mb-1" :class="(this as any).getBalanceTextClass()">
                    {{ (this as any).getFormattedBalance() }}
                </h2>
                <p class="text-caption text-grey-darken-1 mb-0">Income - Expenses</p>
            </v-card-text>
        </v-card>
    </div>
</template>

<style scoped>
/* Modern Income/Expense Container */
.income-expense-container {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    width: 100%;
    height: 100%;
}

/* Income Card */
.income-card {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(76, 175, 80, 0.05) 100%);
    border: 1px solid rgba(76, 175, 80, 0.2);
    position: relative;
    overflow: hidden;
}

.income-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #4CAF50 0%, #8BC34A 100%);
}

.income-avatar {
    background: linear-gradient(135deg, #4CAF50 0%, #8BC34A 100%) !important;
    box-shadow: 0 4px 20px rgba(76, 175, 80, 0.3);
}

/* Expense Card */
.expense-card {
    background: linear-gradient(135deg, rgba(244, 67, 54, 0.1) 0%, rgba(244, 67, 54, 0.05) 100%);
    border: 1px solid rgba(244, 67, 54, 0.2);
    position: relative;
    overflow: hidden;
}

.expense-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #F44336 0%, #FF7043 100%);
}

.expense-avatar {
    background: linear-gradient(135deg, #F44336 0%, #FF7043 100%) !important;
    box-shadow: 0 4px 20px rgba(244, 67, 54, 0.3);
}

/* Balance Card */
.balance-card {
    position: relative;
    overflow: hidden;
}

.balance-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    transition: all 0.3s ease;
}

.positive-balance {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(76, 175, 80, 0.05) 100%);
    border: 1px solid rgba(76, 175, 80, 0.2);
}

.positive-balance::before {
    background: linear-gradient(90deg, #4CAF50 0%, #8BC34A 100%);
}

.negative-balance {
    background: linear-gradient(135deg, rgba(244, 67, 54, 0.1) 0%, rgba(244, 67, 54, 0.05) 100%);
    border: 1px solid rgba(244, 67, 54, 0.2);
}

.negative-balance::before {
    background: linear-gradient(90deg, #F44336 0%, #FF7043 100%);
}

.neutral-balance {
    background: linear-gradient(135deg, rgba(158, 158, 158, 0.1) 0%, rgba(158, 158, 158, 0.05) 100%);
    border: 1px solid rgba(158, 158, 158, 0.2);
}

.neutral-balance::before {
    background: linear-gradient(90deg, #9E9E9E 0%, #BDBDBD 100%);
}

.balance-avatar {
    background: linear-gradient(135deg, #9E9E9E 0%, #BDBDBD 100%) !important;
    box-shadow: 0 4px 20px rgba(158, 158, 158, 0.3);
}

.positive-balance .balance-avatar {
    background: linear-gradient(135deg, #4CAF50 0%, #8BC34A 100%) !important;
    box-shadow: 0 4px 20px rgba(76, 175, 80, 0.3);
}

.negative-balance .balance-avatar {
    background: linear-gradient(135deg, #F44336 0%, #FF7043 100%) !important;
    box-shadow: 0 4px 20px rgba(244, 67, 54, 0.3);
}

/* Hover Effects */
.income-card:hover,
.expense-card:hover,
.balance-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

/* Responsive Design */
@media (max-width: 1200px) {
    .income-expense-container {
        grid-template-columns: 1fr;
        gap: 16px;
    }
}

@media (max-width: 768px) {
    .income-expense-container {
        grid-template-columns: 1fr;
        gap: 12px;
    }
}

@media (max-width: 480px) {
    .income-expense-container {
        gap: 8px;
    }

    .income-card,
    .expense-card,
    .balance-card {
        margin: 0;
    }
}

/* Animation for cards */
.income-card,
.expense-card,
.balance-card {
    animation: fadeInScale 0.6s ease-out;
}

@keyframes fadeInScale {
    from {
        opacity: 0;
        transform: scale(0.9) translateY(20px);
    }

    to {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}

/* Staggered animation */
.income-card {
    animation-delay: 0.1s;
}

.expense-card {
    animation-delay: 0.2s;
}

.balance-card {
    animation-delay: 0.3s;
}
</style>

<script lang="ts">
// import * as Vue from 'vue';
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
    income: number;
    expense: number;
}
export default {
    name: 'IncomeExpense',
    props: {
        transactions: {
            type: Array as () => Transaction[],
            required: true
        }
    },
    data: (): Data => ({
        income: 0,
        expense: 0,
    }),
    mounted() {
        this.calculateIncomeAndExpense();
    },
    watch: {
        transactions: {
            handler: 'calculateIncomeAndExpense',
            deep: true,
        },
    },
    methods: {
        calculateIncomeAndExpense() {
            (this as any).income = (this as any).transactions.filter((transaction: Transaction) => transaction.transaction_type === 'Income').reduce((acc: number, transaction: Transaction) => acc + transaction.total, 0);
            (this as any).expense = Math.abs((this as any).transactions.filter((transaction: Transaction) => transaction.transaction_type === 'Expense').reduce((acc: number, transaction: Transaction) => acc + transaction.total, 0));
        },

        getBalanceCardClass() {
            const balance = (this as any).income - (this as any).expense;
            if (balance > 0) {
                return 'positive-balance';
            } else if (balance < 0) {
                return 'negative-balance';
            } else {
                return 'neutral-balance';
            }
        },

        getBalanceTextClass() {
            const balance = (this as any).income - (this as any).expense;
            if (balance > 0) {
                return 'text-success';
            } else if (balance < 0) {
                return 'text-error';
            } else {
                return 'text-grey-darken-1';
            }
        },

        getFormattedBalance() {
            const balance = (this as any).income - (this as any).expense;
            if (balance > 0) {
                return `+$${balance.toLocaleString()}`;
            } else if (balance < 0) {
                return `-$${Math.abs(balance).toLocaleString()}`;
            } else {
                return `+$${balance.toLocaleString()}`;
            }
        },
    }
}
</script>
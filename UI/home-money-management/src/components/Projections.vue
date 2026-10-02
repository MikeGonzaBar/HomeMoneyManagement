<template>
    <div class="projections-container">
        <!-- Header Section -->
        <div class="projections-header">
            <div class="header-content">
                <v-icon color="primary" class="me-2">mdi-chart-line</v-icon>
                <span class="text-h5 font-weight-bold">Income and spending</span>
            </div>
            <p class="text-subtitle-1 text-grey-darken-1 mb-0">Where your money came from and where it went, month by month
            </p>
        </div>

        <!-- Controls Section -->
        <div class="controls-section">
            <div class="projection-controls-toolbar">
                <v-select v-model="selectedAccount" :items="accountOptions" aria-label="Account Filter"
                    variant="outlined" density="compact" hide-details rounded="lg" prepend-inner-icon="mdi-account"
                    class="projection-control-select" @update:model-value="updateChart"></v-select>
                <v-btn color="primary" variant="outlined" rounded="lg" height="44" class="projection-refresh-button"
                    @click="refreshChart" :loading="isLoading">
                    <v-icon start>mdi-refresh</v-icon>
                    Refresh
                </v-btn>
            </div>
        </div>

        <!-- Chart Section -->
        <div class="chart-section">
            <v-card class="projections-card" elevation="2" rounded="xl">
                <v-card-title class="pa-6 pb-2">
                    <div class="d-flex align-center">
                        <v-avatar size="40" class="me-3 budget-gradient">
                            <v-icon color="white">mdi-chart-line</v-icon>
                        </v-avatar>
                        <div>
                            <h3 class="text-h5 font-weight-bold budget-text-gradient mb-0">Transaction Chart</h3>
                            <p class="text-caption text-grey-darken-1 mb-0">Actual transaction data over time</p>
                        </div>
                    </div>
                </v-card-title>
                <v-card-text class="pa-6 pt-2">
                    <div class="chart-wrapper">
                        <Line :data="chartData" :options="chartOptions" />
                    </div>
                </v-card-text>
            </v-card>
        </div>

        <!-- Legend Section -->
        <div class="legend-section">
            <v-row>
                <v-col cols="12" md="4">
                    <div class="legend-item">
                        <div class="legend-color income-color"></div>
                        <span class="legend-text">Income</span>
                    </div>
                </v-col>
                <v-col cols="12" md="4">
                    <div class="legend-item">
                        <div class="legend-color expense-color"></div>
                        <span class="legend-text">Expenses</span>
                    </div>
                </v-col>
                <v-col cols="12" md="4">
                    <div class="legend-item">
                        <div class="legend-color balance-color"></div>
                        <span class="legend-text">Net (income − spending)</span>
                    </div>
                </v-col>
            </v-row>
        </div>
    </div>
</template>

<style scoped>
.projections-container {
    width: 100%;
    padding: 24px;
    background: var(--bb-surface, #ffffff);
    border-radius: 16px;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
    border: 1px solid var(--bb-border-soft, #f3f4f6);
    color: var(--bb-text-strong, #1f2937);
}

.projections-header {
    text-align: center;
    margin-bottom: 32px;
}

.header-content {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 8px;
    color: #4CAF50;
}

.controls-section {
    margin-bottom: 32px;
}

.projection-controls-toolbar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    flex-wrap: wrap;
}

.projection-control-select {
    flex: 0 1 240px;
    max-width: 240px;
    min-width: 220px;
}

.projection-refresh-button {
    min-width: 132px;
    text-transform: none;
    font-weight: 600;
    letter-spacing: 0;
}

:deep(.projection-control-select .v-field) {
    background: var(--bb-surface-soft, #ffffff);
    border-color: var(--bb-border-soft, #f3f4f6);
    border-radius: 12px;
    height: 44px;
    min-height: 44px;
}

.projection-refresh-button {
    background: var(--bb-surface-soft, #ffffff) !important;
    border-color: rgba(76, 175, 80, 0.35) !important;
    color: #2E7D32 !important;
}

:deep(.projection-control-select .v-field__input) {
    align-items: center;
    font-size: 0.875rem;
    font-weight: 600;
    min-height: 44px;
    padding-bottom: 0;
    padding-top: 0;
}

:deep(.projection-control-select .v-field__prepend-inner) {
    padding-top: 10px;
}

.projection-refresh-button :deep(.v-btn__content) {
    align-items: center;
    gap: 6px;
}

.chart-section {
    margin-bottom: 24px;
}

.projections-card {
    background: var(--bb-surface, #ffffff);
    border: 1px solid var(--bb-border-soft, #f3f4f6);
    box-shadow: none !important;
    color: var(--bb-text-strong, #1f2937);
}

.chart-wrapper {
    position: relative;
    height: 400px;
    width: 100%;
}

.legend-section {
    margin-top: 16px;
}

.legend-item {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}

.legend-color {
    width: 20px;
    height: 4px;
    border-radius: 2px;
}

.income-color {
    background: #4CAF50;
}

.expense-color {
    background: #F44336;
}

.balance-color {
    background: #2196F3;
}

.legend-text {
    font-size: 0.9rem;
    color: var(--bb-text-muted, #6b7280);
}

.explanation-text {
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--bb-text-muted, #6b7280);
    font-size: 0.9rem;
    font-style: italic;
    padding: 8px 0;
}

/* Responsive Design */
@media (max-width: 768px) {
    .projections-container {
        padding: 16px;
    }

    .chart-wrapper {
        height: 300px;
    }

    .legend-item {
        justify-content: flex-start;
    }

    .projection-control-select,
    .projection-refresh-button {
        max-width: none;
        width: 100%;
    }
}
</style>

<script lang="ts">
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

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

interface Account {
    id: number;
    account_type: string;
    bank: string;
    total: number;
    account_name: string;
}

interface MonthlyData {
    month: string;
    income: number;
    expenses: number;
    balance: number;
    isProjected: boolean;
}

interface ProjectionsComponentInstance {
    transactions: Transaction[];
    accounts: Account[];
    selectedAccount: string;
    isLoading: boolean;
    chartData: any;
    chartOptions: any;
    accountOptions: any[];
    monthlyData: MonthlyData[];
    updateChart(): void;
    refreshChart(): void;
    generateChartData(): void;
    getHistoricalData(): MonthlyData[];
    getChartTheme(): {
        textColor: string;
        mutedColor: string;
        gridColor: string;
        tooltipBackground: string;
        tooltipText: string;
    };
    buildChartOptions(): any;
}

export default {
    name: 'Projections',
    components: {
        Line
    },
    props: {
        transactions: {
            type: Array as () => Transaction[],
            required: true
        },
        accounts: {
            type: Array as () => Account[],
            required: true
        }
    },
    data() {
        return {
        selectedAccount: 'all',
        isLoading: false,
        monthlyData: [],
        accountOptions: [
            { title: 'All Accounts', value: 'all' }
        ],
        chartData: {
            labels: [],
            datasets: []
        },
        chartOptions: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index' as const,
                    intersect: false,
                    callbacks: {
                        label: function (context: any) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y;
                            const sign = value >= 0 ? '+' : '';
                            return `${label}: ${sign}$${Math.abs(value).toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Month'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Amount ($)'
                    },
                    ticks: {
                        callback: function (value: any) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest' as const,
                axis: 'x' as const,
                intersect: false
            }
        }
        };
    },
    mounted() {
        this.initializeAccountOptions();
        this.updateChart();
    },
    watch: {
        transactions: {
            handler: 'updateChart',
            deep: true
        },
        accounts: {
            handler: 'initializeAccountOptions',
            deep: true
        }
    },
    methods: {
        initializeAccountOptions(this: ProjectionsComponentInstance) {
            this.accountOptions = [
                { title: 'All Accounts', value: 'all' },
                ...this.accounts.map((account: Account) => ({
                    title: account.account_name,
                    value: account.id.toString()
                }))
            ];
        },

        updateChart(this: ProjectionsComponentInstance) {
            this.monthlyData = this.getHistoricalData();
            this.generateChartData();
        },

        refreshChart(this: ProjectionsComponentInstance) {
            this.isLoading = true;
            setTimeout(() => {
                this.updateChart();
                this.isLoading = false;
            }, 500);
        },

        getChartTheme() {
            const isDark = document.documentElement.classList.contains('app-dark');
            return {
                textColor: isDark ? '#f8fafc' : '#1f2937',
                mutedColor: isDark ? '#cbd5e1' : '#6b7280',
                gridColor: isDark ? 'rgba(203, 213, 225, 0.16)' : 'rgba(107, 114, 128, 0.16)',
                tooltipBackground: isDark ? '#111827' : '#ffffff',
                tooltipText: isDark ? '#f8fafc' : '#1f2937'
            };
        },

        buildChartOptions(this: ProjectionsComponentInstance) {
            const theme = this.getChartTheme();
            return {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index' as const,
                        intersect: false,
                        backgroundColor: theme.tooltipBackground,
                        titleColor: theme.tooltipText,
                        bodyColor: theme.tooltipText,
                        borderColor: theme.gridColor,
                        borderWidth: 1,
                        callbacks: {
                            label: function (context: any) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y;
                                const sign = value >= 0 ? '+' : '';
                                return `${label}: ${sign}$${Math.abs(value).toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Month',
                            color: theme.mutedColor
                        },
                        ticks: {
                            color: theme.mutedColor
                        },
                        grid: {
                            color: theme.gridColor
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Amount ($)',
                            color: theme.mutedColor
                        },
                        ticks: {
                            color: theme.mutedColor,
                            callback: function (value: any) {
                                return '$' + value.toLocaleString();
                            }
                        },
                        grid: {
                            color: theme.gridColor
                        }
                    }
                },
                interaction: {
                    mode: 'nearest' as const,
                    axis: 'x' as const,
                    intersect: false
                }
            };
        },

        getHistoricalData(this: ProjectionsComponentInstance): MonthlyData[] {
            const historicalData: MonthlyData[] = [];
            const currentDate = new Date();
            const currentYear = currentDate.getFullYear();
            const currentMonth = currentDate.getMonth();

            // Get last 12 months including current month (from 11 months ago to current month)
            for (let i = 11; i >= 0; i--) {
                // Calculate the month: current month - i (so i=11 is 11 months ago, i=0 is current month)
                const targetMonth = currentMonth - i;
                let year = currentYear;
                let month = targetMonth;

                // Handle year rollover for months in previous year
                if (targetMonth < 0) {
                    year = currentYear - 1;
                    month = 12 + targetMonth; // e.g., -1 becomes 11 (December)
                }

                const date = new Date(year, month, 1);
                const monthKey = date.toISOString().substring(0, 7); // YYYY-MM format

                let filteredTransactions = this.transactions;
                if (this.selectedAccount !== 'all') {
                    filteredTransactions = this.transactions.filter(
                        (t: Transaction) => t.account_id === this.selectedAccount
                    );
                }

                const monthTransactions = filteredTransactions.filter((t: Transaction) => {
                    const transactionDate = new Date(t.date);
                    return transactionDate.getFullYear() === year &&
                        transactionDate.getMonth() === month;
                });

                const income = monthTransactions
                    .filter((t: Transaction) => t.transaction_type === 'Income')
                    .reduce((sum: number, t: Transaction) => sum + t.total, 0);

                const expenses = Math.abs(monthTransactions
                    .filter((t: Transaction) => t.transaction_type === 'Expense')
                    .reduce((sum: number, t: Transaction) => sum + t.total, 0));

                const balance = income - expenses;

                // Format month label - highlight current month
                const monthLabel = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
                const isCurrentMonth = year === currentYear && month === currentMonth;

                historicalData.push({
                    month: monthLabel,
                    income,
                    expenses,
                    balance,
                    isProjected: false
                });
            }

            return historicalData;
        },

        generateChartData(this: ProjectionsComponentInstance) {
            const labels = this.monthlyData.map(d => d.month);

            const datasets: any[] = [];

            // Income line (only actual data)
            const incomeData = this.monthlyData.map(d => d.income);
            datasets.push({
                label: 'Income',
                data: incomeData,
                borderColor: '#4CAF50',
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6
            });

            // Expenses line (only actual data)
            const expensesData = this.monthlyData.map(d => d.expenses);
            datasets.push({
                label: 'Expenses',
                data: expensesData,
                borderColor: '#F44336',
                backgroundColor: 'rgba(244, 67, 54, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6
            });

            // Balance line (only actual data)
            const balanceData = this.monthlyData.map(d => d.balance);
            datasets.push({
                label: 'Balance',
                data: balanceData,
                borderColor: '#2196F3',
                backgroundColor: 'rgba(33, 150, 243, 0.1)',
                borderWidth: 3,
                fill: false,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6
            });

            this.chartData = {
                labels,
                datasets
            };
            this.chartOptions = this.buildChartOptions();
        }
    }
}
</script>

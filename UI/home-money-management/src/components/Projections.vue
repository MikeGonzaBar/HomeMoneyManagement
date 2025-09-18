<template>
    <div class="projections-container">
        <!-- Header Section -->
        <div class="projections-header">
            <div class="header-content">
                <v-icon color="primary" class="me-2">mdi-chart-line</v-icon>
                <span class="text-h5 font-weight-bold">Financial Projections</span>
            </div>
            <p class="text-subtitle-1 text-grey-darken-1 mb-0">Predict your financial future based on historical data
            </p>
        </div>

        <!-- Controls Section -->
        <div class="controls-section">
            <v-row>
                <v-col cols="12" md="4">
                    <v-select v-model="selectedAccount" :items="accountOptions" label="Account Filter"
                        variant="outlined" rounded="lg" prepend-inner-icon="mdi-account"
                        @update:model-value="updateProjections"></v-select>
                </v-col>
                <v-col cols="12" md="4">
                    <v-select v-model="projectionPeriod" :items="periodOptions" label="Projection Period"
                        variant="outlined" rounded="lg" prepend-inner-icon="mdi-calendar-range"
                        @update:model-value="updateProjections"></v-select>
                </v-col>
                <v-col cols="12" md="4">
                    <v-btn color="primary" variant="outlined" rounded="lg" @click="refreshProjections"
                        :loading="isLoading">
                        <v-icon left>mdi-refresh</v-icon>
                        Refresh
                    </v-btn>
                </v-col>
            </v-row>
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
                            <h3 class="text-h5 font-weight-bold budget-text-gradient mb-0">Projection Chart</h3>
                            <p class="text-caption text-grey-darken-1 mb-0">Historical data and future projections</p>
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
                        <span class="legend-text">Balance</span>
                    </div>
                </v-col>
            </v-row>
            <v-row class="mt-2">
                <v-col cols="12">
                    <div class="explanation-text">
                        <v-icon size="16" class="me-2">mdi-information-outline</v-icon>
                        <span>Solid lines represent current data, dotted lines represent projected data</span>
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
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(76, 175, 80, 0.1);
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
    color: #2E7D32;
}

.controls-section {
    margin-bottom: 32px;
}

.chart-section {
    margin-bottom: 24px;
}

.projections-card {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
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
    color: #666;
}

.explanation-text {
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666;
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
    projectionPeriod: string;
    isLoading: boolean;
    chartData: any;
    chartOptions: any;
    accountOptions: any[];
    periodOptions: any[];
    monthlyData: MonthlyData[];
    updateProjections(): void;
    refreshProjections(): void;
    calculateProjections(): void;
    generateChartData(): void;
    getHistoricalData(): MonthlyData[];
    calculateProjectedData(): MonthlyData[];
    calculateGrowthRate(values: number[]): number;
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
    data: (): Partial<ProjectionsComponentInstance> => ({
        selectedAccount: 'all',
        projectionPeriod: '3months',
        isLoading: false,
        monthlyData: [],
        accountOptions: [
            { title: 'All Accounts', value: 'all' }
        ],
        periodOptions: [
            { title: '3 Months', value: '3months' },
            { title: '6 Months', value: '6months' },
            { title: '1 Year', value: '1year' }
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
                    mode: 'index',
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
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    }),
    mounted() {
        this.initializeAccountOptions();
        this.calculateProjections();
    },
    watch: {
        transactions: {
            handler: 'calculateProjections',
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

        updateProjections(this: ProjectionsComponentInstance) {
            this.calculateProjections();
        },

        refreshProjections(this: ProjectionsComponentInstance) {
            this.isLoading = true;
            setTimeout(() => {
                this.calculateProjections();
                this.isLoading = false;
            }, 1000);
        },

        calculateProjections(this: ProjectionsComponentInstance) {
            this.monthlyData = [
                ...this.getHistoricalData(),
                ...this.calculateProjectedData()
            ];
            this.generateChartData();
        },

        getHistoricalData(this: ProjectionsComponentInstance): MonthlyData[] {
            const historicalData: MonthlyData[] = [];
            const currentDate = new Date();

            // Get last 9 months of data
            for (let i = 8; i >= 0; i--) {
                const date = new Date(currentDate.getFullYear(), currentDate.getMonth() - i, 1);
                const monthKey = date.toISOString().substring(0, 7); // YYYY-MM format

                let filteredTransactions = this.transactions;
                if (this.selectedAccount !== 'all') {
                    filteredTransactions = this.transactions.filter(
                        (t: Transaction) => t.account_id === this.selectedAccount
                    );
                }

                const monthTransactions = filteredTransactions.filter((t: Transaction) => {
                    const transactionDate = new Date(t.date);
                    return transactionDate.getFullYear() === date.getFullYear() &&
                        transactionDate.getMonth() === date.getMonth();
                });

                const income = monthTransactions
                    .filter((t: Transaction) => t.transaction_type === 'Income')
                    .reduce((sum: number, t: Transaction) => sum + t.total, 0);

                const expenses = Math.abs(monthTransactions
                    .filter((t: Transaction) => t.transaction_type === 'Expense')
                    .reduce((sum: number, t: Transaction) => sum + t.total, 0));

                const balance = income - expenses;

                historicalData.push({
                    month: date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
                    income,
                    expenses,
                    balance,
                    isProjected: false
                });
            }

            return historicalData;
        },

        calculateProjectedData(this: ProjectionsComponentInstance): MonthlyData[] {
            const projectedData: MonthlyData[] = [];
            const currentDate = new Date();

            // Get the last month's data as starting point
            const historicalData = this.getHistoricalData();
            if (historicalData.length < 1) return projectedData;

            const lastMonth = historicalData[historicalData.length - 1];
            if (!lastMonth) return projectedData;

            // Project next 3 months
            const monthsToProject = this.projectionPeriod === '3months' ? 3 :
                this.projectionPeriod === '6months' ? 6 : 12;

            let runningBalance = lastMonth.balance;

            for (let i = 1; i <= monthsToProject; i++) {
                const date = new Date(currentDate.getFullYear(), currentDate.getMonth() + i, 1);

                // For projections, keep income and expenses the same as the last known values
                const projectedIncome = lastMonth.income;
                const projectedExpenses = lastMonth.expenses;

                // Calculate balance based on the difference
                const monthlyDifference = projectedIncome - projectedExpenses;
                runningBalance += monthlyDifference;

                projectedData.push({
                    month: date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
                    income: projectedIncome,
                    expenses: projectedExpenses,
                    balance: Math.round(runningBalance),
                    isProjected: true
                });
            }

            return projectedData;
        },

        calculateGrowthRate(this: ProjectionsComponentInstance, values: number[]): number {
            if (values.length < 2) return 0;

            const firstValue = values[0];
            const lastValue = values[values.length - 1];

            if (firstValue === undefined || lastValue === undefined || firstValue === 0) return 0;

            return (lastValue - firstValue) / firstValue / (values.length - 1);
        },

        generateChartData(this: ProjectionsComponentInstance) {
            const labels = this.monthlyData.map(d => d.month);

            // Find the index where projected data starts
            const projectedStartIndex = this.monthlyData.findIndex(d => d.isProjected);

            const datasets: any[] = [];

            // Income line (solid for historical, dotted for projected)
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
                pointHoverRadius: 6,
                segment: {
                    borderDash: (ctx: any) => {
                        // Use dotted line for projected data (after projectedStartIndex)
                        return ctx.p1DataIndex >= projectedStartIndex ? [5, 5] : [];
                    }
                }
            });

            // Expenses line (solid for historical, dotted for projected)
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
                pointHoverRadius: 6,
                segment: {
                    borderDash: (ctx: any) => {
                        // Use dotted line for projected data (after projectedStartIndex)
                        return ctx.p1DataIndex >= projectedStartIndex ? [5, 5] : [];
                    }
                }
            });

            // Balance line (solid for historical, dotted for projected)
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
                pointHoverRadius: 6,
                segment: {
                    borderDash: (ctx: any) => {
                        // Use dotted line for projected data (after projectedStartIndex)
                        return ctx.p1DataIndex >= projectedStartIndex ? [5, 5] : [];
                    }
                }
            });

            this.chartData = {
                labels,
                datasets
            };
        }
    }
}
</script>

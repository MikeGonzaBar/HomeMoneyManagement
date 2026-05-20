<template>
    <div class="chart-container">
        <div class="chart-section">
            <div class="chart-header">
                <h2 class="chart-title">Income</h2>
                <p class="chart-subtitle">Visual breakdown of your income sources</p>
            </div>
            <div class="chart-wrapper">
                <Pie :data="(this as any).incomeChartData" :options="(this as any).incomeOptions" />
            </div>
        </div>

        <div class="chart-section">
            <div class="chart-header">
                <h2 class="chart-title">Expense</h2>
                <p class="chart-subtitle">Visual breakdown of your expenses</p>
            </div>
            <div class="chart-wrapper">
                <Pie :data="(this as any).expenseChartData" :options="(this as any).expenseOptions" />
            </div>
        </div>
    </div>
</template>

<style scoped>
.chart-container {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    width: 100%;
}

.chart-section {
    flex: 1;
    min-width: 240px;
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(76, 175, 80, 0.1);
}

.chart-header {
    text-align: center;
    margin-bottom: 12px;
}

.chart-title {
    color: #2E7D32;
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 4px;
}

.chart-subtitle {
    color: #666;
    font-size: 0.8rem;
    margin: 0;
}

.chart-wrapper {
    position: relative;
    height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Responsive behavior */
@media (max-width: 1200px) {
    .chart-section {
        min-width: 220px;
    }

    .chart-wrapper {
        height: 180px;
    }
}

@media (max-width: 900px) {
    .chart-container {
        flex-direction: column;
    }

    .chart-section {
        min-width: 100%;
        width: 100%;
    }

    .chart-wrapper {
        height: 200px;
    }
}

@media (max-width: 600px) {
    .chart-section {
        padding: 12px;
    }

    .chart-wrapper {
        height: 180px;
    }

    .chart-title {
        font-size: 1rem;
    }
}
</style>

<script lang="ts">
// import * as Vue from 'vue';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Pie } from 'vue-chartjs'
import { getCategoryColor } from '@/constants/categoryStyles'
ChartJS.register(ArcElement, Tooltip, Legend)
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

interface PieChartComponentInstance {
    transactions: Transaction[];
    expenseChartData: any;
    incomeChartData: any;
    incomeOptions: any;
    expenseOptions: any;
    prepareChartData(): void;
    reduction(transactionType: string): { [key: string]: number };
    prepareExpenseChartData(): void;
    prepareIncomeChartData(): void;
}

export default {
    name: 'TransactionPieChart',
    components: {
        Pie
    },
    props: {
        transactions: {
            type: Array as () => Transaction[],
            required: true
        }
    },
    data: () => ({
        expenseChartData: {
            labels: [] as string[],
            datasets: [{
                data: [] as number[],
                backgroundColor: [] as string[],
            }]
        },
        incomeChartData: {
            labels: [] as string[],
            datasets: [{
                data: [] as number[],
                backgroundColor: [] as string[],
            }]
        },
        incomeOptions: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 10,
                        usePointStyle: true,
                        font: {
                            size: 10
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context: { dataset: { data: any[]; }; dataIndex: any; label: any; }) {
                            const total = context.dataset.data.reduce((acc, value) => acc + value, 0);
                            const value = context.dataset.data[Number(context.dataIndex)];
                            const percentage = value / total * 100;
                            return `${context.label}: $${value.toFixed(2)} (${percentage.toFixed(1)}%)`;
                        }
                    }
                }
            }
        },
        expenseOptions: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 10,
                        usePointStyle: true,
                        font: {
                            size: 10
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context: { dataset: { data: any[]; }; dataIndex: any; label: any; }) {
                            const total = context.dataset.data.reduce((acc, value) => acc + value, 0);
                            const value = context.dataset.data[Number(context.dataIndex)];
                            const percentage = value / total * 100;
                            return `${context.label}: $${value.toFixed(2)} (${percentage.toFixed(1)}%)`;
                        }
                    }
                }
            }
        }
    }),
    mounted() {
        (this as any).prepareChartData();
    },
    watch: {
        transactions: {
            handler: 'prepareChartData',
            deep: true,
        },
    },
    methods: {
        prepareChartData(this: PieChartComponentInstance) {
            this.prepareExpenseChartData();
            this.prepareIncomeChartData();
        },
        reduction(this: PieChartComponentInstance, transactionType: string) {
            return this.transactions.reduce((acc: { [key: string]: number }, transaction: Transaction) => {
                if (transaction.transaction_type === transactionType) {
                    const category = transaction.category;
                    if (!acc[category]) {
                        acc[category] = 0;
                    }
                    acc[category] += transaction.total;
                }
                return acc;
            }, {});
        },
        prepareExpenseChartData(this: PieChartComponentInstance) {
            const dataByType = this.reduction('Expense');

            const labels = Object.keys(dataByType);
            const data = Object.values(dataByType);
            const backgroundColor = labels.map((label: string) => getCategoryColor(label));

            this.expenseChartData = {
                labels: labels,
                datasets: [
                    {
                        data: data,
                        backgroundColor: backgroundColor,
                    }
                ]
            };
        },
        prepareIncomeChartData(this: PieChartComponentInstance) {
            const dataByType = this.reduction('Income');
            const labels = Object.keys(dataByType);
            const data = Object.values(dataByType);
            const backgroundColor = labels.map((label: string) => getCategoryColor(label));

            this.incomeChartData = {
                labels: labels,
                datasets: [
                    {
                        data: data,
                        backgroundColor: backgroundColor,
                    }
                ]
            };
        },
    }
}
</script>
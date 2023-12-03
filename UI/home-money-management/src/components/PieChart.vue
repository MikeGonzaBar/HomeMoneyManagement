<template>
    <div class="chart-container">
        <div class="chart">
            <h2>Income</h2>
            <Pie :data="incomeChartData" :options="options" />
        </div>
        <div class="chart">
            <h2>Expense</h2>
            <Pie :data="expenseChartData" :options="options" />
        </div>
    </div>
</template>
  
<style scoped>
.chart-container {
    display: flex;
    justify-content: space-between;
}

.chart {
    width: 45%;
}
</style>
  
<script lang="ts">
import { defineComponent, ref, watch, onMounted } from 'vue';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Pie } from 'vue-chartjs'
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

export default defineComponent({
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
        options: {
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function (context: { dataset: { data: any[]; }; dataIndex: any; label: any; }) {
                            const total = context.dataset.data.reduce((acc, value) => acc + value, 0);
                            const value = context.dataset.data[Number(context.dataIndex)];
                            const percentage = value / total * 100;
                            return `${context.label}: ${value} (${percentage.toFixed(2)}%)`;
                        }
                    },

                }
            }
        }
    }),
    mounted() {
        this.prepareChartData();
    },
    watch: {
        transactions: {
            handler: 'prepareChartData',
            deep: true,
        },
    },
    methods: {
        prepareChartData() {
            this.prepareExpenseChartData();
            this.prepareIncomeChartData();
        },
        reduction(transactionType: string) {
            return this.transactions.reduce((acc: { [key: string]: number }, transaction) => {
                if (transaction.transaction_type === transactionType) {
                    if (!acc[transaction.category]) {
                        acc[transaction.category] = 0;
                    }
                    acc[transaction.category] += transaction.total;
                }
                return acc;
            }, {});
        },
        prepareExpenseChartData() {
            const dataByType = this.reduction('Expense');

            const labels = Object.keys(dataByType);
            const data = Object.values(dataByType);
            const backgroundColor = labels.map(label => this.stringToColor(label));

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
        prepareIncomeChartData() {
            const dataByType = this.reduction('Income');
            const labels = Object.keys(dataByType);
            const data = Object.values(dataByType);
            const backgroundColor = labels.map(label => this.stringToColor(label));

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
        stringToColor(str: string) {
            let hash = 0;
            for (let i = 0; i < str.length; i++) {
                hash = str.charCodeAt(i) + ((hash << 5) - hash);
            }
            let color = '#';
            for (let i = 0; i < 3; i++) {
                let value = (hash >> (i * 8)) & 0xFF;
                value = Math.floor(value * 0.5) + 128; // lighten the color by reducing the value and adding a base
                color += ('00' + value.toString(16)).substr(-2);
            }
            return color;
        },
    },
});
</script>
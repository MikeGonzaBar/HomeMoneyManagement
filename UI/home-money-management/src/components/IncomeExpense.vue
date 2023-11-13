<template>
    <div>
        <div class="income-square">
            <p class="square-text">Income</p>
            <p class="square-value">{{ income }}</p>
        </div>
        <div class="expense-square">
            <p class="square-text">Expense</p>
            <p class="square-value">{{ expense }}</p>
        </div>
    </div>
</template>
  
<style scoped>
.income-square {
    background-color: green;
    border-radius: 10px;
    padding: 10px;
    display: inline-block;
    margin-right: 10px;
}

.expense-square {
    background-color: red;
    border-radius: 10px;
    padding: 10px;
    display: inline-block;
}

.square-text {
    color: white;
    font-weight: bold;
    margin: 0;
}

.square-value {
    color: white;
    font-size: 24px;
    margin: 0;
}
</style>

<script lang="ts">
import { defineComponent } from 'vue';
interface Transaction {
    id: number;
    transaction_type: string,
    category: string,
    date: string,
    title: string,
    total: number,
    owner_id: number,
    account_id: number,
}
interface Data {
    income: number;
    expense: number;
}
export default defineComponent({
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
            this.income = this.transactions.filter((transaction) => transaction.transaction_type === 'Income').reduce((acc, transaction) => acc + transaction.total, 0);
            this.expense = this.transactions.filter((transaction) => transaction.transaction_type === 'Expense').reduce((acc, transaction) => acc + transaction.total, 0);
        },
    },

});
</script>
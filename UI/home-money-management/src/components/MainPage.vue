<template >
    <div class="main-page">
        <div class="user-info">
            <h1>Bienvenido {{ userData.user.first_name }} </h1>
        </div>
        <div class="account-carousel">
            <p>
                <AccountsCarousel :userData="userData" @accountSelected="handleAccountSelected"
                    @allAccountSelected="handleAllAccountSelected" />
            </p>
        </div>
        <v-row class="month-income-expense">
            <v-col cols="6" md="6">
                <div class="month-year">
                    <DatePicker :userData="userData" @dateSelected="handleDatePicked" />
                </div>
            </v-col>
            <v-col cols="12" md="6">
                <div class="income-expense">
                    <IncomeExpense :transactions="transactions" />
                </div>
            </v-col>
        </v-row>
        <v-row class="data-pie-chart">
            <v-col cols="6" md="6">
                <div class="data-table">
                    <TableData :transactions="transactions" />
                </div>
            </v-col>
            <v-col cols="12" md="6">
                <div class="pie-chart">
                    <PieChart :transactions="transactions" />
                </div>
            </v-col>
        </v-row>
    </div>
</template>
  
<script lang="ts">

import AccountsCarousel from '@/components/AccountsCarousel.vue'
import DatePicker from '@/components/DatePicker.vue';
import IncomeExpense from '@/components/IncomeExpense.vue';
import TableData from '@/components/TableData.vue';
import PieChart from '@/components/PieChart.vue';
import axios from 'axios';
import { defineComponent } from 'vue';
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
    owner_id: number,
    account_id: number,
}
interface Data {
    accountSelected: null | Account;
    month: number;
    year: number;
    transactions: Transaction[];
}
export default defineComponent({
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
        transactions: []

    }),
    mounted() {
        const currentDate = new Date();
        this.month = currentDate.getMonth();
        this.year = currentDate.getFullYear();
        console.log('ON MAIN PAGE MOUNTED');
        this.getTransactions();
    },
    components: { AccountsCarousel, DatePicker, IncomeExpense, TableData, PieChart },
    methods: {
        handleDatePicked(date: DateObject) {
            console.log('Recieved date from date picker');
            this.month = date.month;
            this.year = date.year;
            this.getTransactions();
        },
        handleAllAccountSelected(acc: Object) {
            console.log('RECIEVED ACCOUNT SELECTED: ALL');
        },
        handleAccountSelected(acc: Account) {
            console.log('RECIEVED ACCOUNT SELECTED');
            this.accountSelected = acc;
        },
        getTransactions() {
            console.log("GETTING TRANSACTIONS");
            console.log('MONTH', this.month);
            console.log('YEAR', this.year);
            if (this.accountSelected === null) {
                console.log('NO ACCOUNT SELECTED');
                axios.get(`http://localhost:8000/transactions/retrieve/${this.userData.user.id}/0/${this.month + 1}/${this.year}`)
                    .then((response) => {
                        console.log('RESPONSE', response.data);
                        this.transactions = response.data;
                    })
                    .catch((error) => {
                        console.log('ERROR', error);
                    })
            }

        }
    }
});
</script>
  
<style scoped>
.main-page {
    display: flex;
    flex-direction: column;
    padding: 0 50px;
}

.user-info {
    flex: 0 0 auto;
    background-color: #F44336;
}

.account-carousel {
    flex: 0 0 auto;
    background-color: #E91E63;
}

.month-income-expense {
    flex: 1 0 auto;
}

.month-year {
    background-color: #9C27B0;
}

.income-expense {
    background-color: #673AB7;
}

.data-pie-chart {
    flex: 1 0 auto;
}

.data-table {
    background-color: #2196F3;
}

.pie-chart {
    background-color: #009688;
}
</style>
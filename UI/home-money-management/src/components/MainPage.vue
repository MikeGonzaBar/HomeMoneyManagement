<template >
    <div class="main-page">
        <div class="user-info">
            <h1>Bienvenido {{ userData.user.first_name }} </h1>
            <v-btn @click="triggerLogOut" class="logout-button">
                <v-icon left>mdi-logout</v-icon>
                Logout
            </v-btn>
        </div>
        <div class="account-carousel">
            <p>
                <AccountsCarousel ref="accountsCarousel" :userData="userData" @accountSelected="handleAccountSelected"
                    @allAccountSelected="handleAllAccountSelected" @accountsModified="handleAccountsModified" />
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
                    <TableData :transactions="transactions" :userData="userData" :accounts="accounts"
                        @updateAccounts="handleUpdateAccountsMethod" @updateIncomeExpense="handleUpdateIncomeExpense" />
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
        transactions: [],
        accounts: []

    }),
    mounted() {
        const currentDate = new Date();
        this.month = currentDate.getMonth();
        this.year = currentDate.getFullYear();
        this.getTransactions();
    },
    components: { AccountsCarousel, DatePicker, IncomeExpense, TableData, PieChart },
    methods: {
        triggerLogOut() {
            localStorage.removeItem('money_management_user');
            location.reload();
        },
        handleUpdateIncomeExpense() {
            this.getTransactions();
        },
        handleUpdateAccountsMethod() {
            (this.$refs.accountsCarousel as AccountsCarousel).accountTotalUpdated();
        },
        handleDatePicked(date: DateObject) {
            this.month = date.month;
            this.year = date.year;
            this.getTransactions();
        },
        handleAllAccountSelected(acc: Object) {
            this.accountSelected = null;
        },
        handleAccountSelected(acc: Account) {
            this.accountSelected = acc;
            this.getTransactions();
        },
        handleAccountsModified(accs: Array<Account>) {
            this.accounts = accs;
        },
        getTransactions() {
            if (this.accountSelected === null) {
                axios.get(`http://localhost:8000/transactions/retrieve/${this.userData.user.id}/0/${this.month + 1}/${this.year}`)
                    .then((response) => {
                        this.transactions = response.data;
                    })
                    .catch((error) => {
                        console.log('ERROR', error);
                    })
            }
            else {
                axios.get(`http://localhost:8000/transactions/retrieve/${this.userData.user.id}/${this.accountSelected.id}/${this.month + 1}/${this.year}`)
                    .then((response) => {
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
    color: lightgray;
    background-color: #1d1d2893;
    /* light gray */
    box-shadow: 0px 4px 8px 0px rgba(0, 0, 0, 0.0);
    display: flex;
    justify-content: space-between;
    align-items: center;
    /* shadow effect */
}

.logout-button {
    padding: 10px;
    background-color: #f8f9fa;
    border: none;
    cursor: pointer;
}

.account-carousel {
    flex: 0 0 auto;
    background-color: #363542ac;
    /* almost white gray */
    box-shadow: 0px 4px 8px 0px rgba(0, 0, 0, 0.0);
    /* shadow effect */
}

.month-income-expense {
    flex: 1 0 auto;

}



.data-pie-chart {
    flex: 1 0 auto;

}


.pie-chart {
    background-color: #3635420e;
    border-radius: 4px;
    padding: 10px;
}
</style>
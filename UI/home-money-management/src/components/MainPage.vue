<template >
    <div class="main-page">
        <div class="user-info">
            <h1>Bienvenido {{ userData.user.first_name }} </h1>
        </div>
        <div class="account-carousel">
            <p>
                <AccountsCarousel :userData="userData" />
            </p>
        </div>
        <v-row class="month-income-expense">
            <v-col cols="6" md="6">
                <div class="month-year">
                    <p>
                        HERE WILL BE THE MONTH AND YEAR
                    </p>
                </div>
            </v-col>
            <v-col cols="12" md="6">
                <div class="income-expense">
                    <p>
                        HERE WILL BE THE INCOME AND EXPENSE
                    </p>
                </div>
            </v-col>
        </v-row>
        <v-row class="data-pie-chart">
            <v-col cols="6" md="6">
                <div class="data-table">
                    <p>
                        HERE WILL BE THE TABLE WITH DATA
                    </p>
                </div>
            </v-col>
            <v-col cols="12" md="6">
                <div class="pie-chart">
                    <p>
                        HERE WILL BE THE PIE CHART
                    </p>
                </div>
            </v-col>
        </v-row>
    </div>
</template>
  
<script lang="ts">

import AccountsCarousel from '@/components/AccountsCarousel.vue'
export default {
    name: 'MainPage',
    props: {
        userData: {
            type: Object,
            required: true
        }
    },
    components: { AccountsCarousel }
};
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
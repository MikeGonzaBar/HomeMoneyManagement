<template>
    <div>
        <select class="picker" v-model="selectedMonth" @change="emitDate">
            <option v-for="(month, index) in months" :key="index" :value="index">{{ month }}</option>
        </select>
        <select class="picker" v-model="selectedYear" @change="emitDate">
            <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
        </select>
    </div>
</template>

<script lang="ts">
export default {
    name: 'DatePicker',
    props: {
        userData: {
            type: Object,
            required: true
        }
    },
    data() {
        const currentDate = new Date();
        return {
            selectedMonth: currentDate.getMonth(),
            selectedYear: currentDate.getFullYear(),
            months: [
                'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
            ],
            years: [] as number[],
        }
    },
    mounted() {
        const currentYear = new Date().getFullYear()
        for (let i: number = currentYear - 10; i <= currentYear + 10; i++) {
            this.years.push(i);
        }
    },
    emits: ['dateSelected'],
    methods: {
        emitDate() {
            this.$emit('dateSelected', {
                month: this.selectedMonth,
                year: this.selectedYear
            })
        }
    }
}
</script>

<style scoped>
select {
    appearance: none;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 8px 24px 8px 8px;
    background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23333"><path d="M7 10l5 5 5-5z"/></svg>') no-repeat right center / 16px 16px;
    cursor: pointer;
}

.picker {
    background-color: #363542ac;
    /* almost white gray */
    box-shadow: 0px 4px 8px 0px rgba(0, 0, 0, 0.0);
}
</style>
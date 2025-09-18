<template>
    <div class="date-picker-container">
        <!-- Modern Month/Year Selector -->
        <div class="date-selector-card">
            <div class="selector-header">
                <v-icon color="primary" class="me-2">mdi-calendar-range</v-icon>
                <span class="text-subtitle-1 font-weight-medium">Select Period</span>
            </div>

            <div class="selectors-row">
                <v-select v-model="(this as any).selectedMonth" :items="(this as any).monthItems" label="Month"
                    variant="outlined" rounded="lg" prepend-inner-icon="mdi-calendar-month" class="month-selector"
                    @update:model-value="(this as any).emitDate">
                </v-select>

                <v-select v-model="(this as any).selectedYear" :items="(this as any).years" label="Year"
                    variant="outlined" rounded="lg" prepend-inner-icon="mdi-calendar" class="year-selector"
                    @update:model-value="(this as any).emitDate">
                </v-select>
            </div>

            <!-- Quick Action Buttons -->
            <div class="quick-actions">
                <v-btn variant="outlined" size="small" @click="(this as any).setCurrentMonth" class="quick-btn">
                    <v-icon left size="small">mdi-calendar-today</v-icon>
                    This Month
                </v-btn>
                <v-btn variant="outlined" size="small" @click="(this as any).setPreviousMonth" class="quick-btn">
                    <v-icon left size="small">mdi-chevron-left</v-icon>
                    Previous
                </v-btn>
                <v-btn variant="outlined" size="small" @click="(this as any).setNextMonth" class="quick-btn">
                    <v-icon right size="small">mdi-chevron-right</v-icon>
                    Next
                </v-btn>
            </div>
        </div>
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
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ],
            years: [] as number[],
        }
    },
    computed: {
        monthItems() {
            return (this as any).months.map((month: string, index: number) => ({
                title: month,
                value: index
            }));
        }
    },
    mounted() {
        const currentYear = new Date().getFullYear()
        for (let i: number = currentYear - 10; i <= currentYear + 10; i++) {
            (this as any).years.push(i);
        }
    },
    emits: ['dateSelected'],
    methods: {
        emitDate() {
            (this as any).$emit('dateSelected', {
                month: (this as any).selectedMonth,
                year: (this as any).selectedYear
            })
        },
        setCurrentMonth() {
            const currentDate = new Date();
            (this as any).selectedMonth = currentDate.getMonth();
            (this as any).selectedYear = currentDate.getFullYear();
            (this as any).emitDate();
        },
        setPreviousMonth() {
            if ((this as any).selectedMonth === 0) {
                (this as any).selectedMonth = 11;
                (this as any).selectedYear -= 1;
            } else {
                (this as any).selectedMonth -= 1;
            }
            (this as any).emitDate();
        },
        setNextMonth() {
            if ((this as any).selectedMonth === 11) {
                (this as any).selectedMonth = 0;
                (this as any).selectedYear += 1;
            } else {
                (this as any).selectedMonth += 1;
            }
            (this as any).emitDate();
        }
    }
}
</script>

<style scoped>
.date-picker-container {
    width: 100%;
}

.date-selector-card {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(76, 175, 80, 0.1);
}

.selector-header {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
    color: #2E7D32;
}

.selectors-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 16px;
}

.quick-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.quick-btn {
    border-radius: 8px;
    text-transform: none;
    font-size: 0.8rem;
    min-width: auto;
    padding: 0 12px;
}

.quick-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
}

/* Custom styling for v-select components */
:deep(.v-field) {
    border-radius: 12px;
    transition: all 0.3s ease;
}

:deep(.v-field--focused .v-field__outline) {
    border-color: #4CAF50;
    border-width: 2px;
}

:deep(.v-field:hover) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
}

:deep(.v-field--focused) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
}

/* Custom dropdown styling */
:deep(.v-list) {
    border-radius: 12px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

:deep(.v-list-item:hover) {
    background: rgba(76, 175, 80, 0.1);
}

:deep(.v-list-item--active) {
    background: rgba(76, 175, 80, 0.2);
    color: #2E7D32;
}

/* Responsive design */
@media (max-width: 768px) {
    .selectors-row {
        grid-template-columns: 1fr;
        gap: 8px;
    }

    .quick-actions {
        justify-content: center;
    }

    .quick-btn {
        flex: 1;
        min-width: 0;
    }
}
</style>
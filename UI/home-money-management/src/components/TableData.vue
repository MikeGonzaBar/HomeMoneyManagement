<template>
    <div class="transactions-container">
        <v-data-table :headers="(this as any).currentHeaders" :items="(this as any).internalTransactions"
            :sort-by="[{ key: 'date', order: 'desc' }]" class="modern-data-table elevation-0" :items-per-page="10"
            :loading="false">
            <template v-slot:top>
                <div class="table-header">
                    <div class="d-flex align-center justify-end pa-4">
                        <v-btn color="primary" class="smooth-transition hover-lift" @click="openCreate"
                            :prepend-icon="$vuetify.display.smAndUp ? 'mdi-plus' : undefined"
                            :size="$vuetify.display.mobile ? 'default' : 'default'" rounded="lg">
                            <span :class="$vuetify.display.mobile ? 'd-none d-sm-inline' : ''">New
                                Transaction</span>
                            <span :class="$vuetify.display.mobile ? 'd-inline d-sm-none' : 'd-none'">+
                                New</span>
                        </v-btn>
                        <TransactionDialog ref="txDialog" :accounts="accounts"
                            :username="userData?.user?.username || ''" @saved="onSaved" @deleted="onDeleted" />
                    </div>
                </div>
            </template>

            <!-- Custom row styling -->
            <template v-slot:item.transaction_type="{ item }">
                <v-chip :color="getTypeColor(asTransaction(item).transaction_type)" size="small" variant="tonal"
                    class="font-weight-medium">
                    <v-icon :icon="getTypeIcon(asTransaction(item).transaction_type)"
                        size="16" class="me-1"></v-icon>
                    {{ asTransaction(item).transaction_type }}
                </v-chip>
            </template>

            <template v-slot:item.total="{ item }">
                <span class="font-weight-bold"
                    :class="asTransaction(item).transaction_type === 'Income' ? 'text-success' : asTransaction(item).transaction_type === 'Expense' ? 'text-error' : 'text-grey-darken-1'">
                    {{ asTransaction(item).transaction_type === 'Income' ? '+' : asTransaction(item).transaction_type === 'Expense' ? '-' : '' }}${{ Math.abs(asTransaction(item).total).toLocaleString() }}
                </span>
            </template>

            <template v-slot:item.category="{ item }">
                <div class="d-flex align-center">
                    <v-avatar :color="getCategoryStyle(asTransaction(item).category).color" size="28" rounded class="me-2">
                        <v-icon :icon="getCategoryStyle(asTransaction(item).category).icon" size="14" color="white"></v-icon>
                    </v-avatar>
                    <span class="text-body-2">{{ asTransaction(item).category }}</span>
                </div>
            </template>

            <template v-slot:item.date="{ item }">
                <span class="text-body-2">{{ formatDate(asTransaction(item).date) }}</span>
            </template>

            <template v-slot:item.actions="{ item }">
                <div class="d-flex align-center">
                    <v-btn icon size="small" variant="text" color="primary" @click="openEdit(asTransaction(item))" class="me-1">
                        <v-icon size="18">mdi-pencil</v-icon>
                    </v-btn>
                    <v-btn icon size="small" variant="text" color="error" @click="openDelete(asTransaction(item))">
                        <v-icon size="18">mdi-delete</v-icon>
                    </v-btn>
                </div>
            </template>

            <!-- Empty state -->
            <template v-slot:no-data>
                <div class="text-center pa-8">
                    <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-receipt</v-icon>
                    <h3 class="text-h6 text-grey-darken-1 mb-2">No transactions found</h3>
                    <p class="text-body-2 text-grey-darken-1 mb-4">Start by adding your first transaction</p>
                    <v-btn color="primary" @click="openCreate" rounded="lg">
                        <v-icon left>mdi-plus</v-icon>
                        Add Transaction
                    </v-btn>
                </div>
            </template>
        </v-data-table>
    </div>
</template>

<script lang="ts">
import { getCategoryStyle as getCategoryStyleUtil } from '@/constants/categoryStyles';
import { toMoneyNumber } from '@/services/money';
import { formatCalendarDate } from '@/services/calendarDate';
import TransactionDialog from '@/components/TransactionDialog.vue';

interface Transaction {
    id: number;
    transaction_type: string,
    category: string,
    date: string,
    title: string,
    total: number,
    owner_id: string,
    account_id: string,
    from_account_id?: string,
    to_account_id?: string,
}

interface Account {
    id: number;
    account_type: string;
    bank: string;
    total: number;
    account_name: string;
}

export default {
    name: 'TableData',
    components: { TransactionDialog },
    props: {
        transactions: {
            type: Array as () => Transaction[],
            required: true
        },
        userData: {
            type: Object as () => any,
            required: true
        },
        accounts: {
            type: Array as () => Account[],
            required: true
        }
    },
    data() {
        return {
            internalTransactions: [] as Transaction[],
            headers: [
                {
                    title: 'Transaction',
                    align: 'start',
                    sortable: false,
                    key: 'title',
                },
                { title: 'Type', key: 'transaction_type' },
                { title: 'Category', key: 'category' },
                { title: 'Date', key: 'date' },
                { title: 'Total', key: 'total' },
                { title: 'Actions', key: 'actions', sortable: false },
            ] as const,
            mobileHeaders: [
                {
                    title: 'Transaction',
                    align: 'start',
                    sortable: false,
                    key: 'title',
                },
                { title: 'Type', key: 'transaction_type' },
                { title: 'Total', key: 'total' },
                { title: 'Actions', key: 'actions', sortable: false },
            ] as const,
        }
    },

    computed: {
        currentHeaders(): any[] {
            return (this as any).$vuetify.display.mobile ? (this as any).mobileHeaders : (this as any).headers;
        },
    },
    watch: {
        transactions: {
            immediate: true,
            handler(newVal: Transaction[]) {
                (this as any).internalTransactions = []
                newVal.forEach((transaction: Transaction) => {
                    (this as any).internalTransactions.push({
                        ...transaction,
                        total: Math.abs(toMoneyNumber(transaction.total))
                    })
                })
            }
        },
    },

    emits: ['updateAccounts', 'updateIncomeExpense'],
    methods: {
        asTransaction(item: unknown): Transaction {
            return item as Transaction;
        },
        formatDate(dateString: string): string {
            return formatCalendarDate(dateString);
        },
        getCategoryStyle(category: string) {
            return getCategoryStyleUtil(category);
        },
        getTypeColor(type: string): string {
            if (type === 'Income') return 'success';
            if (type === 'Expense') return 'error';
            return 'info';
        },
        getTypeIcon(type: string): string {
            if (type === 'Income') return 'mdi-trending-up';
            if (type === 'Expense') return 'mdi-trending-down';
            return 'mdi-swap-horizontal';
        },

        openCreate() {
            (this as any).$refs.txDialog.openCreate();
        },
        openEdit(item: Transaction) {
            (this as any).$refs.txDialog.openEdit(item);
        },
        openDelete(item: Transaction) {
            (this as any).$refs.txDialog.openDelete(item);
        },
        onSaved(payload: { transaction: Transaction; isNew: boolean }) {
            const normalized = {
                ...payload.transaction,
                total: Math.abs(toMoneyNumber(payload.transaction.total)),
            };
            if (payload.isNew) {
                (this as any).internalTransactions.push(normalized);
            } else {
                const index = (this as any).internalTransactions.findIndex((t: Transaction) => t.id === normalized.id);
                if (index > -1) (this as any).internalTransactions.splice(index, 1, normalized);
            }
            (this as any).$emit('updateAccounts');
            (this as any).$emit('updateIncomeExpense');
        },
        onDeleted(payload: { id: number }) {
            const index = (this as any).internalTransactions.findIndex((t: Transaction) => t.id === payload.id);
            if (index > -1) (this as any).internalTransactions.splice(index, 1);
            (this as any).$emit('updateAccounts');
            (this as any).$emit('updateIncomeExpense');
        },
    }
}
</script>

<style scoped>
/* Modern Transactions Table */
.transactions-container {
    background: transparent;
}

.modern-data-table {
    background: transparent !important;
    border-radius: 16px;
    overflow: hidden;
}

.table-header {
    background: var(--bb-surface, #ffffff);
    border-bottom: 1px solid var(--bb-border-soft, #f3f4f6);
}

/* Modern dialog styling */
.modern-dialog {
    background: var(--bb-surface, #ffffff);
    border: 1px solid var(--bb-border-soft, #f3f4f6);
    box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14);
}

/* Data table custom styling */
:deep(.v-data-table) {
    background: transparent !important;
}

:deep(.v-data-table__wrapper) {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: none;
}

:deep(.v-data-table-header) {
    background: var(--bb-surface-soft, #f9fafb);
    border-bottom: 1px solid var(--bb-border-soft, #f3f4f6) !important;
}

:deep(thead),
:deep(thead tr),
:deep(.v-data-table__th) {
    background: var(--bb-surface-soft, #f9fafb) !important;
}

:deep(.v-data-table-footer) {
    border-top: 1px solid var(--bb-border-soft, #f3f4f6) !important;
    border-bottom: none !important;
}

:deep(.v-data-table) {
    border-bottom: none !important;
}

:deep(.v-data-table__wrapper) {
    border-bottom: none !important;
}

:deep(.v-data-table tbody) {
    border-bottom: none !important;
}

:deep(.v-data-table tbody tr:last-child) {
    border-bottom: none !important;
}

:deep(.v-data-table tbody tr:last-child td) {
    border-bottom: none !important;
}

:deep(.v-data-table__td:last-child) {
    border-bottom: none !important;
}

:deep(.v-data-table__tr:last-child) {
    border-bottom: none !important;
}

:deep(.v-data-table-header th) {
    font-weight: 600;
    color: var(--bb-text-muted, #6b7280);
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.5px;
}

:deep(.v-data-table__th) {
    border-bottom: 1px solid var(--bb-border-soft, #f3f4f6) !important;
    color: var(--bb-text-muted, #6b7280) !important;
}

:deep(.v-data-table__tr) {
    transition: all 0.2s ease;
}

:deep(.v-data-table__tr:hover) {
    background: var(--bb-row-hover, #f9fafb) !important;
    transform: none;
}

:deep(.v-data-table__tr:nth-child(even)) {
    background: var(--bb-surface, #ffffff) !important;
}

:deep(.v-data-table__tr:nth-child(odd)) {
    background: var(--bb-surface, #ffffff) !important;
}

:deep(.v-data-table__td) {
    border-bottom: 1px solid var(--bb-border-soft, #f3f4f6) !important;
    color: var(--bb-text-strong, #1f2937);
    padding: 16px 12px;
}

/* Pagination styling */
:deep(.v-data-table-footer) {
    background: var(--bb-surface, #ffffff);
    border-top: 1px solid var(--bb-border-soft, #f3f4f6);
    padding: 16px 24px;
}

:deep(.v-data-table-footer__items-per-page) {
    color: var(--bb-text-muted, #6b7280);
    font-weight: 500;
}

:deep(.v-data-table-footer__pagination) {
    color: var(--bb-text-muted, #6b7280);
    font-weight: 500;
}

/* Chip styling */
:deep(.v-chip) {
    font-weight: 500;
    border-radius: 8px;
}

/* Button styling */
:deep(.v-btn) {
    text-transform: none;
    font-weight: 500;
}

/* Form field styling */
:deep(.v-field) {
    border-radius: 12px;
}

:deep(.v-field__outline) {
    border-radius: 12px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .table-header {
        padding: 16px;
    }

    :deep(.v-data-table__td) {
        padding: 12px 8px;
        font-size: 0.875rem;
    }

    :deep(.v-data-table-header th) {
        font-size: 0.7rem;
        padding: 12px 8px;
    }
}

/* Mobile-specific improvements */
@media (max-width: 600px) {
    .transactions-container {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        width: 100%;
    }

    .table-header {
        padding: 12px;
    }

    .table-header .d-flex {
        flex-direction: column;
        gap: 12px;
        align-items: stretch !important;
    }

    .table-header .d-flex>div:first-child {
        text-align: center;
    }

    .table-header .d-flex>div:last-child {
        display: flex;
        justify-content: center;
    }

    :deep(.v-data-table__td) {
        padding: 8px 4px;
        font-size: 0.8rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    :deep(.v-data-table-header th) {
        font-size: 0.65rem;
        padding: 8px 4px;
        white-space: nowrap;
    }

    .transactions-container {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }

    :deep(.v-data-table__wrapper) {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        min-width: 400px;
    }

    :deep(.v-data-table) {
        min-width: 400px;
    }

    /* Make transaction title column wider on mobile */
    :deep(.v-data-table__td:first-child) {
        max-width: 120px;
        min-width: 100px;
    }

    /* Make actions column narrower */
    :deep(.v-data-table__td:last-child) {
        width: 80px;
        min-width: 80px;
    }

    /* Adjust button sizes in actions */
    :deep(.v-data-table__td:last-child .v-btn) {
        min-width: 32px;
        width: 32px;
        height: 32px;
    }

    :deep(.v-data-table__td:last-child .v-btn .v-icon) {
        font-size: 16px;
    }
}

/* Extra small screens (iPhone SE) */
@media (max-width: 375px) {
    .transactions-container {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        width: 100%;
    }

    .table-header {
        padding: 8px;
    }

    .table-header .d-flex {
        gap: 8px;
    }

    :deep(.v-data-table__td) {
        padding: 6px 2px;
        font-size: 0.75rem;
    }

    :deep(.v-data-table-header th) {
        font-size: 0.6rem;
        padding: 6px 2px;
    }

    /* Make transaction title column even wider on very small screens */
    :deep(.v-data-table__td:first-child) {
        max-width: 100px;
        min-width: 80px;
    }

    /* Make actions column even narrower */
    :deep(.v-data-table__td:last-child) {
        width: 60px;
        min-width: 60px;
    }

    /* Adjust button sizes in actions for very small screens */
    :deep(.v-data-table__td:last-child .v-btn) {
        min-width: 28px;
        width: 28px;
        height: 28px;
    }

    :deep(.v-data-table__td:last-child .v-btn .v-icon) {
        font-size: 14px;
    }
}

/* Loading state */
:deep(.v-data-table__loading) {
    background: var(--bb-surface, #ffffff);
}

/* Empty state styling */
:deep(.v-data-table__empty-wrapper) {
    background: var(--bb-surface, #ffffff);
    border-radius: 16px;
    margin: 16px;
}
</style>

<template>
    <div class="transactions-container">
        <v-data-table :headers="(this as any).currentHeaders" :items="(this as any).internalTransactions"
            :sort-by="[{ key: 'date', order: 'desc' }]" class="modern-data-table elevation-0" :items-per-page="10"
            :loading="false">
            <template v-slot:top>
                <div class="table-header">
                    <div class="d-flex align-center justify-end pa-4">
                        <v-dialog v-model="(this as any).dialog" :max-width="$vuetify.display.mobile ? '95%' : '600px'"
                            persistent>
                            <template v-slot:activator="{ props }">
                                <v-btn color="primary" class="smooth-transition hover-lift" v-bind="props"
                                    :prepend-icon="$vuetify.display.smAndUp ? 'mdi-plus' : undefined"
                                    :size="$vuetify.display.mobile ? 'default' : 'default'" rounded="lg">
                                    <span :class="$vuetify.display.mobile ? 'd-none d-sm-inline' : ''">New
                                        Transaction</span>
                                    <span :class="$vuetify.display.mobile ? 'd-inline d-sm-none' : 'd-none'">+
                                        New</span>
                                </v-btn>
                            </template>
                            <v-card class="modern-dialog" rounded="xl">
                                <v-card-title class="pa-6 pb-2">
                                    <div class="d-flex align-center">
                                        <v-avatar size="40" class="me-3 budget-gradient">
                                            <v-icon color="white">{{ (this as any).editedIndex === -1 ? 'mdi-plus' :
                                                'mdi-pencil'
                                            }}</v-icon>
                                        </v-avatar>
                                        <div>
                                            <h3 class="text-h5 font-weight-bold budget-text-gradient mb-0">{{ (this as
                                                any).formTitle
                                            }}</h3>
                                            <p class="text-caption text-grey-darken-1 mb-0">Enter transaction details
                                            </p>
                                        </div>
                                    </div>
                                </v-card-title>
                                <v-card-text class="pa-6 pt-2">
                                    <v-container class="pa-0">
                                        <v-row>
                                            <v-col cols="12" md="6">
                                                <v-select v-model="(this as any).editedItem.transaction_type"
                                                    label="Transaction Type" :items="[
                                                        { title: 'Income', value: 'Income', prependIcon: 'mdi-trending-up' },
                                                        { title: 'Expense', value: 'Expense', prependIcon: 'mdi-trending-down' }
                                                    ]" variant="outlined" rounded="lg"></v-select>
                                            </v-col>
                                            <v-col cols="12" md="6">
                                                <v-text-field v-model="editedItem.date" label="Date" type="date"
                                                    variant="outlined" rounded="lg"></v-text-field>
                                            </v-col>
                                        </v-row>
                                        <v-row>
                                            <v-col cols="12" md="8">
                                                <v-text-field v-model="editedItem.title" label="Transaction Title"
                                                    variant="outlined" rounded="lg"></v-text-field>
                                            </v-col>
                                            <v-col cols="12" md="4">
                                                <v-text-field v-model="editedItem.total" label="Amount" type="number"
                                                    step="0.01" variant="outlined" rounded="lg"
                                                    prepend-inner-icon="mdi-currency-usd"></v-text-field>
                                            </v-col>
                                        </v-row>
                                        <v-row>
                                            <v-col cols="12" md="6">
                                                <v-select v-model="editedItem.account_id" label="Account"
                                                    :items="internalAccounts" item-title="title" item-value="value"
                                                    variant="outlined" rounded="lg"
                                                    prepend-inner-icon="mdi-bank"></v-select>
                                            </v-col>
                                            <v-col cols="12" md="6">
                                                <v-select v-model="editedItem.category" label="Category"
                                                    :items="categories" variant="outlined" rounded="lg"
                                                    prepend-inner-icon="mdi-tag"></v-select>
                                            </v-col>
                                        </v-row>
                                    </v-container>
                                </v-card-text>
                                <v-card-actions class="pa-6 pt-0">
                                    <v-spacer></v-spacer>
                                    <v-btn variant="outlined" @click="close" class="me-2" rounded="lg">
                                        Cancel
                                    </v-btn>
                                    <v-btn color="primary" @click="saveTransaction" :disabled="!isFormValid"
                                        rounded="lg" class="smooth-transition">
                                        {{ editedIndex === -1 ? 'Create' : 'Update' }}
                                    </v-btn>
                                </v-card-actions>
                            </v-card>
                        </v-dialog>
                        <v-dialog v-model="dialogDelete" max-width="500px" persistent>
                            <v-card class="modern-dialog" rounded="xl">
                                <v-card-title class="pa-6 pb-2">
                                    <div class="d-flex align-center">
                                        <v-avatar size="40" class="me-3 bg-error">
                                            <v-icon color="white">mdi-delete</v-icon>
                                        </v-avatar>
                                        <div>
                                            <h3 class="text-h5 font-weight-bold text-error mb-0">Delete Transaction</h3>
                                            <p class="text-caption text-grey-darken-1 mb-0">This action cannot be undone
                                            </p>
                                        </div>
                                    </div>
                                </v-card-title>
                                <v-card-text class="pa-6 pt-2">
                                    <p class="text-body-1">Are you sure you want to delete this transaction?</p>
                                </v-card-text>
                                <v-card-actions class="pa-6 pt-0">
                                    <v-spacer></v-spacer>
                                    <v-btn variant="outlined" @click="closeDelete" class="me-2" rounded="lg">
                                        Cancel
                                    </v-btn>
                                    <v-btn color="error" @click="deleteItemConfirm" rounded="lg">
                                        Delete
                                    </v-btn>
                                </v-card-actions>
                            </v-card>
                        </v-dialog>
                    </div>
                </div>
            </template>

            <!-- Custom row styling -->
            <template v-slot:item.transaction_type="{ item }">
                <v-chip :color="asTransaction(item).transaction_type === 'Income' ? 'success' : 'error'" size="small" variant="tonal"
                    class="font-weight-medium">
                    <v-icon :icon="asTransaction(item).transaction_type === 'Income' ? 'mdi-trending-up' : 'mdi-trending-down'"
                        size="16" class="me-1"></v-icon>
                    {{ asTransaction(item).transaction_type }}
                </v-chip>
            </template>

            <template v-slot:item.total="{ item }">
                <span class="font-weight-bold"
                    :class="asTransaction(item).transaction_type === 'Income' ? 'text-success' : 'text-error'">
                    {{ asTransaction(item).transaction_type === 'Income' ? '+' : '-' }}${{ Math.abs(asTransaction(item).total).toLocaleString() }}
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
                    <v-btn icon size="small" variant="text" color="primary" @click="editItem(asTransaction(item))" class="me-1">
                        <v-icon size="18">mdi-pencil</v-icon>
                    </v-btn>
                    <v-btn icon size="small" variant="text" color="error" @click="deleteItem(asTransaction(item))">
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
                    <v-btn color="primary" @click="dialog = true" rounded="lg">
                        <v-icon left>mdi-plus</v-icon>
                        Add Transaction
                    </v-btn>
                </div>
            </template>
        </v-data-table>
    </div>
</template>

<script lang="ts">
import axios from '@/services/api';
import { getCategoryStyle as getCategoryStyleUtil } from '@/constants/categoryStyles';
import { toMoneyNumber } from '@/services/money';

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

interface Account {
    id: number;
    account_type: string;
    bank: string;
    total: number;
    account_name: string;
}

export default {
    name: 'TableData',
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
            internalAccounts: [] as Array<{ title: string; value: string }>,
            dialog: false,
            dialogDelete: false,
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

            editedIndex: -1,
            editedItem: {
                id: 0,
                owner_id: 'temp',
                account_id: '',
                title: '',
                category: '',
                date: '',
                total: 0,
                transaction_type: '',
            } as Transaction,
            defaultItem: {
                id: 0,
                owner_id: '',
                account_id: '',
                title: '',
                category: '',
                date: '',
                total: 0,
                transaction_type: '',
            } as Transaction,
            categories: [
                'Account Transfer',
                'Awards',
                'Balance Transfer',
                'Bills and utilities',
                'Education',
                'Entertainment',
                'Food and drinks',
                'Gifts',
                'Insurance',
                'Investments',
                'Loans',
                'Medical',
                'Money Transfer',
                'Others',
                'Salary',
                'Shopping',
                'Transportation',
                'Transfer',
            ],
        }
    },

    computed: {
        formTitle(): string {
            return (this as any).editedIndex === -1 ? 'New Transaction' : 'Edit Transaction'
        },
        isFormValid(): boolean {
            let isValid = true;
            (this as any).editedItem.owner_id = (this as any).userData.user.username
            Object.values((this as any).editedItem).forEach((value) => {
                if (value === '') {
                    isValid = false;
                }
            });
            return isValid;
        },
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
        dialog(val: boolean) {
            val || (this as any).close()
        },
        dialogDelete(val: boolean) {
            val || (this as any).closeDelete()
        },
        accounts: {
            immediate: true,
            handler(newVal: Account[]) {
                (this as any).internalAccounts = []
                newVal.forEach((account: Account) => {
                    (this as any).internalAccounts.push({
                        title: account.account_name,
                        value: String(account.id)
                    })
                })
            }
        },
    },

    mounted() {
        this.categories.sort()
    },
    emits: ['updateAccounts', 'updateIncomeExpense'],
    methods: {
        asTransaction(item: unknown): Transaction {
            return item as Transaction;
        },
        formatDate(dateString: string): string {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        },
        getCategoryStyle(category: string) {
            return getCategoryStyleUtil(category);
        },

        editItem(item: Transaction) {
            if (!Array.isArray((this as any).internalTransactions)) {
                (this as any).internalTransactions = [];
            }
            (this as any).editedIndex = (this as any).internalTransactions.indexOf(item);
            (this as any).editedItem = Object.assign({}, item);
            if ((this as any).editedItem.total < 0) {
                (this as any).editedItem.total *= -1;
            }
            (this as any).dialog = true;
        },
        deleteItem(item: Transaction) {
            if (!Array.isArray((this as any).internalTransactions)) {
                (this as any).internalTransactions = [];
            }
            (this as any).editedIndex = (this as any).internalTransactions.indexOf(item);
            (this as any).editedItem = Object.assign({}, item);
            (this as any).dialogDelete = true;
        },

        deleteItemConfirm() {
            let idToDelete = (this as any).editedItem.id;
            axios.delete(`/transactions/delete/${idToDelete}/`)
                .then((response: any) => {
                    (this as any).internalTransactions.splice((this as any).editedIndex, 1);
                    (this as any).$emit('updateAccounts');
                    (this as any).$emit('updateIncomeExpense');
                    (this as any).closeDelete();
                })
                .catch((error: any) => {
                    console.log(error);
                });
        },
        close() {
            ; (this as any).dialog = false
                ; (this as any).$nextTick(() => {
                    (this as any).editedItem = Object.assign({}, (this as any).defaultItem)
                        ; (this as any).editedIndex = -1
                })
        },
        closeDelete() {
            ; (this as any).dialogDelete = false
                ; (this as any).$nextTick(() => {
                    (this as any).editedItem = Object.assign({}, (this as any).defaultItem)
                        ; (this as any).editedIndex = -1
                })
        },
        saveTransaction() {
            if ((this as any).editedIndex > -1) {
                let oldTransaction = (this as any).internalTransactions[(this as any).editedIndex];
                if ((this as any).editedItem === oldTransaction) {
                    (this as any).close();
                    return;
                }

                Object.assign((this as any).internalTransactions[(this as any).editedIndex], (this as any).editedItem)
                axios.patch(`/transactions/update/${(this as any).editedItem.id}/`, (this as any).editedItem)
                    .then((response: any) => {
                        (this as any).internalTransactions[(this as any).editedIndex] = response.data.updated_transaction;
                        (this as any).$emit('updateAccounts');
                        (this as any).$emit('updateIncomeExpense');
                    })
                    .catch((error: any) => {
                        console.log(error);
                    });
            } else {
                (this as any).editedItem.owner_id = (this as any).userData.user.username
                axios.post('/transactions/create/', (this as any).editedItem)
                    .then((response: any) => {
                        (this as any).internalTransactions.push(response.data)
                        (this as any).$emit('updateAccounts');
                        (this as any).$emit('updateIncomeExpense');
                    })
                    .catch((error: any) => {
                        console.log(error)
                    })
            }
            (this as any).close()
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
    background: #ffffff;
    border-bottom: 1px solid #f3f4f6;
}

/* Modern dialog styling */
.modern-dialog {
    background: #ffffff;
    border: 1px solid #f3f4f6;
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
    background: #f9fafb;
    border-bottom: 1px solid #f3f4f6 !important;
}

:deep(.v-data-table-footer) {
    border-top: 1px solid #f3f4f6 !important;
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
    color: #2E7D32;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.5px;
}

:deep(.v-data-table__tr) {
    transition: all 0.2s ease;
}

:deep(.v-data-table__tr:hover) {
    background: #f9fafb !important;
    transform: none;
}

:deep(.v-data-table__tr:nth-child(even)) {
    background: #ffffff;
}

:deep(.v-data-table__tr:nth-child(odd)) {
    background: #ffffff;
}

:deep(.v-data-table__td) {
    border-bottom: 1px solid #f3f4f6;
    padding: 16px 12px;
}

/* Pagination styling */
:deep(.v-data-table-footer) {
    background: #ffffff;
    border-top: 1px solid #f3f4f6;
    padding: 16px 24px;
}

:deep(.v-data-table-footer__items-per-page) {
    color: #2E7D32;
    font-weight: 500;
}

:deep(.v-data-table-footer__pagination) {
    color: #2E7D32;
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
    background: #ffffff;
}

/* Empty state styling */
:deep(.v-data-table__empty-wrapper) {
    background: #ffffff;
    border-radius: 16px;
    margin: 16px;
}
</style>

<template>
    <div class="transactions-container">
        <v-data-table :headers="(this as any).headers" :items="(this as any).internalTransactions"
            :sort-by="[{ key: 'date', order: 'desc' }]" class="modern-data-table elevation-0" :items-per-page="10"
            :loading="false">
            <template v-slot:top>
                <div class="table-header">
                    <div class="d-flex align-center justify-space-between pa-4">
                        <div>
                            <p class="text-caption text-grey-darken-1 mb-0">{{ (this as any).internalTransactions.length
                            }}
                                transactions found</p>
                        </div>
                        <v-dialog v-model="(this as any).dialog" max-width="600px" persistent>
                            <template v-slot:activator="{ props }">
                                <v-btn color="primary" class="smooth-transition hover-lift" v-bind="props"
                                    prepend-icon="mdi-plus" rounded="lg">
                                    New Transaction
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
                                                    :items="internalAccounts" variant="outlined" rounded="lg"
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
                <v-chip :color="item.transaction_type === 'Income' ? 'success' : 'error'" size="small" variant="tonal"
                    class="font-weight-medium">
                    <v-icon :icon="item.transaction_type === 'Income' ? 'mdi-trending-up' : 'mdi-trending-down'"
                        size="16" class="me-1"></v-icon>
                    {{ item.transaction_type }}
                </v-chip>
            </template>

            <template v-slot:item.total="{ item }">
                <span class="font-weight-bold"
                    :class="item.transaction_type === 'Income' ? 'text-success' : 'text-error'">
                    {{ item.transaction_type === 'Income' ? '+' : '-' }}${{ Math.abs(item.total).toLocaleString() }}
                </span>
            </template>

            <template v-slot:item.date="{ item }">
                <span class="text-body-2">{{ formatDate(item.date) }}</span>
            </template>

            <template v-slot:item.actions="{ item }">
                <div class="d-flex align-center">
                    <v-btn icon size="small" variant="text" color="primary" @click="editItem(item)" class="me-1">
                        <v-icon size="18">mdi-pencil</v-icon>
                    </v-btn>
                    <v-btn icon size="small" variant="text" color="error" @click="deleteItem(item)">
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
import axios from 'axios';
// import * as Vue from 'vue';

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
            internalAccounts: [] as String[],
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
                'Awards',
                'Bills and utilities',
                'Education',
                'Entertainment',
                'Food and drinks',
                'Gifts',
                'Insurance',
                'Investments',
                'Loans',
                'Medical',
                'Others',
                'Salary',
                'Shopping',
                'Transportation',
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
    },
    watch: {
        transactions: {
            immediate: true,
            handler(newVal: Transaction[]) {
                (this as any).internalTransactions = []
                newVal.forEach((transaction: Transaction) => {
                    let tempTransaction = transaction
                    if (transaction.transaction_type === 'Expense') {
                        tempTransaction.total = -transaction.total
                    }
                    (this as any).internalTransactions.push(tempTransaction)
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
                    (this as any).internalAccounts.push(account.account_name)
                })
            }
        },
    },

    mounted() {
        this.categories.sort()
    },
    emits: ['updateAccounts', 'updateIncomeExpense'],
    methods: {
        formatDate(dateString: string): string {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
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
            let account_id = (this as any).editedItem.account_id;
            let account = (this as any).accounts.find((account: Account) => account.id === Number(account_id));
            let new_total = account!.total + (-1 * ((this as any).editedItem.total));
            axios.delete(`http://localhost:8000/transactions/delete/${idToDelete}/`)
                .then((response: any) => {
                    (this as any).internalTransactions.splice((this as any).editedIndex, 1);
                    axios.patch(`http://localhost:8000/accounts/details/${(this as any).userData.user.username}/${account_id}/`, {
                        "total": new_total,
                    })
                        .then((patchResponse: any) => {
                            (this as any).$emit('updateAccounts');
                            (this as any).$emit('updateIncomeExpense');

                            (this as any).closeDelete();
                        })
                        .catch((patchError: any) => {
                            console.log(patchError);
                        });
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
        getDiff(oldTransaction: Transaction): number {
            let diff = 0;
            if (oldTransaction.transaction_type === (this as any).editedItem.transaction_type) {
                diff = Number((this as any).editedItem.total) - Math.abs(oldTransaction.total);
            } else {
                diff = Math.abs(oldTransaction.total) + Number((this as any).editedItem.total);
                if (oldTransaction.transaction_type === 'Income' && (this as any).editedItem.transaction_type === 'Expense') {
                    diff *= -1;
                }
            }
            return diff;
        },
        saveTransaction() {
            if ((this as any).editedIndex > -1) {
                let oldTransaction = (this as any).internalTransactions[(this as any).editedIndex];
                if ((this as any).editedItem === oldTransaction) {
                    (this as any).close();
                    return;
                }
                let diff = (this as any).getDiff(oldTransaction);

                let account_id = (this as any).editedItem.account_id;
                let account = (this as any).accounts.find((account: Account) => account.id === Number(account_id));
                let new_total = account!.total + diff;

                Object.assign((this as any).internalTransactions[(this as any).editedIndex], (this as any).editedItem)
                axios.patch(`http://localhost:8000/transactions/update/${(this as any).editedItem.id}/`, (this as any).editedItem)
                    .then((response: any) => {
                        axios.patch(`http://localhost:8000/accounts/details/${(this as any).userData.user.username}/${account_id}/`, {
                            "total": new_total,
                        })
                            .then((patchResponse: any) => {
                                console.log(patchResponse);
                                (this as any).$emit('updateAccounts');
                                (this as any).$emit('updateIncomeExpense');
                            })
                            .catch((patchError: any) => {
                                console.log(patchError);
                            });
                    })
                    .catch((error: any) => {
                        console.log(error);
                    });
            } else {
                (this as any).editedItem.owner_id = (this as any).userData.user.username
                let account_name = (this as any).editedItem.account_id;
                let account = (this as any).accounts.find((account: Account) => account.account_name === account_name);
                let account_id = account ? account.id : null;
                (this as any).editedItem.account_id = String(account_id)
                let new_total = account!.total
                if ((this as any).editedItem.transaction_type === 'Expense') {
                    new_total -= Number((this as any).editedItem.total)
                } else {
                    new_total += Number((this as any).editedItem.total)
                }

                axios.post('http://localhost:8000/transactions/create/', (this as any).editedItem)
                    .then((response: any) => {
                        (this as any).internalTransactions.push(response.data)
                        axios.patch(`http://localhost:8000/accounts/details/${(this as any).userData.user.username}/${account_id}/`, {
                            "total": new_total,
                        })
                            .then((patchResponse: any) => {
                                (this as any).$emit('updateAccounts');
                                (this as any).$emit('updateIncomeExpense');
                            })
                            .catch((patchError: any) => {
                                console.log(patchError);
                            });
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
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

/* Modern dialog styling */
.modern-dialog {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Data table custom styling */
:deep(.v-data-table) {
    background: transparent !important;
}

:deep(.v-data-table__wrapper) {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

:deep(.v-data-table-header) {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-bottom: 1px solid rgba(0, 0, 0, 0.1) !important;
}

:deep(.v-data-table-footer) {
    border-top: 1px solid rgba(0, 0, 0, 0.1) !important;
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
    background: rgba(76, 175, 80, 0.05) !important;
    transform: scale(1.01);
}

:deep(.v-data-table__tr:nth-child(even)) {
    background: rgba(248, 249, 250, 0.5);
}

:deep(.v-data-table__tr:nth-child(odd)) {
    background: rgba(255, 255, 255, 0.8);
}

:deep(.v-data-table__td) {
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    padding: 16px 12px;
}

/* Pagination styling */
:deep(.v-data-table-footer) {
    background: rgba(255, 255, 255, 0.9);
    border-top: 1px solid rgba(0, 0, 0, 0.05);
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

/* Animation for table rows */
:deep(.v-data-table__tr) {
    animation: slideInRow 0.3s ease-out;
}

@keyframes slideInRow {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }

    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* Loading state */
:deep(.v-data-table__loading) {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
}

/* Empty state styling */
:deep(.v-data-table__empty-wrapper) {
    background: rgba(255, 255, 255, 0.8);
    border-radius: 16px;
    margin: 16px;
}
</style>
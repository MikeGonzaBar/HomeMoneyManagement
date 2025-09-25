<template>
    <v-dialog v-model="dialog" max-width="1200px" persistent scrollable>
        <v-card class="modern-dialog" rounded="xl">
            <v-card-title class="pa-6 pb-2">
                <div class="d-flex align-center justify-space-between w-100">
                    <div class="d-flex align-center">
                        <v-avatar size="40" class="me-3 budget-gradient">
                            <v-icon color="white">mdi-file-document-edit</v-icon>
                        </v-avatar>
                        <div>
                            <h3 class="text-h5 font-weight-bold budget-text-gradient mb-0">Review Detected Transactions
                            </h3>
                            <p class="text-caption text-grey-darken-1 mb-0">Review and edit transactions before
                                importing</p>
                        </div>
                    </div>
                    <v-btn icon variant="text" @click="closeDialog" class="close-btn">
                        <v-icon>mdi-close</v-icon>
                    </v-btn>
                </div>
            </v-card-title>

            <v-card-text class="pa-6 pt-2">
                <!-- Account Information -->
                <v-card class="mb-6" variant="tonal" color="primary" rounded="lg">
                    <v-card-text class="pa-4">
                        <div class="d-flex align-center justify-space-between mb-3">
                            <div class="d-flex align-center">
                                <v-avatar size="32" class="me-3 bg-primary">
                                    <v-icon color="white">mdi-bank</v-icon>
                                </v-avatar>
                                <div>
                                    <h4 class="text-h6 font-weight-bold mb-1">Detected Account</h4>
                                    <p class="text-caption mb-0">Edit account details below</p>
                                </div>
                            </div>
                            <v-btn icon size="small" variant="text" @click="toggleAccountEdit"
                                :color="isEditingAccount ? 'error' : 'primary'">
                                <v-icon>{{ isEditingAccount ? 'mdi-close' : 'mdi-pencil' }}</v-icon>
                            </v-btn>
                        </div>

                        <!-- Account Edit Form -->
                        <v-form v-if="isEditingAccount" class="account-edit-form">
                            <v-row>
                                <v-col cols="12" md="4">
                                    <v-text-field v-model="editableAccountInfo.name" label="Account Name"
                                        variant="outlined" density="compact" prepend-inner-icon="mdi-account"
                                        class="mb-2"></v-text-field>
                                </v-col>
                                <v-col cols="12" md="4">
                                    <v-text-field v-model="editableAccountInfo.bank" label="Bank Name"
                                        variant="outlined" density="compact" prepend-inner-icon="mdi-bank"
                                        class="mb-2"></v-text-field>
                                </v-col>
                                <v-col cols="12" md="4">
                                    <v-select v-model="editableAccountInfo.account_type" label="Account Type"
                                        :items="accountTypes" variant="outlined" density="compact"
                                        prepend-inner-icon="mdi-credit-card" class="mb-2"></v-select>
                                </v-col>
                            </v-row>
                            <div class="d-flex justify-end">
                                <v-btn size="small" variant="outlined" @click="cancelAccountEdit" class="me-2">
                                    Cancel
                                </v-btn>
                                <v-btn size="small" color="primary" @click="saveAccountEdit">
                                    Save
                                </v-btn>
                            </div>
                        </v-form>

                        <!-- Account Display -->
                        <div v-else class="account-display">
                            <div class="d-flex align-center">
                                <v-avatar size="24" class="me-3 bg-primary">
                                    <v-icon color="white" size="16">mdi-account</v-icon>
                                </v-avatar>
                                <div>
                                    <h5 class="text-subtitle-1 font-weight-bold mb-1">{{ accountInfo.name }}</h5>
                                    <p class="text-caption mb-0">{{ accountInfo.bank }} • {{ accountInfo.account_type }}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </v-card-text>
                </v-card>

                <!-- Transactions Table -->
                <div class="transactions-review">
                    <div class="d-flex align-center justify-space-between mb-4">
                        <h4 class="text-h6 font-weight-bold">Detected Transactions ({{ editableTransactions.length }})
                        </h4>
                        <v-chip color="primary" variant="tonal" size="small">
                            <v-icon left>mdi-check-circle</v-icon>
                            {{ selectedTransactions.length }} selected
                        </v-chip>
                    </div>

                    <v-data-table v-model="selectedTransactions" :headers="headers" :items="editableTransactions"
                        :items-per-page="10" show-select class="modern-data-table elevation-0" :loading="false">
                        <!-- Transaction Type Column -->
                        <template v-slot:item.transaction_type="{ item }">
                            <v-select v-model="item.transaction_type" :items="transactionTypes" variant="outlined"
                                density="compact" hide-details class="transaction-type-select"></v-select>
                        </template>

                        <!-- Title Column -->
                        <template v-slot:item.title="{ item }">
                            <v-text-field v-model="item.title" variant="outlined" density="compact" hide-details
                                class="transaction-title-input"></v-text-field>
                        </template>

                        <!-- Amount Column -->
                        <template v-slot:item.amount="{ item }">
                            <v-text-field v-model="item.amount" type="number" step="0.01" variant="outlined"
                                density="compact" hide-details class="transaction-amount-input"
                                prepend-inner-icon="mdi-currency-usd"></v-text-field>
                        </template>

                        <!-- Date Column -->
                        <template v-slot:item.date="{ item }">
                            <v-text-field v-model="item.date" type="date" variant="outlined" density="compact"
                                hide-details class="transaction-date-input"></v-text-field>
                        </template>

                        <!-- Category Column -->
                        <template v-slot:item.category="{ item }">
                            <v-select v-model="item.category" :items="categories" variant="outlined" density="compact"
                                hide-details class="transaction-category-select"></v-select>
                        </template>

                        <!-- Actions Column -->
                        <template v-slot:item.actions="{ item }">
                            <v-btn icon size="small" variant="text" color="error" @click="removeTransaction(item)">
                                <v-icon size="18">mdi-delete</v-icon>
                            </v-btn>
                        </template>

                        <!-- Empty state -->
                        <template v-slot:no-data>
                            <div class="text-center pa-8">
                                <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-receipt</v-icon>
                                <h3 class="text-h6 text-grey-darken-1 mb-2">No transactions detected</h3>
                                <p class="text-body-2 text-grey-darken-1">No transactions were found in the uploaded
                                    statement</p>
                            </div>
                        </template>
                    </v-data-table>
                </div>
            </v-card-text>

            <v-card-actions class="pa-6 pt-0">
                <v-spacer></v-spacer>
                <v-btn variant="outlined" @click="closeDialog" class="me-2" rounded="lg">
                    Cancel
                </v-btn>
                <v-btn color="primary" @click="importTransactions" :disabled="selectedTransactions.length === 0"
                    rounded="lg" class="smooth-transition">
                    <v-icon left>mdi-import</v-icon>
                    Import {{ selectedTransactions.length }} Transactions
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script lang="ts">
import axios from 'axios';

interface DetectedTransaction {
    id: string;
    title: string;
    amount: number;
    date: string;
    category: string;
    transaction_type: 'Income' | 'Expense';
    account_name: string;
}

interface AccountInfo {
    name: string;
    bank: string;
    account_type: string;
}

interface BankStatementData {
    account_detected: AccountInfo;
    transactions: DetectedTransaction[];
}

export default {
    name: 'BankStatementReview',
    props: {
        userData: {
            type: Object,
            required: true
        },
        accounts: {
            type: Array,
            required: true
        }
    },
    data() {
        return {
            dialog: false,
            accountInfo: {} as AccountInfo,
            editableAccountInfo: {} as AccountInfo,
            isEditingAccount: false,
            editableTransactions: [] as DetectedTransaction[],
            selectedTransactions: [] as DetectedTransaction[],
            headers: [
                { title: 'Type', key: 'transaction_type', sortable: false, width: '120px' },
                { title: 'Description', key: 'title', sortable: false, width: '200px' },
                { title: 'Amount', key: 'amount', sortable: false, width: '120px' },
                { title: 'Date', key: 'date', sortable: false, width: '140px' },
                { title: 'Category', key: 'category', sortable: false, width: '160px' },
                { title: 'Actions', key: 'actions', sortable: false, width: '80px' },
            ],
            transactionTypes: [
                { title: 'Income', value: 'Income' },
                { title: 'Expense', value: 'Expense' },
                { title: 'Transfer', value: 'Transfer' }
            ],
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
                'Transfer',
                'Account Transfer',
                'Money Transfer',
                'Balance Transfer',
            ],
            accountTypes: [
                'Checking',
                'Savings',
                'Credit Card',
                'Investment',
                'Loan',
                'Mortgage',
                'Business',
                'Other'
            ]
        }
    },
    emits: ['transactionsImported', 'dialogClosed'],
    methods: {
        openDialog(bankStatementData: BankStatementData) {
            (this as any).accountInfo = bankStatementData.account_detected;
            (this as any).editableAccountInfo = { ...bankStatementData.account_detected };
            (this as any).editableTransactions = [...bankStatementData.transactions];
            (this as any).selectedTransactions = [...bankStatementData.transactions];
            (this as any).isEditingAccount = false;
            (this as any).dialog = true;
        },

        closeDialog() {
            (this as any).dialog = false;
            (this as any).editableTransactions = [];
            (this as any).selectedTransactions = [];
            (this as any).accountInfo = {} as AccountInfo;
            (this as any).editableAccountInfo = {} as AccountInfo;
            (this as any).isEditingAccount = false;
            (this as any).$emit('dialogClosed');
        },

        toggleAccountEdit() {
            (this as any).isEditingAccount = !(this as any).isEditingAccount;
            if ((this as any).isEditingAccount) {
                (this as any).editableAccountInfo = { ...(this as any).accountInfo };
            }
        },

        cancelAccountEdit() {
            (this as any).isEditingAccount = false;
            (this as any).editableAccountInfo = { ...(this as any).accountInfo };
        },

        saveAccountEdit() {
            (this as any).accountInfo = { ...(this as any).editableAccountInfo };
            (this as any).isEditingAccount = false;

            // Update all transactions with the new account name
            (this as any).editableTransactions.forEach((transaction: DetectedTransaction) => {
                transaction.account_name = (this as any).accountInfo.name;
            });
        },

        removeTransaction(transaction: DetectedTransaction) {
            const index = (this as any).editableTransactions.findIndex((t: DetectedTransaction) => t.id === transaction.id);
            if (index > -1) {
                (this as any).editableTransactions.splice(index, 1);
            }

            const selectedIndex = (this as any).selectedTransactions.findIndex((t: DetectedTransaction) => t.id === transaction.id);
            if (selectedIndex > -1) {
                (this as any).selectedTransactions.splice(selectedIndex, 1);
            }
        },

        async importTransactions() {
            try {
                // Find the account ID for the detected account
                const account = (this as any).accounts.find((acc: any) =>
                    acc.account_name === (this as any).accountInfo.name
                );

                if (!account) {
                    (this as any).$emit('importError', 'Account not found. Please create the account first.');
                    return;
                }

                // Prepare transactions for import
                const transactionsToImport = (this as any).selectedTransactions.map((transaction: DetectedTransaction) => ({
                    title: transaction.title,
                    transaction_type: transaction.transaction_type,
                    category: transaction.category,
                    date: transaction.date,
                    total: transaction.amount,
                    owner_id: (this as any).userData.user.username,
                    account_id: account.id.toString()
                }));

                // Import each transaction
                for (const transaction of transactionsToImport) {
                    await axios.post('http://localhost:8000/transactions/create/', transaction);
                }

                // Update account total
                const totalChange = (this as any).selectedTransactions.reduce((sum: number, transaction: DetectedTransaction) => {
                    return sum + (transaction.transaction_type === 'Income' ? transaction.amount : -transaction.amount);
                }, 0);

                const newTotal = account.total + totalChange;
                await axios.patch(`http://localhost:8000/accounts/details/${(this as any).userData.user.username}/${account.id}/`, {
                    total: newTotal
                });

                (this as any).$emit('transactionsImported', {
                    importedCount: transactionsToImport.length,
                    accountUpdated: account
                });

                (this as any).closeDialog();

            } catch (error) {
                console.error('Error importing transactions:', error);
                (this as any).$emit('importError', 'Failed to import transactions. Please try again.');
            }
        }
    }
}
</script>

<style scoped>
/* Review dialog specific styles */
.modern-dialog {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.close-btn {
    transition: all 0.2s ease;
}

.close-btn:hover {
    background: rgba(0, 0, 0, 0.05);
    transform: scale(1.1);
}

.transactions-review {
    background: transparent;
}

/* Data table styling */
.modern-data-table {
    background: transparent !important;
    border-radius: 16px;
    overflow: hidden;
}

/* Form field styling for inline editing */
:deep(.transaction-type-select .v-field),
:deep(.transaction-title-input .v-field),
:deep(.transaction-amount-input .v-field),
:deep(.transaction-date-input .v-field),
:deep(.transaction-category-select .v-field) {
    border-radius: 8px;
    font-size: 0.875rem;
}

:deep(.transaction-type-select .v-field__outline),
:deep(.transaction-title-input .v-field__outline),
:deep(.transaction-amount-input .v-field__outline),
:deep(.transaction-date-input .v-field__outline),
:deep(.transaction-category-select .v-field__outline) {
    border-radius: 8px;
}

/* Table row styling */
:deep(.v-data-table__tr) {
    transition: all 0.2s ease;
}

:deep(.v-data-table__tr:hover) {
    background: rgba(76, 175, 80, 0.05) !important;
}

:deep(.v-data-table__tr:nth-child(even)) {
    background: rgba(248, 249, 250, 0.5);
}

:deep(.v-data-table__tr:nth-child(odd)) {
    background: rgba(255, 255, 255, 0.8);
}

:deep(.v-data-table__td) {
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    padding: 12px 8px;
}

/* Header styling */
:deep(.v-data-table-header th) {
    font-weight: 600;
    color: #2E7D32;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.5px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

/* Selection styling */
:deep(.v-selection-control) {
    margin: 0;
}

/* Button styling */
:deep(.v-btn) {
    text-transform: none;
    font-weight: 500;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .modern-dialog {
        margin: 16px;
        max-width: calc(100vw - 32px);
    }

    :deep(.v-data-table__td) {
        padding: 8px 4px;
        font-size: 0.8rem;
    }

    :deep(.v-data-table-header th) {
        font-size: 0.7rem;
        padding: 8px 4px;
    }

    /* Make form fields more compact on mobile */
    :deep(.transaction-type-select .v-field),
    :deep(.transaction-title-input .v-field),
    :deep(.transaction-amount-input .v-field),
    :deep(.transaction-date-input .v-field),
    :deep(.transaction-category-select .v-field) {
        font-size: 0.8rem;
    }
}

/* Enhanced form field focus states */
:deep(.transaction-type-select .v-field--focused),
:deep(.transaction-title-input .v-field--focused),
:deep(.transaction-amount-input .v-field--focused),
:deep(.transaction-date-input .v-field--focused),
:deep(.transaction-category-select .v-field--focused) {
    border-color: #4CAF50;
    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
}

/* Account edit form styling */
.account-edit-form {
    background: rgba(255, 255, 255, 0.8);
    border-radius: 12px;
    padding: 16px;
    border: 1px solid rgba(76, 175, 80, 0.2);
}

.account-display {
    background: rgba(255, 255, 255, 0.6);
    border-radius: 8px;
    padding: 12px;
    border: 1px solid rgba(76, 175, 80, 0.1);
}

/* Animation for dialog */
.modern-dialog {
    animation: slideInScale 0.3s ease-out;
}

@keyframes slideInScale {
    from {
        opacity: 0;
        transform: scale(0.9) translateY(-20px);
    }

    to {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}
</style>

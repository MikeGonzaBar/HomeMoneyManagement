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
                <!-- Account Selection -->
                <v-card class="mb-6" variant="tonal" color="primary" rounded="lg">
                    <v-card-text class="pa-4">
                        <div class="d-flex align-center mb-3">
                            <v-avatar size="32" class="me-3 bg-primary">
                                <v-icon color="white">mdi-bank</v-icon>
                            </v-avatar>
                            <div>
                                <h4 class="text-h6 font-weight-bold mb-1">Assign to Account</h4>
                                <p class="text-caption mb-0">Select an existing account or create a new one</p>
                            </div>
                        </div>

                        <!-- Account Selection -->
                        <v-row>
                            <v-col cols="12" md="6">
                                <v-select v-model="selectedAccountId" :items="accountOptions" label="Select Account"
                                    variant="outlined" density="comfortable" prepend-inner-icon="mdi-account"
                                    item-title="title" item-value="value" @update:model-value="handleAccountSelection"
                                    class="mb-2">
                                    <template v-slot:item="{ props, item }">
                                        <v-list-item v-bind="props">
                                            <template v-slot:prepend v-if="item.raw.value !== 'new'">
                                                <v-avatar size="24" class="me-2 bg-primary">
                                                    <v-icon color="white" size="14">mdi-account</v-icon>
                                                </v-avatar>
                                            </template>
                                        </v-list-item>
                                    </template>
                                </v-select>
                            </v-col>
                            <v-col cols="12" md="6">
                                <v-chip v-if="detectedAccountInfo.account_name" color="info" variant="tonal"
                                    class="mb-2">
                                    <v-icon left size="16">mdi-information</v-icon>
                                    Detected: {{ detectedAccountInfo.account_name }} ({{
                                        detectedAccountInfo.account_type }})
                                </v-chip>
                            </v-col>
                        </v-row>

                        <!-- Create New Account Form -->
                        <v-expand-transition>
                            <v-form v-if="selectedAccountId === 'new'" class="account-create-form mt-3">
                                <v-row>
                                    <v-col cols="12" md="4">
                                        <v-text-field v-model="newAccount.name" label="Account Name" variant="outlined"
                                            density="compact" prepend-inner-icon="mdi-account"
                                            :rules="[(v: string) => !!v || 'Account name is required']"
                                            required></v-text-field>
                                    </v-col>
                                    <v-col cols="12" md="4">
                                        <v-text-field v-model="newAccount.bank" label="Bank Name" variant="outlined"
                                            density="compact" prepend-inner-icon="mdi-bank"></v-text-field>
                                    </v-col>
                                    <v-col cols="12" md="4">
                                        <v-select v-model="newAccount.account_type" label="Account Type"
                                            :items="accountTypes" variant="outlined" density="compact"
                                            prepend-inner-icon="mdi-credit-card"
                                            :rules="[(v: string) => !!v || 'Account type is required']"
                                            required></v-select>
                                    </v-col>
                                </v-row>
                            </v-form>
                        </v-expand-transition>
                    </v-card-text>
                </v-card>

                <!-- Display Detected Initial Balance -->
                <v-alert v-if="extractedData?.initial_balance !== null && extractedData?.initial_balance !== undefined"
                    type="info" variant="tonal" class="mt-2" density="compact">
                    <div class="d-flex align-center">
                        <v-icon class="me-2">mdi-information</v-icon>
                        <span>
                            <strong>Detected Initial Balance:</strong>
                            ${{ extractedData.initial_balance.toLocaleString('en-US', {
                                minimumFractionDigits: 2,
                            maximumFractionDigits:
                            2 }) }}
                        </span>
                    </div>
                    <small class="text-grey-darken-1">
                        This will be set as the account's initial balance when creating a new account.
                    </small>
                </v-alert>

                <!-- Statement Period Info -->
                <v-alert v-if="statementPeriod" type="info" variant="tonal" rounded="lg" class="mb-4">
                    <template v-slot:prepend>
                        <v-icon>mdi-calendar-range</v-icon>
                    </template>
                    <div>
                        <strong>Statement Period:</strong>
                        {{ formatDate(statementPeriod.start) }} - {{ formatDate(statementPeriod.end) }}
                    </div>
                </v-alert>

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
                <v-btn color="primary" @click="importTransactions"
                    :disabled="selectedTransactions.length === 0 || !selectedAccountId" rounded="lg"
                    class="smooth-transition">
                    <v-icon left>mdi-content-save</v-icon>
                    Save {{ selectedTransactions.length }} Transaction{{ selectedTransactions.length !== 1 ? 's' : '' }}
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script lang="ts">
import axios from 'axios';

interface DetectedTransaction {
    id?: string;
    title: string;
    amount: number;
    date: string;
    category: string;
    transaction_type: 'Income' | 'Expense' | 'Transfer';
    account_name?: string;
}

interface AccountInfo {
    name: string;
    bank: string;
    account_type: string;
}

interface BankStatementData {
    extracted_data?: {
        transactions: DetectedTransaction[];
        account_name: string;
        account_type: string;
        statement_period?: {
            start: string;
            end: string;
        };
        processing_error?: string;
    };
    account_detected?: AccountInfo;
    transactions?: DetectedTransaction[];
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
            selectedAccountId: null as string | null,
            selectedAccount: null as any,
            detectedAccountInfo: {
                account_name: '',
                account_type: ''
            },
            newAccount: {
                name: '',
                bank: '',
                account_type: ''
            },
            statementPeriod: null as { start: string; end: string } | null,
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
    emits: ['transactionsImported', 'dialogClosed', 'importError'],
    computed: {
        accountOptions() {
            const options = (this as any).accounts.map((acc: any) => ({
                title: `${acc.account_name} (${acc.account_type})`,
                value: acc.id.toString(),
                account: acc
            }));
            options.push({
                title: '+ Create New Account',
                value: 'new',
                account: null
            });
            return options;
        }
    },
    methods: {
        openDialog(bankStatementData: BankStatementData) {
            // Handle new API format with extracted_data
            let transactions: DetectedTransaction[] = [];
            let accountName = '';
            let accountType = '';

            if (bankStatementData.extracted_data) {
                transactions = bankStatementData.extracted_data.transactions || [];
                accountName = bankStatementData.extracted_data.account_name || '';
                accountType = bankStatementData.extracted_data.account_type || '';
                (this as any).statementPeriod = bankStatementData.extracted_data.statement_period || null;
                (this as any).extractedData = bankStatementData.extracted_data; // Store extracted data
            } else if (bankStatementData.transactions) {
                // Fallback to old format
                transactions = bankStatementData.transactions;
                if (bankStatementData.account_detected) {
                    accountName = bankStatementData.account_detected.name || '';
                    accountType = bankStatementData.account_detected.account_type || '';
                }
            }

            // Add unique IDs to transactions if they don't have them
            transactions = transactions.map((t, index) => ({
                ...t,
                id: t.id || `temp-${Date.now()}-${index}`
            }));

            (this as any).detectedAccountInfo = {
                account_name: accountName,
                account_type: accountType
            };

            (this as any).editableTransactions = [...transactions];
            (this as any).selectedTransactions = [...transactions];

            // Try to find matching account (only if accountName is not empty)
            let matchingAccount = null;
            if (accountName && accountName.trim() !== '') {
                matchingAccount = (this as any).accounts.find((acc: any) =>
                    acc.account_name === accountName ||
                    acc.account_name.toLowerCase().includes(accountName.toLowerCase())
                );
            }

            if (matchingAccount) {
                (this as any).selectedAccountId = matchingAccount.id.toString();
                (this as any).selectedAccount = matchingAccount;
            } else {
                (this as any).selectedAccountId = null;
                (this as any).selectedAccount = null;
            }

            // Initialize new account form with detected info
            (this as any).newAccount = {
                name: accountName,
                bank: accountName.split('(')[0]?.trim() || '',
                account_type: accountType || 'Credit Card'
            };

            (this as any).dialog = true;
        },

        closeDialog() {
            (this as any).dialog = false;
            (this as any).editableTransactions = [];
            (this as any).selectedTransactions = [];
            (this as any).selectedAccountId = null;
            (this as any).selectedAccount = null;
            (this as any).detectedAccountInfo = { account_name: '', account_type: '' };
            (this as any).newAccount = { name: '', bank: '', account_type: '' };
            (this as any).statementPeriod = null;
            (this as any).extractedData = null; // Clear extracted data
            (this as any).$emit('dialogClosed');
        },

        formatDate(dateString: string): string {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
        },

        handleAccountSelection(selectedValue: string | null) {
            // Handle null/undefined (user cleared selection)
            if (!selectedValue) {
                (this as any).selectedAccountId = null;
                (this as any).selectedAccount = null;
                return;
            }

            // Handle "new" account option
            if (selectedValue === 'new') {
                (this as any).selectedAccountId = 'new';
                (this as any).selectedAccount = null;
                return;
            }

            // Find the account object from the accounts array
            const account = (this as any).accounts.find((acc: any) => acc.id.toString() === selectedValue);
            if (account) {
                (this as any).selectedAccount = account;
                (this as any).selectedAccountId = selectedValue;
            } else {
                // Account not found - reset selection
                (this as any).selectedAccountId = null;
                (this as any).selectedAccount = null;
            }
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
                let account: any = null;

                // Handle account creation or selection
                if ((this as any).selectedAccountId === 'new') {
                    // Create new account
                    if (!(this as any).newAccount.name || !(this as any).newAccount.account_type) {
                        (this as any).$emit('importError', 'Please fill in all required account fields.');
                        return;
                    }

                    // Use detected initial_balance if available, otherwise default to 0
                    const initialBalance = (this as any).extractedData?.initial_balance ?? 0.0;

                    const accountData = {
                        account_name: (this as any).newAccount.name,
                        account_type: (this as any).newAccount.account_type,
                        bank: (this as any).newAccount.bank || '',
                        total: initialBalance,  // Changed from 0.0 to use detected initial balance
                        owner: (this as any).userData.user.username
                    };

                    const accountResponse = await axios.post('http://localhost:8000/accounts/', accountData);
                    account = accountResponse.data;
                } else if ((this as any).selectedAccountId) {
                    // Use selected account
                    account = (this as any).selectedAccount;
                } else {
                    (this as any).$emit('importError', 'Please select an account or create a new one.');
                    return;
                }

                if (!account || !account.id) {
                    (this as any).$emit('importError', 'Account not found or could not be created.');
                    return;
                }

                // Prepare transactions for import
                const transactionsToImport = (this as any).selectedTransactions.map((transaction: DetectedTransaction) => ({
                    title: transaction.title,
                    transaction_type: transaction.transaction_type,
                    category: transaction.category,
                    date: transaction.date,
                    total: parseFloat(transaction.amount.toString()),
                    owner_id: (this as any).userData.user.username,
                    account_id: account.id.toString()
                }));

                // Import each transaction and track successful imports
                const successfulImports: DetectedTransaction[] = [];
                const failedImports: { transaction: DetectedTransaction; error: any }[] = [];

                for (let i = 0; i < transactionsToImport.length; i++) {
                    try {
                        await axios.post('http://localhost:8000/transactions/create/', transactionsToImport[i]);
                        successfulImports.push((this as any).selectedTransactions[i]);
                    } catch (error: any) {
                        console.error(`Failed to import transaction ${i + 1}:`, error);
                        failedImports.push({
                            transaction: (this as any).selectedTransactions[i],
                            error: error
                        });
                    }
                }

                // Check if all imports failed
                if (successfulImports.length === 0) {
                    const errorMessage = `Failed to import all ${transactionsToImport.length} transactions. Please try again.`;
                    (this as any).$emit('importError', errorMessage);
                    return; // No transactions imported, no balance update needed
                }

                // Update account total based on successfully imported transactions
                // This ensures consistency even if some transactions failed
                const totalChange = successfulImports.reduce((sum: number, transaction: DetectedTransaction) => {
                    const amount = parseFloat(transaction.amount.toString());
                    if (transaction.transaction_type === 'Income') {
                        return sum + amount;
                    } else if (transaction.transaction_type === 'Expense') {
                        return sum - amount;
                    }
                    return sum; // Transfer doesn't change total
                }, 0);

                const currentTotal = account.total || 0;
                const newTotal = currentTotal + totalChange;

                try {
                    await axios.patch(`http://localhost:8000/accounts/details/${(this as any).userData.user.username}/${account.id}/`, {
                        total: newTotal
                    });

                    // Handle partial success scenario
                    if (failedImports.length > 0) {
                        // Some transactions failed but we updated balance for successful ones
                        const warningMessage = `Imported ${successfulImports.length} of ${transactionsToImport.length} transactions. ${failedImports.length} transaction(s) failed to import. Account balance has been updated for the successful imports.`;
                        (this as any).$emit('importError', warningMessage);
                    } else {
                        // All transactions imported successfully
                        (this as any).$emit('transactionsImported', {
                            importedCount: successfulImports.length,
                            accountUpdated: { ...account, total: newTotal }
                        });
                    }
                } catch (balanceError: any) {
                    // Balance update failed - this is a critical error
                    console.error('Failed to update account balance:', balanceError);
                    const errorMessage = `Transactions imported but failed to update account balance. Please update manually.`;
                    (this as any).$emit('importError', errorMessage);
                }

                (this as any).closeDialog();

            } catch (error: any) {
                console.error('Error importing transactions:', error);
                const errorMessage = error.response?.data?.error || error.response?.data?.details || error.message || 'Failed to import transactions. Please try again.';
                (this as any).$emit('importError', errorMessage);
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

/* Account create form styling */
.account-create-form {
    background: rgba(255, 255, 255, 0.8);
    border-radius: 12px;
    padding: 16px;
    border: 1px solid rgba(76, 175, 80, 0.2);
    animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
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

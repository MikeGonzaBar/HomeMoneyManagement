<template>
    <v-slide-group v-model="model" class="pa-2" selected-class="account-selected" mandatory show-arrows>
        <!-- All Accounts Summary Card -->
        <v-slide-group-item v-slot="{ isSelected, toggle, selectedClass }">
            <v-card :class="['ma-2 account-card', selectedClass, { 'selected': isSelected }]"
                :height="$vuetify.display.mobile ? 120 : 140" :width="$vuetify.display.mobile ? 280 : 320"
                @click="toggle" class="smooth-transition hover-lift">
                <v-card-text class="pa-4 d-flex flex-column justify-center align-center text-center h-100">
                    <v-avatar :size="$vuetify.display.mobile ? 32 : ($vuetify.display.mdAndDown ? 36 : 40)"
                        class="mb-1 budget-gradient">
                        <v-icon color="white"
                            :size="$vuetify.display.mobile ? 20 : ($vuetify.display.mdAndDown ? 22 : 24)">mdi-credit-card-multiple-outline</v-icon>
                    </v-avatar>
                    <h5 :class="$vuetify.display.mobile ? 'text-subtitle-2' : ($vuetify.display.mdAndDown ? 'text-subtitle-1' : 'text-h6')"
                        class="font-weight-bold mb-0 budget-text-gradient">All Accounts</h5>
                    <p class="text-caption account-muted-text mb-0">Net Worth</p>
                    <h6 :class="[
                        $vuetify.display.mobile ? 'text-h6' : ($vuetify.display.mdAndDown ? 'text-h6' : 'text-h5'),
                        total >= 0 ? 'account-amount-positive' : 'account-amount-negative',
                        'font-weight-bold mb-0'
                    ]">
                        ${{ total.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
                    </h6>
                </v-card-text>
            </v-card>
        </v-slide-group-item>

        <!-- Individual Account Cards -->
        <v-slide-group-item v-for="(acc, index) in accounts" :key="acc.id"
            v-slot="{ isSelected, toggle, selectedClass }">
            <v-card :class="['ma-2 account-card', selectedClass, { 'selected': isSelected }]"
                :height="$vuetify.display.mobile ? 120 : 140" :width="$vuetify.display.mobile ? 280 : 320"
                @click="toggle" class="smooth-transition hover-lift">
                <!-- Edit Button -->
                <v-btn icon size="small" class="edit-btn" @click.stop="editAccount(acc, index)" variant="text"
                    color="grey-darken-1">
                    <v-icon size="18">mdi-pencil</v-icon>
                </v-btn>

                <v-card-text class="pa-4 d-flex align-center h-100">
                    <!-- Left Side: Icon and Type -->
                    <div class="account-left d-flex flex-column align-center me-4">
                        <!-- Account Type Icon -->
                        <v-avatar :size="$vuetify.display.mobile ? 40 : 48" class="mb-2"
                            :class="getAccountTypeClass(acc.account_type)">
                            <v-icon color="white" :size="$vuetify.display.mobile ? 24 : 28"
                                :icon="getAccountTypeIcon(acc.account_type)" class="account-type-icon"></v-icon>
                        </v-avatar>

                        <!-- Account Type Chip -->
                        <template v-if="getAccountTypeChip(acc.account_type)">
                            <v-chip :color="getAccountTypeChip(acc.account_type)!.color" size="x-small" variant="tonal"
                                class="account-type-chip">
                                <v-icon size="12" class="me-1"
                                    :icon="getAccountTypeChip(acc.account_type)!.icon"></v-icon>
                                {{ getAccountTypeChip(acc.account_type)!.text }}
                            </v-chip>
                        </template>
                    </div>

                    <!-- Right Side: Account Info and Values -->
                    <div class="account-right flex-grow-1">
                        <!-- Account Name and Type -->
                        <div class="mb-2 account-title-wrapper">
                            <h5 :class="[
                                $vuetify.display.mobile ? 'text-subtitle-2' : 'text-subtitle-1',
                                'font-weight-bold mb-1 account-title-truncate'
                            ]" :title="acc.account_name">
                                {{ acc.account_name }}
                            </h5>
                        </div>

                        <!-- Balance Information -->
                        <div v-if="acc.account_type === 'Crédito' || acc.account_type === 'Credit Card' || acc.account_type === 'Credit'"
                            class="credit-balance-info">
                            <!-- Credit Card: Used / Available -->
                            <div class="d-flex justify-space-between align-center mb-1">
                                <span class="text-caption account-muted-text">Used:</span>
                                <span class="text-subtitle-2 font-weight-bold account-amount-warning">
                                    ${{ getUsedCredit(acc).toLocaleString() }}
                                </span>
                            </div>
                            <div class="d-flex justify-space-between align-center mb-1">
                                <span class="text-caption account-muted-text">Available:</span>
                                <span class="text-subtitle-2 font-weight-bold account-amount-positive">
                                    ${{ acc.total.toLocaleString() }}
                                </span>
                            </div>
                            <div class="d-flex justify-space-between align-center">
                                <span class="text-caption account-muted-text">Limit:</span>
                                <span class="text-caption font-weight-medium account-amount-muted">
                                    ${{ getCreditLimit(acc).toLocaleString() }}
                                </span>
                            </div>
                        </div>

                        <div v-else class="regular-balance-info">
                            <!-- Regular Account: Just Balance -->
                            <div class="d-flex justify-space-between align-center">
                                <span class="text-caption" :class="getBalanceLabelClass(acc.account_type)">
                                    {{ getBalanceLabel(acc.account_type, acc.total) }}:
                                </span>
                                <span :class="[
                                    $vuetify.display.mobile ? 'text-subtitle-2' : 'text-subtitle-1',
                                    'font-weight-bold',
                                    getBalanceClass(acc.total, acc.account_type)
                                ]">
                                    ${{ acc.total.toLocaleString() }}
                                </span>
                            </div>
                        </div>
                    </div>
                </v-card-text>
            </v-card>
        </v-slide-group-item>

    </v-slide-group>
    <v-dialog v-model="newAccountModalVisible" max-width="500px" persistent>
        <v-card class="modern-dialog" rounded="xl">
            <v-card-title class="pa-6 pb-2">
                <div class="d-flex align-center">
                    <v-avatar size="40" class="me-3 budget-gradient">
                        <v-icon color="white">mdi-plus</v-icon>
                    </v-avatar>
                    <div>
                        <h3 class="text-h5 font-weight-bold budget-text-gradient mb-0">New Account</h3>
                        <p class="text-caption text-grey-darken-1 mb-0">Create a new financial account</p>
                    </div>
                </div>
            </v-card-title>
            <v-card-text class="pa-6 pt-2">
                <v-container class="pa-0">
                    <v-row>
                        <v-col cols="12">
                            <v-select v-model="newAccountType" :items="accountTypeOptions" label="Account Type"
                                variant="outlined" rounded="lg" prepend-inner-icon="mdi-credit-card"></v-select>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col cols="12">
                            <v-text-field v-model="newBankName" label="Bank Name"
                                :disabled="newAccountType === 'Efectivo'" variant="outlined" rounded="lg"
                                prepend-inner-icon="mdi-bank"></v-text-field>
                        </v-col>
                    </v-row>
                    <v-row v-if="newAccountType === 'Crédito' || newAccountType === 'Credit Card'">
                        <v-col cols="12">
                            <v-alert type="warning" variant="tonal" class="mb-0">
                                <small>Credit card transactions will be recorded as expenses, and payments should be
                                    recorded as income.</small>
                            </v-alert>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col cols="12">
                            <v-text-field v-model="newTotal" label="Initial Balance" type="number" step="0.01"
                                :disabled="newAccountType === 'Crédito'" variant="outlined" rounded="lg"
                                prepend-inner-icon="mdi-currency-usd"></v-text-field>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col cols="12">
                            <v-text-field v-model="newNickname" label="Account Name" variant="outlined" rounded="lg"
                                prepend-inner-icon="mdi-account"></v-text-field>
                        </v-col>
                    </v-row>
                </v-container>
            </v-card-text>
            <v-card-actions class="pa-6 pt-0">
                <v-spacer></v-spacer>
                <v-btn variant="outlined" @click="closeNewAccountModal" class="me-2" rounded="lg">
                    Cancel
                </v-btn>
                <v-btn color="primary" @click="createNewAccount"
                    :disabled="!newAccountType || !newNickname || (newAccountType !== 'Efectivo' && !newBankName) || (newAccountType !== 'Crédito' && !newTotal)"
                    rounded="lg">
                    Create Account
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <v-dialog v-model="editAccountModalVisible" max-width="500px" persistent>
        <v-card class="modern-dialog" rounded="xl">
            <v-card-title class="pa-6 pb-2">
                <div class="d-flex align-center">
                    <v-avatar size="40" class="me-3 budget-gradient">
                        <v-icon color="white">mdi-pencil</v-icon>
                    </v-avatar>
                    <div>
                        <h3 class="text-h5 font-weight-bold budget-text-gradient mb-0">Edit Account</h3>
                        <p class="text-caption text-grey-darken-1 mb-0">Modify account details</p>
                    </div>
                </div>
            </v-card-title>
            <v-card-text class="pa-6 pt-2">
                <v-container class="pa-0">
                    <v-row>
                        <v-col cols="12">
                            <v-select v-model="editAccountType" :items="accountTypeOptions" label="Account Type"
                                variant="outlined" rounded="lg" prepend-inner-icon="mdi-credit-card"></v-select>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col cols="12">
                            <v-text-field v-model="editBankName" label="Bank Name"
                                :disabled="editAccountType === 'Efectivo' || editAccountType === 'Cash'"
                                variant="outlined" rounded="lg" prepend-inner-icon="mdi-bank"></v-text-field>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col cols="12">
                            <v-text-field v-model="editTotal"
                                :label="(editAccountType === 'Crédito' || editAccountType === 'Credit Card' || editAccountType === 'Credit') ? 'Available Credit' : 'Current Balance'"
                                type="number" step="0.01" :disabled="false" variant="outlined" rounded="lg"
                                prepend-inner-icon="mdi-currency-usd"
                                :hint="(editAccountType === 'Crédito' || editAccountType === 'Credit Card' || editAccountType === 'Credit') ? 'For credit cards, this is your available credit (limit - used)' : ''"
                                persistent-hint></v-text-field>
                        </v-col>
                    </v-row>
                    <v-row
                        v-if="editAccountType === 'Crédito' || editAccountType === 'Credit Card' || editAccountType === 'Credit'">
                        <v-col cols="12">
                            <v-text-field v-model="editCreditLimit" label="Credit Limit" type="number" step="0.01"
                                variant="outlined" rounded="lg" prepend-inner-icon="mdi-credit-card-lock"
                                hint="Set the credit limit for this credit card" persistent-hint></v-text-field>
                            <!-- Show calculated used credit -->
                            <v-alert v-if="editCreditLimit && editTotal !== null && editTotal !== undefined" type="info"
                                variant="tonal" density="compact" class="mt-2">
                                <div class="d-flex justify-space-between align-center">
                                    <span class="text-caption">Used Credit:</span>
                                    <span class="font-weight-bold">
                                        ${{ ((editCreditLimit || 0) - (editTotal || 0)).toLocaleString('en-US', {
                                            minimumFractionDigits: 2, maximumFractionDigits: 2
                                        }) }}
                                    </span>
                                </div>
                                <div class="text-caption text-grey-darken-1 mt-1">
                                    Formula: Limit - Available = Used
                                </div>
                            </v-alert>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col cols="12">
                            <v-text-field v-model="editNickname" label="Account Name" variant="outlined" rounded="lg"
                                prepend-inner-icon="mdi-account"></v-text-field>
                        </v-col>
                    </v-row>
                </v-container>
            </v-card-text>
            <v-card-actions class="pa-6 pt-0">
                <v-btn color="error" @click="deleteAccount" variant="outlined" class="me-2" rounded="lg">
                    <v-icon left>mdi-delete</v-icon>
                    Delete
                </v-btn>
                <v-spacer></v-spacer>
                <v-btn variant="outlined" @click="closeEditAccountModal" class="me-2" rounded="lg">
                    Cancel
                </v-btn>
                <v-btn color="primary" @click="sendUpdateAccount" rounded="lg">
                    Update Account
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script lang="ts">
import axios from '@/services/api';
// import Vue from 'vue';
interface Account {
    id: number;
    account_type: string;
    bank: string;
    total: number;
    account_name: string;
    credit_limit?: number | null;
}

interface Data {
    model: number;
    accounts: Account[];
    newAccountModalVisible: boolean;
    editAccountModalVisible: boolean;
    editAccountId: number;
    editAccountIndex: number;
    editAccountType: string;
    editBankName: string;
    editTotal: number;
    editNickname: string;
    editCreditLimit: number | null;
    newAccountType: string;
    newBankName: string;
    newTotal: number;
    newNickname: string;
}

interface ComponentInstance extends Data {
    userData: any;
    $emit(event: string, ...args: any[]): void;
    getAccountTypeIcon(accountType: string): string;
    getAccountTypeClass(accountType: string): string;
    getBalanceClass(balance: number): string;
    deleteAccount(): void;
    accountTotalUpdated(): void;
    sendUpdateAccount(): void;
    editAccount(acc: any, index: number): void;
    closeEditAccountModal(): void;
    closeNewAccountModal(): void;
    createNewAccount(): void;
    total(): number;
}

export default {
    name: 'AccountsCarousel',
    props: {
        userData: {
            type: Object,
            required: true
        }

    },
    data: (): Data => ({
        model: 0,
        accounts: [],
        newAccountModalVisible: false,
        editAccountModalVisible: false,
        editAccountId: 0,
        editAccountIndex: 0,
        editAccountType: '',
        editBankName: '',
        editTotal: 0.0,
        editNickname: '',
        editCreditLimit: null as number | null,
        newAccountType: '',
        newBankName: '',
        newTotal: 0.0,
        newNickname: ''

    }),
    mounted(this: ComponentInstance) {
        axios.get(`/accounts/details/${this.userData.user.username}/0`).then((response: any) => {
            this.accounts = response.data;
        });
        this.model = 0;
    },
    methods: {
        getAccountTypeIcon(this: ComponentInstance, accountType: string): string {
            // Normalize account type for comparison (handle "Savings Account" -> "Savings")
            const normalizedType = accountType.replace(/\s+Account$/i, '').trim();

            switch (normalizedType) {
                case 'Débito':
                case 'Checking':
                case 'Savings':
                    return 'mdi-wallet-outline';
                case 'Crédito':
                case 'Credit Card':
                case 'Credit':
                    return 'mdi-credit-card-outline';
                case 'Efectivo':
                case 'Cash':
                    return 'mdi-cash-multiple';
                case 'Investment':
                    return 'mdi-chart-line';
                case 'Loan':
                case 'Mortgage':
                    return 'mdi-bank-transfer';
                case 'Business':
                    return 'mdi-briefcase';
                default:
                    return 'mdi-bank';
            }
        },

        getAccountTypeClass(this: ComponentInstance, accountType: string): string {
            // Normalize account type for comparison (handle "Savings Account" -> "Savings")
            const normalizedType = accountType.replace(/\s+Account$/i, '').trim();

            switch (normalizedType) {
                case 'Débito':
                case 'Checking':
                case 'Savings':
                    return 'debit-account-gradient';
                case 'Crédito':
                case 'Credit Card':
                case 'Credit':
                    return 'credit-account-gradient';
                case 'Efectivo':
                case 'Cash':
                    return 'cash-account-gradient';
                case 'Investment':
                case 'Loan':
                case 'Mortgage':
                case 'Business':
                case 'Other':
                    return 'budget-gradient';
                default:
                    return 'budget-gradient';
            }
        },

        getAccountTypeChip(this: ComponentInstance, accountType: string): { text: string; color: string; icon: string } | null {
            const normalizedType = accountType?.replace(/\s+Account$/i, '').replace(/\s+Card$/i, '').trim() || '';
            const t = normalizedType.toLowerCase();

            if (['crédito', 'credit card', 'credit'].some(x => t.includes(x) || normalizedType === x)) {
                return { text: 'Credit', color: 'orange', icon: 'mdi-credit-card' };
            }
            if (['débito', 'debit', 'checking', 'savings'].some(x => t.includes(x) || normalizedType === x)) {
                if (t.includes('savings')) return { text: 'Savings', color: 'blue', icon: 'mdi-piggy-bank' };
                if (t.includes('checking')) return { text: 'Checking', color: 'blue', icon: 'mdi-bank' };
                return { text: 'Debit', color: 'blue', icon: 'mdi-wallet-outline' };
            }
            if (['efectivo', 'cash'].some(x => t.includes(x) || normalizedType === x)) {
                return { text: 'Cash', color: 'green', icon: 'mdi-cash-multiple' };
            }
            if (t.includes('investment')) return { text: 'Investment', color: 'purple', icon: 'mdi-chart-line' };
            if (t.includes('loan')) return { text: 'Loan', color: 'amber', icon: 'mdi-bank-transfer' };
            if (t.includes('mortgage')) return { text: 'Mortgage', color: 'brown', icon: 'mdi-home' };
            if (t.includes('business')) return { text: 'Business', color: 'teal', icon: 'mdi-briefcase' };
            return { text: 'Other', color: 'grey', icon: 'mdi-bank' };
        },

        getBalanceClass(this: ComponentInstance, balance: number, accountType: string): string {
            // Normalize account type for comparison
            const normalizedType = accountType.replace(/\s+Account$/i, '').trim();

            if (normalizedType === 'Crédito' || normalizedType === 'Credit Card' || normalizedType === 'Credit') {
                // For credit cards: positive = good (available credit), negative = bad (debt)
                if (balance >= 0) {
                    return 'account-amount-positive';
                } else {
                    return 'account-amount-negative';
                }
            } else {
                // For cash/debit: positive = good, negative = bad
                if (balance >= 0) {
                    return 'account-amount-positive';
                } else {
                    return 'account-amount-negative';
                }
            }
        },

        getBalanceLabel(this: ComponentInstance, accountType: string, balance: number): string {
            // Normalize account type for comparison
            const normalizedType = accountType.replace(/\s+Account$/i, '').trim();

            if (normalizedType === 'Crédito' || normalizedType === 'Credit Card' || normalizedType === 'Credit') {
                if (balance >= 0) {
                    return 'Available Credit';
                } else {
                    return 'Debt';
                }
            } else if (normalizedType === 'Débito' || normalizedType === 'Checking' || normalizedType === 'Savings') {
                return 'Balance';
            } else if (normalizedType === 'Efectivo' || normalizedType === 'Cash') {
                return 'Cash on Hand';
            }
            return 'Balance';
        },

        getBalanceLabelClass(this: ComponentInstance, accountType: string): string {
            // Normalize account type for comparison
            const normalizedType = accountType.replace(/\s+Account$/i, '').trim();

            if (normalizedType === 'Crédito' || normalizedType === 'Credit Card' || normalizedType === 'Credit') {
                return 'account-balance-label account-balance-label--credit';
            } else if (normalizedType === 'Débito' || normalizedType === 'Checking' || normalizedType === 'Savings') {
                return 'account-balance-label account-balance-label--asset';
            } else if (normalizedType === 'Efectivo' || normalizedType === 'Cash') {
                return 'account-balance-label account-balance-label--cash';
            }
            return 'account-balance-label';
        },

        getCreditLimit(this: ComponentInstance, account: any): number {
            // Use credit_limit from database if available, otherwise calculate
            if (account.credit_limit) {
                return account.credit_limit;
            }
            // Fallback: assume credit limit is 1.5x the available credit
            return Math.round(account.total * 1.5);
        },

        getUsedCredit(this: ComponentInstance, account: any): number {
            // Used credit = Credit Limit - Available Credit
            const creditLimit = (this as any).getCreditLimit(account);
            return creditLimit - account.total;
        },

        getAccountNetWorthContribution(this: ComponentInstance, account: Account): number {
            /**
             * Calculate how much this account contributes to net worth.
             * Returns positive for assets, negative for liabilities.
             */
            const accountType = account.account_type;
            const normalizedType = accountType.replace(/\s+Account$/i, '').trim();

            // Credit Cards: Subtract debt (credit_limit - available_credit)
            if (normalizedType === 'Crédito' || normalizedType === 'Credit Card' || normalizedType === 'Credit') {
                if (account.credit_limit) {
                    const debt = account.credit_limit - account.total;
                    return -debt; // Negative because it's debt
                }
                return 0; // No credit limit = no debt
            }

            // Loans and Mortgages: Subtract what you owe
            if (normalizedType === 'Loan' || normalizedType === 'Mortgage') {
                return -account.total; // Negative because it's debt
            }

            // Assets: Add what you have
            // Savings, Checking, Debit, Cash, Investment, Business, Other
            return account.total;
        },

        deleteAccount(this: ComponentInstance) {
            axios.delete(`/accounts/delete/${this.userData.user.username}/${this.editAccountId}/`).then((response: any) => {
                this.editAccountModalVisible = false;
                this.accounts.splice(this.editAccountIndex, 1);
                location.reload();
            });

        },

        accountTotalUpdated(this: ComponentInstance) {
            axios.get(`/accounts/details/${this.userData.user.username}/0`).then((response: any) => {
                this.accounts = response.data;
            });
        },

        sendUpdateAccount(this: ComponentInstance) {
            const editedAccount: any = {
                id: this.editAccountId,
                account_type: this.editAccountType,
                bank: this.editBankName,
                total: this.editTotal,
                account_name: this.editNickname
            }

            // Add credit_limit if it's a credit card account
            if (this.editAccountType === 'Crédito' || this.editAccountType === 'Credit Card' || this.editAccountType === 'Credit') {
                editedAccount.credit_limit = this.editCreditLimit || null;
            } else {
                // Clear credit_limit for non-credit card accounts
                editedAccount.credit_limit = null;
            }

            axios.patch(`/accounts/details/${this.userData.user.username}/${this.editAccountId}/`, editedAccount).then((response: any) => {
                this.editAccountModalVisible = false;
                // Update the account in the local array with the response data
                if (response.data.updated_account) {
                    this.accounts[this.editAccountIndex] = response.data.updated_account;
                } else {
                    this.accounts[this.editAccountIndex] = editedAccount;
                }
                location.reload();
            });

        },
        editAccount(this: ComponentInstance, acc: any, index: number) {
            this.editAccountModalVisible = true;
            this.editAccountType = acc.account_type;
            this.editBankName = acc.bank;
            this.editTotal = acc.total;
            this.editNickname = acc.account_name;
            this.editAccountId = acc.id;
            this.editAccountIndex = index;
            // Set credit_limit if available, otherwise null
            this.editCreditLimit = acc.credit_limit || null;
        },
        closeEditAccountModal(this: ComponentInstance) {
            this.editAccountModalVisible = false;
            this.model = 0;
            // Reset credit limit when closing
            this.editCreditLimit = null;
        },
        openNewAccountModal(this: ComponentInstance) {
            this.newAccountModalVisible = true;
        },
        closeNewAccountModal(this: ComponentInstance) {
            this.newAccountModalVisible = false;
            this.model = 0;
        },
        createNewAccount(this: ComponentInstance) {
            if (this.newAccountType === 'Efectivo' || this.newAccountType === 'Cash') {
                this.newBankName = 'Efectivo';
            }
            if (this.newAccountType === 'Crédito' || this.newAccountType === 'Credit Card') {
                this.newTotal = 0.0;
            }
            axios.post(`/accounts/`, {
                account_type: this.newAccountType,
                bank: this.newBankName,
                total: this.newTotal,
                account_name: this.newNickname
            }).then((response: any) => {
                this.accounts.push(response.data);
                this.newAccountModalVisible = false;
                this.model = 0;
                this.newAccountType = ''
                this.newBankName = ''
                this.newTotal = 0.0
                this.newNickname = ''
                location.reload();
            });
        }
    },
    computed: {
        total(this: ComponentInstance): number {
            /**
             * Calculate net worth (total balance) correctly:
             * - Assets (Savings, Checking, Debit, Cash, Investment, Business, Other): ADD their balance
             * - Liabilities (Credit Cards, Loans, Mortgage): SUBTRACT their debt
             * 
             * For Credit Cards:
             *   - total field = available credit (e.g., $5,209.60)
             *   - debt = credit_limit - available_credit (e.g., $42,000 - $5,209.60 = $36,790.40)
             *   - Net worth contribution = -debt (subtract from net worth)
             */
            return this.accounts.reduce((netWorth: number, account: Account) => {
                return netWorth + (this as any).getAccountNetWorthContribution(account);
            }, 0);
        },
        accountTypeOptions(this: ComponentInstance): Array<{ title: string; value: string }> {
            // Comprehensive list that includes both Spanish (for backward compatibility) 
            // and English types (for AI agent compatibility)
            // Note: "Savings Account" and "Checking Account" are normalized to "Savings" and "Checking" in backend
            return [
                { title: 'Checking', value: 'Checking' },
                { title: 'Savings', value: 'Savings' },
                { title: 'Credit Card', value: 'Credit Card' },
                { title: 'Debit', value: 'Débito' },
                { title: 'Credit', value: 'Crédito' },
                { title: 'Cash', value: 'Efectivo' },
                { title: 'Investment', value: 'Investment' },
                { title: 'Loan', value: 'Loan' },
                { title: 'Mortgage', value: 'Mortgage' },
                { title: 'Business', value: 'Business' },
                { title: 'Other', value: 'Other' }
            ];
        }
    },
    emits: ['accountSelected', 'allAccountSelected', 'accountsModified'],
    watch: {
        accounts: {
            handler(this: ComponentInstance) {
                this.$emit('accountsModified', this.accounts);
            },
            deep: true
        },
        model: {
            handler(this: ComponentInstance, val: number) {
                if (val === 0) {
                    this.$emit('allAccountSelected')
                }
                else {
                    this.$emit('accountSelected', this.accounts[val - 1])
                }
            },
            deep: true
        }
    }
}
</script>

<style scoped>
/* Modern Account Cards */
.account-card {
    --account-accent-blue: #1565c0;
    --account-accent-orange: #c2410c;
    --account-accent-green: #15803d;
    --account-amount-positive: #15803d;
    --account-amount-negative: #dc2626;
    --account-amount-warning: #c2410c;
    background: var(--bb-surface, #ffffff);
    border: 1px solid var(--bb-border-soft, #f3f4f6);
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
    color: var(--bb-text-strong, #1f2937);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    position: relative;
    overflow: hidden;
}

/* Account Type Specific Gradients */
.debit-account-gradient {
    background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
    box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
}

.credit-account-gradient {
    background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
    box-shadow: 0 4px 15px rgba(255, 152, 0, 0.3);
}

.cash-account-gradient {
    background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);
    box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
}

/* Balance Container */
.balance-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
}

/* Account Layout */
.account-left {
    min-width: 60px;
}

.account-right {
    min-width: 0;
    /* Allow flex shrinking */
}

.account-title-wrapper {
    min-width: 0;
}

.account-title-truncate {
    color: var(--bb-text-strong, #1f2937);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.account-muted-text {
    color: var(--bb-text-muted, #6b7280) !important;
}

.account-balance-label {
    color: var(--bb-text-muted, #6b7280) !important;
    font-weight: 700;
}

.account-balance-label--asset {
    color: var(--account-accent-blue) !important;
}

.account-balance-label--credit {
    color: var(--account-accent-orange) !important;
}

.account-balance-label--cash {
    color: var(--account-accent-green) !important;
}

.account-amount-positive {
    color: var(--account-amount-positive) !important;
}

.account-amount-negative {
    color: var(--account-amount-negative) !important;
}

.account-amount-warning {
    color: var(--account-amount-warning) !important;
}

.account-amount-muted {
    color: var(--bb-text-muted, #6b7280) !important;
}

.account-type-chip {
    border: 1px solid color-mix(in srgb, currentColor 28%, transparent);
    font-weight: 700;
}

.account-type-chip :deep(.v-chip__content),
.account-type-chip :deep(.v-icon) {
    color: inherit !important;
}

.account-type-chip :deep(.v-chip__underlay) {
    opacity: 0.12;
}

.credit-balance-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.regular-balance-info {
    display: flex;
    flex-direction: column;
}

/* Credit Card Debt Information */
.credit-debt-info {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1px;
    padding: 4px 8px;
    background: rgba(255, 152, 0, 0.1);
    border-radius: 8px;
    border: 1px solid rgba(255, 152, 0, 0.2);
}

.debt-breakdown {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    min-width: 120px;
}

.account-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
}

.account-card.selected {
    border: 2px solid #4CAF50 !important;
    box-shadow: 0 8px 30px rgba(76, 175, 80, 0.3);
    transform: translateY(-2px);
}

/* Edit Button */
.edit-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    opacity: 0;
    transition: opacity 0.2s ease;
    z-index: 2;
}

.account-card:hover .edit-btn {
    opacity: 1;
}

/* Account Type Specific Colors */
.budget-gradient {
    background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 50%, #8BC34A 100%) !important;
}

.bg-orange {
    background: linear-gradient(135deg, #FF9800 0%, #FFB74D 100%) !important;
}

.bg-blue {
    background: linear-gradient(135deg, #2196F3 0%, #64B5F6 100%) !important;
}

/* Ensure account type icons are white */
.account-type-icon {
    color: white !important;
}

.budget-gradient .v-icon,
.bg-orange .v-icon,
.bg-blue .v-icon {
    color: white !important;
}

/* Specific fixes for account type icons */
.v-avatar.budget-gradient .v-icon,
.v-avatar.bg-orange .v-icon,
.v-avatar.bg-blue .v-icon {
    color: white !important;
}

/* Force white color for all icons in account cards */
.account-card .v-avatar .v-icon {
    color: white !important;
}

/* Smooth transitions for all interactive elements */
.account-card * {
    transition: all 0.2s ease;
}

/* Custom scrollbar for slide group */
.v-slide-group__content {
    scrollbar-width: thin;
    scrollbar-color: #4CAF50 var(--bb-surface-soft, #f1f1f1);
}

.v-slide-group__content::-webkit-scrollbar {
    height: 6px;
}

.v-slide-group__content::-webkit-scrollbar-track {
    background: var(--bb-surface-soft, #f1f1f1);
    border-radius: 3px;
}

.v-slide-group__content::-webkit-scrollbar-thumb {
    background: #4CAF50;
    border-radius: 3px;
}

.v-slide-group__content::-webkit-scrollbar-thumb:hover {
    background: #2E7D32;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .account-card {
        width: 160px !important;
        height: 120px !important;
    }

    .edit-btn {
        opacity: 1;
    }
}

/* Medium screens (tablets, half-monitor) */
@media (max-width: 1280px) and (min-width: 601px) {
    .account-card {
        width: 160px !important;
        height: 130px !important;
    }

    .account-card .v-card-text {
        padding: 14px !important;
    }

    .account-card .v-avatar {
        margin-bottom: 10px !important;
    }

    .account-card h4,
    .account-card h5,
    .account-card h6 {
        line-height: 1.3 !important;
    }

    .account-card p {
        font-size: 0.75rem !important;
        line-height: 1.2 !important;
    }

    .edit-btn {
        top: 6px !important;
        right: 6px !important;
    }

    .edit-btn .v-icon {
        font-size: 18px !important;
    }
}

/* Mobile-specific font size adjustments */
@media (max-width: 600px) {
    .account-card {
        width: 150px !important;
        height: 110px !important;
    }

    .account-card .v-card-text {
        padding: 12px !important;
    }

    .account-card .v-avatar {
        margin-bottom: 8px !important;
    }

    .account-card h4,
    .account-card h5,
    .account-card h6 {
        line-height: 1.2 !important;
    }

    .account-card p {
        font-size: 0.7rem !important;
        line-height: 1.1 !important;
    }

    .edit-btn {
        top: 4px !important;
        right: 4px !important;
    }

    .edit-btn .v-icon {
        font-size: 16px !important;
    }
}

/* Extra small screens (iPhone SE) */
@media (max-width: 375px) {
    .account-card {
        width: 140px !important;
        height: 100px !important;
    }

    .account-card .v-card-text {
        padding: 8px !important;
    }

    .account-card .v-avatar {
        margin-bottom: 6px !important;
    }

    .account-card h4,
    .account-card h5,
    .account-card h6 {
        line-height: 1.1 !important;
    }

    .account-card p {
        font-size: 0.65rem !important;
        line-height: 1.0 !important;
    }
}

/* Modern dialog styling */
.modern-dialog {
    background: var(--bb-surface, #ffffff);
    border: 1px solid var(--bb-border-soft, #f3f4f6);
    box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14);
    color: var(--bb-text-strong, #1f2937);
}

/* Form field styling */
:deep(.v-field) {
    border-radius: 12px;
    transition: all 0.3s ease;
}

:deep(.v-field--focused .v-field__outline) {
    border-color: #4CAF50;
    border-width: 2px;
}

:deep(.v-field:hover) {
    transform: none;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
}

:deep(.v-field--focused) {
    transform: none;
    box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.12);
}
</style>

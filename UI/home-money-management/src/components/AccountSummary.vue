<template>
    <div class="account-summary">
        <!-- Net worth header: the one number the dashboard is about -->
        <div class="account-summary__head">
            <div>
                <p class="dashboard-metric-label mb-0">Net worth</p>
                <p class="account-summary__net-worth"
                    :class="total >= 0 ? 'account-amount-positive' : 'account-amount-negative'">
                    {{ formatMoney(total) }}
                </p>
            </div>
            <div class="d-flex align-center ga-2">
                <v-btn size="small" variant="tonal" color="primary" prepend-icon="mdi-plus" @click="openNewAccountModal">
                    Add account
                </v-btn>
                <v-btn size="small" variant="text" prepend-icon="mdi-refresh" :loading="loading" @click="loadAccounts">
                    Refresh
                </v-btn>
            </div>
        </div>

        <!-- Account filter: All, or one account. Replaces the carousel's slide group.
             Hidden until there is something to filter, so an empty dashboard
             does not open with a pointless dropdown. -->
        <v-select v-if="accounts.length > 0" v-model="selectedAccountId" :items="accountFilterItems"
            item-title="title" item-value="value" label="Show transactions for" density="compact" variant="outlined"
            rounded="lg" hide-details class="account-summary__filter" prepend-inner-icon="mdi-filter-variant" />

        <!-- Load failed: say so, and keep the retry next to the message. -->
        <div v-if="loadError" class="account-summary__empty">
            <v-icon size="40" color="error" class="mb-2">mdi-alert-circle-outline</v-icon>
            <p class="font-semibold text-gray-900 mb-1">We could not load your accounts</p>
            <p class="text-sm text-gray-500 mb-3">{{ loadError }}</p>
            <v-btn color="primary" variant="flat" rounded="lg" size="small" @click="loadAccounts">Try again</v-btn>
        </div>

        <!-- Nothing to show yet -->
        <div v-else-if="!loading && accounts.length === 0" class="account-summary__empty">
            <v-icon size="40" color="grey-lighten-1" class="mb-2">mdi-wallet-outline</v-icon>
            <p class="font-semibold text-gray-900 mb-1">No accounts yet</p>
            <p class="text-sm text-gray-500 mb-3">Add your first account to see it grouped here.</p>
            <v-btn color="primary" variant="flat" rounded="lg" size="small" @click="openNewAccountModal">Add account</v-btn>
        </div>

        <p v-else-if="loading" class="account-summary__empty text-sm text-gray-500">Loading accounts…</p>

        <!-- One row per group, expandable to the accounts inside it -->
        <div v-else class="account-summary__groups">
            <section v-for="group in groups" :key="group.key" class="account-summary__group">
                <header class="account-summary__group-head">
                    <v-avatar size="32" :color="group.key === 'credit' || group.key === 'loans' ? 'deep-orange' : 'primary'">
                        <v-icon size="18" color="white">{{ GROUP_ICONS[group.key] }}</v-icon>
                    </v-avatar>
                    <div class="flex-grow-1">
                        <p class="text-sm font-semibold text-gray-900 mb-0">{{ group.label }}</p>
                        <p class="text-xs text-gray-500 mb-0">
                            {{ group.accounts.length }} account{{ group.accounts.length === 1 ? '' : 's' }}
                        </p>
                    </div>
                    <p class="text-sm font-bold mb-0"
                        :class="group.subtotal >= 0 ? 'account-amount-positive' : 'account-amount-negative'">
                        {{ formatMoney(group.subtotal) }}
                    </p>
                    <v-btn icon size="x-small" variant="text" :aria-label="`Show ${group.label} accounts`"
                        @click="toggleGroup(group.key)">
                        <v-icon size="18">{{ expandedGroups[group.key] ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
                    </v-btn>
                </header>

                <div v-show="expandedGroups[group.key]" class="account-summary__accounts">
                    <div v-for="acc in group.accounts" :key="acc.id" class="account-summary__account"
                        :class="{ 'is-selected': selectedAccountId === acc.id }">
                        <v-avatar size="28" color="grey-lighten-1">
                            <v-icon size="16" color="grey-darken-1">{{ getAccountTypeIcon(acc.account_type) }}</v-icon>
                        </v-avatar>
                        <button type="button" class="account-summary__account-main" @click="selectAccount(acc)">
                            <span class="account-summary__account-name">{{ acc.account_name }}</span>
                            <span class="account-summary__account-meta">
                                {{ acc.bank || 'Unknown institution' }} · {{ getAccountTypeChip(acc.account_type)?.text }}
                                <template v-if="acc.credit_card_statement_snapshot?.summary?.deferred_balance">
                                    · MSI ${{ formatMoney(Number(acc.credit_card_statement_snapshot.summary.deferred_balance)) }}
                                </template>
                            </span>
                        </button>
                        <div class="text-right">
                            <p class="text-sm font-semibold mb-0" :class="getBalanceClass(acc.total, acc.account_type)">
                                {{ getBalanceLabel(acc.account_type, acc.total) }}: {{ formatMoney(acc.total) }}
                            </p>
                            <p v-if="isCreditCard(acc) && getCreditLimit(acc)" class="text-xs text-gray-500 mb-0">
                                {{ formatMoney(getUsedCredit(acc)) }} used of {{ formatMoney(getCreditLimit(acc)) }}
                            </p>
                        </div>
                        <v-btn icon size="x-small" variant="text" :aria-label="`Edit ${acc.account_name}`"
                            @click="editAccount(acc, accounts.indexOf(acc))">
                            <v-icon size="16">mdi-pencil</v-icon>
                        </v-btn>

                        <!-- Statement detail, carried over from the carousel so the
                             AFORE / investment / MSI data is not lost with it. -->
                        <div v-if="hasStatementDetail(acc)" class="account-summary__detail">
                            <div v-if="acc.retirement_metadata?.breakdown">
                                <p class="account-summary__detail-title">
                                    Retirement statement{{ acc.retirement_metadata.statement_date ? ` · ${acc.retirement_metadata.statement_date}` : '' }}
                                </p>
                                <p v-if="acc.retirement_metadata.institution" class="text-xs text-gray-500 mb-1">
                                    {{ acc.retirement_metadata.institution }} · AFORE
                                </p>
                                <p v-for="(amount, name) in acc.retirement_metadata.breakdown.subaccounts || {}"
                                    :key="String(name)" class="text-xs text-gray-600">
                                    {{ name }}: {{ formatMoney(Number(amount)) }}
                                </p>
                            </div>
                            <div v-if="acc.statement_snapshot?.positions?.length">
                                <p class="account-summary__detail-title">
                                    Investment positions{{ acc.statement_snapshot.statement_date ? ` · ${acc.statement_snapshot.statement_date}` : '' }}
                                </p>
                                <p v-for="(position, index) in acc.statement_snapshot.positions" :key="index"
                                    class="text-xs text-gray-600">
                                    {{ position.investment_id || position.name || 'Investment' }} ·
                                    {{ formatMoney(Number(position.total || position.capital || 0)) }}
                                </p>
                            </div>
                            <div v-if="acc.credit_card_statement_snapshot?.deferred_purchases?.length">
                                <p class="account-summary__detail-title">
                                    Deferred purchases{{ acc.credit_card_statement_snapshot.statement_date ? ` · ${acc.credit_card_statement_snapshot.statement_date}` : '' }}
                                </p>
                                <p v-for="plan in acc.credit_card_statement_snapshot.deferred_purchases" :key="plan.source_key"
                                    class="text-xs text-gray-600">
                                    {{ plan.merchant }} · {{ formatMoney(Number(plan.remaining_balance || 0)) }} remaining
                                    <span class="text-gray-400">
                                        ({{ plan.installment_number || '?' }} of {{ plan.installment_count || '?' }})
                                    </span>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>

        <p class="account-summary__footnote">
            <router-link to="/accounts" class="account-summary__link">Manage all accounts</router-link>
        </p>
    </div>

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
                                <small>Card purchases are recorded as <strong>expenses</strong>. Card payments are
                                    <strong>transfers</strong> from a bank account, not income.</small>
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
import { GROUP_ICONS, groupAccounts, netWorthContribution } from '@/services/accountGroups';
import type { GroupKey, SnapshotAccount } from '@/services/accountGroups';
// import Vue from 'vue';
type Account = SnapshotAccount;

interface Data {
    selectedAccountId: number | null;
    expandedGroups: Record<string, boolean>;
    loading: boolean;
    loadError: string;
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
    $router: { push(path: string): void };
    GROUP_ICONS: Record<GroupKey, string>;
    getAccountTypeIcon(accountType: string): string;
    getAccountTypeChip(accountType: string): { text: string; color: string; icon: string } | null;
    getBalanceClass(balance: number, accountType: string): string;
    getBalanceLabel(accountType: string, balance: number): string;
    getCreditLimit(account: Account): number;
    getUsedCredit(account: Account): number;
    isCreditCard(account: Account): boolean;
    hasStatementDetail(account: Account): boolean;
    deleteAccount(): void;
    accountTotalUpdated(): void;
    sendUpdateAccount(): void;
    editAccount(acc: any, index: number): void;
    closeEditAccountModal(): void;
    closeNewAccountModal(): void;
    createNewAccount(): void;
    selectAccount(account: Account): void;
    toggleGroup(key: GroupKey): void;
    formatMoney(value: number): string;
    total(): number;
    groups: Array<{ key: GroupKey; label: string; accounts: Account[]; subtotal: number }>;
    accountFilterItems: Array<{ title: string; value: number | null }>;
}

export default {
    name: 'AccountSummary',
    props: {
        userData: {
            type: Object,
            required: true
        }

    },
    data: (): Data => ({
        selectedAccountId: null,
        // Cash and savings open by default: they are what most visits look at.
        expandedGroups: { cash: true, savings: true },
        loading: true,
        loadError: '',
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
        (this as any).loadAccounts();
    },
    methods: {
        /**
         * The single source of truth for the summary. Kept as one method so the
         * refresh button, mount and post-mutation reloads cannot drift apart.
         */
        loadAccounts(this: ComponentInstance) {
            this.loading = true;
            this.loadError = '';
            axios.get(`/accounts/details/${this.userData.user.username}/0`)
                .then((response: any) => {
                    this.accounts = Array.isArray(response.data) ? response.data : [];
                })
                .catch((error: any) => {
                    this.loadError = error?.response?.data?.error || 'Could not load your accounts.';
                })
                .finally(() => {
                    this.loading = false;
                });
        },

        selectAccount(this: ComponentInstance, account: Account) {
            this.selectedAccountId = this.selectedAccountId === account.id ? null : account.id;
        },

        toggleGroup(this: ComponentInstance, key: GroupKey) {
            this.expandedGroups = { ...this.expandedGroups, [key]: !this.expandedGroups[key] };
        },

        formatMoney(this: ComponentInstance, value: number): string {
            return `$${Number(value || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        },

        /** Whether an account carries statement detail worth showing. */
        hasStatementDetail(this: ComponentInstance, account: Account): boolean {
            return Boolean(
                account.retirement_metadata?.breakdown
                || account.statement_snapshot?.positions?.length
                || account.credit_card_statement_snapshot?.deferred_purchases?.length
            );
        },

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
                case 'Retirement':
                    return 'mdi-piggy-bank-outline';
                case 'Loan':
                case 'Mortgage':
                    return 'mdi-bank-transfer';
                case 'Business':
                    return 'mdi-briefcase';
                default:
                    return 'mdi-bank';
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
            if (t.includes('retirement')) return { text: 'Retirement', color: 'indigo', icon: 'mdi-piggy-bank-outline' };
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
            } else if (normalizedType === 'Retirement') {
                return 'Retirement balance';
            }
            return 'Balance';
        },

        /**
         * The card's real limit, or 0 when none was recorded. The old carousel
         * invented one (1.5x available credit) to fill the card; a made-up limit
         * is worse than an honest blank, and the Accounts page shows the same.
         */
        getCreditLimit(this: ComponentInstance, account: Account): number {
            return Number(account.credit_limit) || 0;
        },

        getUsedCredit(this: ComponentInstance, account: Account): number {
            // Used credit = Credit Limit - Available Credit
            return this.getCreditLimit(account) - Number(account.total || 0);
        },
        isCreditCard(this: ComponentInstance, account: Account): boolean {
            return ['Crédito', 'Credit Card', 'Credit'].includes(account.account_type.replace(/\s+Account$/i, '').trim());
        },

        deleteAccount(this: ComponentInstance) {
            axios.delete(`/accounts/delete/${this.userData.user.username}/${this.editAccountId}/`).then(() => {
                this.editAccountModalVisible = false;
                // Refetch rather than location.reload(): a full reload throws away
                // the page the user came from and every filter they set.
                (this as any).loadAccounts();
            }).catch((error: any) => {
                this.loadError = error?.response?.data?.error || 'Could not delete that account.';
            });
        },

        accountTotalUpdated(this: ComponentInstance) {
            (this as any).loadAccounts();
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

            axios.patch(`/accounts/details/${this.userData.user.username}/${this.editAccountId}/`, editedAccount).then(() => {
                this.editAccountModalVisible = false;
                (this as any).loadAccounts();
            }).catch((error: any) => {
                this.loadError = error?.response?.data?.error || 'Could not update that account.';
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
            // Reset credit limit when closing
            this.editCreditLimit = null;
        },
        openNewAccountModal(this: ComponentInstance) {
            this.newAccountModalVisible = true;
        },
        closeNewAccountModal(this: ComponentInstance) {
            this.newAccountModalVisible = false;
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
            }).then(() => {
                this.newAccountModalVisible = false;
                this.newAccountType = ''
                this.newBankName = ''
                this.newTotal = 0.0
                this.newNickname = '';
                (this as any).loadAccounts();
            }).catch((error: any) => {
                this.loadError = error?.response?.data?.error || 'Could not create that account.';
            });
        }
    },
    computed: {
        /** Exposed so the template can pick a group's icon without importing. */
        GROUP_ICONS(this: ComponentInstance) {
            return GROUP_ICONS;
        },
        /**
         * Net worth straight from the shared rule, so this card, the Accounts
         * page and the API can never disagree. `total` on a card is *available*
         * credit, not money, which is exactly why this is not a plain sum.
         */
        total(this: ComponentInstance): number {
            return this.accounts.reduce((sum: number, account: Account) => sum + netWorthContribution(account), 0);
        },
        /** The same fixed grouping the Accounts page uses. */
        groups(this: ComponentInstance) {
            return groupAccounts(this.accounts).map((group) => ({
                key: group.key,
                label: group.label,
                accounts: group.accounts as Account[],
                subtotal: group.subtotal,
            }));
        },
        /** "All accounts" plus one entry per account, in group order. */
        accountFilterItems(this: ComponentInstance): Array<{ title: string; value: number | null }> {
            const items: Array<{ title: string; value: number | null }> = [{ title: 'All accounts', value: null }];
            for (const group of (this as any).groups) {
                for (const account of group.accounts) {
                    items.push({ title: `${group.label} · ${account.account_name}`, value: account.id });
                }
            }
            return items;
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
                { title: 'Retirement', value: 'Retirement' },
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
        // The carousel used a slide index; the summary drives the same filter
        // from an id, so the parent contract (accountSelected/allAccountSelected)
        // is unchanged.
        selectedAccountId: {
            handler(this: ComponentInstance, val: number | null) {
                if (val === null) {
                    this.$emit('allAccountSelected');
                }
                else {
                    const account = this.accounts.find((item: Account) => item.id === val);
                    if (account) this.$emit('accountSelected', account);
                }
            }
        }
    }
}
</script>

<style scoped>
/* Account group summary. Replaces the carousel's per-account cards: a net
   worth header, an account filter, and one collapsible row per group. */
.account-summary {
    --account-amount-positive: #15803d;
    --account-amount-negative: #dc2626;
    color: var(--bb-text-strong, #1f2937);
}

.account-summary__head {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    justify-content: space-between;
    margin-bottom: 1rem;
}

.account-summary__net-worth {
    font-size: 1.75rem;
    font-weight: 700;
    line-height: 1.2;
    margin: 0.25rem 0 0;
}

.account-amount-positive {
    color: var(--account-amount-positive, #15803d);
}

.account-amount-negative {
    color: var(--account-amount-negative, #dc2626);
}

.account-summary__filter {
    margin-bottom: 1rem;
    max-width: 22rem;
}

.account-summary__empty {
    align-items: center;
    background: var(--bb-surface-soft, #f9fafb);
    border: 1px dashed var(--bb-border-soft, #e5e7eb);
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    padding: 2rem 1rem;
    text-align: center;
}

.account-summary__groups {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.account-summary__group {
    background: var(--bb-surface, #ffffff);
    border: 1px solid var(--bb-border-soft, #f3f4f6);
    border-radius: 12px;
    overflow: hidden;
}

.account-summary__group-head {
    align-items: center;
    display: flex;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
}

.account-summary__accounts {
    border-top: 1px solid var(--bb-border-soft, #f3f4f6);
}

.account-summary__account {
    align-items: center;
    border-bottom: 1px solid var(--bb-border-soft, #f9fafb);
    display: grid;
    gap: 0.75rem;
    grid-template-columns: auto minmax(0, 1fr) auto auto;
    padding: 0.625rem 1rem;
}

.account-summary__account:last-child {
    border-bottom: 0;
}

.account-summary__account.is-selected {
    background: var(--bb-brand-tint, #f0fdf4);
}

/* The row is a filter control, so it must read as one to a screen reader. */
.account-summary__account-main {
    background: none;
    border: 0;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
    min-width: 0;
    padding: 0;
    text-align: left;
}

.account-summary__account-name {
    color: var(--bb-text-strong, #1f2937);
    font-size: 0.875rem;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.account-summary__account-meta {
    color: var(--bb-text-muted, #6b7280);
    font-size: 0.75rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.account-summary__detail {
    grid-column: 1 / -1;
    padding: 0.5rem 0 0.25rem;
}

.account-summary__detail-title {
    color: var(--bb-text-muted, #6b7280);
    font-size: 0.75rem;
    font-weight: 600;
    margin: 0 0 0.25rem;
    text-transform: uppercase;
}

.account-summary__footnote {
    font-size: 0.8125rem;
    margin: 0.75rem 0 0;
    text-align: right;
}

.account-summary__link {
    color: var(--bb-brand-primary, #16a34a);
    font-weight: 600;
    text-decoration: none;
}

.account-summary__link:hover {
    text-decoration: underline;
}

@media (max-width: 640px) {
    .account-summary__account {
        grid-template-columns: auto minmax(0, 1fr) auto;
    }

    /* The edit button drops to its own row rather than squeezing the balance. */
    .account-summary__account > .v-btn {
        grid-column: 3;
        grid-row: 1;
    }
}

.budget-gradient {
    background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
}

.budget-text-gradient {
    background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
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

<template>
    <div>
        <!-- Create / edit transaction -->
        <v-dialog v-model="dialog" :max-width="$vuetify.display.mobile ? '95%' : '600px'" persistent>
            <v-card class="modern-dialog" rounded="xl">
                <v-card-title class="pa-6 pb-2">
                    <div class="d-flex align-center">
                        <v-avatar size="40" class="me-3 budget-gradient">
                            <v-icon color="white">{{ editedItem.id ? 'mdi-pencil' : 'mdi-plus' }}</v-icon>
                        </v-avatar>
                        <div>
                            <h3 class="text-h5 font-weight-bold budget-text-gradient mb-0">{{ formTitle }}</h3>
                            <p class="text-caption text-grey-darken-1 mb-0">Enter transaction details</p>
                        </div>
                    </div>
                </v-card-title>
                <v-card-text class="pa-6 pt-2">
                    <v-container class="pa-0">
                        <v-row>
                            <v-col cols="12" md="6">
                                <v-select v-model="editedItem.transaction_type" label="Transaction Type"
                                    :items="transactionTypes" variant="outlined" rounded="lg"></v-select>
                            </v-col>
                            <v-col cols="12" md="6">
                                <v-text-field v-model="editedItem.date" label="Date" type="date" variant="outlined"
                                    rounded="lg"></v-text-field>
                            </v-col>
                        </v-row>
                        <v-row>
                            <v-col cols="12" md="8">
                                <v-text-field v-model="editedItem.title" label="Transaction Title" variant="outlined"
                                    rounded="lg"></v-text-field>
                            </v-col>
                            <v-col cols="12" md="4">
                                <v-text-field v-model="editedItem.total" label="Amount" type="number" step="0.01"
                                    variant="outlined" rounded="lg"
                                    prepend-inner-icon="mdi-currency-usd"></v-text-field>
                            </v-col>
                        </v-row>
                        <v-row v-if="editedItem.transaction_type === 'Transfer'">
                            <v-col cols="12" md="6">
                                <v-select v-model="editedItem.from_account_id" label="From Account"
                                    :items="internalAccounts" item-title="title" item-value="value"
                                    variant="outlined" rounded="lg"
                                    prepend-inner-icon="mdi-bank-transfer-out"></v-select>
                            </v-col>
                            <v-col cols="12" md="6">
                                <v-select v-model="editedItem.to_account_id" label="To Account"
                                    :items="internalAccounts" item-title="title" item-value="value"
                                    variant="outlined" rounded="lg"
                                    prepend-inner-icon="mdi-bank-transfer-in"></v-select>
                            </v-col>
                        </v-row>
                        <v-row v-else>
                            <v-col cols="12" md="6">
                                <v-select v-model="editedItem.account_id" label="Account" :items="internalAccounts"
                                    item-title="title" item-value="value" variant="outlined" rounded="lg"
                                    prepend-inner-icon="mdi-bank"></v-select>
                            </v-col>
                            <v-col cols="12" md="6">
                                <v-select v-model="editedItem.category" label="Category" :items="categories"
                                    variant="outlined" rounded="lg" prepend-inner-icon="mdi-tag"></v-select>
                            </v-col>
                        </v-row>
                    </v-container>
                </v-card-text>
                <v-card-actions class="pa-6 pt-0">
                    <v-spacer></v-spacer>
                    <v-btn variant="outlined" @click="close" class="me-2" rounded="lg">
                        Cancel
                    </v-btn>
                    <v-btn color="primary" @click="save" :disabled="!isFormValid" rounded="lg"
                        class="smooth-transition">
                        {{ editedItem.id ? 'Update' : 'Create' }}
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- Delete confirmation -->
        <v-dialog v-model="dialogDelete" max-width="500px" persistent>
            <v-card class="modern-dialog" rounded="xl">
                <v-card-title class="pa-6 pb-2">
                    <div class="d-flex align-center">
                        <v-avatar size="40" class="me-3 bg-error">
                            <v-icon color="white">mdi-delete</v-icon>
                        </v-avatar>
                        <div>
                            <h3 class="text-h5 font-weight-bold text-error mb-0">Delete Transaction</h3>
                            <p class="text-caption text-grey-darken-1 mb-0">This action cannot be undone</p>
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
                    <v-btn color="error" @click="confirmDelete" rounded="lg">
                        Delete
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<script lang="ts">
import axios from '@/services/api';
import { CATEGORIES, TRANSACTION_TYPES } from '@/constants/taxonomy';

interface Transaction {
    id: number;
    transaction_type: string;
    category: string;
    date: string;
    title: string;
    total: number;
    owner_id: string;
    account_id: string;
    from_account_id?: string;
    to_account_id?: string;
}

interface Account {
    id: number;
    account_name: string;
}

/**
 * Shared create / edit / delete dialog for transactions.
 *
 * Owned by the pages that need it (the dashboard table and the Transactions
 * page) so the form, validation and API calls live in exactly one place.
 * Call `openCreate()`, `openEdit(item)` or `openDelete(item)` through a template
 * ref. Emits `saved` (`{ transaction, isNew }`) and `deleted` (`{ id }`) so the
 * host can refresh its list.
 */
export default {
    name: 'TransactionDialog',
    props: {
        accounts: {
            type: Array as () => Account[],
            required: true,
        },
        username: {
            type: String,
            default: '',
        },
    },
    emits: ['saved', 'deleted'],
    data() {
        return {
            dialog: false,
            dialogDelete: false,
            editedItem: {
                id: 0,
                owner_id: '',
                account_id: '',
                title: '',
                category: '',
                date: '',
                total: 0,
                transaction_type: '',
                from_account_id: '',
                to_account_id: '',
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
                from_account_id: '',
                to_account_id: '',
            } as Transaction,
            // Sorted copy so the in-place sort never touches the shared list.
            categories: [...CATEGORIES].sort(),
            transactionTypes: TRANSACTION_TYPES,
        };
    },
    computed: {
        formTitle(): string {
            return (this as any).editedItem.id ? 'Edit Transaction' : 'New Transaction';
        },
        internalAccounts(): Array<{ title: string; value: string }> {
            return ((this as any).accounts as Account[]).map((account) => ({
                title: account.account_name,
                value: String(account.id),
            }));
        },
        isFormValid(): boolean {
            const item = (this as any).editedItem;
            // Transfers do not show a category selector. They always use the
            // ledger category "Account Transfer", so do not block a complete
            // transfer form because that hidden field is blank.
            const hasCategory = item.transaction_type === 'Transfer' || !!item.category;
            const base = !!item.transaction_type && hasCategory && !!item.date && !!item.title && Number(item.total) > 0;
            if (item.transaction_type === 'Transfer') {
                return base && !!item.from_account_id && !!item.to_account_id && item.from_account_id !== item.to_account_id;
            }
            return base && !!item.account_id;
        },
    },
    methods: {
        openCreate() {
            (this as any).editedItem = { ...(this as any).defaultItem };
            (this as any).dialog = true;
        },
        openEdit(item: Transaction) {
            const copy: any = { ...item };
            const total = Number(copy.total);
            if (total < 0) copy.total = Math.abs(total);
            (this as any).editedItem = copy;
            (this as any).dialog = true;
        },
        openDelete(item: Transaction) {
            (this as any).editedItem = { ...item };
            (this as any).dialogDelete = true;
        },
        close() {
            (this as any).dialog = false;
            (this as any).$nextTick(() => {
                (this as any).editedItem = { ...(this as any).defaultItem };
            });
        },
        closeDelete() {
            (this as any).dialogDelete = false;
            (this as any).$nextTick(() => {
                (this as any).editedItem = { ...(this as any).defaultItem };
            });
        },
        save() {
            const item: any = { ...(this as any).editedItem };
            item.owner_id = (this as any).username;
            if (item.transaction_type === 'Transfer') {
                item.account_id = null;
                item.category = 'Account Transfer';
            } else {
                item.from_account_id = null;
                item.to_account_id = null;
            }
            const isNew = !item.id;
            const request = isNew
                ? axios.post('/transactions/create/', item)
                : axios.patch(`/transactions/update/${item.id}/`, item);
            request
                .then((response: any) => {
                    const transaction = isNew
                        ? response.data
                        : (response.data.updated_transaction ?? response.data);
                    (this as any).$emit('saved', { transaction, isNew });
                })
                .catch((error: any) => {
                    console.log(error);
                });
            (this as any).close();
        },
        confirmDelete() {
            const id = (this as any).editedItem.id;
            axios.delete(`/transactions/delete/${id}/`)
                .then(() => {
                    (this as any).$emit('deleted', { id });
                })
                .catch((error: any) => {
                    console.log(error);
                });
            (this as any).closeDelete();
        },
    },
};
</script>

<style scoped>
.modern-dialog {
    background: var(--bb-surface, #ffffff);
    border: 1px solid var(--bb-border-soft, #f3f4f6);
    box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14);
}

:deep(.v-field) {
    border-radius: 12px;
}
</style>

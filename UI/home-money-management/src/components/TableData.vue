<template>
    <v-data-table :headers="headers" :items="internalTransactions" :sort-by="[{ key: 'date', order: 'asc' }]"
        class="elevation-1">
        <template v-slot:top>
            <v-toolbar flat>
                <v-toolbar-title>Transactions</v-toolbar-title>
                <v-divider class="mx-4" inset vertical></v-divider>
                <v-spacer></v-spacer>
                <v-dialog v-model="dialog" max-width="500px">
                    <template v-slot:activator="{ props }">
                        <v-btn color="primary" dark class="mb-2" v-bind="props">
                            New Transaction
                        </v-btn>
                    </template>
                    <v-card>
                        <v-card-title>
                            <span class="text-h5">{{ formTitle }}</span>
                        </v-card-title>
                        <v-card-text>
                            <v-container>
                                <v-row>
                                    <v-col>
                                        <v-select v-model="editedItem.transaction_type" label="Transaction type"
                                            :items="['Expense', 'Income',]"></v-select>
                                    </v-col>
                                    <v-col>
                                        <v-text-field v-model="editedItem.date" label="Date" type="date">

                                        </v-text-field>
                                    </v-col>
                                </v-row>
                                <v-row>
                                    <v-col>
                                        <v-text-field v-model="editedItem.title" label="Title">
                                        </v-text-field>
                                    </v-col>
                                    <v-col>
                                        <v-text-field v-model="editedItem.total" label="Transaction Total">
                                        </v-text-field>
                                    </v-col>
                                </v-row>
                                <v-row>
                                    <v-col>
                                        <v-select v-model="editedItem.account_id" label="Account"
                                            :items="internalAccounts"></v-select>

                                    </v-col>
                                </v-row>
                                <v-row>
                                    <v-col>
                                        <v-select v-model="editedItem.category" label="Category"
                                            :items="categories"></v-select>

                                    </v-col>
                                </v-row>
                            </v-container>
                        </v-card-text>
                        <v-card-actions>
                            <v-spacer></v-spacer>
                            <v-btn color="blue-darken-1" variant="text" @click="close">
                                Cancel
                            </v-btn>
                            <v-btn color="blue-darken-1" variant="text" @click="saveTransaction" :disabled="!isFormValid">
                                Save
                            </v-btn>
                        </v-card-actions>
                    </v-card>
                </v-dialog>
                <v-dialog v-model="dialogDelete" max-width="500px">
                    <v-card>
                        <v-card-title class="text-h5">Are you sure you want to delete this item?</v-card-title>
                        <v-card-actions>
                            <v-spacer></v-spacer>
                            <v-btn color="blue-darken-1" variant="text" @click="closeDelete">Cancel</v-btn>
                            <v-btn color="blue-darken-1" variant="text" @click="deleteItemConfirm">OK</v-btn>
                            <v-spacer></v-spacer>
                        </v-card-actions>
                    </v-card>
                </v-dialog>
            </v-toolbar>
        </template>
        <template v-slot:item.actions="{ item }">
            <v-icon size="small" class="me-2" @click="editItem(item)">
                mdi-pencil
            </v-icon>
            <v-icon size="small" @click="deleteItem(item)">
                mdi-delete
            </v-icon>
        </template>

    </v-data-table>
</template>

<style scoped></style>

<script lang="ts">
import axios from 'axios';
import { defineComponent } from 'vue';
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

export default defineComponent({
    name: 'TableData',
    props: {
        transactions: {
            type: Array as () => Transaction[],
            required: true
        },
        userData: {
            type: Object,
            required: true
        },
        accounts: {
            type: Array as () => Account[],
            required: true
        }
    },
    data: () => ({
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
            { title: 'Category', key: 'category' },
            { title: 'Date', key: 'date' },
            { title: 'Total', key: 'total' },
            { title: 'Actions', key: 'actions', sortable: false },
        ],

        editedIndex: -1,
        editedItem: {
            id: 0, // replace with actual id
            owner_id: 'temp', // replace with actual owner_id
            account_id: '', // replace with actual account_id
            title: '',
            category: '',
            date: '',
            total: 0,
            transaction_type: '',
        },
        defaultItem: {
            id: 0, // replace with actual id
            owner_id: '', // replace with actual owner_id
            account_id: '', // replace with actual account_id
            title: '',
            category: '',
            date: '',
            total: 0,
            transaction_type: '',
        },
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
    }),

    computed: {
        formTitle() {
            return this.editedIndex === -1 ? 'New Transaction' : 'Edit Transaction'
        },
        isFormValid(): boolean {
            let isValid = true;
            Object.values(this.editedItem).forEach((value) => {
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
            handler(newVal) {
                this.internalTransactions = []
                newVal.forEach((transaction: Transaction) => {
                    let tempTransaction = transaction
                    if (transaction.transaction_type === 'Expense') {
                        tempTransaction.total = -transaction.total
                    }
                    this.internalTransactions.push(tempTransaction)
                })
            }
        },
        dialog(val) {
            val || this.close()
        },
        dialogDelete(val) {
            val || this.closeDelete()
        },
        accounts: {
            immediate: true,
            handler(newVal) {
                this.internalAccounts = []
                newVal.forEach((account: Account) => {
                    this.internalAccounts.push(account.account_name)
                })
            }
        },
    },

    mounted() {
        this.categories.sort()
    },
    emits: ['updateAccounts', 'updateIncomeExpense'],
    methods: {
        editItem(item: Transaction) {
            this.editedIndex = this.internalTransactions.indexOf(item)
            this.editedItem = Object.assign({}, item)
            if (this.editedItem.total < 0) {
                this.editedItem.total *= -1;
            }
            this.dialog = true
        },
        deleteItem(item: Transaction) {
            this.editedIndex = this.internalTransactions.indexOf(item)
            this.editedItem = Object.assign({}, item)
            this.dialogDelete = true
        },

        deleteItemConfirm() {
            let idToDelete = this.editedItem.id;
            let account_id = this.editedItem.account_id;
            let account = this.accounts.find(account => account.id === Number(account_id));
            let new_total = account!.total + (-1 * (this.editedItem.total));
            axios.delete(`http://localhost:8000/transactions/delete/${idToDelete}/`)
                .then(response => {
                    this.internalTransactions.splice(this.editedIndex, 1);
                    axios.patch(`http://localhost:8000/accounts/details/${this.userData.user.username}/${account_id}/`, {
                        "total": new_total,
                    })
                        .then(patchResponse => {
                            this.$emit('updateAccounts');
                            this.$emit('updateIncomeExpense');

                            this.closeDelete();
                        })
                        .catch(patchError => {
                            console.log(patchError);
                        });
                })
                .catch(error => {
                    console.log(error);
                });
        },
        close() {
            this.dialog = false
            this.$nextTick(() => {
                this.editedItem = Object.assign({}, this.defaultItem)
                this.editedIndex = -1
            })
        },
        closeDelete() {
            this.dialogDelete = false
            this.$nextTick(() => {
                this.editedItem = Object.assign({}, this.defaultItem)
                this.editedIndex = -1
            })
        },

        getDiff(oldTransaction: Transaction) {
            let diff = 0;
            if (oldTransaction.transaction_type === 'Expense' && this.editedItem.transaction_type === 'Expense') {
                diff = Math.abs(oldTransaction.total) - this.editedItem.total;
            }
            else if (oldTransaction.transaction_type === 'Income' && this.editedItem.transaction_type === 'Income') {
                diff = -(oldTransaction.total) + Number(this.editedItem.total);
            }
            else {
                diff = Math.abs(oldTransaction.total) + Number(this.editedItem.total);
                if (oldTransaction.transaction_type === 'Income' && this.editedItem.transaction_type === 'Expense') {
                    diff *= -1;
                }
            }
            return diff;

        },
        saveTransaction() {
            if (this.editedIndex > -1) {
                let oldTransaction = this.internalTransactions[this.editedIndex];
                if (this.editedItem === oldTransaction) {
                    this.close();
                    return;
                }
                let diff = this.getDiff(oldTransaction);

                let account_id = this.editedItem.account_id;
                let account = this.accounts.find(account => account.id === Number(account_id));
                let new_total = account!.total + diff;

                Object.assign(this.internalTransactions[this.editedIndex], this.editedItem)
                axios.patch(`http://localhost:8000/transactions/update/${this.editedItem.id}/`, this.editedItem)
                    .then(response => {
                        console.log(response);
                        axios.patch(`http://localhost:8000/accounts/details/${this.userData.user.username}/${account_id}/`, {
                            "total": new_total,
                        })
                            .then(patchResponse => {
                                console.log(patchResponse);
                                this.$emit('updateAccounts');
                                this.$emit('updateIncomeExpense');
                            })
                            .catch(patchError => {
                                console.log(patchError);
                            });
                    })
                    .catch(error => {
                        console.log(error);
                    });
            } else {
                // this.internalTransactions.push(this.editedItem)
                this.editedItem.owner_id = this.userData.user.id
                let account_name = this.editedItem.account_id;
                let account = this.accounts.find(account => account.account_name === account_name);
                let account_id = account ? account.id : null;
                this.editedItem.account_id = String(account_id)
                let new_total = account!.total
                if (this.editedItem.transaction_type === 'Expense') {
                    new_total -= Number(this.editedItem.total)
                } else {
                    new_total += Number(this.editedItem.total)
                }

                axios.post('http://localhost:8000/transactions/create/', this.editedItem)
                    .then(response => {
                        console.log(response)
                        this.internalTransactions.push(response.data)
                        // Make the PATCH request here
                        axios.patch(`http://localhost:8000/accounts/details/${this.userData.user.username}/${account_id}/`, {
                            "total": new_total,
                        })
                            .then(patchResponse => {
                                console.log(patchResponse);
                                this.$emit('updateAccounts');
                                this.$emit('updateIncomeExpense');
                            })
                            .catch(patchError => {
                                console.log(patchError);
                            });
                    })
                    .catch(error => {
                        console.log(error)
                    })
            }
            this.close()
        },
    },
});
</script>
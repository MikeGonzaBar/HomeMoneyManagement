<template>
    <v-slide-group v-model="model" class="pa-2" selected-class="account-selected" mandatory show-arrows>
        <!-- All Accounts Summary Card -->
        <v-slide-group-item v-slot="{ isSelected, toggle, selectedClass }">
            <v-card :class="['ma-2 account-card', selectedClass, { 'selected': isSelected }]" height="140" width="180"
                @click="toggle" class="smooth-transition hover-lift">
                <v-card-text class="pa-4 d-flex flex-column justify-center align-center text-center h-100">
                    <v-avatar :size="$vuetify.display.mobile ? 32 : ($vuetify.display.mdAndDown ? 36 : 40)"
                        class="mb-1 budget-gradient">
                        <v-icon color="white"
                            :size="$vuetify.display.mobile ? 20 : ($vuetify.display.mdAndDown ? 22 : 24)">mdi-credit-card-multiple-outline</v-icon>
                    </v-avatar>
                    <h5 :class="$vuetify.display.mobile ? 'text-subtitle-2' : ($vuetify.display.mdAndDown ? 'text-subtitle-1' : 'text-h6')"
                        class="font-weight-bold mb-0 budget-text-gradient">All Accounts</h5>
                    <p class="text-caption text-grey-darken-1 mb-0">Total Balance</p>
                    <h6 :class="$vuetify.display.mobile ? 'text-h6' : ($vuetify.display.mdAndDown ? 'text-h6' : 'text-h5')"
                        class="font-weight-bold budget-text-gradient mb-0">${{ total.toLocaleString()
                        }}</h6>
                </v-card-text>
            </v-card>
        </v-slide-group-item>

        <!-- Individual Account Cards -->
        <v-slide-group-item v-for="(acc, index) in accounts" :key="acc.id"
            v-slot="{ isSelected, toggle, selectedClass }">
            <v-card :class="['ma-2 account-card', selectedClass, { 'selected': isSelected }]" height="140" width="180"
                @click="toggle" class="smooth-transition hover-lift">
                <!-- Edit Button -->
                <v-btn icon size="small" class="edit-btn" @click.stop="editAccount(acc, index)" variant="text"
                    color="grey-darken-1">
                    <v-icon size="18">mdi-pencil</v-icon>
                </v-btn>

                <v-card-text class="pa-4 d-flex flex-column justify-center align-center text-center h-100">
                    <!-- Account Type Icon -->
                    <v-avatar :size="$vuetify.display.mobile ? 32 : ($vuetify.display.mdAndDown ? 36 : 40)" class="mb-3"
                        :class="getAccountTypeClass(acc.account_type)">
                        <v-icon color="white"
                            :size="$vuetify.display.mobile ? 20 : ($vuetify.display.mdAndDown ? 22 : 24)"
                            :icon="getAccountTypeIcon(acc.account_type)" class="account-type-icon"></v-icon>
                    </v-avatar>

                    <!-- Account Name -->
                    <h5 :class="[
                        $vuetify.display.mobile ? 'text-caption' : ($vuetify.display.mdAndDown ? 'text-caption' : 'text-h7'),
                        $vuetify.display.mobile ? 'text-truncate' : '',
                        'font-weight-bold'
                    ]" :style="$vuetify.display.mobile ? 'max-width: 140px;' : ''">
                        {{ acc.account_name }}
                    </h5>

                    <!-- Account Type -->
                    <p class="text-caption text-grey-darken-1 mb-2">{{ acc.account_type }}</p>

                    <!-- Balance -->
                    <h4
                        :class="[$vuetify.display.mobile ? 'text-subtitle-2' : ($vuetify.display.mdAndDown ? 'text-subtitle-2' : 'text-h7'), 'font-weight-bold mb-0', getBalanceClass(acc.total)]">
                        ${{ acc.total.toLocaleString() }}
                    </h4>
                </v-card-text>
            </v-card>
        </v-slide-group-item>

        <!-- Add Account Card -->
        <v-slide-group-item v-slot="{ isSelected, toggle, selectedClass }">
            <v-card :class="['ma-2 account-card add-account-card', selectedClass]" height="140" width="180"
                @click="toggle" class="smooth-transition hover-lift" variant="outlined">
                <v-card-text class="pa-4 d-flex flex-column justify-center align-center text-center h-100">
                    <v-avatar :size="$vuetify.display.mobile ? 32 : ($vuetify.display.mdAndDown ? 36 : 40)" class="mb-3"
                        color="grey-lighten-3">
                        <v-icon color="grey-darken-1"
                            :size="$vuetify.display.mobile ? 20 : ($vuetify.display.mdAndDown ? 22 : 24)">mdi-plus</v-icon>
                    </v-avatar>
                    <h4 :class="$vuetify.display.mobile ? 'text-caption' : ($vuetify.display.mdAndDown ? 'text-caption' : 'text-h6')"
                        class="font-weight-bold text-grey-darken-1">Add Account</h4>
                    <p class="text-caption text-grey-darken-1 mb-0">Create new account</p>
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
                            <v-select v-model="newAccountType" :items="[
                                { title: 'Debit', value: 'Débito' },
                                { title: 'Credit', value: 'Crédito' },
                                { title: 'Cash', value: 'Efectivo' }
                            ]" label="Account Type" variant="outlined" rounded="lg"
                                prepend-inner-icon="mdi-credit-card"></v-select>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col cols="12">
                            <v-text-field v-model="newBankName" label="Bank Name"
                                :disabled="newAccountType === 'Efectivo'" variant="outlined" rounded="lg"
                                prepend-inner-icon="mdi-bank"></v-text-field>
                        </v-col>
                    </v-row>
                    <v-row v-if="newAccountType === 'Crédito'">
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
                            <v-select v-model="editAccountType" :items="[
                                { title: 'Debit', value: 'Débito' },
                                { title: 'Credit', value: 'Crédito' },
                                { title: 'Cash', value: 'Efectivo' }
                            ]" label="Account Type" variant="outlined" rounded="lg"
                                prepend-inner-icon="mdi-credit-card"></v-select>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col cols="12">
                            <v-text-field v-model="editBankName" label="Bank Name"
                                :disabled="editAccountType === 'Efectivo'" variant="outlined" rounded="lg"
                                prepend-inner-icon="mdi-bank"></v-text-field>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col cols="12">
                            <v-text-field v-model="editTotal" label="Current Balance" type="number" step="0.01"
                                :disabled="true" variant="outlined" rounded="lg"
                                prepend-inner-icon="mdi-currency-usd"></v-text-field>
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
import axios from 'axios';
// import Vue from 'vue';
interface Account {
    id: number;
    account_type: string;
    bank: string;
    total: number;
    account_name: string;
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
        newAccountType: '',
        newBankName: '',
        newTotal: 0.0,
        newNickname: ''

    }),
    mounted(this: ComponentInstance) {
        axios.get(`http://localhost:8000/accounts/details/${this.userData.user.username}/0`).then((response: any) => {
            this.accounts = response.data;
        });
        this.model = 0;
    },
    methods: {
        getAccountTypeIcon(this: ComponentInstance, accountType: string): string {
            switch (accountType) {
                case 'Débito':
                    return 'mdi-wallet-outline';
                case 'Crédito':
                    return 'mdi-credit-card-outline';
                case 'Efectivo':
                    return 'mdi-cash-multiple';
                default:
                    return 'mdi-bank';
            }
        },

        getAccountTypeClass(this: ComponentInstance, accountType: string): string {
            switch (accountType) {
                case 'Débito':
                    return 'budget-gradient';
                case 'Crédito':
                    return 'bg-orange';
                case 'Efectivo':
                    return 'bg-blue';
                default:
                    return 'budget-gradient';
            }
        },

        getBalanceClass(this: ComponentInstance, balance: number): string {
            if (balance >= 0) {
                return 'text-success';
            } else {
                return 'text-error';
            }
        },

        deleteAccount(this: ComponentInstance) {
            axios.delete(`http://localhost:8000/accounts/delete/${this.userData.user.username}/${this.editAccountId}/`).then((response: any) => {
                this.editAccountModalVisible = false;
                this.accounts.splice(this.editAccountIndex, 1);
                location.reload();
            });

        },

        accountTotalUpdated(this: ComponentInstance) {
            axios.get(`http://localhost:8000/accounts/details/${this.userData.user.username}/0`).then((response: any) => {
                this.accounts = response.data;
            });
        },

        sendUpdateAccount(this: ComponentInstance) {
            const editedAccount = {
                id: this.editAccountId,
                account_type: this.editAccountType,
                bank: this.editBankName,
                total: this.editTotal,
                account_name: this.editNickname,
                owner: this.userData.user.username
            }
            axios.patch(`http://localhost:8000/accounts/details/${this.userData.user.username}/${this.editAccountId}/`, editedAccount).then((response: any) => {
                this.editAccountModalVisible = false;
                this.accounts[this.editAccountIndex] = editedAccount;
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
        },
        closeEditAccountModal(this: ComponentInstance) {
            this.editAccountModalVisible = false;
            this.model = 0;
        },
        closeNewAccountModal(this: ComponentInstance) {
            this.newAccountModalVisible = false;
            this.model = 0;
        },
        createNewAccount(this: ComponentInstance) {
            if (this.newAccountType === 'Efectivo') {
                this.newBankName = 'Efectivo';
            }
            if (this.newAccountType === 'Crédito') {
                this.newTotal = 0.0;
            }
            axios.post(`http://localhost:8000/accounts/`, {
                account_type: this.newAccountType,
                bank: this.newBankName,
                total: this.newTotal,
                account_name: this.newNickname,
                owner: this.userData.user.username
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
            return this.accounts.reduce((acc: number, item: Account) => acc + item.total, 0);
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
                else if (val === this.accounts.length + 1) {
                    this.newAccountModalVisible = !this.newAccountModalVisible;
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
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    position: relative;
    overflow: hidden;
}

.account-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.account-card.selected {
    border: 2px solid #4CAF50;
    box-shadow: 0 8px 30px rgba(76, 175, 80, 0.3);
    transform: translateY(-2px);
}

.add-account-card {
    border: 2px dashed #BDBDBD !important;
    background: rgba(255, 255, 255, 0.7) !important;
}

.add-account-card:hover {
    border-color: #4CAF50 !important;
    background: rgba(76, 175, 80, 0.05) !important;
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
    scrollbar-color: #4CAF50 #f1f1f1;
}

.v-slide-group__content::-webkit-scrollbar {
    height: 6px;
}

.v-slide-group__content::-webkit-scrollbar-track {
    background: #f1f1f1;
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

/* Animation for new cards */
.account-card {
    animation: slideInUp 0.4s ease-out;
}

@keyframes slideInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Modern dialog styling */
.modern-dialog {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.2);
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
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
}

:deep(.v-field--focused) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
}
</style>
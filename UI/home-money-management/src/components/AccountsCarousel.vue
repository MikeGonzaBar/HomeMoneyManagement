<template>
    <v-slide-group v-model="model" class="pa-4" selected-class="bg-primary" mandatory show-arrows>
        <v-slide-group-item v-slot="{ isSelected, toggle, selectedClass }">
            <v-card color="white" :class="['ma-4', selectedClass]" height="auto" width="160" @click="toggle">
                <v-icon>mdi-credit-card-multiple-outline</v-icon>
                <b>Todas tus cuentas</b>
                <br>
                <br>
                <p>${{ total }}</p>
                <div class="d-flex fill-height align-center justify-center">
                    <v-scale-transition>

                    </v-scale-transition>
                </div>
            </v-card>
        </v-slide-group-item>
        <v-slide-group-item v-for="(acc, index) in accounts" :key="acc.id" v-slot="{ isSelected, toggle, selectedClass }">
            <v-card color="white" :class="['ma-4', selectedClass]" height="auto" width="160" @click="toggle">
                <v-btn icon class="ma-1"
                    style="position: absolute; top: 0; right: 0; width: 32px; height: 32px; min-width: 32px; min-height: 32px; border-radius: 0;"
                    :rounded="false" elevation="0">
                    <v-icon @click.stop="editAccount(acc, index)">mdi-pencil</v-icon>
                </v-btn>
                <v-icon v-if="acc.account_type === 'Débito'">mdi-wallet-outline</v-icon>
                <v-icon v-else-if="acc.account_type === 'Crédito'">mdi-credit-card-outline</v-icon>
                <v-icon v-else="acc.account_type === 'Efectivo'">mdi-cash-multiple</v-icon>
                <b>
                    {{ acc.account_name }}
                </b>
                <br>
                <i>{{ acc.account_type }}</i>
                <p>${{ acc.total }}</p>
                <div class="d-flex fill-height align-center justify-center">
                    <v-scale-transition>

                    </v-scale-transition>
                </div>
            </v-card>
        </v-slide-group-item>
        <v-slide-group-item v-slot="{ isSelected, toggle, selectedClass }">
            <v-card color="white" :class="['ma-4', selectedClass]" height="auto" width="106" @click="toggle">
                <b>AGREGAR CUENTA+</b>
                <div class="d-flex fill-height align-center justify-center">
                    <v-scale-transition>

                    </v-scale-transition>
                </div>
            </v-card>
        </v-slide-group-item>
    </v-slide-group>
    <v-dialog v-model="newAccountModalVisible">
        <v-card style="width: 400px;" class="mx-auto">
            <v-card-title>
                Nueva cuenta
            </v-card-title>
            <v-card-text>
                <v-select v-model="newAccountType" :items="['Débito', 'Crédito', 'Efectivo']"
                    label="Tipo de cuenta"></v-select>
                <v-text-field v-model="newBankName" label="Nombre del banco"
                    :disabled="newAccountType === 'Efectivo'"></v-text-field>
                <div v-if="newAccountType === 'Crédito'" style="color: red;">
                    <small>Cuando una cuenta es de crédito, las transacciones dadas de alta se pondrán como gasto y el
                        pago
                        de esta tarjeta deberá de seleccionarse como ingreso</small>
                </div>
                <v-text-field v-model="newTotal" label="Total" type="number"
                    :disabled="newAccountType === 'Crédito'"></v-text-field>
                <v-text-field v-model="newNickname" label="Nombre de la cuenta"></v-text-field>
            </v-card-text>
            <v-card-actions>
                <v-btn color="primary" @click="createNewAccount"
                    :disabled="(!newAccountType || !newNickname || (newAccountType !== 'Efectivo' && !newBankName) || (newAccountType !== 'Crédito' && !newTotal)) && (!newAccountType || !newNickname || (newAccountType === 'Efectivo') || (newAccountType === 'Crédito'))">Crear</v-btn>
                <v-btn @click="closeNewAccountModal">Cancelar</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <v-dialog v-model="editAccountModalVisible">
        <v-card style="width: 400px;" class="mx-auto">
            <v-card-title>
                Editar cuenta
            </v-card-title>
            <v-card-text>
                <v-select v-model="editAccountType" :items="['Débito', 'Crédito', 'Efectivo']"
                    label="Tipo de cuenta"></v-select>
                <v-text-field v-model="editBankName" label="Nombre del banco"
                    :disabled="newAccountType === 'Efectivo'"></v-text-field>
                <v-text-field v-model="editTotal" label="Total" type="number" :disabled=true></v-text-field>
                <v-text-field v-model="editNickname" label="Nombre de la cuenta"></v-text-field>
            </v-card-text>
            <v-card-actions>
                <v-btn color="primary" @click="sendUpdateAccount">Actualizar</v-btn>
                <v-btn @click="closeEditAccountModal">Cancelar</v-btn>
                <v-btn color="red" @click="deleteAccount">Borrar</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script lang="ts">
import axios from 'axios';
import { defineComponent } from 'vue';
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

export default defineComponent({
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
    mounted() {
        axios.get(`http://localhost:8000/accounts/details/${this.userData.user.username}/0`).then(response => {
            this.accounts = response.data;
        });
        this.model = 0;
    },
    methods: {
        deleteAccount() {
            axios.delete(`http://localhost:8000/accounts/delete/${this.userData.user.username}/${this.editAccountId}/`).then(response => {
                this.editAccountModalVisible = false;
                this.accounts.splice(this.editAccountIndex, 1);
            });
        },

        accountTotalUpdated() {
            axios.get(`http://localhost:8000/accounts/details/${this.userData.user.username}/0`).then(response => {
                this.accounts = response.data;
            });
        },

        sendUpdateAccount() {
            const editedAccount = {
                id: this.editAccountId,
                account_type: this.editAccountType,
                bank: this.editBankName,
                total: this.editTotal,
                account_name: this.editNickname,
                owner: this.userData.user.username
            }
            axios.patch(`http://localhost:8000/accounts/details/${this.userData.user.username}/${this.editAccountId}/`, editedAccount).then(response => {
                this.editAccountModalVisible = false;
                this.accounts[this.editAccountIndex] = editedAccount;
            });
        },
        editAccount(acc: any, index: number) {
            this.editAccountModalVisible = true;
            this.editAccountType = acc.account_type;
            this.editBankName = acc.bank;
            this.editTotal = acc.total;
            this.editNickname = acc.account_name;
            this.editAccountId = acc.id;
            this.editAccountIndex = index;
        },
        closeEditAccountModal() {
            this.editAccountModalVisible = false;
            this.model = 0;
        },
        closeNewAccountModal() {
            this.newAccountModalVisible = false;
            this.model = 0;
        },
        createNewAccount() {
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
            }).then(response => {
                this.accounts.push(response.data);
                this.newAccountModalVisible = false;
                this.model = 0;
                this.newAccountType = ''
                this.newBankName = ''
                this.newTotal = 0.0
                this.newNickname = ''
            });
        }
    },
    computed: {
        total(): number {
            return this.accounts.reduce((acc, item) => acc + item.total, 0);
        }
    },
    emits: ['accountSelected', 'allAccountSelected', 'accountsModified'],
    watch: {
        accounts: {
            handler() {
                this.$emit('accountsModified', this.accounts);
            },
            deep: true
        },
        model: {
            handler(val) {
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
    },
});
</script>
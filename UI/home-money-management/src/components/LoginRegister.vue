<template>
    <div>
        <v-card class="card">
            <v-card-title class="card-title">
                {{ cardTitle }}
            </v-card-title>
            <v-card-text class="form-container">
                <v-form v-if="loginFormVisible">
                    <v-text-field label="Username" v-model="loginUsername" required></v-text-field>
                    <v-text-field label="Password" v-model="loginPassword" required type="password"></v-text-field>
                    <v-btn @click="login" class="primary">Login</v-btn>
                </v-form>

                <v-form v-else>
                    <v-text-field label="Username" v-model="registerUsername" required></v-text-field>
                    <v-text-field label="First name" v-model="registerFirstname" required></v-text-field>
                    <v-text-field label="Last name" v-model="registerLastname" required></v-text-field>
                    <v-text-field label="Password" v-model="registerPassword" required type="password"></v-text-field>
                    <v-text-field label="Confirm your password" v-model="registerConfirmPassword" required
                        type="password"></v-text-field>
                    <v-btn @click="register" class="primary">Register</v-btn>
                </v-form>

                <div class="toggle-text">
                    <span>
                        {{ toggleButtonText }}
                    </span>
                    <v-btn @click="toggleForm" class="link-btn">{{ toggleButtonAction }}</v-btn>
                </div>
            </v-card-text>
        </v-card>
    </div>
</template>
  
<script lang="ts">
import axios from 'axios';
export default {
    name: 'LoginRegister',
    data() {
        return {
            loginFormVisible: true,
            loginUsername: '',
            loginPassword: '',
            registerUsername: '',
            registerFirstname: '',
            registerLastname: '',
            registerPassword: '',
            registerConfirmPassword: '',
        };
    },
    computed: {
        cardTitle() {
            return this.loginFormVisible ? 'Login' : 'Register';
        },
        toggleButtonText() {
            return this.loginFormVisible
                ? "If you don't have an account, click here to register"
                : 'If you already have an account, click here to login';
        },
        toggleButtonAction() {
            return this.loginFormVisible ? 'Register' : 'Login';
        },
    },
    methods: {
        login(): void {
            axios.post(`http://localhost:8000/user/${this.loginUsername}/`, {
                password: this.loginPassword,
            }).then(response => {
                this.$emit('userDataSent', response.data.user)
                localStorage.setItem('money_management_user', JSON.stringify(response.data));
            });
        },
        register(): void {
            axios.post('http://localhost:8000/user/', {
                username: this.registerUsername,
                password: this.registerPassword,
                first_name: this.registerFirstname,
                last_name: this.registerLastname
            }).then(response => {
                this.$emit('userDataSent', response.data)
                localStorage.setItem('money_management_user', JSON.stringify(response.data));

            });
        },
        toggleForm() {
            this.loginFormVisible = !this.loginFormVisible;
        },
    },
};
</script>
  
<style scoped>
/* Styles for Login/Register component */
.card {
    max-width: 400px;
    margin: auto;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.card-title {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 20px;
}

.form-container {
    display: flex;
    flex-direction: column;
}

.btn {
    margin-top: 10px;
}

.v-text-field {
    margin-bottom: 10px;
}

.v-btn {
    color: white;
}

.v-btn.primary {
    background-color: #2196F3;
}

.v-btn.link-btn {
    color: #2196F3;
    text-decoration: none;
}

.toggle-text {
    margin-top: 20px;
    text-align: center;
}
</style>
  
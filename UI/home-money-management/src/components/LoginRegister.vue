<template>
    <div class="login-register-container">
        <!-- Main Content Container -->
        <div class="main-content-wrapper">
            <!-- Right Side - Login Form -->
            <div class="auth-section">
                <v-card class="modern-auth-card glass-card shadow-strong" rounded="xl"
                    :max-width="$vuetify.display.mobile ? '100%' : '500'">
                    <!-- Header with Logo -->
                    <v-card-title :class="$vuetify.display.mobile ? 'pa-4 pb-2 text-center' : 'pa-8 pb-4 text-center'">
                        <div class="d-flex flex-column align-center">
                            <v-avatar :size="$vuetify.display.mobile ? 60 : 80" class="mb-4 budget-gradient">
                                <v-img src="@/assets/logo.png" alt="Home Money Management" />
                            </v-avatar>
                            <h1 :class="$vuetify.display.mobile ? 'text-h5' : 'text-h4'"
                                class="font-weight-bold budget-text-gradient mb-2">Get Started</h1>
                            <p :class="$vuetify.display.mobile ? 'text-caption' : 'text-body-1'"
                                class="text-grey-darken-1 mb-0">Manage your finances with ease</p>
                        </div>
                    </v-card-title>

                    <v-card-text :class="$vuetify.display.mobile ? 'pa-4 pt-2' : 'pa-8 pt-2'">
                        <!-- Login Form -->
                        <v-form v-if="(this as any).loginFormVisible" @submit.prevent="(this as any).login">
                            <v-text-field v-model="(this as any).loginUsername" label="Username" variant="outlined"
                                rounded="lg" prepend-inner-icon="mdi-account"
                                :class="$vuetify.display.mobile ? 'mb-3' : 'mb-4'" required></v-text-field>

                            <v-text-field v-model="(this as any).loginPassword" label="Password" type="password"
                                variant="outlined" rounded="lg" prepend-inner-icon="mdi-lock"
                                :class="$vuetify.display.mobile ? 'mb-3' : 'mb-4'" @keyup.enter="(this as any).login"
                                required></v-text-field>

                            <!-- Login Error Message -->
                            <v-alert v-if="(this as any).loginError" type="error" variant="tonal"
                                :class="$vuetify.display.mobile ? 'mb-3' : 'mb-4'" closable
                                @click:close="(this as any).loginError = ''">
                                <v-icon left>mdi-alert-circle</v-icon>
                                {{ (this as any).loginError }}
                            </v-alert>

                            <v-btn @click="(this as any).login" color="primary"
                                :size="$vuetify.display.mobile ? 'default' : 'large'" block rounded="lg"
                                class="smooth-transition hover-lift" :class="$vuetify.display.mobile ? 'mb-3' : 'mb-4'"
                                :loading="(this as any).isLoading" :disabled="(this as any).isLoading">
                                <v-icon left v-if="!(this as any).isLoading">mdi-login</v-icon>
                                {{ (this as any).isLoading ? 'Signing In...' : 'Sign In' }}
                            </v-btn>
                        </v-form>

                        <!-- Register Form -->
                        <v-form v-else @submit.prevent="(this as any).register">
                            <v-text-field v-model="(this as any).registerUsername" label="Username" variant="outlined"
                                rounded="lg" prepend-inner-icon="mdi-account"
                                :class="$vuetify.display.mobile ? 'mb-3' : 'mb-3'" required></v-text-field>

                            <v-row>
                                <v-col :cols="$vuetify.display.mobile ? 12 : 6">
                                    <v-text-field v-model="(this as any).registerFirstname" label="First Name"
                                        variant="outlined" rounded="lg"
                                        :class="$vuetify.display.mobile ? 'mb-3' : 'mb-3'" required></v-text-field>
                                </v-col>
                                <v-col :cols="$vuetify.display.mobile ? 12 : 6">
                                    <v-text-field v-model="(this as any).registerLastname" label="Last Name"
                                        variant="outlined" rounded="lg"
                                        :class="$vuetify.display.mobile ? 'mb-3' : 'mb-3'" required></v-text-field>
                                </v-col>
                            </v-row>

                            <v-text-field v-model="(this as any).registerPassword" label="Password" type="password"
                                variant="outlined" rounded="lg" prepend-inner-icon="mdi-lock"
                                :class="$vuetify.display.mobile ? 'mb-3' : 'mb-3'" required></v-text-field>

                            <v-text-field v-model="(this as any).registerConfirmPassword" label="Confirm Password"
                                type="password" variant="outlined" rounded="lg" prepend-inner-icon="mdi-lock-check"
                                @keyup.enter="(this as any).register" :class="$vuetify.display.mobile ? 'mb-3' : 'mb-4'"
                                required></v-text-field>

                            <!-- Registration Error Message -->
                            <v-alert v-if="(this as any).registerError" type="error" variant="tonal"
                                :class="$vuetify.display.mobile ? 'mb-3' : 'mb-4'" closable
                                @click:close="(this as any).registerError = ''">
                                <v-icon left>mdi-alert-circle</v-icon>
                                {{ (this as any).registerError }}
                            </v-alert>

                            <v-btn @click="(this as any).register" color="primary"
                                :size="$vuetify.display.mobile ? 'default' : 'large'" block rounded="lg"
                                class="smooth-transition hover-lift" :class="$vuetify.display.mobile ? 'mb-3' : 'mb-4'"
                                :loading="(this as any).isLoading" :disabled="(this as any).isLoading">
                                <v-icon left v-if="!(this as any).isLoading">mdi-account-plus</v-icon>
                                {{ (this as any).isLoading ? 'Creating Account...' : 'Create Account' }}
                            </v-btn>
                        </v-form>

                        <!-- Toggle Form -->
                        <div class="text-center">
                            <p class="text-body-2 text-grey-darken-1 mb-2">
                                {{ (this as any).toggleButtonText }}
                            </p>
                            <v-btn @click="(this as any).toggleForm" variant="text" color="primary"
                                class="smooth-transition">
                                {{ (this as any).toggleButtonAction }}
                            </v-btn>
                        </div>
                    </v-card-text>
                </v-card>
            </div>
        </div>
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
            loginError: '',
            registerError: '',
            isLoading: false,
        };
    },
    computed: {
        cardTitle(): string {
            return (this as any).loginFormVisible ? 'Login' : 'Register';
        },
        toggleButtonText(): string {
            return (this as any).loginFormVisible
                ? "Don't have an account?"
                : 'Already have an account?';
        },
        toggleButtonAction(): string {
            return (this as any).loginFormVisible ? 'Register' : 'Sign In';
        },
    },
    methods: {
        login(): void {
            // Clear previous errors
            (this as any).loginError = '';

            // Validate form data
            if (!(this as any).loginUsername || !(this as any).loginPassword) {
                (this as any).loginError = 'Please fill in both username and password fields.';
                return;
            }

            // Show loading state
            (this as any).isLoading = true;

            axios.post(`http://localhost:8000/user/${(this as any).loginUsername}/`, {
                password: (this as any).loginPassword,
            }).then(response => {
                // Success - user authenticated
                (this as any).$emit('userDataSent', response.data.user)
                localStorage.setItem('money_management_user', JSON.stringify(response.data));
                location.reload();
            }).catch(error => {
                // Handle authentication errors
                console.error('Login error:', error);

                let errorMessage = 'Login failed. Please try again.';

                if (error.response) {
                    // Server responded with error status
                    if (error.response.status === 401) {
                        // Check if it's a specific error message from server
                        if (error.response.data && error.response.data.error) {
                            if (error.response.data.error === 'User not found') {
                                errorMessage = 'Username not found. Please check your username or create a new account.';
                            } else if (error.response.data.error === 'Incorrect password') {
                                errorMessage = 'Incorrect password. Please check your password.';
                            } else {
                                errorMessage = 'Invalid username or password. Please check your credentials.';
                            }
                        } else {
                            errorMessage = 'Invalid username or password. Please check your credentials.';
                        }
                    } else if (error.response.status === 404) {
                        errorMessage = 'User not found. Please check your username.';
                    } else if (error.response.status === 500) {
                        errorMessage = 'Server error. Please try again later.';
                    } else if (error.response.data && error.response.data.error) {
                        errorMessage = error.response.data.error;
                    }
                } else if (error.request) {
                    // Network error
                    errorMessage = 'Network error. Please check your connection.';
                }

                // Show error message in the form
                (this as any).loginError = errorMessage;

                // Reset loading state
                (this as any).isLoading = false;
            });
        },
        register(): void {
            // Clear previous errors
            (this as any).registerError = '';

            // Validate passwords match
            if ((this as any).registerPassword !== (this as any).registerConfirmPassword) {
                (this as any).registerError = 'Passwords do not match. Please try again.';
                return;
            }

            // Validate required fields
            if (!(this as any).registerUsername || !(this as any).registerFirstname || !(this as any).registerLastname || !(this as any).registerPassword) {
                (this as any).registerError = 'Please fill in all required fields.';
                return;
            }

            // Show loading state
            (this as any).isLoading = true;

            axios.post('http://localhost:8000/user/', {
                username: (this as any).registerUsername,
                password: (this as any).registerPassword,
                first_name: (this as any).registerFirstname,
                last_name: (this as any).registerLastname
            }).then(response => {
                // Success - user registered
                (this as any).$emit('userDataSent', response.data)
                localStorage.setItem('money_management_user', JSON.stringify(response.data));
                (this as any).$emit('forceRemount');
            }).catch(error => {
                // Handle registration errors
                console.error('Registration error:', error);

                let errorMessage = 'Registration failed. Please try again.';

                if (error.response) {
                    // Server responded with error status
                    if (error.response.status === 400) {
                        if (error.response.data && error.response.data.error) {
                            errorMessage = error.response.data.error;
                        } else {
                            errorMessage = 'Invalid registration data. Please check all fields.';
                        }
                    } else if (error.response.status === 500) {
                        errorMessage = 'Server error. Please try again later.';
                    }
                } else if (error.request) {
                    // Network error
                    errorMessage = 'Network error. Please check your connection.';
                }

                // Show error message in the form
                (this as any).registerError = errorMessage;

                // Reset loading state
                (this as any).isLoading = false;
            });
        },
        toggleForm() {
            (this as any).loginFormVisible = !(this as any).loginFormVisible;
            // Clear errors when switching forms
            (this as any).loginError = '';
            (this as any).registerError = '';
        },
    },
};
</script>

<style scoped>
/* Modern Login/Register Container */
.login-register-container {
    position: relative;
    min-height: 100vh;
    padding: 20px;
    background: transparent;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Main Content Wrapper */
.main-content-wrapper {
    position: relative;
    z-index: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    max-width: 600px;
}

.modern-auth-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    animation: slideInUp 0.6s ease-out;
}

/* Form animations */
.v-form {
    animation: fadeIn 0.4s ease-out;
}

@keyframes slideInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }

    to {
        opacity: 1;
    }
}

/* Form field enhancements */
:deep(.v-field) {
    border-radius: 12px;
    transition: all 0.3s ease;
}

:deep(.v-field__outline) {
    border-radius: 12px;
    transition: all 0.3s ease;
}

:deep(.v-field--focused .v-field__outline) {
    border-color: #4CAF50;
    border-width: 2px;
}

/* Button enhancements */
:deep(.v-btn) {
    text-transform: none;
    font-weight: 500;
    letter-spacing: 0.5px;
}

/* Auth Section */
.auth-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 24px;
    width: 100%;
}

/* Responsive design */
@media (max-width: 768px) {
    .login-register-container {
        padding: 16px;
    }

    .modern-auth-card {
        width: 100%;
        max-width: 100%;
    }
}

@media (max-width: 600px) {
    .login-register-container {
        padding: 12px;
    }

    .v-card-title {
        padding: 24px 16px 16px 16px !important;
    }

    .v-card-text {
        padding: 16px !important;
    }
}

/* Loading state for buttons */
:deep(.v-btn--loading) {
    pointer-events: none;
}

/* Focus states */
:deep(.v-field--focused) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
}

/* Hover effects for form elements */
:deep(.v-field:hover) {
    transform: translateY(-1px);
    transition: transform 0.2s ease;
}
</style>

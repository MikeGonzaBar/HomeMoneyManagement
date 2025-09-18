<template>
    <div class="login-register-container">
        <!-- Decorative Background Elements -->
        <div class="background-decoration">
            <div class="floating-shape shape-1"></div>
            <div class="floating-shape shape-2"></div>
            <div class="floating-shape shape-3"></div>
            <div class="floating-shape shape-4"></div>
        </div>

        <!-- Main Content Container -->
        <div class="main-content-wrapper">
            <!-- Left Side - Hero & Features -->
            <div class="hero-features-section">
                <!-- Hero Section -->
                <div class="hero-content">
                    <div class="hero-badge">
                        <v-icon color="primary" size="16" class="me-2">mdi-star</v-icon>
                        <span>Trusted by 10,000+ users</span>
                    </div>

                    <h1 class="hero-title">
                        Take Control of Your
                        <span class="gradient-text">Finances</span>
                    </h1>

                    <p class="hero-description">
                        Budget Buddy helps you track expenses, manage multiple accounts, and achieve your financial
                        goals with smart budgeting tools and secure, private data management.
                    </p>

                    <!-- Key Benefits -->
                    <div class="key-benefits">
                        <div class="benefit-item">
                            <v-icon color="success" size="20" class="me-2">mdi-check-circle</v-icon>
                            <span>Free to use forever</span>
                        </div>
                        <div class="benefit-item">
                            <v-icon color="success" size="20" class="me-2">mdi-check-circle</v-icon>
                            <span>Bank-level security</span>
                        </div>
                        <div class="benefit-item">
                            <v-icon color="success" size="20" class="me-2">mdi-check-circle</v-icon>
                            <span>Works on all devices</span>
                        </div>
                    </div>
                </div>

                <!-- Features Grid -->
                <div class="features-grid">
                    <div class="feature-card">
                        <div class="feature-icon">
                            <v-icon color="primary" size="28">mdi-chart-line</v-icon>
                        </div>
                        <h3 class="feature-title">Smart Tracking</h3>
                        <p class="feature-description">Automatically categorize and track your income and expenses with
                            intelligent insights.</p>
                    </div>

                    <div class="feature-card">
                        <div class="feature-icon">
                            <v-icon color="primary" size="28">mdi-piggy-bank</v-icon>
                        </div>
                        <h3 class="feature-title">Budget Planning</h3>
                        <p class="feature-description">Create personalized budgets and get alerts when you're
                            approaching limits.</p>
                    </div>

                    <div class="feature-card">
                        <div class="feature-icon">
                            <v-icon color="primary" size="28">mdi-account-multiple</v-icon>
                        </div>
                        <h3 class="feature-title">Multi-Account</h3>
                        <p class="feature-description">Manage checking, savings, and investment accounts all in one
                            place.</p>
                    </div>

                    <div class="feature-card">
                        <div class="feature-icon">
                            <v-icon color="primary" size="28">mdi-shield-check</v-icon>
                        </div>
                        <h3 class="feature-title">Secure & Private</h3>
                        <p class="feature-description">Your data is encrypted and never shared. Your privacy is our
                            priority.</p>
                    </div>
                </div>
            </div>

            <!-- Right Side - Login Form -->
            <div class="auth-section">
                <v-card class="modern-auth-card glass-card shadow-strong" rounded="xl" max-width="500">
                    <!-- Header with Budget Buddy Logo -->
                    <v-card-title class="pa-8 pb-4 text-center">
                        <div class="d-flex flex-column align-center">
                            <v-avatar size="80" class="mb-4 budget-gradient">
                                <v-img src="@/assets/logo.png" alt="Budget Buddy" />
                            </v-avatar>
                            <h1 class="text-h4 font-weight-bold budget-text-gradient mb-2">Get Started</h1>
                            <p class="text-body-1 text-grey-darken-1 mb-0">Join thousands of users managing their
                                finances</p>
                        </div>
                    </v-card-title>

                    <v-card-text class="pa-8 pt-2">
                        <!-- Login Form -->
                        <v-form v-if="(this as any).loginFormVisible" @submit.prevent="(this as any).login">
                            <v-text-field v-model="(this as any).loginUsername" label="Username" variant="outlined"
                                rounded="lg" prepend-inner-icon="mdi-account" class="mb-4" required></v-text-field>

                            <v-text-field v-model="(this as any).loginPassword" label="Password" type="password"
                                variant="outlined" rounded="lg" prepend-inner-icon="mdi-lock" class="mb-6"
                                required></v-text-field>

                            <v-btn @click="(this as any).login" color="primary" size="large" block rounded="lg"
                                class="smooth-transition hover-lift mb-4">
                                <v-icon left>mdi-login</v-icon>
                                Sign In to Dashboard
                            </v-btn>
                        </v-form>

                        <!-- Register Form -->
                        <v-form v-else @submit.prevent="(this as any).register">
                            <v-text-field v-model="(this as any).registerUsername" label="Username" variant="outlined"
                                rounded="lg" prepend-inner-icon="mdi-account" class="mb-3" required></v-text-field>

                            <v-row>
                                <v-col cols="6">
                                    <v-text-field v-model="(this as any).registerFirstname" label="First Name"
                                        variant="outlined" rounded="lg" class="mb-3" required></v-text-field>
                                </v-col>
                                <v-col cols="6">
                                    <v-text-field v-model="(this as any).registerLastname" label="Last Name"
                                        variant="outlined" rounded="lg" class="mb-3" required></v-text-field>
                                </v-col>
                            </v-row>

                            <v-text-field v-model="(this as any).registerPassword" label="Password" type="password"
                                variant="outlined" rounded="lg" prepend-inner-icon="mdi-lock" class="mb-3"
                                required></v-text-field>

                            <v-text-field v-model="(this as any).registerConfirmPassword" label="Confirm Password"
                                type="password" variant="outlined" rounded="lg" prepend-inner-icon="mdi-lock-check"
                                class="mb-6" required></v-text-field>

                            <v-btn @click="(this as any).register" color="primary" size="large" block rounded="lg"
                                class="smooth-transition hover-lift mb-4">
                                <v-icon left>mdi-account-plus</v-icon>
                                Start Free Account
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

                <!-- Trust Indicators -->
                <div class="trust-indicators">
                    <div class="trust-item">
                        <v-icon color="success" size="20" class="me-2">mdi-shield-check</v-icon>
                        <span>256-bit SSL encryption</span>
                    </div>
                    <div class="trust-item">
                        <v-icon color="success" size="20" class="me-2">mdi-lock</v-icon>
                        <span>Your data stays private</span>
                    </div>
                </div>
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
        };
    },
    computed: {
        cardTitle(): string {
            return (this as any).loginFormVisible ? 'Login' : 'Register';
        },
        toggleButtonText(): string {
            return (this as any).loginFormVisible
                ? "New to Budget Buddy? Create your free account"
                : 'Already have an account? Sign in here';
        },
        toggleButtonAction(): string {
            return (this as any).loginFormVisible ? 'Register' : 'Login';
        },
    },
    methods: {
        login(): void {
            axios.post(`http://localhost:8000/user/${(this as any).loginUsername}/`, {
                password: (this as any).loginPassword,
            }).then(response => {
                (this as any).$emit('userDataSent', response.data.user)
                localStorage.setItem('money_management_user', JSON.stringify(response.data));
                location.reload();
            });
        },
        register(): void {
            axios.post('http://localhost:8000/user/', {
                username: (this as any).registerUsername,
                password: (this as any).registerPassword,
                first_name: (this as any).registerFirstname,
                last_name: (this as any).registerLastname
            }).then(response => {
                (this as any).$emit('userDataSent', response.data)
                localStorage.setItem('money_management_user', JSON.stringify(response.data));
                (this as any).$emit('forceRemount');

            });
        },
        toggleForm() {
            (this as any).loginFormVisible = !(this as any).loginFormVisible;
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
}

/* Background Decoration */
.background-decoration {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
    z-index: 0;
}

.floating-shape {
    position: absolute;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(139, 195, 74, 0.1) 100%);
    animation: float 6s ease-in-out infinite;
}

.shape-1 {
    width: 120px;
    height: 120px;
    top: 10%;
    left: 10%;
    animation-delay: 0s;
}

.shape-2 {
    width: 80px;
    height: 80px;
    top: 20%;
    right: 15%;
    animation-delay: 2s;
}

.shape-3 {
    width: 100px;
    height: 100px;
    bottom: 20%;
    left: 20%;
    animation-delay: 4s;
}

.shape-4 {
    width: 60px;
    height: 60px;
    bottom: 10%;
    right: 10%;
    animation-delay: 1s;
}

@keyframes float {

    0%,
    100% {
        transform: translateY(0px) rotate(0deg);
    }

    50% {
        transform: translateY(-20px) rotate(180deg);
    }
}

/* Main Content Wrapper */
.main-content-wrapper {
    position: relative;
    z-index: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    gap: 60px;
    max-width: 1400px;
    margin: 0 auto;
}

/* Hero & Features Section */
.hero-features-section {
    flex: 1;
    max-width: 600px;
    padding: 40px;
}

/* Hero Content */
.hero-content {
    margin-bottom: 48px;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    background: rgba(76, 175, 80, 0.1);
    color: #2E7D32;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 500;
    margin-bottom: 24px;
    border: 1px solid rgba(76, 175, 80, 0.2);
}

.hero-title {
    font-size: 3.2rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 24px;
    color: #1a1a1a;
}

.gradient-text {
    background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-description {
    font-size: 1.2rem;
    color: #666;
    line-height: 1.6;
    margin-bottom: 32px;
    font-weight: 400;
}

.key-benefits {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.benefit-item {
    display: flex;
    align-items: center;
    font-size: 1rem;
    color: #2E7D32;
    font-weight: 500;
}

/* Features Grid */
.features-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 24px;
}

.feature-card {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(20px);
    border-radius: 16px;
    padding: 24px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    transition: all 0.3s ease;
}

.feature-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.feature-icon {
    width: 56px;
    height: 56px;
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(139, 195, 74, 0.1) 100%);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
}

.feature-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #1a1a1a;
    margin-bottom: 8px;
}

.feature-description {
    font-size: 0.9rem;
    color: #666;
    line-height: 1.5;
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

/* Enhanced glassmorphism for auth card */
.modern-auth-card {
    position: relative;
    overflow: hidden;
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
}

.trust-indicators {
    display: flex;
    gap: 24px;
    justify-content: center;
    flex-wrap: wrap;
}

.trust-item {
    display: flex;
    align-items: center;
    font-size: 0.9rem;
    color: #2E7D32;
    font-weight: 500;
}

/* Responsive design */
@media (max-width: 1200px) {
    .main-content-wrapper {
        flex-direction: column;
        gap: 40px;
        padding: 20px;
    }

    .hero-features-section {
        max-width: 100%;
        padding: 20px;
    }

    .hero-title {
        font-size: 2.5rem;
    }

    .features-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .main-content-wrapper {
        gap: 30px;
    }

    .hero-features-section {
        padding: 20px;
    }

    .hero-title {
        font-size: 2.2rem;
    }

    .hero-description {
        font-size: 1.1rem;
    }

    .trust-indicators {
        flex-direction: column;
        gap: 12px;
    }
}

@media (max-width: 600px) {
    .login-register-container {
        padding: 16px;
    }

    .modern-auth-card {
        max-width: 100%;
    }

    .v-card-title {
        padding: 24px 16px 16px 16px !important;
    }

    .v-card-text {
        padding: 16px !important;
    }

    .hero-features-section {
        padding: 10px;
    }

    .hero-title {
        font-size: 1.8rem;
    }

    .hero-description {
        font-size: 1rem;
    }

    .feature-card {
        padding: 16px;
    }

    .floating-shape {
        display: none;
        /* Hide decorative shapes on very small screens */
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

/* Custom scrollbar for the card if needed */
.modern-auth-card {
    scrollbar-width: thin;
    scrollbar-color: #4CAF50 #f1f1f1;
}

.modern-auth-card::-webkit-scrollbar {
    width: 6px;
}

.modern-auth-card::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
}

.modern-auth-card::-webkit-scrollbar-thumb {
    background: #4CAF50;
    border-radius: 3px;
}

.modern-auth-card::-webkit-scrollbar-thumb:hover {
    background: #2E7D32;
}
</style>

<template>
    <v-container fluid class="profile-container">
        <!-- Header -->
        <v-row class="mb-6">
            <v-col cols="12">
                <v-card class="glass-card shadow-medium" rounded="xl">
                    <v-card-title class="pa-6 pb-2">
                        <div class="d-flex align-center justify-space-between w-100">
                            <div class="d-flex align-center">
                                <v-avatar size="40" class="me-3 budget-gradient">
                                    <v-icon color="white">mdi-account-circle</v-icon>
                                </v-avatar>
                                <div class="d-flex flex-column justify-center">
                                    <h4 class="budget-text-gradient font-weight-bold mb-0">User Profile</h4>
                                    <p class="text-grey-darken-1 mb-0 text-caption">Manage your account settings and
                                        preferences
                                    </p>
                                </div>
                            </div>
                            <v-btn color="primary" variant="outlined" rounded="lg" @click="goToHome"
                                :size="$vuetify.display.mobile ? 'default' : 'default'"
                                class="smooth-transition hover-lift">
                                <v-icon :left="$vuetify.display.smAndUp"
                                    :class="$vuetify.display.mobile ? '' : 'me-2'">mdi-home</v-icon>
                                <span :class="$vuetify.display.mobile ? 'd-none d-sm-inline' : ''">Back to Home</span>
                                <span :class="$vuetify.display.mobile ? 'd-inline d-sm-none' : 'd-none'">Home</span>
                            </v-btn>
                        </div>
                    </v-card-title>
                </v-card>
            </v-col>
        </v-row>

        <!-- Main Content -->
        <v-row>
            <!-- Sidebar -->
            <v-col cols="12" md="3">
                <v-card class="glass-card shadow-medium" rounded="xl">
                    <v-list class="pa-2">
                        <v-list-item v-for="item in sidebarItems" :key="item.title"
                            :class="{ 'active-sidebar-item': activeSection === item.value }"
                            @click="activeSection = item.value" class="sidebar-item">
                            <template v-slot:prepend>
                                <v-icon :color="activeSection === item.value ? 'primary' : 'grey'">
                                    {{ item.icon }}
                                </v-icon>
                            </template>
                            <v-list-item-title>{{ item.title }}</v-list-item-title>
                        </v-list-item>
                    </v-list>
                </v-card>
            </v-col>

            <!-- Content Area -->
            <v-col cols="12" md="9">
                <!-- Personal Info Section -->
                <v-card v-if="activeSection === 'personal'" class="glass-card shadow-medium" rounded="xl">
                    <v-card-title class="pa-6 pb-2">
                        <div class="d-flex align-center">
                            <v-avatar size="32" class="me-3" color="primary">
                                <v-icon color="white">mdi-account-edit</v-icon>
                            </v-avatar>
                            <h5 class="font-weight-bold">Personal Information</h5>
                        </div>
                    </v-card-title>
                    <v-card-text class="pa-6 pt-2">
                        <v-form ref="personalForm" v-model="personalFormValid">
                            <!-- Username -->
                            <v-text-field v-model="userInfo.username" label="Username" variant="outlined" rounded="lg"
                                :rules="usernameRules" class="mb-4" prepend-inner-icon="mdi-account"></v-text-field>

                            <!-- First Name -->
                            <v-text-field v-model="userInfo.first_name" label="First Name" variant="outlined"
                                rounded="lg" :rules="nameRules" class="mb-4"
                                prepend-inner-icon="mdi-account-outline"></v-text-field>

                            <!-- Last Name -->
                            <v-text-field v-model="userInfo.last_name" label="Last Name" variant="outlined" rounded="lg"
                                :rules="nameRules" class="mb-4" prepend-inner-icon="mdi-account-outline"></v-text-field>

                            <!-- Save Personal Info Button -->
                            <v-btn color="primary" :size="$vuetify.display.mobile ? 'default' : 'large'" rounded="lg"
                                :loading="savingPersonalInfo" :disabled="!personalFormValid" @click="savePersonalInfo"
                                class="smooth-transition hover-lift">
                                <v-icon :left="$vuetify.display.smAndUp"
                                    :class="$vuetify.display.mobile ? '' : 'me-2'">mdi-content-save</v-icon>
                                <span :class="$vuetify.display.mobile ? 'd-none d-sm-inline' : ''">Save Changes</span>
                                <span :class="$vuetify.display.mobile ? 'd-inline d-sm-none' : 'd-none'">Save</span>
                            </v-btn>
                        </v-form>

                        <v-divider class="my-6"></v-divider>

                        <h6 class="font-weight-bold mb-4">Appearance</h6>
                        <div class="d-flex flex-wrap align-center gap-3 mb-6">
                            <v-select v-model="themePreference" :items="themeOptions" label="Theme"
                                variant="outlined" rounded="lg" hide-details class="theme-select"></v-select>
                            <v-btn color="primary" variant="outlined" rounded="lg" :loading="savingTheme"
                                @click="saveThemePreference">
                                Save Theme
                            </v-btn>
                        </div>

                        <v-divider class="my-6"></v-divider>

                        <!-- Change Password Section -->
                        <h6 class="font-weight-bold mb-4">Change Password</h6>
                        <v-form ref="passwordForm" v-model="passwordFormValid">
                            <!-- Current Password -->
                            <v-text-field v-model="passwordData.currentPassword" label="Current Password"
                                type="password" variant="outlined" rounded="lg" :rules="passwordRules" class="mb-4"
                                prepend-inner-icon="mdi-lock"></v-text-field>

                            <!-- New Password -->
                            <v-text-field v-model="passwordData.newPassword" label="New Password" type="password"
                                variant="outlined" rounded="lg" :rules="newPasswordRules" class="mb-4"
                                prepend-inner-icon="mdi-lock-plus"></v-text-field>

                            <!-- Confirm New Password -->
                            <v-text-field v-model="passwordData.confirmPassword" label="Confirm New Password"
                                type="password" variant="outlined" rounded="lg" :rules="confirmPasswordRules"
                                class="mb-4" prepend-inner-icon="mdi-lock-check"></v-text-field>

                            <!-- Change Password Button -->
                            <v-btn color="primary" :size="$vuetify.display.mobile ? 'default' : 'large'" rounded="lg"
                                :loading="changingPassword" :disabled="!passwordFormValid" @click="changePassword"
                                class="smooth-transition hover-lift">
                                <v-icon :left="$vuetify.display.smAndUp"
                                    :class="$vuetify.display.mobile ? '' : 'me-2'">mdi-key</v-icon>
                                <span :class="$vuetify.display.mobile ? 'd-none d-sm-inline' : ''">Change
                                    Password</span>
                                <span :class="$vuetify.display.mobile ? 'd-inline d-sm-none' : 'd-none'">Change</span>
                            </v-btn>
                        </v-form>
                    </v-card-text>
                </v-card>

            </v-col>
        </v-row>

    </v-container>
</template>

<script lang="ts">
import axios from '@/services/api';
import { getStoredSession, setStoredSession } from '@/services/session';
import { applyDocumentTheme, type ThemePreference } from '@/services/theme';

interface UserInfo {
    username: string;
    first_name: string;
    last_name: string;
    theme_preference?: ThemePreference;
}

interface PasswordData {
    currentPassword: string;
    newPassword: string;
    confirmPassword: string;
}

export default {
    name: 'Profile',
    data() {
        return {
            activeSection: 'personal' as string,
            sidebarItems: [
                { title: 'Personal Info', icon: 'mdi-account-edit', value: 'personal' },
            ],

            // Personal Info
            userInfo: {
                username: '',
                first_name: '',
                last_name: ''
            } as UserInfo,
            personalFormValid: false,
            savingPersonalInfo: false,
            themePreference: 'system' as ThemePreference,
            savingTheme: false,
            themeOptions: [
                { title: 'Use system setting', value: 'system' },
                { title: 'Light', value: 'light' },
                { title: 'Dark', value: 'dark' }
            ],

            // Password Change
            passwordData: {
                currentPassword: '',
                newPassword: '',
                confirmPassword: ''
            } as PasswordData,
            passwordFormValid: false,
            changingPassword: false,

            // Form Rules
            usernameRules: [
                (v: string) => !!v || 'Username is required',
                (v: string) => (v && v.length >= 3) || 'Username must be at least 3 characters',
                (v: string) => (v && v.length <= 150) || 'Username must be less than 150 characters'
            ],
            nameRules: [
                (v: string) => !!v || 'This field is required',
                (v: string) => (v && v.length >= 2) || 'Must be at least 2 characters',
                (v: string) => (v && v.length <= 30) || 'Must be less than 30 characters'
            ],
            passwordRules: [
                (v: string) => !!v || 'Current password is required'
            ],
            newPasswordRules: [
                (v: string) => !!v || 'New password is required',
                (v: string) => (v && v.length >= 8) || 'Password must be at least 8 characters'
            ],
            confirmPasswordRules: [
                (v: string) => !!v || 'Please confirm your password',
                (v: string) => v === (this as any).passwordData.newPassword || 'Passwords do not match'
            ]
        }
    },
    mounted() {
        this.loadUserInfo();
    },
    methods: {
        loadUserInfo() {
            const session = getStoredSession();
            if (session) {
                (this as any).userInfo = {
                    username: session.user.username,
                    first_name: session.user.first_name,
                    last_name: session.user.last_name,
                    theme_preference: session.user.theme_preference
                };
                (this as any).themePreference = session.user.theme_preference || 'system';
            }
        },

        async savePersonalInfo() {
            (this as any).savingPersonalInfo = true;
            try {
                const response = await axios.put('/user/update-info/', {
                    new_username: (this as any).userInfo.username,
                    first_name: (this as any).userInfo.first_name,
                    last_name: (this as any).userInfo.last_name
                });

                if (response.data.message) {
                    alert('Personal information updated successfully!');

                    const session = getStoredSession();
                    if (session) {
                        setStoredSession({
                            token: session.token,
                            user: response.data.user
                        });
                    }
                }
            } catch (error: any) {
                console.error('Error updating personal info:', error);
                let errorMessage = 'Failed to update personal information. Please try again.';

                if (error.response?.data?.message) {
                    errorMessage = error.response.data.message;
                } else if (error.response?.data?.error) {
                    errorMessage = error.response.data.error;
                }

                alert(errorMessage);
            } finally {
                (this as any).savingPersonalInfo = false;
            }
        },

        async changePassword() {
            (this as any).changingPassword = true;
            try {
                const response = await axios.put('/user/change-password/', {
                    current_password: (this as any).passwordData.currentPassword,
                    new_password: (this as any).passwordData.newPassword
                });

                if (response.data.message) {
                    alert('Password changed successfully!');

                    // Clear password fields
                    (this as any).passwordData = {
                        currentPassword: '',
                        newPassword: '',
                        confirmPassword: ''
                    };
                }
            } catch (error: any) {
                console.error('Error changing password:', error);
                let errorMessage = 'Failed to change password. Please try again.';

                if (error.response?.data?.message) {
                    errorMessage = error.response.data.message;
                } else if (error.response?.data?.error) {
                    errorMessage = error.response.data.error;
                }

                alert(errorMessage);
            } finally {
                (this as any).changingPassword = false;
            }
        },

        async saveThemePreference() {
            (this as any).savingTheme = true;
            try {
                const response = await axios.put('/user/preferences/', {
                    theme_preference: (this as any).themePreference
                });
                applyDocumentTheme((this as any).themePreference);
                const session = getStoredSession();
                if (session && response.data?.user) {
                    setStoredSession({ token: session.token, user: response.data.user });
                }
            } catch (error) {
                console.error('Error saving theme preference:', error);
                alert('Failed to save theme preference. Please try again.');
            } finally {
                (this as any).savingTheme = false;
            }
        },

        goToHome() {
            // Navigate back to home page
            (this as any).$router.push('/');
        },

    }
}
</script>

<style scoped>
.profile-container {
    min-height: 100vh;
    background: #f9fafb;
    padding: 24px;
}

.glass-card {
    background: #ffffff;
    border: 1px solid #f3f4f6;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
}

.shadow-medium {
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}

.budget-gradient {
    background: linear-gradient(135deg, #4caf50 0%, #8bc34a 100%);
}

.budget-text-gradient {
    background: linear-gradient(135deg, #4caf50 0%, #8bc34a 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.sidebar-item {
    border-radius: 12px;
    margin: 4px 0;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-item:hover {
    background: rgba(76, 175, 80, 0.1);
    transform: none;
}

.active-sidebar-item {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(139, 195, 74, 0.1) 100%);
    border: 1px solid rgba(76, 175, 80, 0.2);
}

.smooth-transition {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.hover-lift:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
}

/* Mobile-specific improvements */
@media (max-width: 640px) {
    .profile-container {
        overflow-x: hidden;
    }

    .profile-container :deep(.v-row) {
        margin-left: 0;
        margin-right: 0;
    }
}

@media (max-width: 600px) {
    .profile-container {
        padding: 12px;
    }

    .glass-card {
        margin-bottom: 16px;
    }

    .v-card-title {
        padding: 16px !important;
    }

    .v-card-text {
        padding: 16px !important;
    }

    /* Header adjustments */
    .v-card-title .d-flex {
        flex-direction: column;
        gap: 12px;
        align-items: stretch !important;
    }

    .v-card-title .d-flex>div:first-child {
        text-align: center;
    }

    .v-card-title .d-flex>div:last-child {
        display: flex;
        justify-content: center;
    }

    /* Button adjustments */
    .v-btn {
        font-size: 0.9rem;
        min-width: auto;
    }

    /* Form adjustments */
    .v-text-field {
        margin-bottom: 12px;
    }

    /* Sidebar adjustments */
    .v-list {
        padding: 8px !important;
    }

    .sidebar-item {
        margin: 2px 0;
    }

    .v-list-item-title {
        font-size: 0.9rem;
    }

    .v-list-item-subtitle {
        font-size: 0.8rem;
    }
}

/* Extra small screens (iPhone SE) */
@media (max-width: 375px) {
    .profile-container {
        padding: 8px;
    }

    .v-card-title {
        padding: 12px !important;
    }

    .v-card-text {
        padding: 12px !important;
    }

    .v-btn {
        font-size: 0.8rem;
        padding: 8px 12px;
    }

    .v-text-field {
        margin-bottom: 10px;
    }

    .v-list {
        padding: 6px !important;
    }

    .v-list-item-title {
        font-size: 0.85rem;
    }

    .v-list-item-subtitle {
        font-size: 0.75rem;
    }
}
</style>

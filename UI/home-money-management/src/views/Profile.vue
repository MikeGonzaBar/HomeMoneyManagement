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
                                        files
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

                <!-- My Files Section -->
                <v-card v-if="activeSection === 'files'" class="glass-card shadow-medium" rounded="xl">
                    <v-card-title class="pa-6 pb-2">
                        <div class="d-flex align-center">
                            <v-avatar size="32" class="me-3" color="primary">
                                <v-icon color="white">mdi-file-pdf-box</v-icon>
                            </v-avatar>
                            <h5 class="font-weight-bold">My Files</h5>
                        </div>
                    </v-card-title>
                    <v-card-text class="pa-6 pt-2">
                        <!-- Loading State -->
                        <div v-if="loadingFiles" class="text-center pa-8">
                            <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
                            <p class="mt-4 text-grey-darken-1">Loading your files...</p>
                        </div>

                        <!-- No Files State -->
                        <div v-else-if="userFiles.length === 0" class="text-center pa-8">
                            <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-file-pdf-box-outline</v-icon>
                            <h6 class="text-h6 text-grey-darken-1 mb-2">No Files Uploaded</h6>
                            <p class="text-body-2 text-grey-darken-1 mb-4">
                                You haven't uploaded any bank statement PDFs yet.
                            </p>
                            <v-btn color="primary" variant="outlined" rounded="lg" @click="goToUpload"
                                :size="$vuetify.display.mobile ? 'default' : 'default'"
                                class="smooth-transition hover-lift">
                                <v-icon :left="$vuetify.display.smAndUp"
                                    :class="$vuetify.display.mobile ? '' : 'me-2'">mdi-upload</v-icon>
                                <span :class="$vuetify.display.mobile ? 'd-none d-sm-inline' : ''">Upload Bank
                                    Statement</span>
                                <span :class="$vuetify.display.mobile ? 'd-inline d-sm-none' : 'd-none'">Upload</span>
                            </v-btn>
                        </div>

                        <!-- Files List -->
                        <div v-else>
                            <div class="d-flex justify-space-between align-center mb-4">
                                <h6 class="font-weight-bold">Uploaded Bank Statements ({{ userFiles.length }})</h6>
                                <v-btn color="primary" variant="outlined" size="small" rounded="lg"
                                    @click="refreshFiles" :loading="loadingFiles">
                                    <v-icon left>mdi-refresh</v-icon>
                                    Refresh
                                </v-btn>
                            </div>

                            <v-list class="pa-0">
                                <v-list-item v-for="file in userFiles" :key="file.id" class="file-item mb-2">
                                    <template v-slot:prepend>
                                        <v-avatar color="red-lighten-4" size="40">
                                            <v-icon color="red">mdi-file-pdf-box</v-icon>
                                        </v-avatar>
                                    </template>

                                    <v-list-item-title class="font-weight-medium">
                                        {{ file.original_filename }}
                                    </v-list-item-title>
                                    <v-list-item-subtitle>
                                        {{ file.file_size_display }} • Uploaded {{ file.upload_date_display }}
                                    </v-list-item-subtitle>

                                    <template v-slot:append>
                                        <div class="d-flex align-center">
                                            <!-- Processing Status -->
                                            <v-chip :color="getStatusColor(file.processing_status)" size="small"
                                                variant="tonal" class="me-2">
                                                {{ file.processing_status }}
                                            </v-chip>

                                            <!-- Delete Button -->
                                            <v-btn icon="mdi-delete" color="red" variant="text" size="small"
                                                @click="confirmDeleteFile(file)" class="smooth-transition"></v-btn>
                                        </div>
                                    </template>
                                </v-list-item>
                            </v-list>
                        </div>
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>

        <!-- Delete Confirmation Dialog -->
        <v-dialog v-model="deleteDialog" max-width="400">
            <v-card rounded="xl">
                <v-card-title class="pa-6 pb-2">
                    <div class="d-flex align-center">
                        <v-avatar size="32" class="me-3" color="red">
                            <v-icon color="white">mdi-delete</v-icon>
                        </v-avatar>
                        <h6 class="font-weight-bold">Delete File</h6>
                    </div>
                </v-card-title>
                <v-card-text class="pa-6 pt-2">
                    <p>Are you sure you want to delete <strong>{{ fileToDelete?.original_filename }}</strong>?</p>
                    <p class="text-caption text-grey-darken-1">This action cannot be undone.</p>
                </v-card-text>
                <v-card-actions class="pa-6 pt-2">
                    <v-spacer></v-spacer>
                    <v-btn color="grey" variant="text" @click="deleteDialog = false">
                        Cancel
                    </v-btn>
                    <v-btn color="red" variant="flat" :loading="deletingFile" @click="deleteFile">
                        Delete
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </v-container>
</template>

<script lang="ts">
import axios from 'axios';

interface UserInfo {
    username: string;
    first_name: string;
    last_name: string;
}

interface PasswordData {
    currentPassword: string;
    newPassword: string;
    confirmPassword: string;
}

interface UserFile {
    id: number;
    original_filename: string;
    file_size: number;
    file_size_display: string;
    upload_date: string;
    upload_date_display: string;
    processed: boolean;
    processing_status: string;
    error_message: string | null;
}

export default {
    name: 'Profile',
    data() {
        return {
            activeSection: 'personal' as string,
            sidebarItems: [
                { title: 'Personal Info', icon: 'mdi-account-edit', value: 'personal' },
                { title: 'My Files', icon: 'mdi-file-pdf-box', value: 'files' }
            ],

            // Personal Info
            userInfo: {
                username: '',
                first_name: '',
                last_name: ''
            } as UserInfo,
            personalFormValid: false,
            savingPersonalInfo: false,

            // Password Change
            passwordData: {
                currentPassword: '',
                newPassword: '',
                confirmPassword: ''
            } as PasswordData,
            passwordFormValid: false,
            changingPassword: false,

            // Files
            userFiles: [] as UserFile[],
            loadingFiles: false,

            // Delete Dialog
            deleteDialog: false,
            fileToDelete: null as UserFile | null,
            deletingFile: false,

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
        this.loadUserFiles();
    },
    methods: {
        loadUserInfo() {
            // Load user info from localStorage
            const userDataString = localStorage.getItem('money_management_user');
            if (userDataString) {
                const parsedUserData = JSON.parse(userDataString);
                if (parsedUserData.user) {
                    (this as any).userInfo = {
                        username: parsedUserData.user.username,
                        first_name: parsedUserData.user.first_name,
                        last_name: parsedUserData.user.last_name
                    };
                }
            }
        },

        async savePersonalInfo() {
            (this as any).savingPersonalInfo = true;
            try {
                const response = await axios.put('http://localhost:8000/user/update-info/', {
                    username: (this as any).userInfo.username,
                    new_username: (this as any).userInfo.username,
                    first_name: (this as any).userInfo.first_name,
                    last_name: (this as any).userInfo.last_name
                });

                if (response.data.message) {
                    alert('Personal information updated successfully!');

                    // Update localStorage with new user info
                    const userDataString = localStorage.getItem('money_management_user');
                    if (userDataString) {
                        const parsedUserData = JSON.parse(userDataString);
                        if (parsedUserData.user) {
                            parsedUserData.user.username = response.data.user.username;
                            parsedUserData.user.first_name = response.data.user.first_name;
                            parsedUserData.user.last_name = response.data.user.last_name;
                            localStorage.setItem('money_management_user', JSON.stringify(parsedUserData));
                        }
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
                const response = await axios.put('http://localhost:8000/user/change-password/', {
                    username: (this as any).userInfo.username,
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

        async loadUserFiles() {
            (this as any).loadingFiles = true;
            try {
                const userDataString = localStorage.getItem('money_management_user');
                if (userDataString) {
                    const parsedUserData = JSON.parse(userDataString);
                    const username = parsedUserData.user?.username;

                    if (username) {
                        const response = await axios.get(`http://localhost:8000/bank-statements/user/${username}/`);
                        (this as any).userFiles = response.data.statements || [];
                    }
                }
            } catch (error) {
                console.error('Error loading user files:', error);
                (this as any).userFiles = [];
            } finally {
                (this as any).loadingFiles = false;
            }
        },

        async refreshFiles() {
            await (this as any).loadUserFiles();
        },

        goToHome() {
            // Navigate back to home page
            (this as any).$router.push('/');
        },

        goToUpload() {
            // Navigate back to home page where upload component is
            (this as any).$router.push('/');
        },

        getStatusColor(status: string) {
            switch (status) {
                case 'completed': return 'green';
                case 'processing': return 'orange';
                case 'failed': return 'red';
                default: return 'grey';
            }
        },

        confirmDeleteFile(file: UserFile) {
            (this as any).fileToDelete = file;
            (this as any).deleteDialog = true;
        },

        async deleteFile() {
            if (!(this as any).fileToDelete) return;

            (this as any).deletingFile = true;
            try {
                await axios.delete(`http://localhost:8000/bank-statements/delete/${(this as any).fileToDelete.id}/`);

                // Remove from local list
                (this as any).userFiles = (this as any).userFiles.filter(
                    (file: UserFile) => file.id !== (this as any).fileToDelete.id
                );

                (this as any).deleteDialog = false;
                (this as any).fileToDelete = null;

                alert('File deleted successfully!');
            } catch (error) {
                console.error('Error deleting file:', error);
                alert('Failed to delete file. Please try again.');
            } finally {
                (this as any).deletingFile = false;
            }
        }
    }
}
</script>

<style scoped>
.profile-container {
    min-height: 100vh;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.glass-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.shadow-medium {
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
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
    transform: translateX(4px);
}

.active-sidebar-item {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(139, 195, 74, 0.1) 100%);
    border: 1px solid rgba(76, 175, 80, 0.2);
}

.file-item {
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 12px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.file-item:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
}

.smooth-transition {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.hover-lift:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

/* Mobile-specific improvements */
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

    /* File list adjustments */
    .file-item {
        margin-bottom: 8px;
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

    .file-item {
        margin-bottom: 6px;
    }

    .v-list-item-title {
        font-size: 0.85rem;
    }

    .v-list-item-subtitle {
        font-size: 0.75rem;
    }
}
</style>

<template>
    <v-card class="glass-card shadow-medium" rounded="xl">
        <v-card-title class="pa-6 pb-2">
            <div class="d-flex align-center">
                <v-avatar size="40" class="me-3 budget-gradient">
                    <v-icon color="white">mdi-file-pdf-box</v-icon>
                </v-avatar>
                <div>
                    <h4 class="budget-text-gradient font-weight-bold mb-0">Bank Statement Upload</h4>
                    <p class="text-grey-darken-1 mb-0 text-caption">Upload your bank statement PDF for automatic
                        transaction detection</p>
                </div>
            </div>
        </v-card-title>
        <v-card-text class="pa-6 pt-2">
            <v-file-input ref="fileInput" v-model="selectedFile" accept=".pdf" label="Select Bank Statement PDF"
                prepend-icon="mdi-file-pdf-box" variant="outlined" rounded="lg" :rules="fileRules"
                :loading="isUploading" @change="handleFileSelect" class="mb-4" clearable show-size
                density="comfortable"></v-file-input>

            <div v-if="selectedFile" class="file-preview mb-4">
                <v-alert type="info" variant="tonal" rounded="lg" class="mb-3">
                    <template v-slot:prepend>
                        <v-icon>mdi-information</v-icon>
                    </template>
                    <div>
                        <strong>Selected File:</strong> {{ selectedFile[0]?.name }}
                        <br>
                        <small class="text-grey-darken-1">Size: {{ formatFileSize(selectedFile[0]?.size) }}</small>
                    </div>
                </v-alert>

                <!-- Password field for password-protected PDFs -->
                <v-text-field v-if="showPasswordField || passwordRequired" v-model="pdfPassword" label="PDF Password"
                    type="password" variant="outlined" prepend-inner-icon="mdi-lock"
                    hint="Enter the password for this password-protected PDF" persistent-hint :error="passwordRequired"
                    :error-messages="passwordRequired ? 'Password is required for this PDF' : ''" class="mb-3"
                    rounded="lg" density="comfortable" clearable></v-text-field>

                <v-btn color="primary" size="large" rounded="lg" :loading="isUploading"
                    :disabled="!selectedFile || isUploading || (passwordRequired && !pdfPassword)"
                    @click="uploadBankStatement" class="smooth-transition hover-lift" block>
                    <v-icon left>mdi-upload</v-icon>
                    {{ isUploading ? 'Processing...' : 'Upload & Process Statement' }}
                </v-btn>
            </div>

            <div v-else class="upload-placeholder text-center pa-6" @click="triggerFileInput">
                <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-cloud-upload</v-icon>
                <h3 class="text-h6 text-grey-darken-1 mb-2">Upload Your Bank Statement</h3>
                <p class="text-body-2 text-grey-darken-1 mb-4">
                    Click here or use the file input above to select a PDF file of your bank statement
                </p>
                <v-chip color="primary" variant="tonal" size="small">
                    <v-icon left>mdi-information</v-icon>
                    PDF files only
                </v-chip>
            </div>
        </v-card-text>
    </v-card>
</template>

<script lang="ts">
import axios from 'axios';

interface DetectedTransaction {
    id: string;
    title: string;
    amount: number;
    date: string;
    category: string;
    transaction_type: 'Income' | 'Expense';
    account_name: string;
}

interface BankStatementData {
    account_detected: {
        name: string;
        bank: string;
        account_type: string;
    };
    transactions: DetectedTransaction[];
}

export default {
    name: 'BankStatementUpload',
    props: {
        userData: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            selectedFile: null as File[] | null,
            isUploading: false,
            pdfPassword: '',
            showPasswordField: false,
            passwordRequired: false,
            fileRules: [
                (value: File[]) => {
                    if (!value || value.length === 0) return true;
                    const file = value[0];
                    if (file && file.type !== 'application/pdf') {
                        return 'Please select a PDF file';
                    }
                    if (file && file.size > 10 * 1024 * 1024) { // 10MB limit
                        return 'File size must be less than 10MB';
                    }
                    return true;
                }
            ]
        }
    },
    emits: ['statementProcessed', 'uploadError'],
    methods: {
        handleFileSelect() {
            // File selection is handled by v-file-input
            console.log('File selected:', (this as any).selectedFile);
            // Reset password fields when new file is selected
            (this as any).pdfPassword = '';
            (this as any).showPasswordField = false;
            (this as any).passwordRequired = false;
        },

        triggerFileInput() {
            // Trigger the file input when clicking the placeholder
            const fileInput = (this as any).$refs.fileInput;
            if (fileInput) {
                fileInput.$el.querySelector('input[type="file"]').click();
            }
        },

        formatFileSize(bytes: number): string {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },

        async uploadBankStatement() {
            if (!(this as any).selectedFile || (this as any).selectedFile.length === 0) return;

            (this as any).isUploading = true;

            try {
                const formData = new FormData();
                formData.append('pdf_file', (this as any).selectedFile[0]);
                formData.append('user_id', (this as any).userData.user.username);

                // Add password if provided
                if ((this as any).pdfPassword) {
                    formData.append('pdf_password', (this as any).pdfPassword);
                }

                // Upload to the actual API endpoint
                const response = await axios.post('http://localhost:8000/bank-statements/upload/', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                });

                if (response.data.status === 'success') {
                    // Check if we have extracted transaction data
                    if (response.data.extracted_data && response.data.extracted_data.transactions && response.data.extracted_data.transactions.length > 0) {
                        // We have transactions to review - emit with extracted data
                        (this as any).$emit('statementProcessed', {
                            message: response.data.message,
                            file_details: response.data.file_details,
                            extracted_data: response.data.extracted_data,
                            status: 'processed'
                        });
                    } else {
                        // Just uploaded, no transactions extracted yet
                        (this as any).$emit('statementProcessed', {
                            message: response.data.message,
                            file_details: response.data.file_details,
                            status: 'uploaded'
                        });
                    }

                    // Reset form
                    (this as any).selectedFile = null;
                    (this as any).pdfPassword = '';
                    (this as any).showPasswordField = false;
                    (this as any).passwordRequired = false;
                } else {
                    throw new Error(response.data.message || 'Upload failed');
                }

            } catch (error: any) {
                console.error('Error uploading bank statement:', error);

                let errorMessage = 'Failed to upload bank statement. Please try again.';

                // Check if password is required
                if (error.response?.data?.requires_password) {
                    (this as any).passwordRequired = true;
                    (this as any).showPasswordField = true;
                    errorMessage = error.response.data.message || 'This PDF is password-protected. Please enter the password.';
                } else if (error.response?.data?.message) {
                    errorMessage = error.response.data.message;
                } else if (error.response?.data?.error) {
                    errorMessage = error.response.data.error;
                    // Check if it's a password-related error
                    if (error.response.data.error.toLowerCase().includes('password') ||
                        error.response.data.error.toLowerCase().includes('decrypt')) {
                        (this as any).passwordRequired = true;
                        (this as any).showPasswordField = true;
                    }
                } else if (error.message) {
                    errorMessage = error.message;
                }

                // Show error message to user
                (this as any).$emit('uploadError', errorMessage);
            } finally {
                (this as any).isUploading = false;
            }
        },

        // Simulate bank statement processing - replace with actual API call
        async simulateBankStatementProcessing(): Promise<BankStatementData> {
            // Simulate processing delay
            await new Promise(resolve => setTimeout(resolve, 2000));

            // Return mock data - replace with actual API response
            return {
                account_detected: {
                    name: "Chase Checking Account",
                    bank: "Chase Bank",
                    account_type: "Checking"
                },
                transactions: [
                    {
                        id: "1",
                        title: "GROCERY STORE PURCHASE",
                        amount: 45.67,
                        date: "2024-01-15",
                        category: "Food and drinks",
                        transaction_type: "Expense",
                        account_name: "Chase Checking Account"
                    },
                    {
                        id: "2",
                        title: "SALARY DEPOSIT",
                        amount: 2500.00,
                        date: "2024-01-14",
                        category: "Salary",
                        transaction_type: "Income",
                        account_name: "Chase Checking Account"
                    },
                    {
                        id: "3",
                        title: "GAS STATION",
                        amount: 32.15,
                        date: "2024-01-13",
                        category: "Transportation",
                        transaction_type: "Expense",
                        account_name: "Chase Checking Account"
                    },
                    {
                        id: "4",
                        title: "NETFLIX SUBSCRIPTION",
                        amount: 15.99,
                        date: "2024-01-12",
                        category: "Entertainment",
                        transaction_type: "Expense",
                        account_name: "Chase Checking Account"
                    },
                    {
                        id: "5",
                        title: "UTILITY BILL PAYMENT",
                        amount: 89.45,
                        date: "2024-01-11",
                        category: "Bills and utilities",
                        transaction_type: "Expense",
                        account_name: "Chase Checking Account"
                    }
                ]
            };
        }
    }
}
</script>

<style scoped>
/* Upload component specific styles */
.file-preview {
    animation: slideInUp 0.3s ease-out;
}

.upload-placeholder {
    background: rgba(76, 175, 80, 0.05);
    border: 2px dashed rgba(76, 175, 80, 0.3);
    border-radius: 16px;
    transition: all 0.3s ease;
    cursor: pointer;
}

.upload-placeholder:hover {
    background: rgba(76, 175, 80, 0.1);
    border-color: rgba(76, 175, 80, 0.5);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(76, 175, 80, 0.15);
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

/* File input styling */
:deep(.v-file-input .v-field) {
    border-radius: 12px;
    min-height: 56px;
    border: 2px dashed rgba(76, 175, 80, 0.3);
    background: rgba(76, 175, 80, 0.05);
    transition: all 0.3s ease;
}

:deep(.v-file-input .v-field:hover) {
    border-color: rgba(76, 175, 80, 0.6);
    background: rgba(76, 175, 80, 0.12);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
}

:deep(.v-file-input .v-field__outline) {
    border-radius: 12px;
}

:deep(.v-file-input .v-field__input) {
    padding: 16px;
    font-weight: 500;
}

:deep(.v-file-input .v-field__prepend-inner) {
    margin-right: 12px;
}

/* Alert styling */
:deep(.v-alert) {
    border-radius: 12px;
}

/* Button styling */
:deep(.v-btn) {
    text-transform: none;
    font-weight: 500;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .upload-placeholder {
        padding: 24px 16px;
    }

    .upload-placeholder h3 {
        font-size: 1.1rem;
    }

    .upload-placeholder p {
        font-size: 0.9rem;
    }

    :deep(.v-file-input .v-field) {
        font-size: 0.9rem;
    }
}

/* Loading state styling */
:deep(.v-file-input .v-field--loading) {
    opacity: 0.7;
}

/* Success state styling */
:deep(.v-file-input .v-field--success) {
    border-color: #4CAF50;
}

/* Error state styling */
:deep(.v-file-input .v-field--error) {
    border-color: #f44336;
}
</style>

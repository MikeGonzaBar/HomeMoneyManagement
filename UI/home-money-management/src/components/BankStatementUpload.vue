<template>
    <div class="bank-upload-content">
        <div class="upload-form">
            <!-- Single unified drop zone: click to browse, or drag & drop -->
            <div class="upload-placeholder text-center" :class="{
                'is-dragging': isDragging,
                'has-file': !!selectedPdfFile,
                'has-error': !!fileError
            }" role="button" tabindex="0"
                :aria-label="selectedPdfFile ? `Selected PDF: ${selectedPdfFile.name}. Click to choose a different file.` : 'Select or drop a bank statement PDF'"
                @click="openFilePicker" @keydown.enter.prevent="openFilePicker"
                @keydown.space.prevent="openFilePicker" @dragenter.prevent="isDragging = true"
                @dragover.prevent="isDragging = true" @dragleave="onDragLeave" @drop.prevent="onDrop">
                <input ref="fileInput" class="upload-native-input" type="file" accept=".pdf,application/pdf"
                    @change="onInputChange" />

                <!-- Empty state -->
                <template v-if="!selectedPdfFile">
                    <svg class="upload-icon mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg">
                        <path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                            stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                    </svg>
                    <h4 class="upload-title mb-2">Upload Your Bank Statement</h4>
                    <p class="upload-hint mb-4">Drag &amp; drop a PDF here, or click to browse</p>
                    <span class="upload-badge">
                        <svg class="badge-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        PDF files only · up to 10 MB
                    </span>
                </template>

                <!-- File selected state -->
                <template v-else>
                    <svg class="upload-icon upload-file-icon mb-3" fill="none" stroke="currentColor"
                        viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z">
                        </path>
                    </svg>
                    <h4 class="upload-title mb-1">{{ selectedPdfFile.name }}</h4>
                    <p class="upload-hint mb-3">{{ formatFileSize(selectedPdfFile.size) }} · PDF</p>
                    <p class="upload-hint upload-replace-hint">Click to choose a different file</p>
                </template>
            </div>

            <p v-if="fileError" class="upload-error mt-2">{{ fileError }}</p>

            <template v-if="selectedPdfFile">
                <!-- Password field for password-protected PDFs -->
                <v-text-field v-if="showPasswordField || passwordRequired" v-model="pdfPassword" label="PDF Password"
                    type="password" variant="outlined" prepend-inner-icon="mdi-lock"
                    hint="Enter the password for this password-protected PDF" persistent-hint :error="passwordRequired"
                    :error-messages="passwordRequired ? 'Password is required for this PDF' : ''"
                    class="mt-4 mb-3 pdf-password-field" rounded="lg" density="comfortable" clearable></v-text-field>

                <v-btn color="primary" size="large" rounded="lg" :loading="isUploading"
                    :disabled="isUploading || (passwordRequired && !pdfPassword)" @click="uploadBankStatement"
                    class="smooth-transition hover-lift mt-4" block>
                    <v-icon left>mdi-upload</v-icon>
                    {{ isUploading ? 'Processing...' : 'Upload & Process Statement' }}
                </v-btn>
            </template>
        </div>
    </div>
</template>

<script lang="ts">
import axios from '@/services/api';

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
            selectedPdfFile: null as File | null,
            isUploading: false,
            isDragging: false,
            fileError: '',
            pdfPassword: '',
            showPasswordField: false,
            passwordRequired: false
        }
    },
    emits: ['statementProcessed', 'uploadError'],
    methods: {
        openFilePicker() {
            // Clicking anywhere on the single drop zone opens the native picker.
            const input = (this as any).$refs.fileInput as HTMLInputElement | undefined;
            input?.click();
        },

        onInputChange(event: Event) {
            const input = event.target as HTMLInputElement;
            const file = input.files?.[0];
            if (file) {
                this.acceptFile(file);
            }
            // Allow picking the same file again later.
            input.value = '';
        },

        onDragLeave(event: DragEvent) {
            // Ignore dragleave events fired while moving over child elements.
            const current = event.currentTarget as Node | null;
            const related = (event.relatedTarget as Node | null) ?? null;
            if (!current || !related || !current.contains(related)) {
                (this as any).isDragging = false;
            }
        },

        onDrop(event: DragEvent) {
            (this as any).isDragging = false;
            const file = event.dataTransfer?.files?.[0];
            if (file) {
                this.acceptFile(file);
            }
        },

        acceptFile(file: File) {
            (this as any).fileError = '';
            const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
            if (!isPdf) {
                (this as any).fileError = 'Please select a PDF file';
                return;
            }
            if (file.size > 10 * 1024 * 1024) { // 10MB limit
                (this as any).fileError = 'File size must be less than 10MB';
                return;
            }

            (this as any).selectedPdfFile = file;
            // Reset password fields when a new file is chosen.
            (this as any).pdfPassword = '';
            (this as any).showPasswordField = false;
            (this as any).passwordRequired = false;
        },

        formatFileSize(bytes: number): string {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },

        async uploadBankStatement() {
            const file = (this as any).selectedPdfFile as File | null;
            if (!file) return;

            (this as any).isUploading = true;

            try {
                const formData = new FormData();
                formData.append('pdf_file', file);

                // Add password if provided
                if ((this as any).pdfPassword) {
                    formData.append('pdf_password', (this as any).pdfPassword);
                }

                // Upload to the actual API endpoint
                const response = await axios.post('/bank-statements/upload/', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                });

                if (response.data.status === 'processing') {
                    // Uploading and AI extraction are separate operations. The
                    // worker continues in the background and Profile exposes
                    // the processing state/retry action.
                    (this as any).$emit('statementProcessed', {
                        ...response.data,
                        status: 'uploaded'
                    });

                    // Reset form
                    (this as any).selectedPdfFile = null;
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
.bank-upload-content {
    width: 100%;
}

.upload-form {
    width: 100%;
}

.file-preview {
    animation: slideInUp 0.3s ease-out;
}

/* The native input stays in the DOM (so the picker can be triggered from JS)
   but is visually replaced by the unified drop zone. */
.upload-native-input {
    display: none;
}

.upload-placeholder {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.06) 0%, rgba(232, 245, 233, 0.4) 100%);
    border: 2px dashed rgba(76, 175, 80, 0.4);
    border-radius: 16px;
    padding: 32px 24px !important;
    transition: all 0.25s ease;
    cursor: pointer;
    outline: none;
}

.upload-placeholder:hover {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(232, 245, 233, 0.6) 100%);
    border-color: rgba(76, 175, 80, 0.6);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(76, 175, 80, 0.12);
}

.upload-placeholder:focus-visible {
    border-color: #4CAF50;
    box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.18);
}

.upload-placeholder.is-dragging {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.16) 0%, rgba(232, 245, 233, 0.8) 100%);
    border-color: #4CAF50;
    border-style: solid;
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(76, 175, 80, 0.18);
}

.upload-placeholder.has-file {
    border-style: solid;
    border-color: rgba(76, 175, 80, 0.65);
}

.upload-placeholder.has-error {
    border-color: #f44336;
    background: rgba(244, 67, 54, 0.05);
}

.upload-icon {
    width: 56px;
    height: 56px;
    color: #9E9E9E;
    display: block;
    margin-left: auto;
    margin-right: auto;
}

.upload-placeholder:hover .upload-icon {
    color: #4CAF50;
}

.upload-file-icon {
    color: #4CAF50;
}

.upload-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--bb-text-muted, #374151);
    word-break: break-word;
}

.upload-hint {
    font-size: 0.9rem;
    color: var(--bb-text-muted, #6b7280);
}

.upload-replace-hint {
    font-size: 0.8rem;
    color: var(--bb-text-muted, #9ca3af);
}

.upload-error {
    font-size: 0.85rem;
    color: #f44336;
    text-align: center;
}

.upload-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.8rem;
    color: #4CAF50;
    background: rgba(76, 175, 80, 0.1);
    padding: 6px 12px;
    border-radius: 8px;
}

.badge-icon {
    width: 16px;
    height: 16px;
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

/* Use one continuous password-field border instead of Vuetify's segmented outline. */
:deep(.pdf-password-field .v-field) {
    border: 1px solid #d1d5db;
    border-radius: 12px;
    background: var(--bb-surface, #ffffff);
    box-shadow: none;
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
}

:deep(.pdf-password-field .v-field__outline) {
    display: none;
}

:deep(.pdf-password-field .v-field--focused) {
    border-color: #4CAF50;
    box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.12);
}

:deep(.pdf-password-field .v-field--error) {
    border-color: #f44336;
    box-shadow: 0 0 0 3px rgba(244, 67, 54, 0.12);
}

:deep(.pdf-password-field .v-field-label--floating) {
    background: var(--bb-surface, #ffffff);
    padding: 0 6px;
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
}
</style>

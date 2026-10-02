<template>
    <div class="bg-gray-50 text-gray-900 font-sans antialiased min-h-screen flex flex-col">
        <AppHeader :userData="userData" />

        <main class="w-full flex-1 px-4 sm:px-6 lg:px-8 py-6">
            <!-- Loading -->
            <div v-if="loading" class="text-center pa-12">
                <v-progress-circular indeterminate color="primary" size="56"></v-progress-circular>
                <p class="mt-4 text-grey-darken-1">Loading review batch…</p>
            </div>

            <!-- Load error -->
            <v-alert v-else-if="loadError" type="error" variant="tonal" class="mb-6">
                {{ loadError }}
                <template #append>
                    <v-btn variant="text" @click="leave">Back</v-btn>
                </template>
            </v-alert>

            <template v-else>
                <!-- Sticky progress bar -->
                <div class="review-progress-bar">
                    <div class="min-w-0">
                        <h1 class="text-lg font-bold truncate mb-0">Import: {{ statementFilename || 'Bank statement' }}</h1>
                        <p class="text-sm text-grey-darken-1 mb-0">
                            <strong>{{ resolvedCount }}</strong> resolved ·
                            <strong :class="{ 'review-count-warning': actionRequiredCount > 0 }">{{ actionRequiredCount }}</strong>
                            require action ·
                            <strong>{{ duplicateCount }}</strong> duplicate{{ duplicateCount === 1 ? '' : 's' }}
                        </p>
                    </div>
                    <div class="d-flex align-center ga-2 flex-shrink-0">
                        <v-btn variant="outlined" size="small" :loading="savingDraft" @click="saveDraft">Save draft</v-btn>
                        <v-btn variant="outlined" size="small" @click="leave">Close</v-btn>
                        <v-btn color="primary" size="small" @click="importTransactions"
                            :disabled="selectedTransactions.length === 0 || (extractedData?.statement_kind !== 'multi_product' && !selectedAccountId) || unresolvedTransferCount > 0 || !canImportRetirement || (!creditCardIsReconciled && !creditCardImportTransactionsOnly) || !multiProductReady || (isExistingRetirementAccount && retirementIsReconciled && !retirementSnapshotConfirmed) || (isExistingCreditCardAccount && !creditCardSnapshotConfirmed && !creditCardImportTransactionsOnly)">
                            <v-icon left size="18">mdi-content-save</v-icon>
                            Save {{ selectedTransactions.length }} transaction{{ selectedTransactions.length !== 1 ? 's' : '' }}
                        </v-btn>
                    </div>
                </div>

                <v-alert v-if="actionError" type="error" variant="tonal" closable class="mt-4"
                    @click:close="actionError = ''">{{ actionError }}</v-alert>

                <div class="review-layout">
                    <!-- LEFT: accounts & balances -->
                    <aside class="review-left">

                <!-- Account Selection -->
                <v-card v-if="extractedData?.statement_kind !== 'multi_product'" class="mb-6" variant="tonal" color="primary" rounded="lg">
                    <v-card-text class="pa-4">
                        <div class="d-flex align-center mb-3">
                            <v-avatar size="32" class="me-3 bg-primary">
                                <v-icon color="white">mdi-bank</v-icon>
                            </v-avatar>
                            <div>
                                <h4 class="text-h6 font-weight-bold mb-1">Assign to Account</h4>
                                <p class="text-caption mb-0">Select an existing account or create a new one</p>
                            </div>
                        </div>

                        <!-- Account Selection -->
                        <v-row>
                            <v-col cols="12" md="6">
                                <v-select v-model="selectedAccountId" :items="accountOptions" label="Select Account"
                                    variant="outlined" density="comfortable" prepend-inner-icon="mdi-account"
                                    item-title="title" item-value="value" @update:model-value="handleAccountSelection"
                                    class="mb-2">
                                    <template v-slot:item="{ props, item }">
                                        <v-list-item v-bind="props">
                                            <template v-slot:prepend v-if="accountOptionRawValue(item) !== 'new'">
                                                <v-avatar size="24" class="me-2 bg-primary">
                                                    <v-icon color="white" size="14">mdi-account</v-icon>
                                                </v-avatar>
                                            </template>
                                        </v-list-item>
                                    </template>
                                </v-select>
                            </v-col>
                            <v-col cols="12" md="6">
                                <v-chip v-if="detectedAccountInfo.account_name" color="info" variant="tonal"
                                    class="mb-2">
                                    <v-icon left size="16">mdi-information</v-icon>
                                    Detected: {{ detectedAccountInfo.account_name }} ({{
                                        detectedAccountInfo.account_type }})
                                </v-chip>
                            </v-col>
                        </v-row>

                        <!-- Create New Account Form -->
                        <v-expand-transition>
                            <v-form v-if="selectedAccountId === 'new'" class="account-create-form mt-3">
                                <v-row>
                                    <v-col cols="12" md="4">
                                        <v-text-field v-model="newAccount.name" label="Account Name" variant="outlined"
                                            density="compact" prepend-inner-icon="mdi-account"
                                            :rules="[(v: string) => !!v || 'Account name is required']"
                                            required></v-text-field>
                                    </v-col>
                                    <v-col cols="12" md="4">
                                        <v-text-field v-model="newAccount.bank" label="Bank Name" variant="outlined"
                                            density="compact" prepend-inner-icon="mdi-bank"></v-text-field>
                                    </v-col>
                                    <v-col cols="12" md="4">
                                        <v-select v-model="newAccount.account_type" label="Account Type"
                                            :items="accountTypes" variant="outlined" density="compact"
                                            prepend-inner-icon="mdi-credit-card"
                                            :rules="[(v: string) => !!v || 'Account type is required']"
                                            required></v-select>
                                    </v-col>
                                </v-row>
                            </v-form>
                        </v-expand-transition>
                    </v-card-text>
                </v-card>

                <v-alert v-if="importWarning" type="success" variant="tonal" class="mb-4">
                    {{ importWarning }}
                </v-alert>

                <v-alert v-if="unresolvedTransferCount" type="warning" variant="tonal" class="mb-4">
                    {{ unresolvedTransferCount }} transfer{{ unresolvedTransferCount !== 1 ? 's' : '' }} need{{ unresolvedTransferCount === 1 ? 's' : '' }} different source and destination accounts before this statement can be imported.
                </v-alert>

                <v-card v-if="extractedData?.statement_kind === 'multi_product'" class="mb-6" variant="tonal" color="primary" rounded="lg">
                    <v-card-text class="pa-4">
                        <h4 class="text-h6 font-weight-bold mb-1">Detected accounts</h4>
                        <p class="text-caption mb-3">Review each detected account, its balances, and where its transactions belong.</p>
                        <v-card v-for="product in multiProducts" :key="product.id" variant="outlined" rounded="lg" class="mb-3 bg-surface">
                            <v-card-text>
                                <div class="d-flex flex-wrap align-center justify-space-between ga-2 mb-3">
                                    <div>
                                        <strong>{{ product.name || 'Unnamed account' }}</strong>
                                        <div class="text-caption text-medium-emphasis">{{ displayAccountType(product.product_type) }}</div>
                                    </div>
                                    <v-chip :color="productBalanceMatches(product) ? 'success' : 'warning'" size="small">
                                        {{ productBalanceMatches(product) ? 'Balance matches' : 'Balance needs review' }}
                                    </v-chip>
                                </div>
                                <v-row dense>
                                    <v-col cols="12" md="4"><v-text-field v-model="product.name" label="Account name" density="compact" variant="outlined" hide-details></v-text-field></v-col>
                                    <v-col cols="12" md="4"><v-text-field v-model="product.bank_name" label="Bank name" density="compact" variant="outlined" hide-details></v-text-field></v-col>
                                    <v-col cols="12" md="4"><v-select v-model="product.product_type" :items="accountTypes" label="Account type" density="compact" variant="outlined" hide-details></v-select></v-col>
                                    <v-col cols="12" md="3"><v-text-field v-model.number="product.opening_balance" type="number" step="0.01" prefix="$" label="Starting balance" density="compact" variant="outlined" hide-details></v-text-field></v-col>
                                    <v-col cols="12" md="3"><v-text-field v-model.number="product.closing_balance" type="number" step="0.01" prefix="$" label="Expected ending balance" density="compact" variant="outlined" hide-details></v-text-field></v-col>
                                    <v-col cols="12" md="3">
                                        <v-alert :type="productBalanceMatches(product) ? 'success' : 'warning'" variant="tonal" density="compact">
                                            <strong>Calculated ending:</strong><br>${{ formatMoney(calculatedProductBalance(product)) }}
                                        </v-alert>
                                    </v-col>
                                    <v-col cols="12" md="3"><v-select v-model="productSelections[product.id]" :items="productAccountOptions(product)" label="Save to account" density="compact" variant="outlined" hide-details></v-select></v-col>
                                </v-row>
                                <small class="d-block mt-2 text-medium-emphasis">
                                    {{ isNewProductAccount(product) ? 'A new account will be created with the starting balance above.' : 'Transactions will be applied to the selected existing account.' }}
                                </small>
                            </v-card-text>
                        </v-card>
                    </v-card-text>
                </v-card>

                <!-- Display Detected Initial Balance -->
                <v-alert v-if="extractedData?.initial_balance !== null && extractedData?.initial_balance !== undefined"
                    type="info" variant="tonal" class="mt-2" density="compact">
                    <div class="d-flex align-center">
                        <v-icon class="me-2">mdi-information</v-icon>
                        <span>
                            <strong>Detected Initial Balance:</strong>
                            ${{ extractedData.initial_balance.toLocaleString('en-US', {
                                minimumFractionDigits: 2,
                            maximumFractionDigits:
                            2 }) }}
                        </span>
                    </div>
                    <small class="text-grey-darken-1">
                        This will be set as the account's initial balance when creating a new account.
                    </small>
                </v-alert>

                <v-alert v-if="extractedData?.statement_kind === 'retirement'" :type="retirementIsReconciled ? 'success' : 'warning'" variant="tonal" rounded="lg" class="mb-4">
                    <div class="d-flex align-center mb-2"><v-icon class="me-2">mdi-piggy-bank-outline</v-icon><strong>Retirement / AFORE statement</strong></div>
                    <div><strong>Balance period:</strong> {{ formatDate(extractedData.balance_period?.start || '') }} - {{ formatDate(extractedData.balance_period?.end || '') }}</div>
                    <div><strong>Movement period:</strong> {{ formatDate(extractedData.movements_period?.start || '') }} - {{ formatDate(extractedData.movements_period?.end || '') }}</div>
                    <div v-for="(amount, label) in extractedData.retirement_breakdown?.subaccounts || {}" :key="String(label)"><strong>{{ label }}:</strong> ${{ Number(amount).toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</div>
                    <small v-if="!retirementIsReconciled">{{ extractedData.reconciliation?.reason || 'This statement cannot safely update a balance until it reconciles.' }}</small>
                </v-alert>

                <v-alert v-if="canUseRetirementOpeningBalanceImport" type="warning" variant="tonal" rounded="lg" class="mb-4">
                    <v-checkbox v-model="retirementOpeningBalanceConfirmed" color="warning" hide-details>
                        <template #label>
                            <span>I understand the closing balance is unverified. Import the selected movements using the opening balance of <strong>${{ retirementOpeningBalance?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong> only.</span>
                        </template>
                    </v-checkbox>
                </v-alert>

                <v-card v-if="extractedData?.statement_kind === 'credit_card_deferred_payments'" class="mb-4" variant="tonal" :color="creditCardIsReconciled ? 'success' : 'warning'" rounded="lg">
                    <v-card-text class="pa-4">
                        <div class="d-flex align-center mb-2"><v-icon class="me-2">mdi-credit-card-clock-outline</v-icon><strong>Credit card / deferred payments</strong></div>
                        <v-row dense>
                            <v-col cols="6" md="3"><small>Limit</small><div>${{ Number(extractedData.card_summary?.credit_limit || 0).toLocaleString() }}</div></v-col>
                            <v-col cols="6" md="3"><small>Available</small><div>${{ Number(extractedData.card_summary?.available_credit || 0).toLocaleString() }}</div></v-col>
                            <v-col cols="6" md="3"><small>Total debt</small><div>${{ Number(extractedData.card_summary?.total_debt || 0).toLocaleString() }}</div></v-col>
                            <v-col cols="6" md="3"><small>MSI debt</small><div>${{ Number(extractedData.card_summary?.deferred_balance || 0).toLocaleString() }}</div></v-col>
                        </v-row>
                        <v-row class="mt-2" dense>
                            <v-col cols="12" md="4"><v-text-field v-model.number="creditCardOpeningBalance" type="number" prefix="$" label="Opening available credit" density="compact" variant="outlined" hide-details></v-text-field></v-col>
                            <v-col cols="12" md="4"><v-text-field v-model.number="creditCardClosingBalance" type="number" prefix="$" label="Expected closing available credit" density="compact" variant="outlined" hide-details></v-text-field></v-col>
                            <v-col cols="12" md="4"><v-alert density="compact" variant="tonal" :type="creditCardBalanceMatches ? 'success' : 'warning'"><strong>Calculated:</strong> ${{ calculatedCreditCardBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</v-alert></v-col>
                        </v-row>
                        <small class="d-block mt-2">Calculated balance applies the selected reviewed rows to the opening available credit. Changing the expected closing value does not silently alter the account balance.</small>
                        <v-checkbox v-if="!creditCardIsReconciled" v-model="creditCardImportTransactionsOnly" color="warning" hide-details class="mt-2">
                            <template #label><span>I reviewed these transactions. Import transactions only; do not save the unverified card balance or MSI snapshot.</span></template>
                        </v-checkbox>
                        <small v-if="!creditCardIsReconciled">{{ extractedData.reconciliation?.reason || 'This card statement cannot safely update a balance.' }}</small>
                        <v-expansion-panels v-if="extractedData.deferred_purchases?.length" variant="accordion" class="mt-3">
                            <v-expansion-panel :title="`Deferred purchases / MSI (${extractedData.deferred_purchases.length})`">
                                <v-expansion-panel-text>
                                    <div v-for="plan in extractedData.deferred_purchases" :key="plan.source_key" class="mb-2">
                                        <strong>{{ plan.merchant }}</strong> · ${{ Number(plan.remaining_balance || 0).toLocaleString() }} remaining
                                        <v-row dense class="mt-1">
                                            <v-col cols="12" sm="4"><v-text-field v-model.number="plan.current_installment" type="number" min="0.01" step="0.01" prefix="$" label="Payment this month" density="compact" variant="outlined" hide-details></v-text-field></v-col>
                                            <v-col cols="6" sm="4"><v-text-field v-model.number="plan.installment_number" type="number" min="1" step="1" label="Current installment" density="compact" variant="outlined" hide-details></v-text-field></v-col>
                                            <v-col cols="6" sm="4"><v-text-field v-model.number="plan.installment_count" type="number" min="1" step="1" label="Total installments" density="compact" variant="outlined" hide-details></v-text-field></v-col>
                                        </v-row>
                                    </div>
                                    <v-btn color="primary" variant="tonal" size="small" :loading="savingMsi" @click="saveMsiDetails">Save MSI edits</v-btn>
                                    <small class="d-block mt-2 text-grey-darken-1">MSI schedules are informational; only the matching posted transaction is imported.</small>
                                </v-expansion-panel-text>
                            </v-expansion-panel>
                        </v-expansion-panels>
                    </v-card-text>
                </v-card>

                <!-- Statement Period Info -->
                <v-alert v-if="statementPeriod" type="info" variant="tonal" rounded="lg" class="mb-4">
                    <template v-slot:prepend>
                        <v-icon>mdi-calendar-range</v-icon>
                    </template>
                    <div>
                        <strong>Statement Period:</strong>
                        {{ formatDate(statementPeriod.start) }} - {{ formatDate(statementPeriod.end) }}
                    </div>
                </v-alert>
                    </aside>

                    <!-- CENTER: transaction review table -->
                    <section class="review-center">
                        <div class="review-filter-bar">
                            <v-btn v-for="option in filterOptions" :key="option.value" size="small"
                                :variant="statusFilter === option.value ? 'flat' : 'text'"
                                :color="statusFilter === option.value ? 'primary' : 'default'"
                                @click="statusFilter = option.value">
                                {{ option.title }}
                                <v-chip v-if="option.value === 'needs_review' && actionRequiredCount" size="x-small"
                                    color="warning" class="ms-2">{{ actionRequiredCount }}</v-chip>
                            </v-btn>
                            <v-spacer></v-spacer>
                            <span class="text-caption text-grey-darken-1 me-2">{{ filteredTransactions.length }} of {{
                                editableTransactions.length }} rows</span>
                            <v-btn size="small" color="primary" variant="tonal" @click="addTransaction"><v-icon
                                    start>mdi-plus</v-icon>Add row</v-btn>
                        </div>

                        <div class="transactions-review">
                            <v-data-table v-model="selectedTransactions" :headers="visibleHeaders"
                                :items="filteredTransactions" :items-per-page="50" show-select fixed-header
                                height="62vh" class="modern-data-table elevation-0 review-table" :loading="false"
                                item-value="id" @click:row="handleRowClick">

                        <!-- Status Column -->
                        <template v-slot:item.status="{ item }">
                            <v-chip :color="statusColor(item)" variant="tonal" size="small">{{ statusLabel(item) }}</v-chip>
                        </template>

                        <!-- Transaction Type Column -->
                        <template v-slot:item.transaction_type="{ item }">
                            <span class="review-cell-text">{{ item.transaction_type }}</span>
                        </template>

                        <!-- Title Column -->
                        <template v-slot:item.title="{ item }">
                            <span class="review-cell-text">{{ item.title }}</span>
                        </template>

                        <!-- Amount Column -->
                        <template v-slot:item.amount="{ item }">
                            <span class="review-cell-text">${{ Number(item.amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</span>
                        </template>

                        <!-- Date Column -->
                        <template v-slot:item.date="{ item }">
                            <span class="review-cell-text">{{ formatDate(item.date) }}</span>
                        </template>

                        <!-- Category Column -->
                        <template v-slot:item.category="{ item }">
                            <span class="review-cell-text">{{ item.category }}</span>
                        </template>


                        <template v-slot:item.products="{ item }">
                            <span class="review-cell-text">{{ productSummary(item) }}</span>
                        </template>


                        <!-- Match Column -->
                        <template v-slot:item.matches="{ item }">
                            <v-menu v-if="item.possible_matches?.length" location="bottom">
                                <template v-slot:activator="{ props }">
                                    <v-chip v-bind="props" color="warning" variant="tonal" size="small">
                                        {{ item.possible_matches.length }} match{{ item.possible_matches.length !== 1 ? 'es' : '' }}
                                    </v-chip>
                                </template>
                                <v-list density="compact" class="match-menu">
                                    <v-list-item v-for="match in item.possible_matches" :key="match.id"
                                        @click="linkToExisting(item, match)">
                                        <v-list-item-title>{{ match.title }}</v-list-item-title>
                                        <v-list-item-subtitle>
                                            {{ formatDate(match.date) }} • ${{ Number(match.total).toFixed(2) }}
                                        </v-list-item-subtitle>
                                    </v-list-item>
                                </v-list>
                            </v-menu>
                            <v-chip v-else-if="item.linked_transaction_id" color="success" variant="tonal" size="small">
                                Linked
                            </v-chip>
                            <v-chip v-else color="grey" variant="tonal" size="small">New</v-chip>
                        </template>

                        <!-- Actions Column -->
                        <template v-slot:item.actions="{ item }">
                            <v-btn icon size="small" variant="text" color="error" @click.stop="removeTransaction(item)">
                                <v-icon size="18">mdi-delete</v-icon>
                            </v-btn>
                        </template>

                        <!-- Empty state -->
                        <template v-slot:no-data>
                            <div class="text-center pa-8">
                                <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-receipt</v-icon>
                                <h3 class="text-h6 text-grey-darken-1 mb-2">No rows to show</h3>
                                <p class="text-body-2 text-grey-darken-1">No transactions match the current filter.</p>
                            </div>
                        </template>
                    </v-data-table>
                        </div>
                    </section>

                    <!-- RIGHT: selected row inspector -->
                    <aside class="review-right">
                        <div v-if="!selectedRow" class="review-inspector-empty">
                            <v-icon size="40" color="grey-lighten-1" class="mb-2">mdi-cursor-default-click-outline</v-icon>
                            <p class="text-body-2 text-grey-darken-1 mb-0">Select a row to review and edit its details.</p>
                        </div>

                        <template v-else>
                            <div class="d-flex align-center justify-space-between mb-3">
                                <h3 class="text-subtitle-1 font-weight-bold mb-0">Row details</h3>
                                <v-chip :color="statusColor(selectedRow)" variant="tonal" size="small">{{ statusLabel(selectedRow) }}</v-chip>
                            </div>

                            <v-select v-model="selectedRow.transaction_type" :items="transactionTypes" label="Type"
                                density="compact" variant="outlined" hide-details class="mb-3"></v-select>
                            <v-text-field v-model="selectedRow.title" label="Description" density="compact"
                                variant="outlined" hide-details class="mb-3"></v-text-field>
                            <v-row dense class="mb-1">
                                <v-col cols="6"><v-text-field v-model="selectedRow.amount" type="number" step="0.01"
                                        prefix="$" label="Amount" density="compact" variant="outlined"
                                        hide-details></v-text-field></v-col>
                                <v-col cols="6"><v-text-field v-model="selectedRow.date" type="date" label="Date"
                                        density="compact" variant="outlined" hide-details></v-text-field></v-col>
                            </v-row>
                            <v-select v-model="selectedRow.category" :items="categories" label="Category"
                                density="compact" variant="outlined" hide-details class="mb-3"></v-select>

                            <!-- Account / product assignment -->
                            <template v-if="extractedData?.statement_kind === 'multi_product'">
                                <v-select v-model="selectedRow.source_product_id" :items="statementProductOptions"
                                    :label="selectedRow.transaction_type === 'Transfer' ? 'From account' : 'Account'"
                                    density="compact" variant="outlined" hide-details class="mb-3"></v-select>
                                <v-select v-if="selectedRow.transaction_type === 'Transfer'"
                                    v-model="selectedRow.destination_product_id" :items="statementProductOptions"
                                    label="To account" density="compact" variant="outlined" hide-details
                                    class="mb-3"></v-select>
                            </template>
                            <template v-else-if="selectedRow.transaction_type === 'Transfer'">
                                <v-select v-model="selectedRow.from_account_id" :items="transferAccountOptions"
                                    label="From account" density="compact" variant="outlined" hide-details
                                    class="mb-3"></v-select>
                                <v-select v-model="selectedRow.to_account_id" :items="transferAccountOptions"
                                    label="To account" density="compact" variant="outlined" hide-details
                                    class="mb-3"></v-select>
                            </template>
                            <v-alert v-if="rowNeedsReview(selectedRow)" type="warning" variant="tonal" density="compact"
                                class="mb-3">This row still needs different source and destination accounts.</v-alert>

                            <!-- Suggested matches -->
                            <div v-if="selectedRow.possible_matches?.length" class="mb-3">
                                <p class="text-caption font-weight-bold mb-1">Suggested matches</p>
                                <v-btn v-for="match in selectedRow.possible_matches" :key="match.id" variant="tonal"
                                    size="small" block class="mb-1 justify-start"
                                    @click="linkToExisting(selectedRow, match)">
                                    {{ match.title }} · {{ formatDate(match.date) }} · ${{ Number(match.total).toFixed(2) }}
                                </v-btn>
                            </div>
                            <v-chip v-else-if="selectedRow.linked_transaction_id" color="success" variant="tonal"
                                size="small" class="mb-3">Linked to existing transaction</v-chip>
                        </template>

                        <!-- Commit confirmations (always visible while reviewing) -->
                        <v-divider class="my-4"></v-divider>
                        <v-checkbox v-if="isExistingRetirementAccount" v-model="retirementSnapshotConfirmed"
                            color="primary" hide-details
                            label="This statement is newer than the latest retirement snapshot."></v-checkbox>
                        <v-checkbox v-if="isExistingCreditCardAccount" v-model="creditCardSnapshotConfirmed"
                            color="primary" hide-details
                            label="This statement is newer than the latest credit-card snapshot."></v-checkbox>
                    </aside>
                </div>
            </template>
        </main>
    </div>
</template>


<script lang="ts">
import axios from '@/services/api';
import { getStoredSession } from '@/services/session';
import AppHeader from '@/components/AppHeader.vue';
import { rowStatus as classifyRowStatus, rowNeedsReview as rowNeedsReviewRule, summarizeRows } from '@/services/importReviewStatus';

interface DetectedTransaction {
    id?: string;
    candidate_id?: number;
    title: string;
    amount: number;
    date: string;
    category: string;
    transaction_type: 'Income' | 'Expense' | 'Transfer';
    account_name?: string;
    possible_matches?: TransactionMatch[];
    linked_transaction_id?: number | null;
    from_account_id?: string | null;
    to_account_id?: string | null;
    status?: 'pending' | 'imported' | 'skipped' | 'linked';
    requires_resolution?: boolean;
    source_product_id?: string | null;
    destination_product_id?: string | null;
}

interface AccountInfo {
    name: string;
    bank: string;
    account_type: string;
}

interface TransactionMatch {
    id: number;
    title: string;
    transaction_type: string;
    category: string;
    date: string;
    total: number;
    account_id?: string | null;
    from_account_id?: string | null;
    to_account_id?: string | null;
}

interface ImportBatch {
    id: number;
    detected_account_name?: string;
    detected_account_type?: string;
    initial_balance?: number | null;
    statement_period?: {
        start: string | null;
        end: string | null;
    };
    statement_kind?: string;
    balance_period?: { start: string; end: string };
    movements_period?: { start: string; end: string };
    retirement_breakdown?: { institution?: string; subaccounts?: Record<string, number> };
    card_summary?: CardSummary;
    deferred_purchases?: DeferredPurchase[];
    reconciliation?: { is_reconciled?: boolean; reason?: string; opening_balance?: number; closing_balance?: number };
    products?: ImportProduct[];
    candidates: DetectedTransaction[];
}

interface CardSummary { credit_limit?: number; available_credit?: number; opening_total_debt?: number; total_debt?: number; regular_debt?: number; deferred_balance?: number; payment_due?: number; statement_date?: string; }
interface DeferredPurchase { source_key: string; merchant: string; original_amount?: number; remaining_balance?: number; current_installment?: number; installment_number?: number; installment_count?: number; }

interface ImportProduct {
    id: number;
    source_product_id: string;
    name: string;
    bank_name: string;
    product_type: string;
    opening_balance?: number | null;
    closing_balance?: number | null;
    calculated_closing_balance?: number | null;
    reconciliation?: { is_reconciled?: boolean; reason?: string; valuation_change?: number; calculated_closing_balance?: number };
    positions?: unknown[];
    linked_account_id?: number | null;
}

interface BankStatementData {
    review_batch_id?: number;
    import_batch?: ImportBatch;
    extracted_data?: {
        transactions: DetectedTransaction[];
        account_name: string;
        account_type: string;
        initial_balance?: number | null;
        statement_period?: {
            start: string;
            end: string;
        };
        statement_kind?: string;
        balance_period?: { start: string; end: string };
        movements_period?: { start: string; end: string };
        retirement_breakdown?: { institution?: string; subaccounts?: Record<string, number> };
        card_summary?: CardSummary;
        deferred_purchases?: DeferredPurchase[];
        reconciliation?: { is_reconciled?: boolean; reason?: string; opening_balance?: number; closing_balance?: number };
        processing_error?: string;
    };
    account_detected?: AccountInfo;
    transactions?: DetectedTransaction[];
}

export default {
    name: 'ImportReview',
    components: {
        AppHeader
    },
    data() {
        return {
            loading: false,
            loadError: '',
            actionError: '',
            savingDraft: false,
            statementFilename: '',
            statusFilter: 'needs_review',
            selectedRowKey: null as string | number | null,
            userData: { user: {} } as any,
            accounts: [] as any[],
            filterOptions: [
                { title: 'Needs review', value: 'needs_review' },
                { title: 'All', value: 'all' },
                { title: 'Imported', value: 'imported' },
                { title: 'Skipped', value: 'skipped' },
                { title: 'Linked', value: 'linked' },
            ],
            selectedAccountId: null as string | null,
            selectedAccount: null as any,
            detectedAccountInfo: {
                account_name: '',
                account_type: ''
            },
            newAccount: {
                name: '',
                bank: '',
                account_type: ''
            },
            statementPeriod: null as { start: string; end: string } | null,
            retirementSnapshotConfirmed: false,
            retirementOpeningBalanceConfirmed: false,
            creditCardSnapshotConfirmed: false,
            creditCardImportTransactionsOnly: false,
            creditCardOpeningBalance: null as number | null,
            creditCardClosingBalance: null as number | null,
            savingMsi: false,
            importWarning: '',
            multiProducts: [] as ImportProduct[],
            productSelections: {} as Record<number, string>,
            editableTransactions: [] as DetectedTransaction[],
            selectedTransactions: [] as DetectedTransaction[],
            reviewBatchId: null as number | null,
            removedCandidateIds: [] as number[],
            headers: [
                { title: 'Status', key: 'status', sortable: false, width: '130px' },
                { title: 'Type', key: 'transaction_type', sortable: false, width: '120px' },
                { title: 'Description', key: 'title', sortable: false, width: '200px' },
                { title: 'Amount', key: 'amount', sortable: false, width: '120px' },
                { title: 'Date', key: 'date', sortable: false, width: '140px' },
                { title: 'Category', key: 'category', sortable: false, width: '160px' },
                { title: 'Account', key: 'products', sortable: false, width: '210px' },
                { title: 'Matches', key: 'matches', sortable: false, width: '120px' },
                { title: 'Actions', key: 'actions', sortable: false, width: '80px' },
            ],
            transactionTypes: [
                { title: 'Income', value: 'Income' },
                { title: 'Expense', value: 'Expense' },
                { title: 'Transfer', value: 'Transfer' }
            ],
            categories: [
                'Account Transfer',
                'Awards',
                'Balance Transfer',
                'Bills and utilities',
                'Education',
                'Entertainment',
                'Food and drinks',
                'Gifts',
                'Insurance',
                'Investments',
                'Loans',
                'Medical',
                'Money Transfer',
                'Others',
                'Salary',
                'Shopping',
                'Transportation',
                'Transfer',
                'Retirement contribution',
                'Investment return',
                'Retirement fee',
                'Retirement interest',
            ],
            extractedData: null as BankStatementData['extracted_data'] | null,
            accountTypes: [
                { title: 'Business', value: 'Business' },
                { title: 'Checking', value: 'Checking' },
                { title: 'Credit Card', value: 'Credit Card' },
                { title: 'Debit', value: 'Débito' },
                { title: 'Cash', value: 'Efectivo' },
                { title: 'Investment', value: 'Investment' },
                { title: 'Loan', value: 'Loan' },
                { title: 'Mortgage', value: 'Mortgage' },
                { title: 'Other', value: 'Other' },
                { title: 'Savings', value: 'Savings' },
                { title: 'Retirement', value: 'Retirement' },
            ]
        }
    },
    emits: ['transactionsImported', 'importError'],
    computed: {
        selectedRow(): DetectedTransaction | null {
            return (this as any).editableTransactions.find((row: DetectedTransaction) => row.id === (this as any).selectedRowKey) || null;
        },
        reviewSummary(): { resolved: number; actionRequired: number; duplicates: number } {
            return summarizeRows((this as any).editableTransactions);
        },
        resolvedCount(): number {
            return (this as any).reviewSummary.resolved;
        },
        actionRequiredCount(): number {
            return (this as any).reviewSummary.actionRequired;
        },
        duplicateCount(): number {
            return (this as any).reviewSummary.duplicates;
        },
        filteredTransactions(): DetectedTransaction[] {
            const filter = (this as any).statusFilter;
            if (filter === 'all') return (this as any).editableTransactions;
            return (this as any).editableTransactions.filter((row: DetectedTransaction) => (this as any).rowStatus(row) === filter);
        },
        retirementIsReconciled(): boolean {
            return this.extractedData?.statement_kind !== 'retirement' || !!this.extractedData?.reconciliation?.is_reconciled;
        },
        retirementOpeningBalance(): number | null {
            const rawBalance = this.extractedData?.initial_balance ?? this.extractedData?.reconciliation?.opening_balance;
            const balance = Number(rawBalance);
            return Number.isFinite(balance) ? balance : null;
        },
        canUseRetirementOpeningBalanceImport(): boolean {
            return this.extractedData?.statement_kind === 'retirement'
                && !this.retirementIsReconciled
                && this.retirementOpeningBalance !== null;
        },
        canImportRetirement(): boolean {
            return this.retirementIsReconciled
                || (this.canUseRetirementOpeningBalanceImport && this.retirementOpeningBalanceConfirmed);
        },
        isExistingRetirementAccount(): boolean {
            return this.extractedData?.statement_kind === 'retirement' && this.selectedAccountId !== 'new' && !!this.selectedAccountId;
        },
        creditCardIsReconciled(): boolean {
            return this.extractedData?.statement_kind !== 'credit_card_deferred_payments' || !!this.extractedData?.reconciliation?.is_reconciled;
        },
        isExistingCreditCardAccount(): boolean {
            return this.extractedData?.statement_kind === 'credit_card_deferred_payments' && this.selectedAccountId !== 'new' && !!this.selectedAccountId;
        },
        calculatedCreditCardBalance(): number {
            const opening = Number(this.creditCardOpeningBalance ?? this.selectedAccount?.total ?? this.extractedData?.card_summary?.available_credit ?? 0);
            return this.selectedTransactions.reduce((balance: number, transaction: DetectedTransaction) => {
                const amount = Number(transaction.amount) || 0;
                if (transaction.transaction_type === 'Expense') return balance - amount;
                if (transaction.transaction_type === 'Income') return balance + amount;
                return balance;
            }, opening);
        },
        creditCardBalanceMatches(): boolean {
            const expected = Number(this.creditCardClosingBalance);
            return Number.isFinite(expected) && Math.abs(expected - this.calculatedCreditCardBalance) < 0.01;
        },
        multiProductReady(): boolean {
            return this.extractedData?.statement_kind !== 'multi_product' || this.multiProducts.every(product =>
                !!product.name?.trim()
                && !!product.product_type
                && product.opening_balance !== null && product.opening_balance !== undefined
                && product.closing_balance !== null && product.closing_balance !== undefined
                && this.productBalanceMatches(product)
                && !!this.productSelections[product.id]
            );
        },
        visibleHeaders() {
            return this.extractedData?.statement_kind === 'multi_product'
                ? (this as any).headers
                : (this as any).headers.filter((header: { key: string }) => header.key !== 'products');
        },
        statementProductOptions() {
            return this.multiProducts.map(product => ({ title: product.name || 'Unnamed account', value: product.source_product_id }));
        },
        unresolvedTransferCount(): number {
            return this.editableTransactions.filter((transaction: DetectedTransaction) =>
                transaction.transaction_type === 'Transfer'
                && (!transaction.from_account_id || !transaction.to_account_id || transaction.from_account_id === transaction.to_account_id)
            ).length;
        },
        accountOptions() {
            const options = (this as any).accounts.map((acc: any) => ({
                title: `${acc.account_name} (${acc.account_type})`,
                value: acc.id.toString(),
                account: acc
            }));
            options.push({
                title: '+ Create New Account',
                value: 'new',
                account: null
            });
            return options;
        },
        transferAccountOptions() {
            return (this as any).accounts.map((account: any) => ({
                title: `${account.account_name} (${account.account_type})`,
                value: account.id.toString()
            }));
        }
    },
    async mounted() {
        const session = getStoredSession();
        if (session) (this as any).userData = { user: session.user };
        (this as any).statementFilename = String((this as any).$route?.query?.filename || '');
        try {
            const username = (this as any).userData?.user?.username;
            if (username) {
                const response = await axios.get(`/accounts/details/${username}/0`);
                (this as any).accounts = response.data;
            }
        } catch {
            // Accounts are only needed for transfer mapping; the batch can still load.
        }
        const batchId = Number((this as any).$route?.params?.batchId);
        if (Number.isFinite(batchId) && batchId > 0) {
            await (this as any).loadBatch(batchId);
        } else {
            (this as any).loadError = 'No review batch was specified.';
        }
    },
    methods: {
        applyBatch(bankStatementData: BankStatementData) {
            // Handle new API format with extracted_data
            let transactions: DetectedTransaction[] = [];
            let accountName = '';
            let accountType = '';
            const importBatch = bankStatementData.import_batch || ((bankStatementData as any).candidates ? bankStatementData as any : null);

            (this as any).reviewBatchId = bankStatementData.review_batch_id || importBatch?.id || null;
            (this as any).removedCandidateIds = [];
            (this as any).importWarning = '';

            if (importBatch) {
                transactions = (importBatch.candidates || []).map((candidate: any) => ({
                    id: `candidate-${candidate.id}`,
                    candidate_id: candidate.id,
                    title: candidate.title,
                    amount: candidate.amount,
                    date: candidate.date,
                    category: candidate.category,
                    transaction_type: candidate.transaction_type,
                    possible_matches: candidate.possible_matches || [],
                    linked_transaction_id: candidate.linked_transaction_id,
                    requires_resolution: candidate.requires_resolution,
                    source_product_id: candidate.source_product_id,
                    destination_product_id: candidate.destination_product_id,
                    from_account_id: candidate.from_account_id || null,
                    // A transfer cannot use the same account at both ends. Clear
                    // stale values from earlier imports so the user must choose
                    // the other side explicitly.
                    to_account_id: candidate.to_account_id && candidate.to_account_id !== candidate.from_account_id
                        ? candidate.to_account_id
                        : null,
                    status: candidate.status
                }));
                accountName = importBatch.detected_account_name || '';
                accountType = importBatch.detected_account_type || '';
                (this as any).statementPeriod = importBatch.statement_period?.start || importBatch.statement_period?.end
                    ? importBatch.statement_period
                    : null;
                this.extractedData = {
                    transactions,
                    account_name: accountName,
                    account_type: accountType,
                    initial_balance: importBatch.initial_balance ?? null,
                    statement_period: (this as any).statementPeriod || undefined,
                    statement_kind: importBatch.statement_kind,
                    balance_period: importBatch.balance_period,
                    movements_period: importBatch.movements_period,
                    retirement_breakdown: importBatch.retirement_breakdown,
                    card_summary: importBatch.card_summary,
                    deferred_purchases: importBatch.deferred_purchases,
                    reconciliation: importBatch.reconciliation,
                };
                (this as any).multiProducts = importBatch.products || [];
                (this as any).productSelections = {};
                (this as any).multiProducts.forEach((product: ImportProduct) => {
                    const match = (this as any).accounts.find((account: any) => account.account_name === product.name || account.account_name.toLowerCase().includes(product.name.toLowerCase()));
                    (this as any).productSelections[product.id] = match ? match.id.toString() : `new:${product.id}`;
                });
            } else if (bankStatementData.extracted_data) {
                transactions = bankStatementData.extracted_data.transactions || [];
                accountName = bankStatementData.extracted_data.account_name || '';
                accountType = bankStatementData.extracted_data.account_type || '';
                (this as any).statementPeriod = bankStatementData.extracted_data.statement_period || null;
                this.extractedData = bankStatementData.extracted_data; // Store extracted data
            } else if (bankStatementData.transactions) {
                // Fallback to old format
                transactions = bankStatementData.transactions;
                if (bankStatementData.account_detected) {
                    accountName = bankStatementData.account_detected.name || '';
                    accountType = bankStatementData.account_detected.account_type || '';
                }
            }

            // Add unique IDs to transactions if they don't have them
            transactions = transactions.map((t, index) => ({
                ...t,
                id: t.id || `temp-${Date.now()}-${index}`
            }));

            (this as any).detectedAccountInfo = {
                account_name: accountName,
                account_type: accountType
            };

            (this as any).editableTransactions = [...transactions];
            // Imported and skipped candidates are historical review rows. They
            // must stay visible but must never be submitted a second time.
            (this as any).selectedTransactions = transactions.filter((transaction: DetectedTransaction) =>
                !transaction.status || transaction.status === 'pending' || transaction.status === 'linked'
            );

            // Try to find matching account (only if accountName is not empty)
            let matchingAccount = null;
            if (accountName && accountName.trim() !== '') {
                matchingAccount = (this as any).accounts.find((acc: any) =>
                    acc.account_name === accountName ||
                    acc.account_name.toLowerCase().includes(accountName.toLowerCase())
                );
            }

            if (matchingAccount) {
                (this as any).selectedAccountId = matchingAccount.id.toString();
                (this as any).selectedAccount = matchingAccount;
            } else {
                (this as any).selectedAccountId = null;
                (this as any).selectedAccount = null;
            }

            // Initialize new account form with detected info
            (this as any).newAccount = {
                name: accountName,
                bank: accountName.split('(')[0]?.trim() || '',
                account_type: accountType || 'Credit Card'
            };
            (this as any).creditCardImportTransactionsOnly = false;
            (this as any).creditCardOpeningBalance = matchingAccount?.total ?? importBatch?.card_summary?.available_credit ?? null;
            (this as any).creditCardClosingBalance = importBatch?.card_summary?.available_credit ?? null;

            (this as any).selectedRowKey = null;
        },

        async loadBatch(batchId: number) {
            (this as any).loading = true;
            (this as any).loadError = '';
            try {
                const response = await axios.get(`/bank-statements/import-batches/${batchId}/`);
                (this as any).applyBatch({ review_batch_id: response.data.id, import_batch: response.data });
            } catch (error: any) {
                (this as any).loadError = error.response?.data?.message || 'Unable to load that import review batch.';
            } finally {
                (this as any).loading = false;
            }
        },

        leave() {
            (this as any).$router.push('/');
        },

        reportError(message: string) {
            (this as any).actionError = message;
        },

        handleImported() {
            (this as any).leave();
        },

        handleRowClick(_event: unknown, slot: { item: DetectedTransaction }) {
            (this as any).selectedRowKey = slot?.item?.id ?? null;
        },

        rowStatus(transaction: DetectedTransaction): string {
            return classifyRowStatus(transaction);
        },

        rowNeedsReview(transaction: DetectedTransaction): boolean {
            return rowNeedsReviewRule(transaction);
        },

        statusLabel(transaction: DetectedTransaction): string {
            const status = (this as any).rowStatus(transaction);
            const labels: Record<string, string> = { needs_review: 'Needs review', ready: 'Ready', imported: 'Imported', skipped: 'Skipped', linked: 'Linked' };
            return labels[status] || status;
        },

        statusColor(transaction: DetectedTransaction): string {
            const status = (this as any).rowStatus(transaction);
            const colors: Record<string, string> = { needs_review: 'warning', ready: 'success', imported: 'primary', skipped: 'grey', linked: 'success' };
            return colors[status] || 'grey';
        },

        productSummary(transaction: DetectedTransaction): string {
            const accountNameFor = (value?: string | null) => {
                if (!value) return '';
                const match = (this as any).accounts.find((account: any) => String(account.id) === String(value));
                return match?.account_name || String(value);
            };
            if ((this as any).extractedData?.statement_kind === 'multi_product') {
                const productNameFor = (productId?: string | null) => {
                    const product = (this as any).multiProducts.find((item: ImportProduct) => item.source_product_id === productId);
                    return product?.name || productId || '';
                };
                if (transaction.transaction_type === 'Transfer') {
                    return `${productNameFor(transaction.source_product_id) || '?'} → ${productNameFor(transaction.destination_product_id) || '?'}`;
                }
                return productNameFor(transaction.source_product_id) || '—';
            }
            if (transaction.transaction_type === 'Transfer') {
                return `${accountNameFor(transaction.from_account_id) || '?'} → ${accountNameFor(transaction.to_account_id) || '?'}`;
            }
            return accountNameFor(transaction.account_name) || '—';
        },

        async saveDraft() {
            if (!(this as any).reviewBatchId) return;
            (this as any).savingDraft = true;
            (this as any).actionError = '';
            try {
                const patches = (this as any).editableTransactions
                    .filter((row: DetectedTransaction) => row.candidate_id && row.status !== 'imported')
                    .map((row: DetectedTransaction) => axios.patch(
                        `/bank-statements/import-candidates/${row.candidate_id}/`,
                        (this as any).candidatePatchPayload(row, '', row.status || 'pending')
                    ));
                await Promise.all(patches);
                (this as any).importWarning = 'Draft saved. Your review decisions are stored and will be here when you return.';
            } catch (error: any) {
                (this as any).reportError(error.response?.data?.message || error.message || 'Could not save the draft.');
            } finally {
                (this as any).savingDraft = false;
            }
        },

        accountOptionRawValue(item: { raw?: unknown }): string {
            const raw = item.raw as { value?: string } | undefined;
            return raw?.value ?? '';
        },

        formatDate(dateString: string): string {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
        },

        handleAccountSelection(selectedValue: string | null) {
            // Handle null/undefined (user cleared selection)
            if (!selectedValue) {
                (this as any).selectedAccountId = null;
                (this as any).selectedAccount = null;
                return;
            }

            // Handle "new" account option
            if (selectedValue === 'new') {
                (this as any).selectedAccountId = 'new';
                (this as any).selectedAccount = null;
                return;
            }

            // Find the account object from the accounts array
            const account = (this as any).accounts.find((acc: any) => acc.id.toString() === selectedValue);
            if (account) {
                (this as any).selectedAccount = account;
                (this as any).selectedAccountId = selectedValue;
            } else {
                // Account not found - reset selection
                (this as any).selectedAccountId = null;
                (this as any).selectedAccount = null;
            }
        },

        productAccountOptions(product: ImportProduct) {
            const items = (this as any).accounts
                .filter((account: any) => account.account_type === product.product_type)
                .map((account: any) => ({ title: `${account.account_name} (${(this as any).displayAccountType(account.account_type)})`, value: account.id.toString() }));
            items.push({ title: `+ Create ${product.name}`, value: `new:${product.id}` });
            return items;
        },

        displayAccountType(type: string) {
            return ({ 'Débito': 'Debit', 'Efectivo': 'Cash', 'Crédito': 'Credit Card' } as Record<string, string>)[type] || type;
        },

        formatMoney(value: number) {
            return Number(value || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        },

        isNewProductAccount(product: ImportProduct) {
            return String((this as any).productSelections[product.id] || '').startsWith('new:');
        },

        calculatedProductBalance(product: ImportProduct) {
            let balance = Number(product.opening_balance || 0);
            for (const transaction of (this as any).selectedTransactions as DetectedTransaction[]) {
                const amount = Number(transaction.amount) || 0;
                if (transaction.transaction_type === 'Transfer') {
                    if (transaction.source_product_id === product.source_product_id) balance -= amount;
                    if (transaction.destination_product_id === product.source_product_id) balance += amount;
                } else if (transaction.source_product_id === product.source_product_id) {
                    balance += transaction.transaction_type === 'Income' ? amount : -amount;
                }
            }
            balance += Number(product.reconciliation?.valuation_change || 0);
            return Math.round((balance + Number.EPSILON) * 100) / 100;
        },

        productBalanceMatches(product: ImportProduct) {
            const expected = Number(product.closing_balance);
            return Number.isFinite(expected) && Math.abs(expected - (this as any).calculatedProductBalance(product)) < 0.01;
        },

        removeTransaction(transaction: DetectedTransaction) {
            if (transaction.candidate_id) {
                (this as any).removedCandidateIds.push(transaction.candidate_id);
            }
            const index = (this as any).editableTransactions.findIndex((t: DetectedTransaction) => t.id === transaction.id);
            if (index > -1) {
                (this as any).editableTransactions.splice(index, 1);
            }

            const selectedIndex = (this as any).selectedTransactions.findIndex((t: DetectedTransaction) => t.id === transaction.id);
            if (selectedIndex > -1) {
                (this as any).selectedTransactions.splice(selectedIndex, 1);
            }
        },

        addTransaction() {
            const firstProduct = (this as any).multiProducts[0] as ImportProduct | undefined;
            const secondProduct = (this as any).multiProducts[1] as ImportProduct | undefined;
            const transaction: DetectedTransaction = {
                id: `manual-${Date.now()}`,
                title: 'Manual transaction', amount: 0, date: new Date().toISOString().slice(0, 10),
                transaction_type: 'Expense', category: 'Others', possible_matches: [],
                source_product_id: firstProduct?.source_product_id || null,
                destination_product_id: secondProduct?.source_product_id || null,
            };
            (this as any).editableTransactions.push(transaction);
            (this as any).selectedTransactions.push(transaction);
        },

        async saveMsiDetails(raiseOnError = false) {
            if (!(this as any).reviewBatchId || !this.extractedData?.deferred_purchases) return;
            (this as any).savingMsi = true;
            try {
                const response = await axios.patch(
                    `/bank-statements/import-batches/${(this as any).reviewBatchId}/msi/`,
                    { deferred_purchases: this.extractedData.deferred_purchases }
                );
                this.extractedData.deferred_purchases = response.data.deferred_purchases;
            } catch (error: any) {
                if (raiseOnError) throw error;
                (this as any).reportError(error.response?.data?.message || 'Failed to save MSI details.');
            } finally {
                (this as any).savingMsi = false;
            }
        },

        linkToExisting(transaction: DetectedTransaction, match: TransactionMatch) {
            transaction.linked_transaction_id = match.id;
            transaction.status = 'linked';
            transaction.possible_matches = [];
            const selected = (this as any).selectedTransactions;
            if (!selected.some((item: DetectedTransaction) => item.id === transaction.id)) {
                selected.push(transaction);
            }
        },

        candidatePatchPayload(transaction: DetectedTransaction, accountId: number | string, statusValue: string) {
            const payload: any = {
                title: transaction.title,
                transaction_type: transaction.transaction_type,
                category: transaction.category,
                date: transaction.date,
                amount: parseFloat(transaction.amount.toString()),
                status: statusValue
            };
            if (this.extractedData?.statement_kind === 'multi_product') {
                payload.source_product_id = transaction.source_product_id || '';
                payload.destination_product_id = transaction.transaction_type === 'Transfer'
                    ? transaction.destination_product_id || ''
                    : '';
                if (transaction.linked_transaction_id) payload.linked_transaction_id = transaction.linked_transaction_id;
                return payload;
            }
            if (transaction.linked_transaction_id) {
                payload.linked_transaction_id = transaction.linked_transaction_id;
            } else if (transaction.transaction_type === 'Transfer') {
                payload.from_account_id = (transaction as any).from_account_id || '';
                payload.to_account_id = (transaction as any).to_account_id || '';
            } else {
                payload.account_id = accountId;
            }
            return payload;
        },

        async importMultiProductTransactions() {
            if (!(this as any).reviewBatchId) throw new Error('The statement review batch is missing.');
            if (!this.multiProductReady) throw new Error('Review the account details and make every calculated ending balance match.');

            await Promise.all(((this as any).multiProducts as ImportProduct[]).map((product: ImportProduct) =>
                axios.patch(`/bank-statements/import-products/${product.id}/`, {
                    name: product.name,
                    bank_name: product.bank_name || '',
                    product_type: product.product_type,
                    opening_balance: Number(product.opening_balance),
                    closing_balance: Number(product.closing_balance),
                })
            ));

            const selectedManualTransactions = (this as any).selectedTransactions
                .filter((transaction: DetectedTransaction) => !transaction.candidate_id);
            for (const transaction of selectedManualTransactions as DetectedTransaction[]) {
                const response = await axios.post(
                    `/bank-statements/import-batches/${(this as any).reviewBatchId}/candidates/`,
                    {
                        title: transaction.title,
                        transaction_type: transaction.transaction_type,
                        category: transaction.category,
                        date: transaction.date,
                        amount: Number(transaction.amount),
                        source_product_id: transaction.source_product_id,
                        destination_product_id: transaction.transaction_type === 'Transfer' ? transaction.destination_product_id : null,
                    }
                );
                transaction.candidate_id = response.data.candidate.id;
            }

            const selectedKeys = new Set(
                (this as any).selectedTransactions.map((transaction: DetectedTransaction) => transaction.candidate_id || transaction.id)
            );
            const patchPromises = (this as any).editableTransactions
                .filter((transaction: DetectedTransaction) => transaction.candidate_id && transaction.status !== 'imported')
                .map((transaction: DetectedTransaction) => {
                    const key = transaction.candidate_id || transaction.id;
                    const nextStatus = transaction.linked_transaction_id ? 'linked' : selectedKeys.has(key) ? 'pending' : 'skipped';
                    return axios.patch(
                        `/bank-statements/import-candidates/${transaction.candidate_id}/`,
                        (this as any).candidatePatchPayload(transaction, '', nextStatus)
                    );
                });
            const removedPromises = (this as any).removedCandidateIds.map((candidateId: number) =>
                axios.patch(`/bank-statements/import-candidates/${candidateId}/`, { status: 'skipped' })
            );
            await Promise.all([...patchPromises, ...removedPromises]);

            const refreshed = await axios.get(`/bank-statements/import-batches/${(this as any).reviewBatchId}/`);
            const refreshedProducts = refreshed.data.products as ImportProduct[];
            if (refreshedProducts.some(product => !product.reconciliation?.is_reconciled)) {
                (this as any).multiProducts = refreshedProducts;
                throw new Error('The saved account balances do not reconcile with their assigned transactions.');
            }

            const productAccountMap: Record<string, string> = {};
            for (const product of refreshedProducts) {
                const selected = (this as any).productSelections[product.id];
                if (!selected) throw new Error(`Select where to save ${product.name}.`);
                if (selected.startsWith('new:')) {
                    const response = await axios.post('/accounts/', {
                        account_name: product.name,
                        account_type: product.product_type,
                        bank: product.bank_name || '',
                        total: product.opening_balance ?? 0,
                    });
                    productAccountMap[product.id] = response.data.id.toString();
                } else {
                    productAccountMap[product.id] = selected;
                }
            }

            const commitResponse = await axios.post(
                `/bank-statements/import-batches/${(this as any).reviewBatchId}/commit/`,
                { product_account_map: productAccountMap }
            );
            (this as any).handleImported({ importedCount: commitResponse.data?.imported?.length || 0 });
            (this as any).leave();
        },

        async reloadReviewBatch() {
            if (!(this as any).reviewBatchId) return;
            await (this as any).loadBatch((this as any).reviewBatchId);
        },

        async importTransactions() {
            try {
                let account: any = null;
                if (this.extractedData?.statement_kind === 'multi_product') {
                    await (this as any).importMultiProductTransactions();
                    return;
                }
                if (this.extractedData?.statement_kind === 'retirement' && !this.canImportRetirement) {
                    (this as any).reportError('Confirm the opening-balance-only import before importing this unreconciled retirement statement.');
                    return;
                }
                if (this.extractedData?.statement_kind === 'credit_card_deferred_payments' && !this.creditCardIsReconciled && !this.creditCardImportTransactionsOnly) {
                    (this as any).reportError('This credit-card statement does not reconcile and is review-only.');
                    return;
                }

                // Handle account creation or selection
                if ((this as any).selectedAccountId === 'new') {
                    // Create new account
                    if (!(this as any).newAccount.name || !(this as any).newAccount.account_type) {
                        (this as any).reportError('Please fill in all required account fields.');
                        return;
                    }

                    // Use detected initial_balance if available, otherwise default to 0
                    const initialBalance = this.extractedData?.statement_kind === 'retirement'
                        ? (this.retirementOpeningBalance ?? 0.0)
                        : this.extractedData?.statement_kind === 'credit_card_deferred_payments'
                            ? (this.creditCardOpeningBalance ?? 0.0)
                        : (this.extractedData?.initial_balance ?? 0.0);

                    const accountData = {
                        account_name: (this as any).newAccount.name,
                        account_type: (this as any).newAccount.account_type,
                        bank: (this as any).newAccount.bank || '',
                        total: initialBalance
                    };
                    if (this.extractedData?.statement_kind === 'credit_card_deferred_payments') {
                        accountData.account_type = 'Credit Card';
                        (accountData as any).credit_limit = this.extractedData.card_summary?.credit_limit;
                    }

                    const accountResponse = await axios.post('/accounts/', accountData);
                    account = accountResponse.data;
                } else if ((this as any).selectedAccountId) {
                    // Use selected account
                    account = (this as any).selectedAccount;
                } else {
                    (this as any).reportError('Please select an account or create a new one.');
                    return;
                }

                if (!account || !account.id) {
                    (this as any).reportError('Account not found or could not be created.');
                    return;
                }

                if ((this as any).reviewBatchId) {
                    await (this as any).saveMsiDetails(true);
                    const selectedManualTransactions = (this as any).selectedTransactions
                        .filter((transaction: DetectedTransaction) => !transaction.candidate_id);
                    await Promise.all(selectedManualTransactions.map(async (transaction: DetectedTransaction) => {
                        const response = await axios.post(
                            `/bank-statements/import-batches/${(this as any).reviewBatchId}/candidates/`,
                            {
                                title: transaction.title,
                                transaction_type: transaction.transaction_type,
                                category: transaction.category,
                                date: transaction.date,
                                amount: parseFloat(transaction.amount.toString()),
                            }
                        );
                        transaction.candidate_id = response.data.candidate.id;
                    }));
                    const selectedKeys = new Set(
                        (this as any).selectedTransactions.map((transaction: DetectedTransaction) =>
                            transaction.candidate_id || transaction.id
                        )
                    );
                    const patchPromises = (this as any).editableTransactions
                        .filter((transaction: DetectedTransaction) => transaction.candidate_id && transaction.status !== 'imported')
                        .map((transaction: DetectedTransaction) => {
                            const key = transaction.candidate_id || transaction.id;
                            const nextStatus = transaction.linked_transaction_id
                                ? 'linked'
                                : selectedKeys.has(key)
                                    ? 'pending'
                                    : 'skipped';
                            return axios.patch(
                                `/bank-statements/import-candidates/${transaction.candidate_id}/`,
                                (this as any).candidatePatchPayload(transaction, account.id, nextStatus)
                            );
                        });

                    const removedPromises = (this as any).removedCandidateIds.map((candidateId: number) =>
                        axios.patch(`/bank-statements/import-candidates/${candidateId}/`, { status: 'skipped' })
                    );
                    await Promise.all([...patchPromises, ...removedPromises]);

                    const commitResponse = await axios.post(
                        `/bank-statements/import-batches/${(this as any).reviewBatchId}/commit/`,
                        { account_id: account.id.toString(), confirm_retirement_snapshot: (this as any).retirementSnapshotConfirmed,
                          confirm_credit_card_snapshot: (this as any).creditCardSnapshotConfirmed,
                          import_transactions_only: (this as any).creditCardImportTransactionsOnly,
                          use_retirement_opening_balance_only: (this as any).retirementOpeningBalanceConfirmed }
                    );
                    const importedCount = commitResponse.data?.imported?.length || 0;
                    const failedCount = commitResponse.data?.failed?.length || 0;
                    if (failedCount > 0) {
                        const failedTitles = (commitResponse.data?.failed || [])
                            .map((candidate: any) => candidate.title)
                            .filter(Boolean)
                            .join(', ');
                        (this as any).handleImported({ importedCount, accountUpdated: account });
                        await (this as any).reloadReviewBatch();
                        (this as any).importWarning = `${importedCount} transaction${importedCount === 1 ? '' : 's'} saved. Review ${failedTitles || `${failedCount} remaining candidate${failedCount === 1 ? '' : 's'}`} and choose different source and destination accounts.`;
                        return;
                    } else {
                        (this as any).handleImported({
                            importedCount,
                            accountUpdated: account
                        });
                    }
                    (this as any).leave();
                    return;
                }

                // Prepare transactions for import
                const transactionsToImport = (this as any).selectedTransactions.map((transaction: DetectedTransaction) => ({
                    title: transaction.title,
                    transaction_type: transaction.transaction_type,
                    category: transaction.category,
                    date: transaction.date,
                    total: parseFloat(transaction.amount.toString()),
                    owner_id: (this as any).userData.user.username,
                    account_id: account.id.toString()
                }));

                // Import each transaction and track successful imports
                const successfulImports: DetectedTransaction[] = [];
                const failedImports: { transaction: DetectedTransaction; error: any }[] = [];

                for (let i = 0; i < transactionsToImport.length; i++) {
                    try {
                        await axios.post('/transactions/create/', transactionsToImport[i]);
                        successfulImports.push((this as any).selectedTransactions[i]);
                    } catch (error: any) {
                        console.error(`Failed to import transaction ${i + 1}:`, error);
                        failedImports.push({
                            transaction: (this as any).selectedTransactions[i],
                            error: error
                        });
                    }
                }

                // Check if all imports failed
                if (successfulImports.length === 0) {
                    const errorMessage = `Failed to import all ${transactionsToImport.length} transactions. Please try again.`;
                    (this as any).reportError(errorMessage);
                    return; // No transactions imported, no balance update needed
                }

                if (failedImports.length > 0) {
                    const warningMessage = `Imported ${successfulImports.length} of ${transactionsToImport.length} transactions. ${failedImports.length} transaction(s) failed to import.`;
                    (this as any).reportError(warningMessage);
                } else {
                    (this as any).handleImported({
                        importedCount: successfulImports.length,
                        accountUpdated: account
                    });
                }

                (this as any).leave();

            } catch (error: any) {
                console.error('Error importing transactions:', error);
                const errorMessage = error.response?.data?.message || error.response?.data?.error || error.response?.data?.details || error.message || 'Failed to import transactions. Please try again.';
                (this as any).reportError(errorMessage);
            }
        }
    }
}
</script>

<style scoped>
/* Review dialog specific styles */
.modern-dialog {
    background: var(--bb-surface, #ffffff);
    border: 1px solid var(--bb-border-soft, #f3f4f6);
    box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14);
}

.close-btn {
    transition: all 0.2s ease;
}

.close-btn:hover {
    background: var(--bb-surface-soft, #f9fafb);
    transform: none;
}

.transactions-review {
    background: transparent;
}

/* Data table styling */
.modern-data-table {
    background: transparent !important;
    border-radius: 16px;
    overflow: hidden;
}

/* Form field styling for inline editing */
:deep(.transaction-type-select .v-field),
:deep(.transaction-title-input .v-field),
:deep(.transaction-amount-input .v-field),
:deep(.transaction-date-input .v-field),
:deep(.transaction-category-select .v-field) {
    border-radius: 8px;
    font-size: 0.875rem;
}

:deep(.transaction-type-select .v-field__outline),
:deep(.transaction-title-input .v-field__outline),
:deep(.transaction-amount-input .v-field__outline),
:deep(.transaction-date-input .v-field__outline),
:deep(.transaction-category-select .v-field__outline) {
    border-radius: 8px;
}

/* Table row styling */
:deep(.v-data-table__tr) {
    transition: all 0.2s ease;
}

:deep(.v-data-table__tr:hover) {
    background: #f9fafb !important;
}

:deep(.v-data-table__tr:nth-child(even)) {
    background: var(--bb-surface, #ffffff);
}

:deep(.v-data-table__tr:nth-child(odd)) {
    background: var(--bb-surface, #ffffff);
}

:deep(.v-data-table__td) {
    border-bottom: 1px solid var(--bb-border-soft, #f3f4f6);
    padding: 12px 8px;
}

/* Header styling */
:deep(.v-data-table-header th) {
    font-weight: 600;
    color: #2E7D32;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.5px;
    background: var(--bb-surface-soft, #f9fafb);
}

/* Selection styling */
:deep(.v-selection-control) {
    margin: 0;
}

/* Button styling */
:deep(.v-btn) {
    text-transform: none;
    font-weight: 500;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .modern-dialog {
        margin: 16px;
        max-width: calc(100vw - 32px);
    }

    :deep(.v-data-table__td) {
        padding: 8px 4px;
        font-size: 0.8rem;
    }

    :deep(.v-data-table-header th) {
        font-size: 0.7rem;
        padding: 8px 4px;
    }

    /* Make form fields more compact on mobile */
    :deep(.transaction-type-select .v-field),
    :deep(.transaction-title-input .v-field),
    :deep(.transaction-amount-input .v-field),
    :deep(.transaction-date-input .v-field),
    :deep(.transaction-category-select .v-field) {
        font-size: 0.8rem;
    }
}

/* Enhanced form field focus states */
:deep(.transaction-type-select .v-field--focused),
:deep(.transaction-title-input .v-field--focused),
:deep(.transaction-amount-input .v-field--focused),
:deep(.transaction-date-input .v-field--focused),
:deep(.transaction-category-select .v-field--focused) {
    border-color: #4CAF50;
    box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.12);
}

/* Account create form styling */
.account-create-form {
    background: var(--bb-surface, #ffffff);
    border-radius: 12px;
    padding: 16px;
    border: 1px solid rgba(76, 175, 80, 0.35);
    animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Animation for dialog */
.modern-dialog {
    animation: slideInScale 0.3s ease-out;
}

@keyframes slideInScale {
    from {
        opacity: 0;
        transform: scale(0.9) translateY(-20px);
    }

    to {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}

/* ===== Import Review workspace ===== */
.review-progress-bar {
    align-items: center;
    background: var(--bb-surface, #ffffff);
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 16px;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
    display: flex;
    gap: 1rem;
    justify-content: space-between;
    padding: 0.85rem 1.25rem;
    position: sticky;
    top: 72px;
    z-index: 40;
}

.review-count-warning {
    color: #b45309;
}

.review-layout {
    align-items: start;
    display: grid;
    gap: 1.5rem;
    grid-template-columns: minmax(0, 1fr);
    margin-top: 1.5rem;
}

@media (min-width: 1280px) {
    .review-layout {
        grid-template-columns: 340px minmax(0, 1fr) 380px;
    }
}

.review-left,
.review-center,
.review-right {
    min-width: 0;
}

.review-right {
    position: sticky;
    top: 160px;
}

.review-filter-bar {
    align-items: center;
    background: var(--bb-surface, #ffffff);
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 12px;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    padding: 0.5rem 0.75rem;
}

.review-cell-text {
    color: var(--bb-text-muted, #374151);
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.review-inspector-empty {
    align-items: center;
    border: 1px dashed rgba(15, 23, 42, 0.15);
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    padding: 2rem 1rem;
    text-align: center;
}

.review-table :deep(.v-data-table__th) {
    background: var(--bb-surface-soft, #f9fafb);
}
</style>

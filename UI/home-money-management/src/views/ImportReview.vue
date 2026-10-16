<template>
    <div class="bg-gray-50 text-gray-900 font-sans antialiased flex flex-col">
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
                        <v-btn color="primary" size="small" @click="importTransactions" :disabled="!canSaveImport">
                            <v-icon left size="18">mdi-content-save</v-icon>
                            Save {{ selectedTransactions.length }} transaction{{ selectedTransactions.length !== 1 ? 's' : '' }}
                        </v-btn>
                    </div>
                    <div class="review-progress-note">
                        <small v-if="saveBlockedReason" class="review-blocked-reason" data-testid="save-blocked-reason">{{ saveBlockedReason }}</small>
                        <!-- Inline commit confirmations: the blocked reason and the action
                             that clears it stay side by side at every viewport width, so
                             the fix is never stranded in the off-screen inspector column. -->
                        <v-checkbox v-if="isExistingCreditCardAccount && !creditCardImportTransactionsOnly"
                            v-model="creditCardSnapshotConfirmed" color="primary" density="compact" hide-details
                            class="review-progress-confirm" data-testid="credit-card-snapshot-confirm-inline">
                            <template #label>
                                <span>
                                    Confirm snapshot replacement
                                    <span v-if="creditCardSnapshotEffectiveDate"> · effective {{ creditCardSnapshotEffectiveDate }}</span>
                                    <span v-if="creditCardSnapshotBeforeAfter"> · available credit {{ creditCardSnapshotBeforeAfter }}</span>
                                </span>
                            </template>
                        </v-checkbox>
                        <v-checkbox v-if="isExistingRetirementAccount" v-model="retirementSnapshotConfirmed"
                            color="primary" density="compact" hide-details class="review-progress-confirm"
                            data-testid="retirement-snapshot-confirm-inline">
                            <template #label>
                                <span>Confirm this statement is newer than the latest retirement snapshot.</span>
                            </template>
                        </v-checkbox>
                    </div>
                </div>

                <v-alert v-if="actionError" type="error" variant="tonal" closable class="mt-4"
                    @click:close="actionError = ''">{{ actionError }}</v-alert>

                <v-card v-if="extractedData?.statement_kind !== 'multi_product'" class="mt-4" rounded="lg" variant="outlined">
                    <v-card-text class="pa-4">
                        <div class="d-flex flex-wrap align-center justify-space-between ga-3 mb-3">
                            <div>
                                <h2 class="text-h6 font-weight-bold mb-1">Destination account</h2>
                                <p class="text-caption mb-0">Choose where reviewed transactions will be saved. This decision is saved immediately.</p>
                            </div>
                            <v-chip :color="selectedAccountId ? 'success' : 'warning'" variant="tonal">
                                {{ selectedAccountId === 'new' ? 'New account draft' : selectedAccount ? 'Destination saved' : 'Not assigned' }}
                            </v-chip>
                        </div>
                        <v-alert v-if="detectedAccountInfo.account_name" type="info" variant="tonal" density="compact" class="mb-3">
                            AI detected <strong>{{ detectedAccountInfo.account_name }}</strong><span v-if="detectedAccountInfo.account_type"> ({{ detectedAccountInfo.account_type }})</span>.
                            <v-btn v-if="suggestedAccount" size="small" variant="text" color="primary" class="ml-2" @click="useDetectedAccount">Use detected account</v-btn>
                        </v-alert>
                        <v-row dense>
                            <v-col cols="12" md="6">
                                <v-autocomplete v-model="selectedAccountId" :items="accountOptions" label="Save transactions to"
                                    variant="outlined" density="comfortable" item-title="title" item-value="value"
                                    clearable @update:model-value="handleAccountSelection" />
                            </v-col>
                            <v-col cols="12" md="6" class="d-flex align-center">
                                <span class="text-caption text-medium-emphasis">{{ assignmentSaveState }}</span>
                            </v-col>
                        </v-row>
                        <v-expand-transition>
                            <v-row v-if="selectedAccountId === 'new'" dense class="mt-1">
                                <v-col cols="12" md="4"><v-text-field v-model="newAccount.name" label="Account name" variant="outlined" density="compact" @update:model-value="queueNewAccountDraft" /></v-col>
                                <v-col cols="12" md="4"><v-text-field v-model="newAccount.bank" label="Bank name" variant="outlined" density="compact" @update:model-value="queueNewAccountDraft" /></v-col>
                                <v-col cols="12" md="4"><v-select v-model="newAccount.account_type" :items="accountTypes" label="Account type" variant="outlined" density="compact" @update:model-value="queueNewAccountDraft" /></v-col>
                            </v-row>
                        </v-expand-transition>
                    </v-card-text>
                </v-card>

                <!-- Multi-product setup needs a full-width workspace. Keeping it
                     in the narrow review sidebar collapses every field and leaves
                     a large, unusable card below the account controls. -->
                <v-card v-if="extractedData?.statement_kind === 'multi_product'" class="mt-4 detected-accounts-panel" variant="tonal" color="primary" rounded="lg">
                    <v-card-text class="pa-4">
                        <div class="d-flex flex-wrap align-center justify-space-between ga-3 mb-3">
                            <div>
                                <h2 class="text-h6 font-weight-bold mb-1">Detected accounts</h2>
                                <p class="text-caption mb-0">Review each detected account, its balances, and where its transactions belong.</p>
                            </div>
                            <v-chip :color="multiProductReady ? 'success' : 'warning'" size="small">
                                {{ multiProductReady ? 'Ready to import' : 'Account review required' }}
                            </v-chip>
                        </div>
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
                                            <div><strong>Transaction sum:</strong> {{ formatSignedMoney(productTransactionSum(product)) }}</div>
                                            <div><strong>Calculated ending:</strong> ${{ formatMoney(calculatedProductBalance(product)) }}</div>
                                            <div v-if="Number(product.reconciliation?.valuation_change || 0)" class="text-caption">
                                                Includes valuation change {{ formatSignedMoney(Number(product.reconciliation?.valuation_change || 0)) }}
                                            </div>
                                            <div v-if="!productBalanceMatches(product)" class="text-caption">
                                                {{ productBalanceDifferenceLabel(product) }}
                                            </div>
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

                <!-- Credit-card reconciliation and MSI schedules need a full-width
                     workspace. The review sidebar is intentionally narrow, which
                     makes the three schedule inputs unreadable when several plans
                     are present. -->
                <v-card v-if="extractedData?.statement_kind === 'credit_card_deferred_payments'" class="mt-4 credit-card-workspace" variant="tonal" :color="creditCardIsReconciled ? 'success' : 'warning'" rounded="lg">
                    <v-card-text class="pa-4">
                        <div class="d-flex flex-wrap align-center justify-space-between ga-3 mb-3">
                            <div class="d-flex align-center">
                                <v-icon class="me-2">mdi-credit-card-clock-outline</v-icon>
                                <div>
                                    <h2 class="text-h6 font-weight-bold mb-0">Credit card / deferred payments</h2>
                                    <p class="text-caption mb-0">Review the card reconciliation and MSI schedule before importing.</p>
                                </div>
                            </div>
                            <v-chip :color="creditCardIsReconciled ? 'success' : 'warning'" variant="tonal">
                                {{ creditCardIsReconciled ? 'Balance reconciled' : 'Balance needs review' }}
                            </v-chip>
                        </div>
                        <v-row dense>
                            <v-col cols="6" sm="3"><small>Limit</small><div>${{ Number(extractedData.card_summary?.credit_limit || 0).toLocaleString() }}</div></v-col>
                            <v-col cols="6" sm="3"><small>Available</small><div>${{ Number(extractedData.card_summary?.available_credit || 0).toLocaleString() }}</div></v-col>
                            <v-col cols="6" sm="3"><small>Total debt</small><div>${{ Number(extractedData.card_summary?.total_debt || 0).toLocaleString() }}</div></v-col>
                            <v-col cols="6" sm="3"><small>MSI debt</small><div>${{ Number(extractedData.card_summary?.deferred_balance || 0).toLocaleString() }}</div></v-col>
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
                            <v-expansion-panel :title="`Deferred purchases / financing (${extractedData.deferred_purchases.length})`">
                                <v-expansion-panel-text>
                                    <div class="msi-plan-list">
                                        <v-card v-for="plan in extractedData.deferred_purchases" :key="plan.source_key" class="msi-plan" variant="outlined">
                                            <v-card-text class="pa-3">
                                                <div class="d-flex flex-wrap align-center justify-space-between ga-2 mb-2">
                                                    <strong class="msi-plan-merchant">{{ plan.merchant }}</strong>
                                                    <v-chip size="small" variant="tonal" :color="financingTypeColor(plan.financing_type)">
                                                        {{ financingTypeLabel(plan.financing_type) }}
                                                    </v-chip>
                                                    <v-chip size="small" variant="tonal">${{ formatMoney(Number(plan.remaining_balance || 0)) }} remaining</v-chip>
                                                </div>
                                                <v-row dense>
                                                    <v-col cols="12" sm="4"><v-text-field v-model.number="plan.current_installment" type="number" min="0.01" step="0.01" prefix="$" label="Payment this month" density="compact" variant="outlined" hide-details></v-text-field></v-col>
                                                    <v-col cols="6" sm="4"><v-text-field v-model.number="plan.installment_number" type="number" min="1" step="1" label="Current installment" density="compact" variant="outlined" hide-details></v-text-field></v-col>
                                                    <v-col cols="6" sm="4"><v-text-field v-model.number="plan.installment_count" type="number" min="1" step="1" label="Total installments" density="compact" variant="outlined" hide-details></v-text-field></v-col>
                                                </v-row>
                                                <small v-if="!plan.installment_count || !plan.installment_number" class="d-block mt-2 text-grey-darken-1">
                                                    Installment details unavailable — the statement did not specify an installment number or total count.
                                                </small>
                                            </v-card-text>
                                        </v-card>
                                    </div>
                                    <div class="d-flex flex-wrap align-center ga-3 mt-3">
                                        <v-btn color="primary" variant="tonal" size="small" :loading="savingMsi" @click="saveMsiDetails">Save financing edits</v-btn>
                                        <small class="text-grey-darken-1">Financing schedules are informational; only the matching posted transaction is imported.</small>
                                    </div>
                                </v-expansion-panel-text>
                            </v-expansion-panel>
                        </v-expansion-panels>
                    </v-card-text>
                </v-card>

                <div class="review-layout">
                    <!-- LEFT: accounts & balances -->
                    <aside class="review-left">

                <!-- Account Selection -->
                <v-card v-if="false && extractedData?.statement_kind !== 'multi_product'" class="mb-6" variant="tonal" color="primary" rounded="lg">
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

                <!-- Display Detected Initial Balance -->
                <v-alert v-if="selectedAccountId === 'new' && extractedData?.initial_balance !== null && extractedData?.initial_balance !== undefined"
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
                                :items="filteredTransactions" :items-per-page="50" show-select return-object fixed-header
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
                            <v-btn icon size="small" variant="text" color="error"
                                :aria-label="`Remove ${item.title || 'this row'}`"
                                @click.stop="removeTransaction(item)">
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
                                <v-select :model-value="multiProductEndpointValue(selectedRow, 'from')" :items="multiProductEndpointOptions"
                                    :label="selectedRow.transaction_type === 'Transfer' ? 'From account' : 'Account'"
                                    density="compact" variant="outlined" hide-details class="mb-3"
                                    @update:model-value="setMultiProductEndpoint(selectedRow, 'from', $event)"></v-select>
                                <v-select v-if="selectedRow.transaction_type === 'Transfer'"
                                    :model-value="multiProductEndpointValue(selectedRow, 'to')" :items="multiProductEndpointOptions"
                                    label="To account" density="compact" variant="outlined" hide-details
                                    class="mb-3" @update:model-value="setMultiProductEndpoint(selectedRow, 'to', $event)"></v-select>
                            </template>
                            <template v-else-if="selectedRow.transaction_type === 'Transfer'">
                                <v-select v-model="selectedRow.from_account_id" :items="transferAccountOptions"
                                    label="From account" density="compact" variant="outlined" hide-details
                                    class="mb-3"></v-select>
                                <v-select v-model="selectedRow.to_account_id" :items="transferAccountOptions"
                                    label="To account" density="compact" variant="outlined" hide-details
                                    class="mb-3"></v-select>
                                <v-alert v-if="selectedRow.from_account_id === batchDraftAccountValue || selectedRow.to_account_id === batchDraftAccountValue"
                                    type="info" variant="tonal" density="compact" class="mb-3">
                                    This endpoint will use the new account for this statement when you save the import.
                                </v-alert>
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
                        <div v-if="isExistingCreditCardAccount" class="mt-2">
                            <v-checkbox v-model="creditCardSnapshotConfirmed" color="primary" hide-details
                                data-testid="credit-card-snapshot-confirm">
                                <template #label>
                                    <span>
                                        Replace the latest credit-card snapshot with this statement.
                                        <span v-if="creditCardSnapshotEffectiveDate">
                                            Effective {{ creditCardSnapshotEffectiveDate }}
                                        </span>
                                        <span v-if="creditCardSnapshotBeforeAfter">
                                            · available credit {{ creditCardSnapshotBeforeAfter }}
                                        </span>
                                    </span>
                                </template>
                            </v-checkbox>
                            <small class="d-block text-grey-darken-1 mt-1">
                                Checking this box confirms this statement is newer than the account's latest
                                snapshot and intentionally replaces that snapshot and its MSI schedule. Your
                                reviewed transactions are still validated on their own; this only authorizes
                                replacing the stored snapshot.
                            </small>
                        </div>
                    </aside>
                </div>
            </template>
        </main>
    </div>
</template>


<script lang="ts">
import axios from '@/services/api';
import { getStoredSession } from '@/services/session';
import { todayLocalISO } from '@/services/calendarDate';
import AppHeader from '@/components/AppHeader.vue';
import { rowStatus as classifyRowStatus, rowNeedsReview as rowNeedsReviewRule, summarizeRows } from '@/services/importReviewStatus';
import { formatCalendarDate } from '@/services/calendarDate';
import { CATEGORIES, ACCOUNT_TYPES, TRANSACTION_TYPES } from '@/constants/taxonomy';

const BATCH_DRAFT_ACCOUNT = '__batch_destination_draft__';

interface DetectedTransaction {
    id?: string;
    candidate_id?: number;
    title: string;
    amount: number;
    date: string;
    category: string;
    transaction_type: 'Income' | 'Expense' | 'Transfer' | 'External Deposit' | 'External Withdrawal';
    account_name?: string;
    possible_matches?: TransactionMatch[];
    linked_transaction_id?: number | null;
    from_account_id?: string | null;
    to_account_id?: string | null;
    from_uses_batch_draft?: boolean;
    to_uses_batch_draft?: boolean;
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
    reconciliation?: { is_reconciled?: boolean; reason?: string; opening_balance?: number; closing_balance?: number; reviewed_opening_balance?: number; opening_balance_source?: string };
    products?: ImportProduct[];
    candidates: DetectedTransaction[];
    draft_assignment?: { kind: 'existing' | 'new'; account_id?: number; account_name?: string; account_type?: string; name?: string; bank?: string } | null;
    scan_summary?: { importable_candidate_count?: number };
}

interface CardSummary { credit_limit?: number; available_credit?: number; opening_total_debt?: number; total_debt?: number; regular_debt?: number; deferred_balance?: number; payment_due?: number; statement_date?: string; }
interface DeferredPurchase { source_key: string; merchant: string; original_amount?: number; remaining_balance?: number; current_installment?: number; installment_number?: number; installment_count?: number; financing_type?: 'interest_free' | 'interest_bearing' | 'unknown'; }

interface ImportProduct {
    id: number;
    source_product_id: string;
    name: string;
    bank_name: string;
    product_type: string;
    opening_balance?: number | null;
    closing_balance?: number | null;
    calculated_closing_balance?: number | null;
    reconciliation?: { is_reconciled?: boolean; reason?: string; cash_movements?: number; valuation_change?: number; calculated_closing_balance?: number };
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
        reconciliation?: { is_reconciled?: boolean; reason?: string; opening_balance?: number; closing_balance?: number; reviewed_opening_balance?: number; opening_balance_source?: string };
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
            assignmentSaveState: '',
            assignmentSaveTimer: null as ReturnType<typeof setTimeout> | null,
            batchDraftAccountValue: BATCH_DRAFT_ACCOUNT,
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
            reviewDraftAssignment: null as ImportBatch['draft_assignment'],
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
            transactionTypes: [...TRANSACTION_TYPES],
            categories: [...CATEGORIES],
            extractedData: null as BankStatementData['extracted_data'] | null,
            accountTypes: [...ACCOUNT_TYPES]
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
        creditCardAccountIds(): Set<string> {
            // The card can be the selected existing account, or the pending
            // new-account draft for this statement (the batch-draft sentinel).
            const ids = new Set<string>();
            const selected = (this as any).selectedAccountId;
            if (selected && selected !== 'new') ids.add(String(selected));
            if ((this as any).selectedAccountId === 'new'
                || (this as any).reviewDraftAssignment?.kind === 'new') {
                ids.add(BATCH_DRAFT_ACCOUNT);
            }
            return ids;
        },
        calculatedCreditCardBalance(): number {
            const opening = Number(this.creditCardOpeningBalance ?? this.selectedAccount?.total ?? this.extractedData?.reconciliation?.opening_balance ?? this.extractedData?.card_summary?.available_credit ?? 0);
            const cardIds = (this as any).creditCardAccountIds as Set<string>;
            return this.selectedTransactions.reduce((balance: number, transaction: DetectedTransaction) => {
                const amount = Number(transaction.amount) || 0;
                if (transaction.transaction_type === 'Expense') return balance - amount;
                if (transaction.transaction_type === 'Income') return balance + amount;
                // A credit-card account tracks available credit. A card payment
                // is a Transfer *into* the card (Hey -> Tarjeta): it reduces the
                // debt and so raises available credit. A Transfer *out of* the
                // card (a cash advance or balance transfer) lowers it. Only the
                // leg touching this card moves its available credit; the other
                // account's balance is unaffected here.
                if (transaction.transaction_type === 'Transfer') {
                    const to = transaction.to_account_id ? String(transaction.to_account_id) : '';
                    const from = transaction.from_account_id ? String(transaction.from_account_id) : '';
                    if (to && cardIds.has(to)) return balance + amount;
                    if (from && cardIds.has(from)) return balance - amount;
                }
                return balance;
            }, opening);
        },
        creditCardBalanceMatches(): boolean {
            const expected = Number(this.creditCardClosingBalance);
            return Number.isFinite(expected) && Math.abs(expected - this.calculatedCreditCardBalance) < 0.01;
        },
        creditCardSnapshotEffectiveDate(): string {
            // The date the replacement snapshot takes effect: the statement's own
            // period end when present, otherwise the extracted card statement date.
            const periodEnd = this.extractedData?.statement_period?.end;
            if (periodEnd) return (this as any).formatDate(periodEnd);
            const statementDate = this.extractedData?.card_summary?.statement_date;
            return statementDate ? (this as any).formatDate(statementDate) : '';
        },
        creditCardSnapshotBeforeAfter(): string {
            // Before/after available credit for the snapshot being replaced, so the
            // confirmation states its real accounting impact instead of a bare label.
            const before = this.selectedAccount?.total;
            const after = Number(this.creditCardClosingBalance);
            if (!Number.isFinite(after)) return '';
            const beforeText = Number.isFinite(Number(before))
                ? `$${(this as any).formatMoney(Number(before))}`
                : 'unknown';
            return `${beforeText} → $${(this as any).formatMoney(after)}`;
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
        saveBlockedReason(): string {
            // Explain the exact condition keeping Save disabled, so a reconciled
            // header never sits beside an inexplicably disabled button. Keep the
            // order aligned with the button's :disabled expression.
            if (this.selectedTransactions.length === 0) return 'Select at least one transaction to import.';
            if (this.extractedData?.statement_kind !== 'multi_product' && !this.selectedAccountId) {
                return 'Choose a destination account for these transactions.';
            }
            if (this.unresolvedTransferCount > 0) {
                return `${this.unresolvedTransferCount} transfer${this.unresolvedTransferCount === 1 ? '' : 's'} still need a source and destination account.`;
            }
            if (this.extractedData?.statement_kind === 'retirement' && !this.canImportRetirement) {
                return 'Confirm the opening-balance-only import for this unreconciled retirement statement.';
            }
            if (this.extractedData?.statement_kind === 'credit_card_deferred_payments' && !this.creditCardIsReconciled && !this.creditCardImportTransactionsOnly) {
                return 'This credit-card statement does not reconcile. Review it, or confirm "import transactions only".';
            }
            if (!this.multiProductReady) {
                return 'Every detected product needs a name, type, matching balances, and a destination.';
            }
            if (this.isExistingRetirementAccount && this.retirementIsReconciled && !this.retirementSnapshotConfirmed) {
                return 'Confirm this retirement statement is newer than the latest snapshot.';
            }
            if (this.isExistingCreditCardAccount && !this.creditCardSnapshotConfirmed && !this.creditCardImportTransactionsOnly) {
                return 'Confirm this statement replaces the latest credit-card snapshot.';
            }
            return '';
        },
        canSaveImport(): boolean {
            return this.saveBlockedReason === '';
        },
        visibleHeaders() {
            return this.extractedData?.statement_kind === 'multi_product'
                ? (this as any).headers
                : (this as any).headers.filter((header: { key: string }) => header.key !== 'products');
        },
        multiProductEndpointOptions() {
            const productOptions = this.multiProducts.map(product => ({
                title: `${product.name || 'Unnamed account'} (this statement)`,
                value: `product:${product.source_product_id}`,
            }));
            const externalAccountOptions = (this as any).accounts.map((account: any) => ({
                title: `${account.account_name} (${account.account_type})`,
                value: `account:${account.id}`,
            }));
            return [...productOptions, ...externalAccountOptions];
        },
        unresolvedTransferCount(): number {
            // An unchecked row is being intentionally skipped. It will be
            // persisted as skipped immediately before the batch commit, so it
            // must not keep the Save action disabled.
            return this.selectedTransactions.filter((transaction: DetectedTransaction) =>
                rowNeedsReviewRule(transaction)
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
        suggestedAccount() {
            const detected = (this as any).detectedAccountInfo.account_name?.toLowerCase();
            return detected ? (this as any).accounts.find((account: any) => account.account_name.toLowerCase() === detected || account.account_name.toLowerCase().includes(detected)) : null;
        },
        transferAccountOptions() {
            const options = (this as any).accounts.map((account: any) => ({
                title: `${account.account_name} (${account.account_type})`,
                value: account.id.toString()
            }));
            // The assignment PATCH is asynchronous. Use the local new-account
            // form while it is saving, then replace it with the saved draft
            // once the response arrives. This keeps the future account
            // selectable in a transfer without requiring a page reload.
            const savedDraft = (this as any).reviewDraftAssignment;
            const draft = savedDraft?.kind === 'new'
                ? savedDraft
                : (this as any).selectedAccountId === 'new'
                    ? { kind: 'new', ...(this as any).newAccount }
                    : null;
            if (draft?.kind === 'new') {
                options.push({
                    title: `New account for this statement · ${draft.name || 'Unnamed account'} (${draft.account_type || 'Account'})`,
                    value: BATCH_DRAFT_ACCOUNT,
                });
            }
            return options;
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
                    from_account_id: candidate.from_uses_batch_draft
                        ? BATCH_DRAFT_ACCOUNT
                        : candidate.from_account_id || null,
                    to_account_id: candidate.to_uses_batch_draft
                        ? BATCH_DRAFT_ACCOUNT
                        : (candidate.to_account_id && candidate.to_account_id !== candidate.from_account_id
                            ? candidate.to_account_id
                            : null),
                    from_uses_batch_draft: Boolean(candidate.from_uses_batch_draft),
                    to_uses_batch_draft: Boolean(candidate.to_uses_batch_draft),
                    status: candidate.status
                }));
                accountName = importBatch.detected_account_name || '';
                accountType = importBatch.detected_account_type || '';
                (this as any).reviewDraftAssignment = importBatch.draft_assignment || null;
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
                    const productName = String(product.name || '').trim().toLowerCase();
                    const productBank = String(product.bank_name || '').trim().toLowerCase();
                    const match = (this as any).accounts.find((account: any) => {
                        const accountName = String(account.account_name || '').trim().toLowerCase();
                        const accountBank = String(account.bank || '').trim().toLowerCase();
                        return account.account_name === product.name
                            || accountName.includes(productName)
                            || (
                                !!productBank
                                && accountBank === productBank
                                && productName.includes(accountName)
                            );
                    });
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

            const draft = importBatch?.draft_assignment;
            const matchingAccount = draft?.kind === 'existing'
                ? (this as any).accounts.find((account: any) => String(account.id) === String(draft.account_id))
                : null;
            (this as any).selectedAccountId = matchingAccount ? String(matchingAccount.id) : (draft?.kind === 'new' ? 'new' : null);
            (this as any).selectedAccount = matchingAccount || null;

            // Initialize new account form with detected info
            (this as any).newAccount = {
                name: draft?.kind === 'new' ? (draft.name || '') : accountName,
                bank: draft?.kind === 'new' ? (draft.bank || '') : accountName.split('(')[0]?.trim() || '',
                account_type: draft?.kind === 'new' ? (draft.account_type || '') : accountType || 'Credit Card'
            };
            (this as any).creditCardImportTransactionsOnly = false;
            // Prefer a persisted reviewed opening available credit (the value a
            // reviewer corrected and saved), then the existing account's current
            // available credit, then the extraction. This keeps a corrected
            // opening balance stable across reloads instead of snapping back to
            // a stale scan value.
            (this as any).creditCardOpeningBalance = importBatch?.reconciliation?.reviewed_opening_balance
                ?? matchingAccount?.total
                ?? importBatch?.reconciliation?.opening_balance
                ?? importBatch?.card_summary?.available_credit
                ?? null;
            (this as any).creditCardClosingBalance = importBatch?.card_summary?.available_credit ?? null;

            (this as any).selectedRowKey = null;
        },

        async loadBatch(batchId: number) {
            (this as any).loading = true;
            (this as any).loadError = '';
            try {
                const response = await axios.get(`/bank-statements/import-batches/${batchId}/`);
                if ((response.data.candidates || []).length === 0 && response.data.status === 'review') {
                    await (this as any).$router.replace(`/statements/${batchId}/scan-result`);
                    return;
                }
                (this as any).applyBatch({ review_batch_id: response.data.id, import_batch: response.data });
            } catch (error: any) {
                (this as any).loadError = error.response?.data?.message || 'Unable to load that import review batch.';
            } finally {
                (this as any).loading = false;
            }
        },

        leave() {
            (this as any).$router.push('/statements');
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
                const endpointNameFor = (productId?: string | null, accountId?: string | null) =>
                    productNameFor(productId) || accountNameFor(accountId) || '';
                if (transaction.transaction_type === 'Transfer') {
                    return `${endpointNameFor(transaction.source_product_id, transaction.from_account_id) || '?'} → ${endpointNameFor(transaction.destination_product_id, transaction.to_account_id) || '?'}`;
                }
                return endpointNameFor(transaction.source_product_id, transaction.from_account_id) || '—';
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
                if (this.extractedData?.statement_kind === 'multi_product') {
                    await Promise.all(((this as any).multiProducts as ImportProduct[]).map((product: ImportProduct) =>
                        axios.patch(`/bank-statements/import-products/${product.id}/`, {
                            name: product.name,
                            bank_name: product.bank_name || '',
                            product_type: product.product_type,
                            opening_balance: Number(product.opening_balance),
                            closing_balance: Number(product.closing_balance),
                        })
                    ));
                }
                const selectedKeys = new Set(
                    (this as any).selectedTransactions.map((row: DetectedTransaction) => row.candidate_id || row.id)
                );
                const patches = (this as any).editableTransactions
                    .filter((row: DetectedTransaction) => row.candidate_id && row.status !== 'imported')
                    .map((row: DetectedTransaction) => axios.patch(
                        `/bank-statements/import-candidates/${row.candidate_id}/`,
                        (this as any).candidatePatchPayload(
                            row,
                            '',
                            row.linked_transaction_id ? 'linked' : selectedKeys.has(row.candidate_id || row.id) ? 'pending' : 'skipped'
                        )
                    ));
                const removed = (this as any).removedCandidateIds.map((candidateId: number) =>
                    axios.patch(`/bank-statements/import-candidates/${candidateId}/`, { status: 'skipped' })
                );
                await Promise.all([...patches, ...removed]);
                // Persist a corrected opening available credit for credit-card
                // batches so a "Save draft" also stores the reviewed balance.
                if (this.extractedData?.statement_kind === 'credit_card_deferred_payments' && (this as any).selectedAccountId) {
                    await (this as any).persistAssignment();
                }
                await (this as any).reloadReviewBatch();
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
            // Django DateField values are calendar dates, not UTC instants.
            return formatCalendarDate(dateString);
        },

        handleAccountSelection(selectedValue: string | null) {
            // Handle null/undefined (user cleared selection)
            if (!selectedValue) {
                (this as any).selectedAccountId = null;
                (this as any).selectedAccount = null;
                void (this as any).persistAssignment();
                return;
            }

            // Handle "new" account option
            if (selectedValue === 'new') {
                (this as any).selectedAccountId = 'new';
                (this as any).selectedAccount = null;
                // Do not leave a previously selected account displayed as the
                // saved destination while the user starts a new-account draft.
                void (this as any).persistAssignment(true);
                return;
            }

            // Find the account object from the accounts array
            const account = (this as any).accounts.find((acc: any) => acc.id.toString() === selectedValue);
            if (account) {
                (this as any).selectedAccount = account;
                (this as any).selectedAccountId = selectedValue;
                void (this as any).persistAssignment();
            } else {
                // Account not found - reset selection
                (this as any).selectedAccountId = null;
                (this as any).selectedAccount = null;
                void (this as any).persistAssignment();
            }
        },

        useDetectedAccount() {
            const account = (this as any).suggestedAccount;
            if (!account) return;
            (this as any).selectedAccountId = String(account.id);
            (this as any).selectedAccount = account;
            void (this as any).persistAssignment();
        },

        queueNewAccountDraft() {
            if ((this as any).assignmentSaveTimer) clearTimeout((this as any).assignmentSaveTimer);
            (this as any).assignmentSaveTimer = setTimeout(() => {
                void (this as any).persistAssignment();
            }, 400);
        },

        async persistAssignment(clearOnly = false) {
            const batchId = (this as any).reviewBatchId;
            if (!batchId) return;
            const selected = (this as any).selectedAccountId;
            let payload: any = {};
            if (clearOnly || !selected) {
                payload = { account_id: '', new_account: null };
            } else if (selected === 'new') {
                const draft = (this as any).newAccount;
                if (!draft.name?.trim() || !draft.account_type) {
                    (this as any).assignmentSaveState = 'Complete the new account details to save this draft.';
                    return;
                }
                payload = { new_account: { name: draft.name, bank: draft.bank, account_type: draft.account_type } };
            } else {
                payload = { account_id: selected };
            }
            // Persist a corrected opening available credit alongside the
            // destination so it survives reload and is the canonical value the
            // commit validates. The source scan value is preserved server-side.
            if (!clearOnly && selected
                && this.extractedData?.statement_kind === 'credit_card_deferred_payments'
                && this.creditCardOpeningBalance !== null
                && this.creditCardOpeningBalance !== undefined) {
                payload.opening_available_credit = Number(this.creditCardOpeningBalance);
            }
            (this as any).assignmentSaveState = 'Saving destination…';
            try {
                const response = await axios.patch(`/bank-statements/import-batches/${batchId}/assignment/`, payload);
                (this as any).reviewDraftAssignment = response.data?.import_batch?.draft_assignment || null;
                (this as any).assignmentSaveState = selected ? 'Destination saved' : 'Destination cleared';
            } catch (error: any) {
                (this as any).assignmentSaveState = 'Could not save destination';
                (this as any).reportError(error.response?.data?.message || 'Could not save the destination account.');
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

        financingTypeLabel(type?: string) {
            // Interest-free MSI, interest-bearing financing, and unknown terms
            // are distinct. Never present interest-bearing financing as MSI.
            if (type === 'interest_free') return 'MSI (no interest)';
            if (type === 'interest_bearing') return 'Financing (with interest)';
            return 'Financing (terms unknown)';
        },

        financingTypeColor(type?: string) {
            if (type === 'interest_free') return 'success';
            if (type === 'interest_bearing') return 'warning';
            return 'grey';
        },

        formatSignedMoney(value: number) {
            const amount = Number(value || 0);
            return `${amount < 0 ? '-' : '+'}$${(Math.abs(amount)).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        },

        isNewProductAccount(product: ImportProduct) {
            return String((this as any).productSelections[product.id] || '').startsWith('new:');
        },

        productTransactionSum(product: ImportProduct) {
            let movement = 0;
            for (const transaction of (this as any).selectedTransactions as DetectedTransaction[]) {
                const amount = Number(transaction.amount) || 0;
                if (transaction.transaction_type === 'Transfer') {
                    if (transaction.source_product_id === product.source_product_id) movement -= amount;
                    if (transaction.destination_product_id === product.source_product_id) movement += amount;
                } else if (transaction.source_product_id === product.source_product_id) {
                    movement += transaction.transaction_type === 'Income' || transaction.transaction_type === 'External Deposit'
                        ? amount
                        : -amount;
                }
            }
            return Math.round((movement + Number.EPSILON) * 100) / 100;
        },

        calculatedProductBalance(product: ImportProduct) {
            const balance = Number(product.opening_balance || 0)
                + (this as any).productTransactionSum(product)
                + Number(product.reconciliation?.valuation_change || 0);
            return Math.round((balance + Number.EPSILON) * 100) / 100;
        },

        productBalanceMatches(product: ImportProduct) {
            const expected = Number(product.closing_balance);
            // The API reconciles Decimal values at cent precision. Compare
            // rounded cents here too, rather than accepting a one-cent gap
            // caused by JavaScript floating-point representation.
            return Number.isFinite(expected)
                && Math.round(expected * 100) === Math.round((this as any).calculatedProductBalance(product) * 100);
        },

        productBalanceDifferenceLabel(product: ImportProduct) {
            const difference = (this as any).calculatedProductBalance(product) - Number(product.closing_balance);
            return `Calculated ending is ${difference > 0 ? 'higher' : 'lower'} by ${(this as any).formatSignedMoney(Math.abs(difference)).replace('+', '')}.`;
        },

        productReconciliationError(product: ImportProduct) {
            const expected = Number(product.closing_balance);
            const calculated = Number(product.reconciliation?.calculated_closing_balance ?? product.calculated_closing_balance);
            const difference = calculated - expected;
            const direction = difference > 0 ? 'higher' : 'lower';
            return `${product.name || 'Unnamed account'}: calculated ending $${(this as any).formatMoney(calculated)}, expected $${(this as any).formatMoney(expected)} (${direction} by $${(this as any).formatMoney(Math.abs(difference))}).`;
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
                title: 'Manual transaction', amount: 0, date: todayLocalISO(),
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
                payload.from_account_id = transaction.from_account_id || '';
                payload.to_account_id = transaction.transaction_type === 'Transfer'
                    ? transaction.to_account_id || ''
                    : '';
                if (transaction.linked_transaction_id) payload.linked_transaction_id = transaction.linked_transaction_id;
                return payload;
            }
            if (transaction.linked_transaction_id) {
                payload.linked_transaction_id = transaction.linked_transaction_id;
            } else if (transaction.transaction_type === 'Transfer') {
                const fromUsesBatchDraft = (transaction as any).from_account_id === BATCH_DRAFT_ACCOUNT;
                const toUsesBatchDraft = (transaction as any).to_account_id === BATCH_DRAFT_ACCOUNT;
                payload.from_account_id = fromUsesBatchDraft ? '' : (transaction as any).from_account_id || '';
                payload.to_account_id = toUsesBatchDraft ? '' : (transaction as any).to_account_id || '';
                payload.from_uses_batch_draft = fromUsesBatchDraft;
                payload.to_uses_batch_draft = toUsesBatchDraft;
            } else {
                payload.account_id = accountId;
            }
            return payload;
        },

        multiProductEndpointValue(transaction: DetectedTransaction, endpoint: 'from' | 'to') {
            const productId = endpoint === 'from' ? transaction.source_product_id : transaction.destination_product_id;
            const accountId = endpoint === 'from' ? transaction.from_account_id : transaction.to_account_id;
            return productId ? `product:${productId}` : accountId ? `account:${accountId}` : null;
        },

        setMultiProductEndpoint(transaction: DetectedTransaction, endpoint: 'from' | 'to', value: string | null) {
            const productField = endpoint === 'from' ? 'source_product_id' : 'destination_product_id';
            const accountField = endpoint === 'from' ? 'from_account_id' : 'to_account_id';
            const [kind, rawId] = String(value || '').split(':', 2);
            if (kind === 'product' && rawId) {
                (transaction as any)[productField] = rawId;
                (transaction as any)[accountField] = null;
            } else if (kind === 'account' && rawId) {
                (transaction as any)[productField] = null;
                (transaction as any)[accountField] = rawId;
            } else {
                (transaction as any)[productField] = null;
                (transaction as any)[accountField] = null;
            }
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
            const unreconciledProducts = refreshedProducts.filter(product => !product.reconciliation?.is_reconciled);
            if (unreconciledProducts.length) {
                (this as any).multiProducts = refreshedProducts;
                throw new Error(`Review these account balances before saving: ${unreconciledProducts.map((product) => (this as any).productReconciliationError(product)).join(' ')}`);
            }

            const productAccountMap: Record<string, string> = {};
            const newProductIds: number[] = [];
            for (const product of refreshedProducts) {
                const selected = (this as any).productSelections[product.id];
                if (!selected) throw new Error(`Select where to save ${product.name}.`);
                if (selected.startsWith('new:')) {
                    newProductIds.push(product.id);
                } else {
                    productAccountMap[product.id] = selected;
                }
            }

            const commitResponse = await axios.post(
                `/bank-statements/import-batches/${(this as any).reviewBatchId}/commit/`,
                { product_account_map: productAccountMap, new_product_ids: newProductIds }
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
                let newAccountInitialBalance: number | undefined;
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

                // Existing accounts are ready now. New-account drafts stay
                // drafts until the atomic batch commit, so transfers can refer
                // to that future account without a temporary fake id.
                if ((this as any).selectedAccountId === 'new') {
                    if (!(this as any).newAccount.name || !(this as any).newAccount.account_type) {
                        (this as any).reportError('Please fill in all required account fields.');
                        return;
                    }
                    newAccountInitialBalance = this.extractedData?.statement_kind === 'retirement'
                        ? (this.retirementOpeningBalance ?? 0.0)
                        : this.extractedData?.statement_kind === 'credit_card_deferred_payments'
                            ? (this.creditCardOpeningBalance ?? 0.0)
                        : (this.extractedData?.initial_balance ?? 0.0);
                    await (this as any).persistAssignment();
                } else if ((this as any).selectedAccountId) {
                    account = (this as any).selectedAccount;
                } else {
                    (this as any).reportError('Please select an account or create a new one.');
                    return;
                }

                if ((this as any).selectedAccountId !== 'new' && (!account || !account.id)) {
                    (this as any).reportError('Account not found. Please select a destination account again.');
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
                                (this as any).candidatePatchPayload(transaction, account?.id || '', nextStatus)
                            );
                        });

                    const removedPromises = (this as any).removedCandidateIds.map((candidateId: number) =>
                        axios.patch(`/bank-statements/import-candidates/${candidateId}/`, { status: 'skipped' })
                    );
                    await Promise.all([...patchPromises, ...removedPromises]);

                    // For an existing credit-card account, send the reviewed
                    // opening available credit so the backend validates against
                    // the corrected value (which may differ from a stale scan),
                    // rather than only the extraction's opening balance.
                    const reviewedOpening = this.extractedData?.statement_kind === 'credit_card_deferred_payments'
                        && (this as any).selectedAccountId !== 'new'
                        && this.creditCardOpeningBalance !== null
                        && this.creditCardOpeningBalance !== undefined
                        ? Number(this.creditCardOpeningBalance)
                        : undefined;
                    const commitResponse = await axios.post(
                        `/bank-statements/import-batches/${(this as any).reviewBatchId}/commit/`,
                        { account_id: account?.id?.toString() || '', new_account_initial_balance: newAccountInitialBalance,
                          opening_available_credit: reviewedOpening,
                          confirm_retirement_snapshot: (this as any).retirementSnapshotConfirmed,
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
                const apiError = error.response?.data?.message || error.response?.data?.error || error.response?.data?.details;
                const errorMessage = Array.isArray(apiError)
                    ? apiError.join(' ')
                    : apiError || error.message || 'Failed to import transactions. Please try again.';
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
    flex-wrap: wrap;
    gap: 1rem;
    justify-content: space-between;
    padding: 0.85rem 1.25rem;
    position: sticky;
    top: 72px;
    z-index: 40;
}

/* Second row of the sticky bar: the save-blocked reason and, right beside it,
   the confirmation that clears it. Full width so it never competes for space
   with the title/buttons row. */
.review-progress-note {
    align-items: center;
    display: flex;
    flex-basis: 100%;
    flex-wrap: wrap;
    gap: 0.25rem 1.25rem;
    width: 100%;
}

.review-progress-confirm {
    flex: 0 0 auto;
}

.review-count-warning,
.review-blocked-reason {
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

.credit-card-workspace {
    overflow: hidden;
}

.msi-plan-list {
    display: grid;
    gap: 0.75rem;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

.msi-plan {
    min-width: 0;
}

.msi-plan-merchant {
    min-width: 0;
    overflow-wrap: anywhere;
}

/* The inspector's confirmation copy spans the full column width and otherwise
   sits flush against the panel edge, which reads as clipped. Reserve end
   padding so the text always keeps clear of the border, and let long tokens
   wrap instead of overflowing. */
.review-right :deep(.v-checkbox .v-label) {
    overflow-wrap: anywhere;
    padding-inline-end: 0.75rem;
}

.review-right small {
    padding-inline-end: 0.75rem;
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

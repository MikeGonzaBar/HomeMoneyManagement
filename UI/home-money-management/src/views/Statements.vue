<template>
  <div class="bg-gray-50 text-gray-900 font-sans antialiased">
    <AppHeader :userData="userData" />

    <main class="w-full px-4 sm:px-6 py-6">
      <div class="flex flex-wrap items-start justify-between gap-4 mb-6">
        <div>
          <h1 class="text-gray-900 text-3xl font-bold tracking-tight">Statements</h1>
          <p class="text-gray-500">
            {{ userFiles.length }} uploaded statement{{ userFiles.length === 1 ? '' : 's' }}<span
              v-if="needsReviewCount"> · {{ needsReviewCount }} waiting for review</span>
          </p>
        </div>
        <div class="flex items-center gap-3">
          <v-btn color="primary" variant="outlined" rounded="lg" :loading="loadingFiles" @click="refreshFiles">
            <v-icon start>mdi-refresh</v-icon>Refresh
          </v-btn>
          <v-btn color="primary" variant="flat" rounded="lg" @click="goToUpload">
            <v-icon start>mdi-upload</v-icon>Upload
          </v-btn>
        </div>
      </div>

      <!-- Filters -->
      <section class="grid gap-3 mb-6 sm:grid-cols-2 lg:grid-cols-4">
        <v-text-field v-model="search" prepend-inner-icon="mdi-magnify" label="Search file or bank"
          variant="outlined" density="compact" hide-details clearable />
        <v-select v-model="bankFilter" :items="bankOptions" label="Bank / account" variant="outlined"
          density="compact" hide-details clearable />
        <v-select v-model="statusFilter" :items="STATUS_OPTIONS" item-title="title" item-value="value"
          label="Status" variant="outlined" density="compact" hide-details />
        <v-select v-model="dateFilter" :items="DATE_OPTIONS" item-title="title" item-value="value"
          label="Uploaded" variant="outlined" density="compact" hide-details />
      </section>

      <!-- Loading -->
      <section v-if="loadingFiles && userFiles.length === 0" class="statements-empty">
        <v-progress-circular indeterminate color="primary" size="56" />
        <p class="text-gray-500 mt-4">Loading your statements…</p>
      </section>

      <!-- Nothing uploaded yet -->
      <section v-else-if="userFiles.length === 0" class="statements-empty">
        <v-icon size="56" color="grey-lighten-1" class="mb-3">mdi-file-pdf-box-outline</v-icon>
        <h2 class="text-lg font-semibold text-gray-900">No statements uploaded</h2>
        <p class="text-gray-500 text-sm mt-1">Upload a bank statement PDF to start reviewing transactions.</p>
        <v-btn color="primary" variant="flat" rounded="lg" class="mt-5" @click="goToUpload">
          Upload Bank Statement
        </v-btn>
      </section>

      <!-- Filters matched nothing -->
      <section v-else-if="filteredFiles.length === 0" class="statements-empty">
        <v-icon size="56" color="grey-lighten-1" class="mb-3">mdi-filter-remove-outline</v-icon>
        <h2 class="text-lg font-semibold text-gray-900">No statements match these filters</h2>
        <v-btn color="primary" variant="text" rounded="lg" class="mt-3" @click="clearFilters">Clear filters</v-btn>
      </section>

      <!-- Statement list -->
      <section v-else class="space-y-3">
        <article v-for="file in filteredFiles" :key="file.id" class="statements-row">
          <div class="statements-row__identity">
            <v-avatar color="red-lighten-4" size="44">
              <v-icon color="red">mdi-file-pdf-box</v-icon>
            </v-avatar>
            <div class="min-w-0">
              <p class="font-semibold text-gray-900 truncate">{{ file.original_filename }}</p>
              <p class="text-xs text-gray-500 mt-0.5">
                {{ file.file_size_display }} · Uploaded {{ formatTimestamp(file.upload_date) }}
              </p>
              <p class="text-xs text-gray-500 mt-0.5">
                <v-icon size="13" class="mr-1">mdi-robot-outline</v-icon>AI detected: {{ detectedAccountLabel(file) }}
              </p>
            </div>
          </div>

          <div class="statements-row__meta">
            <p class="text-sm font-medium text-gray-700">{{ periodLabel(file) }}</p>
            <v-chip :color="statusColor(file)" size="small" variant="tonal" class="mt-1">
              {{ statusLabel(file) }}
            </v-chip>
            <p v-if="retryLabel(file)" class="text-xs text-orange-darken-2 mt-1">
              {{ retryLabel(file) }}
            </p>
            <p v-if="failureReasonLabel(file)" class="text-xs text-red-darken-2 mt-1" data-testid="failure-reason">
              {{ failureReasonLabel(file) }}
            </p>
          </div>

          <div class="statements-row__progress">
            <template v-if="file.review_candidate_count">
              <p class="text-sm font-semibold text-gray-900">
                {{ resolvedCount(file) }}/{{ file.review_candidate_count }} resolved
              </p>
              <v-progress-linear :model-value="progressPercent(file)"
                :color="pendingCount(file) ? 'warning' : 'success'" height="6" rounded class="mt-1" />
              <p v-if="pendingCount(file)" class="text-xs text-warning-darken-1 mt-1">
                {{ pendingCount(file) }} need attention
              </p>
            </template>
            <template v-else-if="file.processing_status === 'completed'">
              <p class="text-sm font-semibold text-gray-900">No importable transactions found</p>
              <p class="text-xs text-gray-500 mt-1">{{ file.review_scan_summary?.zero_result_reason || 'No importable transactions are available from this scan.' }}</p>
            </template>
            <p v-else class="text-sm text-gray-400">Awaiting scan result</p>
          </div>

          <div class="statements-row__assignment">
            <p class="text-xs font-semibold uppercase tracking-wide text-gray-500">Destination account</p>
            <p class="text-sm font-medium text-gray-800 mt-1">{{ draftAssignmentLabel(file) }}</p>
          </div>

          <div class="statements-row__actions">
            <v-btn v-if="isProcessing(file)" color="primary" variant="tonal" size="small" rounded="lg" disabled>
              Scanning statement…</v-btn>
            <v-btn v-else-if="canViewScanResult(file)" color="primary" variant="flat" size="small" rounded="lg"
              @click="viewScanResult(file)">View scan result</v-btn>
            <v-btn v-else-if="canResume(file)" color="primary" variant="flat" size="small" rounded="lg"
              @click="resumeReview(file)">{{ file.review_draft_assignment ? 'Continue review' : 'Assign account & review' }}</v-btn>
            <v-btn v-if="canViewImported(file)" color="success" variant="tonal" size="small" rounded="lg"
              @click="viewImported(file)">View imported</v-btn>
            <v-btn v-if="canViewDetails(file)" color="primary" variant="tonal" size="small" rounded="lg"
              @click="viewDetails(file)">Details</v-btn>
            <v-btn v-if="file.processing_status === 'failed'" color="warning" variant="tonal" size="small"
              rounded="lg" :loading="retryingFileId === file.id" @click="retryFile(file)">Retry</v-btn>
            <v-btn icon="mdi-delete" color="red" variant="text" size="small" @click="confirmDeleteFile(file)" />
          </div>
        </article>
      </section>

    </main>

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
          <v-btn color="grey" variant="text" @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="red" variant="flat" :loading="deletingFile" @click="deleteFile">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Statement Details Dialog: imported statement summary, card
         summary and the deferred-purchase schedule, with in-place
         corrections for committed card statements. -->
    <v-dialog v-model="detailsDialog" max-width="760">
      <v-card rounded="xl" v-if="detailsBatch">
        <v-card-title class="pa-6 pb-2">
          <div class="d-flex align-center">
            <v-avatar size="32" class="me-3" color="red">
              <v-icon color="white">mdi-file-pdf-box</v-icon>
            </v-avatar>
            <div class="min-w-0">
              <h6 class="font-weight-bold text-truncate">{{ detailsBatch.bank_statement_filename }}</h6>
              <p class="text-caption text-grey-darken-1">
                {{ detailsBatch.detected_account_name || 'Account not detected' }}
                <span v-if="detailsBatch.statement_period?.start || detailsBatch.statement_period?.end">
                  · {{ statementPeriodLabel() }}</span>
              </p>
            </div>
          </div>
        </v-card-title>
        <v-card-text class="pa-6 pt-2">
          <v-progress-circular v-if="detailsLoading" indeterminate color="primary"
            class="d-block mx-auto my-6"></v-progress-circular>
          <template v-else>
            <v-row v-if="detailsBatch.statement_kind === 'credit_card_deferred_payments' && detailsBatch.card_summary"
              dense class="mb-4">
              <v-col cols="6" md="4">
                <p class="text-caption text-grey-darken-1">Total debt</p>
                <p class="text-h6 font-weight-semibold">{{ money(detailsBatch.card_summary.total_debt) }}</p>
              </v-col>
              <v-col cols="6" md="4">
                <p class="text-caption text-grey-darken-1">Regular purchases</p>
                <p class="text-h6 font-weight-semibold">{{ money(detailsBatch.card_summary.regular_debt) }}</p>
              </v-col>
              <v-col cols="6" md="4">
                <p class="text-caption text-grey-darken-1">Deferred purchases</p>
                <p class="text-h6 font-weight-semibold">{{ money(detailsBatch.card_summary.deferred_balance) }}</p>
              </v-col>
              <v-col cols="6" md="4">
                <p class="text-caption text-grey-darken-1">Available credit</p>
                <p class="text-h6 font-weight-semibold">{{ money(detailsBatch.card_summary.available_credit) }}</p>
              </v-col>
              <v-col cols="6" md="4">
                <p class="text-caption text-grey-darken-1">Credit limit</p>
                <p class="text-h6 font-weight-semibold">{{ money(detailsBatch.card_summary.credit_limit) }}</p>
              </v-col>
              <v-col cols="6" md="4">
                <p class="text-caption text-grey-darken-1">Statement date</p>
                <p class="text-h6 font-weight-semibold">{{ detailsBatch.card_summary.statement_date || '—' }}</p>
              </v-col>
            </v-row>

            <p class="text-sm font-semibold text-gray-900">
              Deferred purchases ({{ dialogPlans.length }})
            </p>
            <p class="text-caption text-grey-darken-1 mb-3">
              Plan metadata describes debt the account totals already include; it never moves money on its own.
            </p>
            <div v-for="plan in dialogPlans" :key="plan.source_key" class="statement-plan">
              <div class="statement-plan__head">
                <p class="font-weight-semibold text-gray-900">{{ plan.merchant || 'Unknown merchant' }}</p>
                <p class="text-sm font-semibold" :class="remainingClass(plan)">{{ money(plan.remaining_balance) }}</p>
              </div>
              <template v-if="!msiEditing">
                <p class="text-sm text-gray-600 mt-1">
                  Original purchase {{ money(plan.original_amount) }}<span
                    v-if="plan.original_purchase_date"> on {{ plan.original_purchase_date }}</span>
                  · Current installment {{ planCurrentInstallment(plan) }}
                </p>
                <p class="text-sm text-gray-600">
                  Installment {{ plan.installment_number ?? '?' }} of {{ plan.installment_count ?? '?' }}
                  · {{ financingLabel(plan) }}
                  <span v-if="plan.issuer_reference">· Ref {{ plan.issuer_reference }}</span>
                </p>
                <p class="text-caption text-grey-darken-1">
                  Source: {{ planSourceLabel(plan) }}<span
                    v-if="plan.source_evidence?.section"> — “{{ plan.source_evidence.section }}”</span>
                </p>
              </template>
              <template v-else>
                <v-row dense class="mt-2">
                  <v-col cols="6" md="3">
                    <v-text-field v-model.number="plan.remaining_balance" type="number" min="0" step="0.01"
                      label="Remaining balance" variant="outlined" density="compact" hide-details></v-text-field>
                  </v-col>
                  <v-col cols="6" md="3">
                    <v-text-field v-model="plan.current_installment" type="number" min="0" step="0.01"
                      label="Current installment" variant="outlined" density="compact" hide-details></v-text-field>
                  </v-col>
                  <v-col cols="6" md="3">
                    <v-text-field v-model.number="plan.installment_number" type="number" min="1" step="1"
                      label="Installment no." variant="outlined" density="compact" hide-details></v-text-field>
                  </v-col>
                  <v-col cols="6" md="3">
                    <v-text-field v-model.number="plan.installment_count" type="number" min="1" step="1"
                      label="Installments" variant="outlined" density="compact" hide-details></v-text-field>
                  </v-col>
                </v-row>
              </template>
            </div>
            <v-alert v-if="!dialogPlans.length" density="compact" variant="tonal" type="info" class="mt-3">
              No deferred purchases were detected on this statement.
            </v-alert>
          </template>
        </v-card-text>
        <v-card-actions class="pa-6 pt-2">
          <v-spacer></v-spacer>
          <template v-if="msiEditing">
            <v-btn color="grey" variant="text" @click="cancelMsiEdit">Cancel</v-btn>
            <v-btn color="primary" variant="flat" :loading="msiSaving" @click="saveMsiEdit">Save corrections</v-btn>
          </template>
          <template v-else>
            <v-btn v-if="canCorrectMsi" color="primary" variant="tonal" rounded="lg" @click="startMsiEdit">
              Correct MSI details</v-btn>
            <v-btn color="grey" variant="text" @click="detailsDialog = false">Close</v-btn>
          </template>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import AppHeader from '@/components/AppHeader.vue'
import axios, { getAllPages } from '@/services/api';
import { getStoredSession } from '@/services/session';

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
  retry_count: number;
  next_retry_at: string | null;
  failure_class: string;
  review_batch_id?: number | null;
  review_batch_status?: string | null;
  review_candidate_count?: number;
  review_resolved_count?: number;
  review_period_start?: string | null;
  review_period_end?: string | null;
  review_account_name?: string | null;
  review_account_type?: string | null;
  review_draft_assignment?: { kind: 'existing' | 'new'; account_id?: number; account_name?: string; account_type?: string; name?: string; bank?: string } | null;
  review_scan_summary?: { raw_transaction_count?: number; importable_candidate_count?: number; zero_result_reason?: string } | null;
}

const STATUS_OPTIONS = [
  { title: 'All statuses', value: 'all' },
  { title: 'Needs review', value: 'needs-review' },
  { title: 'Imported', value: 'imported' },
  { title: 'Processing', value: 'processing' },
  { title: 'Failed', value: 'failed' },
  { title: 'Completed', value: 'completed' },
];

const DATE_OPTIONS = [
  { title: 'Any time', value: 'all' },
  { title: 'Last 7 days', value: '7' },
  { title: 'Last 30 days', value: '30' },
];

function statusKey(file: UserFile): string {
  if (file.processing_status === 'failed') return 'failed';
  if (file.processing_status === 'pending' || file.processing_status === 'processing') return 'processing';
  if (file.review_batch_status === 'review') return 'needs-review';
  if (file.review_batch_status === 'committed') return 'imported';
  return 'completed';
}

function statusLabel(file: UserFile): string {
  switch (statusKey(file)) {
    case 'needs-review': return 'Needs review';
    case 'imported': return 'Imported';
    case 'processing': return file.next_retry_at ? 'Retry scheduled' : (file.processing_status === 'pending' ? 'Queued' : 'Processing');
    case 'failed': return 'Failed';
    default: return 'Completed';
  }
}

// Format a stored timestamp instant in the viewer's own timezone, labelled, so
// every timestamp on this page reads the same way. The backend stores UTC
// instants (USE_TZ, TIME_ZONE=UTC); rendering them raw showed UTC while retry
// times were already rendered in local time, a ~6h mismatch for
// America/Mexico_City. Keep the instant intact; only the display is localized.
function formatTimestamp(value: string | null | undefined): string {
  if (!value) return '—';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  const zone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'local time';
  const formatted = parsed.toLocaleString(undefined, {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true,
  });
  return `${formatted} (${zone})`;
}

function retryLabel(file: UserFile): string | null {
  if (!file.next_retry_at) return null;
  const retryAt = new Date(file.next_retry_at);
  if (Number.isNaN(retryAt.getTime())) return 'Automatic retry scheduled';
  const zone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'local time';
  return `Retry ${file.retry_count || 1} scheduled for ${retryAt.toLocaleString()} (${zone})`;
}

// Map the backend's sanitized failure_class to a short, actionable reason.
// The raw provider/parser text is never shown; only a stable category and the
// attempt count, so a failed scan is self-explanatory and manually retryable.
const FAILURE_REASONS: Record<string, string> = {
  malformed_response: 'The scan response was unreadable. Retry to scan again.',
  rate_limited: 'The AI provider was rate limited. Retry shortly.',
  timeout: 'The scan timed out. Retry to scan again.',
  provider_unavailable: 'The AI provider was temporarily unavailable. Retry shortly.',
  permanent: 'The scan could not be completed. Retry or upload the statement again.',
};

function failureReasonLabel(file: UserFile): string | null {
  if (file.processing_status !== 'failed') return null;
  const reason = FAILURE_REASONS[file.failure_class] || 'The scan failed. Retry to try again.';
  const attempts = file.retry_count ? ` (after ${file.retry_count} attempt${file.retry_count === 1 ? '' : 's'})` : '';
  return `${reason}${attempts}`;
}

function statusColor(file: UserFile): string {
  switch (statusKey(file)) {
    case 'failed': return 'red';
    case 'processing': return 'orange';
    case 'needs-review': return 'primary';
    default: return 'green';
  }
}

function periodLabel(file: UserFile): string {
  const start = file.review_period_start;
  const end = file.review_period_end;
  if (!start && !end) return 'Period not detected';
  if (start && end) return start === end ? start : `${start} → ${end}`;
  return (start || end) as string;
}

function resolvedCount(file: UserFile): number {
  return file.review_resolved_count ?? 0;
}

function pendingCount(file: UserFile): number {
  return Math.max(0, (file.review_candidate_count ?? 0) - resolvedCount(file));
}

function progressPercent(file: UserFile): number {
  const total = file.review_candidate_count ?? 0;
  if (!total) return 0;
  return Math.round((resolvedCount(file) / total) * 100);
}

function detectedAccountLabel(file: UserFile): string {
  if (!file.review_account_name) return 'Account not detected';
  return file.review_account_type ? `${file.review_account_name} (${file.review_account_type})` : file.review_account_name;
}

function draftAssignmentLabel(file: UserFile): string {
  const draft = file.review_draft_assignment;
  if (!draft) return 'Not assigned';
  if (draft.kind === 'new') return `New account: ${draft.name || 'Unnamed account'}`;
  return draft.account_type ? `${draft.account_name} (${draft.account_type})` : (draft.account_name || 'Selected account');
}

export default defineComponent({
  name: 'Statements',
  components: { AppHeader },
  data() {
    const session = getStoredSession();
    return {
      userData: { user: session?.user ?? {} },
      userFiles: [] as UserFile[],
      loadingFiles: false,
      retryingFileId: null as number | null,
      filesPollTimer: null as ReturnType<typeof setInterval> | null,
      deleteDialog: false,
      fileToDelete: null as UserFile | null,
      deletingFile: false,
      detailsDialog: false,
      detailsBatch: null as null | Record<string, any>,
      detailsLoading: false,
      msiEditing: false,
      msiSaving: false,
      msiPlans: [] as Array<Record<string, any>>,
      search: '',
      bankFilter: null as string | null,
      statusFilter: 'all',
      dateFilter: 'all',
      STATUS_OPTIONS,
      DATE_OPTIONS,
    };
  },
  computed: {
    bankOptions(): string[] {
      const names = new Set<string>();
      for (const file of this.userFiles) {
        if (file.review_account_name) names.add(file.review_account_name);
      }
      return [...names].sort();
    },
    filteredFiles(): UserFile[] {
      const query = this.search.trim().toLowerCase();
      const bank = this.bankFilter;
      const status = this.statusFilter;
      const cutoff = this.dateFilter === 'all' ? null : Date.now() - Number(this.dateFilter) * 86400000;
      return this.userFiles.filter((file) => {
        const haystack = `${file.original_filename} ${file.review_account_name ?? ''}`.toLowerCase();
        if (query && !haystack.includes(query)) return false;
        if (bank && (file.review_account_name ?? '') !== bank) return false;
        if (status !== 'all' && statusKey(file) !== status) return false;
        if (cutoff !== null && new Date(file.upload_date).getTime() < cutoff) return false;
        return true;
      });
    },
    needsReviewCount(): number {
      return this.userFiles.filter((file) => statusKey(file) === 'needs-review').length;
    },
    dialogPlans(): Array<Record<string, any>> {
      // While correcting, the editable copies; otherwise the
      // statement's own detected schedule.
      return this.msiEditing
        ? this.msiPlans
        : ((this.detailsBatch?.deferred_purchases as Array<Record<string, any>>) || []);
    },
    canCorrectMsi(): boolean {
      return this.detailsBatch?.status === 'committed'
        && this.detailsBatch?.statement_kind === 'credit_card_deferred_payments';
    },
  },
  mounted() {
    this.loadUserFiles();
  },
  beforeUnmount() {
    this.stopFilesPolling();
  },
  methods: {
    statusKey,
    statusLabel,
    statusColor,
    retryLabel,
    failureReasonLabel,
    formatTimestamp,
    periodLabel,
    resolvedCount,
    pendingCount,
    progressPercent,
    detectedAccountLabel,
    draftAssignmentLabel,

    async loadUserFiles() {
      this.loadingFiles = true;
      try {
        const session = getStoredSession();
        if (session?.user.username) {
          const files = await getAllPages<UserFile>(
            `/bank-statements/user/${session.user.username}/`,
            (data) => data.statements as unknown as UserFile[],
          );
          this.userFiles = files;
          this.syncFilesPolling();
        }
      } catch (error) {
        console.error('Error loading statements:', error);
        this.userFiles = [];
      } finally {
        this.loadingFiles = false;
      }
    },

    async refreshFiles() {
      await this.loadUserFiles();
    },

    syncFilesPolling() {
      const hasActiveFiles = this.userFiles.some(
        (file) => file.processing_status === 'pending' || file.processing_status === 'processing',
      );
      if (hasActiveFiles && !this.filesPollTimer) {
        this.filesPollTimer = setInterval(() => {
          if (!this.loadingFiles) void this.loadUserFiles();
        }, 10000);
      }
      if (!hasActiveFiles) this.stopFilesPolling();
    },

    stopFilesPolling() {
      if (this.filesPollTimer) clearInterval(this.filesPollTimer);
      this.filesPollTimer = null;
    },

    goToUpload() {
      this.$router.push('/');
    },

    clearFilters() {
      this.search = '';
      this.bankFilter = null;
      this.statusFilter = 'all';
      this.dateFilter = 'all';
    },

    canResume(file: UserFile): boolean {
      return !!file.review_batch_id && file.review_batch_status === 'review' && (file.review_candidate_count ?? 0) > 0;
    },

    canViewScanResult(file: UserFile): boolean {
      return !!file.review_batch_id && file.processing_status === 'completed'
        && file.review_batch_status === 'review' && (file.review_candidate_count ?? 0) === 0;
    },

    isProcessing(file: UserFile): boolean {
      return file.processing_status === 'pending' || file.processing_status === 'processing';
    },

    canViewImported(file: UserFile): boolean {
      return file.review_batch_status === 'committed' && (file.review_candidate_count ?? 0) > 0;
    },

    resumeReview(file: UserFile) {
      if (!file.review_batch_id) return;
      this.$router.push(`/statements/${file.review_batch_id}/review`);
    },

    viewScanResult(file: UserFile) {
      if (!file.review_batch_id) return;
      this.$router.push(`/statements/${file.review_batch_id}/scan-result`);
    },

    viewImported(file: UserFile) {
      this.$router.push({ path: '/transactions', query: { statementBatch: String(file.review_batch_id || '') } });
    },

    canViewDetails(file: UserFile): boolean {
      return !!file.review_batch_id && file.review_batch_status === 'committed';
    },

    async viewDetails(file: UserFile) {
      if (!file.review_batch_id) return;
      this.detailsBatch = null;
      this.detailsLoading = true;
      this.msiEditing = false;
      this.msiPlans = [];
      this.detailsDialog = true;
      try {
        const { data } = await axios.get(
          `/bank-statements/import-batches/${file.review_batch_id}/`,
        );
        this.detailsBatch = data;
      } catch (error) {
        console.error('Error loading statement details:', error);
      } finally {
        this.detailsLoading = false;
      }
    },

    startMsiEdit() {
      this.msiPlans = this.dialogPlans.map((plan) => ({ ...plan }));
      this.msiEditing = true;
    },

    cancelMsiEdit() {
      this.msiEditing = false;
      this.msiPlans = [];
    },

    async saveMsiEdit() {
      if (!this.detailsBatch?.id) return;
      this.msiSaving = true;
      try {
        const { data } = await axios.patch(
          `/bank-statements/import-batches/${this.detailsBatch.id}/msi/`,
          { deferred_purchases: this.msiPlans },
        );
        this.detailsBatch = { ...this.detailsBatch, deferred_purchases: data.deferred_purchases };
        this.msiEditing = false;
        this.msiPlans = [];
        await this.loadUserFiles();
      } catch (error: any) {
        console.error('Error saving MSI corrections:', error);
        alert(error.response?.data?.message || 'Failed to save MSI corrections.');
      } finally {
        this.msiSaving = false;
      }
    },

    statementPeriodLabel(): string {
      const period = (this.detailsBatch?.statement_period || {}) as { start?: string; end?: string };
      const { start, end } = period;
      if (!start && !end) return 'Period not detected';
      if (start && end) return start === end ? start : `${start} → ${end}`;
      return (start || end) as string;
    },

    money(value: unknown): string {
      if (value == null || value === '') return '—';
      const number = Number(value);
      if (Number.isNaN(number)) return String(value);
      return `$${number.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    },

    // The reviewed installment when set, otherwise the value
    // printed on the statement.
    planCurrentInstallment(plan: Record<string, any>): string {
      return this.money(plan.current_installment ?? plan.current_installment_amount);
    },

    financingLabel(plan: Record<string, any>): string {
      switch (plan.financing_type) {
        case 'interest_free': return 'Interest-free financing';
        case 'interest_bearing': return 'Interest-bearing financing';
        default:
          return plan.financing_type
            ? String(plan.financing_type).replace(/_/g, ' ')
            : 'Financing type not detected';
      }
    },

    planSourceLabel(plan: Record<string, any>): string {
      const evidence = plan.source_evidence || {};
      const parts: string[] = [];
      if (evidence.page) parts.push(`page ${evidence.page}`);
      if (evidence.row_reference) parts.push(`row ${evidence.row_reference}`);
      return parts.length ? parts.join(', ') : 'not recorded';
    },

    remainingClass(plan: Record<string, any>): string {
      return Number(plan.remaining_balance || 0) > 0 ? 'text-gray-900' : 'text-green-darken-2';
    },

    async retryFile(file: UserFile) {
      this.retryingFileId = file.id;
      try {
        await axios.post(`/bank-statements/retry/${file.id}/`);
        await this.loadUserFiles();
      } catch (error: any) {
        alert(error.response?.data?.message || 'Failed to retry bank statement.');
      } finally {
        this.retryingFileId = null;
      }
    },

    confirmDeleteFile(file: UserFile) {
      this.fileToDelete = file;
      this.deleteDialog = true;
    },

    async deleteFile() {
      if (!this.fileToDelete) return;
      const fileId = this.fileToDelete.id;
      this.deletingFile = true;
      try {
        await axios.delete(`/bank-statements/delete/${fileId}/`);
        this.userFiles = this.userFiles.filter((file) => file.id !== fileId);
        this.deleteDialog = false;
        this.fileToDelete = null;
        alert('File deleted successfully!');
      } catch (error) {
        console.error('Error deleting file:', error);
        alert('Failed to delete file. Please try again.');
      } finally {
        this.deletingFile = false;
      }
    },
  },
});
</script>

<style scoped>
.statements-empty {
  align-items: center;
  background: var(--bb-surface, #ffffff);
  border: 1px solid var(--bb-border-soft, #f3f4f6);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  padding: 48px 24px;
  text-align: center;
}

.statements-row {
  align-items: center;
  background: var(--bb-surface, #ffffff);
  border: 1px solid var(--bb-border-soft, #f3f4f6);
  border-radius: 16px;
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(0, 1fr) 180px 220px 180px auto;
  padding: 16px;
  transition: box-shadow 0.2s ease;
}

.statements-row:hover {
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}

.statement-plan {
  border: 1px solid var(--bb-border-soft, #f3f4f6);
  border-radius: 12px;
  margin-bottom: 12px;
  padding: 12px 14px;
}

.statement-plan__head {
  align-items: baseline;
  display: flex;
  gap: 12px;
  justify-content: space-between;
}

.statements-row__identity {
  align-items: flex-start;
  display: flex;
  gap: 12px;
  min-width: 0;
}

.statements-row__meta,
.statements-row__progress,
.statements-row__assignment {
  min-width: 0;
}

.statements-row__actions {
  align-items: center;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

@media (max-width: 900px) {
  .statements-row {
    grid-template-columns: minmax(0, 1fr);
  }

  .statements-row__actions {
    flex-wrap: wrap;
    justify-content: flex-start;
  }
}
</style>

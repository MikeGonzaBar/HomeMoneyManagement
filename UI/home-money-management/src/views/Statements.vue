<template>
  <div class="bg-gray-50 text-gray-900 font-sans antialiased min-h-screen">
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
                {{ file.file_size_display }} · Uploaded {{ file.upload_date_display }}
              </p>
              <p class="text-xs text-gray-500 mt-0.5">
                <v-icon size="13" class="mr-1">mdi-bank</v-icon>{{ file.review_account_name || 'Bank not detected' }}
              </p>
            </div>
          </div>

          <div class="statements-row__meta">
            <p class="text-sm font-medium text-gray-700">{{ periodLabel(file) }}</p>
            <v-chip :color="statusColor(file)" size="small" variant="tonal" class="mt-1">
              {{ statusLabel(file) }}
            </v-chip>
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
            <p v-else class="text-sm text-gray-400">No review data</p>
          </div>

          <div class="statements-row__actions">
            <v-btn v-if="canResume(file)" color="primary" variant="tonal" size="small" rounded="lg"
              @click="resumeReview(file)">Resume review</v-btn>
            <v-btn v-if="canViewImported(file)" color="success" variant="tonal" size="small" rounded="lg"
              @click="viewImported(file)">View imported</v-btn>
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
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import AppHeader from '@/components/AppHeader.vue';
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
  review_batch_id?: number | null;
  review_batch_status?: string | null;
  review_candidate_count?: number;
  review_resolved_count?: number;
  review_period_start?: string | null;
  review_period_end?: string | null;
  review_account_name?: string | null;
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
    case 'processing': return file.processing_status === 'pending' ? 'Queued' : 'Processing';
    case 'failed': return 'Failed';
    default: return 'Completed';
  }
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
    periodLabel,
    resolvedCount,
    pendingCount,
    progressPercent,

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
      return !!file.review_batch_id && file.review_batch_status === 'review';
    },

    canViewImported(file: UserFile): boolean {
      return file.review_batch_status === 'committed' && (file.review_candidate_count ?? 0) > 0;
    },

    resumeReview(file: UserFile) {
      if (!file.review_batch_id) return;
      this.$router.push(`/statements/${file.review_batch_id}/review`);
    },

    viewImported(_file: UserFile) {
      this.$router.push('/transactions');
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
  grid-template-columns: minmax(0, 1fr) 180px 170px auto;
  padding: 16px;
  transition: box-shadow 0.2s ease;
}

.statements-row:hover {
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}

.statements-row__identity {
  align-items: flex-start;
  display: flex;
  gap: 12px;
  min-width: 0;
}

.statements-row__meta,
.statements-row__progress {
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



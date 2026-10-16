<template>
  <div class="bg-gray-50 text-gray-900 font-sans antialiased min-h-screen">
    <AppHeader :userData="userData" />
    <main class="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      <v-progress-circular v-if="loading" indeterminate color="primary" class="d-block mx-auto mt-12" />
      <v-alert v-else-if="error" type="error" variant="tonal">
        {{ error }}
        <template #append><v-btn variant="text" @click="$router.push('/statements')">Back to statements</v-btn></template>
      </v-alert>
      <v-card v-else rounded="xl" class="pa-2">
        <v-card-title class="pt-6 px-6 d-flex align-center ga-3">
          <v-avatar color="primary" variant="tonal"><v-icon>mdi-file-search-outline</v-icon></v-avatar>
          <div>
            <div class="text-h5 font-weight-bold">Scan result</div>
            <div class="text-body-2 text-medium-emphasis">{{ batch?.bank_statement_filename || 'Bank statement' }}</div>
          </div>
        </v-card-title>
        <v-card-text class="px-6 pb-4">
          <v-alert type="info" variant="tonal" class="mb-5">
            <strong>No importable transactions found.</strong><br>
            {{ batch?.scan_summary?.zero_result_reason || 'No importable transactions are available from this scan.' }}
          </v-alert>
          <v-row dense>
            <v-col cols="12" sm="6"><div class="label">Statement period</div><div>{{ periodLabel }}</div></v-col>
            <v-col cols="12" sm="6"><div class="label">AI detected</div><div>{{ detectedAccountLabel }}</div></v-col>
            <v-col cols="12" sm="6"><div class="label">Rows identified</div><div>{{ batch?.scan_summary?.raw_transaction_count ?? 0 }}</div></v-col>
            <v-col cols="12" sm="6"><div class="label">Importable rows</div><div>{{ batch?.scan_summary?.importable_candidate_count ?? 0 }}</div></v-col>
          </v-row>
          <v-alert v-if="batch?.initial_balance !== null && batch?.initial_balance !== undefined" type="info" variant="tonal" density="compact" class="mt-5">
            Detected initial balance: <strong>${{ Number(batch.initial_balance).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong>
          </v-alert>
          <p class="text-body-2 text-medium-emphasis mt-5 mb-0">This scan completed successfully. To try another PDF, delete this statement and upload a corrected or replacement file.</p>
        </v-card-text>
        <v-card-actions class="px-6 pb-6">
          <v-btn variant="outlined" @click="$router.push('/statements')">Back to statements</v-btn>
          <v-spacer />
          <v-btn color="primary" variant="flat" @click="$router.push('/')">Upload another statement</v-btn>
        </v-card-actions>
      </v-card>
    </main>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import AppHeader from '@/components/AppHeader.vue';
import axios from '@/services/api';
import { getStoredSession } from '@/services/session';

export default defineComponent({
  name: 'StatementScanResult',
  components: { AppHeader },
  data() {
    return { loading: true, error: '', userData: { user: getStoredSession()?.user ?? {} } as any, batch: null as any };
  },
  computed: {
    periodLabel(): string {
      const period = this.batch?.statement_period;
      if (!period?.start && !period?.end) return 'Period not detected';
      return period.start && period.end ? `${period.start} → ${period.end}` : (period.start || period.end);
    },
    detectedAccountLabel(): string {
      if (!this.batch?.detected_account_name) return 'Account not detected';
      return this.batch.detected_account_type ? `${this.batch.detected_account_name} (${this.batch.detected_account_type})` : this.batch.detected_account_name;
    },
  },
  async mounted() {
    try {
      const response = await axios.get(`/bank-statements/import-batches/${this.$route.params.batchId}/`);
      if ((response.data.candidates || []).length > 0) {
        this.$router.replace(`/statements/${this.$route.params.batchId}/review`);
        return;
      }
      this.batch = response.data;
    } catch (error: any) {
      this.error = error.response?.data?.message || 'Unable to load this scan result.';
    } finally {
      this.loading = false;
    }
  },
});
</script>

<style scoped>
.label { color: #6b7280; font-size: 0.75rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; margin-bottom: .25rem; }
</style>

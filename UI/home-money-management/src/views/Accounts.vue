<template>
  <div class="bg-gray-50 text-gray-900 font-sans antialiased min-h-screen">
    <AppHeader :userData="userData" />

    <main class="w-full px-4 sm:px-6 py-6">
      <!-- Page title + layout controls -->
      <div class="flex flex-wrap items-start justify-between gap-4 mb-6">
        <div>
          <h1 class="text-gray-900 text-3xl font-bold tracking-tight">Accounts</h1>
          <p class="text-gray-500">
            {{ accounts.length }} account{{ accounts.length === 1 ? '' : 's' }}<span v-if="!loading"> · Net worth
            {{ formatMoney(netWorth) }}</span>
          </p>
        </div>
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-1 rounded-full border border-gray-100 bg-gray-50 p-1" role="group"
            aria-label="Account layout">
            <button type="button" class="accounts-view-button" :class="{ 'is-active': viewMode === 'list' }"
              :aria-pressed="viewMode === 'list'" aria-label="List view" @click="viewMode = 'list'">
              <v-icon size="18">mdi-format-list-bulleted</v-icon>
            </button>
            <button type="button" class="accounts-view-button" :class="{ 'is-active': viewMode === 'grid' }"
              :aria-pressed="viewMode === 'grid'" aria-label="Grid view" @click="viewMode = 'grid'">
              <v-icon size="18">mdi-view-grid-outline</v-icon>
            </button>
          </div>
          <v-btn color="primary" variant="outlined" rounded="lg" :loading="loading" @click="loadAccounts">
            <v-icon start>mdi-refresh</v-icon>Refresh
          </v-btn>
        </div>
      </div>

      <!-- Filters -->
      <section class="grid gap-3 mb-6 sm:grid-cols-2 lg:grid-cols-4">
        <v-text-field v-model="search" prepend-inner-icon="mdi-magnify" label="Search name or institution"
          variant="outlined" density="compact" hide-details clearable />
        <v-select v-model="groupBy" :items="groupByOptions" item-title="title" item-value="value" label="Group by"
          variant="outlined" density="compact" hide-details />
        <v-select v-model="typeFilter" :items="typeOptions" item-title="title" item-value="value" label="Account group"
          variant="outlined" density="compact" hide-details />
        <v-select v-model="sortBy" :items="sortOptions" item-title="title" item-value="value" label="Sort"
          variant="outlined" density="compact" hide-details />
      </section>

      <!-- Loading -->
      <section v-if="loading && accounts.length === 0" class="accounts-empty">
        <v-progress-circular indeterminate color="primary" size="56" />
        <p class="text-gray-500 mt-4">Loading your accounts…</p>
      </section>

      <!-- Load failed -->
      <section v-else-if="loadError" class="accounts-empty">
        <v-icon size="56" color="grey-lighten-1" class="mb-3">mdi-alert-circle-outline</v-icon>
        <h2 class="text-lg font-semibold text-gray-900">We could not load your accounts</h2>
        <p class="text-gray-500 text-sm mt-1">{{ loadError }}</p>
        <v-btn color="primary" variant="flat" rounded="lg" class="mt-5" @click="loadAccounts">Try again</v-btn>
      </section>

      <!-- Nothing to show yet -->
      <section v-else-if="accounts.length === 0" class="accounts-empty">
        <v-icon size="56" color="grey-lighten-1" class="mb-3">mdi-wallet-outline</v-icon>
        <h2 class="text-lg font-semibold text-gray-900">No accounts yet</h2>
        <p class="text-gray-500 text-sm mt-1">Add your first account from the dashboard and it will show up here.</p>
        <v-btn color="primary" variant="flat" rounded="lg" class="mt-5" @click="goToDashboard">Go to dashboard</v-btn>
      </section>

      <!-- Filters matched nothing -->
      <section v-else-if="visibleGroups.length === 0" class="accounts-empty">
        <v-icon size="56" color="grey-lighten-1" class="mb-3">mdi-filter-remove-outline</v-icon>
        <h2 class="text-lg font-semibold text-gray-900">No accounts match these filters</h2>
        <v-btn color="primary" variant="text" rounded="lg" class="mt-3" @click="clearFilters">Clear filters</v-btn>
      </section>

      <!-- Account groups -->
      <div v-else class="space-y-6">
        <section v-for="group in visibleGroups" :key="group.key"
          class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <header class="accounts-group-header">
            <div class="flex items-center gap-3 min-w-0">
              <span class="accounts-group-icon" :class="`is-${group.key}`">
                <v-icon size="20" color="white">{{ group.icon }}</v-icon>
              </span>
              <div class="min-w-0">
                <h2 class="text-base font-bold text-gray-900 truncate">{{ group.label }}</h2>
                <p class="text-sm text-gray-500">
                  {{ group.accounts.length }} account{{ group.accounts.length === 1 ? '' : 's' }}
                </p>
              </div>
            </div>
            <div class="text-right shrink-0">
              <p class="accounts-figure-label">Net worth</p>
              <p class="font-bold" :class="group.subtotal >= 0 ? 'text-income' : 'text-expense'">
                {{ formatMoney(group.subtotal) }}
              </p>
            </div>
          </header>

          <div v-for="section in group.sections" :key="section.bank || 'all'" class="border-t border-gray-100">
            <div v-if="groupBy === 'institution'" class="accounts-inst-header">
              <span class="font-semibold text-gray-900 truncate">{{ section.bank }}</span>
              <span class="text-sm text-gray-500">
                {{ section.cards.length }} account{{ section.cards.length === 1 ? '' : 's' }}
              </span>
              <span class="font-semibold shrink-0" :class="section.subtotal >= 0 ? 'text-income' : 'text-expense'">
                {{ formatMoney(section.subtotal) }}
              </span>
            </div>

            <div class="p-4" :class="viewMode === 'grid' ? 'accounts-grid' : 'accounts-list'">
              <article v-for="card in section.cards" :key="card.id" class="accounts-card">
                <div class="accounts-card__head">
                  <span class="accounts-bank-logo">
                    <BankLogo :bank="card.bank" :size="64" />
                  </span>
                  <span class="accounts-group-icon" :class="`is-${group.key}`">
                    <v-icon size="20" color="white">{{ group.icon }}</v-icon>
                  </span>
                  <div class="min-w-0 flex-1">
                    <div class="flex items-center gap-2 flex-wrap">
                      <p class="font-semibold text-gray-900 truncate">{{ card.name }}</p>
                      <span v-if="card.badge" class="accounts-badge" :class="`is-${card.badge.tone}`">
                        {{ card.badge.label }}
                      </span>
                    </div>
                    <p class="text-sm text-gray-500 truncate">{{ card.bank }} · {{ card.typeLabel }}</p>
                    <template v-if="card.usage">
                      <div class="accounts-usage">
                        <span class="accounts-usage__bar" :class="`is-${card.usage.tone}`"
                          :style="{ width: card.usage.percent + '%' }"></span>
                      </div>
                      <p class="text-xs text-gray-500">
                        {{ formatMoney(card.usage.used) }} of {{ formatMoney(card.usage.limit) }} limit used
                      </p>
                    </template>
                  </div>
                </div>
                <div class="accounts-card__figures">
                  <div>
                    <p class="accounts-figure-label">{{ card.balanceLabel }}</p>
                    <p class="font-bold" :class="card.balance >= 0 ? 'text-income' : 'text-expense'">
                      {{ formatMoney(card.balance) }}
                    </p>
                  </div>
                  <div class="accounts-card__networth">
                    <p class="accounts-figure-label">Net worth</p>
                    <p class="font-bold" :class="card.netWorth >= 0 ? 'text-income' : 'text-expense'">
                      {{ formatMoney(card.netWorth) }}
                    </p>
                  </div>
                </div>
              </article>
            </div>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script lang="ts">
import axios from '@/services/api';
import AppHeader from '@/components/AppHeader.vue';
import BankLogo from '@/components/BankLogo.vue';
import { getStoredSession } from '@/services/session';
import { toMoneyNumber } from '@/services/money';
import {
  ACCOUNT_GROUPS,
  creditUtilization,
  filterAccounts,
  groupAccounts,
  groupKeyFor,
  healthBadge,
  netWorthContribution,
  sortAccounts,
  GROUP_ICONS,
} from '@/services/accountGroups';
import type { AccountGroupKey, AccountLike, AccountSort, GroupKey, HealthTone } from '@/services/accountGroups';

interface CardModel {
  id: number;
  name: string;
  bank: string;
  typeLabel: string;
  badge: { label: string; tone: HealthTone } | null;
  usage: { percent: number; used: number; limit: number; tone: HealthTone } | null;
  balanceLabel: string;
  balance: number;
  netWorth: number;
}

interface SectionModel {
  bank: string;
  subtotal: number;
  cards: CardModel[];
}

interface GroupModel {
  key: GroupKey;
  label: string;
  icon: string;
  accounts: AccountLike[];
  subtotal: number;
  sections: SectionModel[];
}

export default {
  name: 'AccountsPage',
  components: { AppHeader, BankLogo },
  data() {
    return {
      userData: null as any,
      accounts: [] as AccountLike[],
      loading: true,
      loadError: '',
      search: '',
      groupBy: 'type',
      typeFilter: 'all',
      sortBy: 'name',
      viewMode: 'list',
      groupByOptions: [
        { title: 'Account type', value: 'type' },
        { title: 'Institution', value: 'institution' },
      ],
      sortOptions: [
        { title: 'Name A–Z', value: 'name' },
        { title: 'Name Z–A', value: '-name' },
        { title: 'Net worth high–low', value: '-networth' },
        { title: 'Net worth low–high', value: 'networth' },
        { title: 'Institution A–Z', value: 'bank' },
      ],
    };
  },
  computed: {
    netWorth(): number {
      return this.accounts.reduce((total: number, account: AccountLike) => total + netWorthContribution(account), 0);
    },
    typeOptions(): Array<{ title: string; value: string }> {
      return [
        { title: 'All groups', value: 'all' },
        ...ACCOUNT_GROUPS.map((group) => ({ title: group.label, value: group.key as string })),
      ];
    },
    visibleGroups(): GroupModel[] {
      const filtered = filterAccounts(this.accounts, this.search, this.typeFilter as AccountGroupKey);
      const sorted = sortAccounts(filtered, this.sortBy as AccountSort);
      return groupAccounts(sorted).map((group) => ({
        key: group.key,
        label: group.label,
        icon: GROUP_ICONS[group.key],
        accounts: group.accounts,
        subtotal: group.subtotal,
        sections:
          this.groupBy === 'institution'
            ? group.institutions.map((section) => ({
                bank: section.bank,
                subtotal: section.subtotal,
                cards: section.accounts.map((account) => this.toCard(account, group.key)),
              }))
            : [
                {
                  bank: '',
                  subtotal: group.subtotal,
                  cards: group.accounts.map((account) => this.toCard(account, group.key)),
                },
              ],
      }));
    },
  },
  mounted() {
    const session = getStoredSession();
    if (session?.user?.username) {
      this.userData = session;
      this.loadAccounts();
    } else {
      this.loading = false;
    }
  },
  methods: {
    async loadAccounts(): Promise<void> {
      const username = this.userData?.user?.username;
      if (!username) return;
      this.loading = true;
      this.loadError = '';
      try {
        const response = await axios.get(`/accounts/details/${username}/0`);
        this.accounts = Array.isArray(response.data) ? response.data : [];
      } catch (error: any) {
        this.loadError = error?.response?.data?.error || 'Please check your connection and try again.';
      } finally {
        this.loading = false;
      }
    },

    clearFilters(): void {
      this.search = '';
      this.groupBy = 'type';
      this.typeFilter = 'all';
      this.sortBy = 'name';
    },

    goToDashboard(): void {
      this.$router.push('/');
    },

    formatMoney(value: number): string {
      return `$${toMoneyNumber(value).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`;
    },

    balanceLabel(account: AccountLike): string {
      const group = groupKeyFor(account.account_type);
      if (group === 'credit') return 'Available credit';
      if (group === 'loans') return 'Amount owed';
      return 'Balance';
    },

    toCard(account: AccountLike, groupKey: GroupKey): CardModel {
      const utilization = creditUtilization(account);
      const badge = healthBadge(account);
      const limit = toMoneyNumber(account.credit_limit);
      return {
        id: account.id,
        name: account.account_name,
        bank: account.bank || 'Unknown institution',
        typeLabel: account.account_type,
        badge,
        usage:
          utilization === null || limit <= 0
            ? null
            : {
                percent: Math.round(utilization * 100),
                used: limit - toMoneyNumber(account.total),
                limit,
                tone: badge?.tone ?? 'good',
              },
        balanceLabel: this.balanceLabel(account),
        balance: toMoneyNumber(account.total),
        netWorth: netWorthContribution(account),
      };
    },
  },
};
</script>

<style scoped>
.accounts-empty {
  align-items: center;
  background: var(--bb-surface, #ffffff);
  border: 1px solid var(--bb-border-soft, #f3f4f6);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  padding: 48px 24px;
  text-align: center;
}

.accounts-view-button {
  align-items: center;
  background: transparent;
  border: 0;
  border-radius: 9999px;
  color: var(--bb-text-muted, #6b7280);
  cursor: pointer;
  display: inline-flex;
  height: 32px;
  justify-content: center;
  width: 32px;
}

.accounts-view-button.is-active {
  background: var(--bb-surface, #ffffff);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.1);
  color: #2e7d32;
}

.accounts-group-header {
  align-items: center;
  background: var(--bb-surface-soft, #f9fafb);
  display: flex;
  gap: 16px;
  justify-content: space-between;
  padding: 16px 20px;
}

.accounts-bank-logo {
    display: block;
    flex-shrink: 0;
    height: 2rem;
    width: 2rem;
}

.accounts-group-icon {
  align-items: center;
  border-radius: 12px;
  display: inline-flex;
  flex-shrink: 0;
  height: 40px;
  justify-content: center;
  width: 40px;
}

.accounts-group-icon.is-cash { background: #2563eb; }
.accounts-group-icon.is-savings { background: #059669; }
.accounts-group-icon.is-investments { background: #7c3aed; }
.accounts-group-icon.is-credit { background: #ea580c; }
.accounts-group-icon.is-loans { background: #d97706; }
.accounts-group-icon.is-other { background: #6b7280; }

.accounts-inst-header {
  align-items: center;
  background: var(--bb-surface-soft, #f9fafb);
  display: flex;
  gap: 12px;
  padding: 10px 20px;
}

.accounts-inst-header>span:first-child {
  flex: 1 1 auto;
  min-width: 0;
}

.accounts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.accounts-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
}

.accounts-card {
  background: var(--bb-surface, #ffffff);
  border: 1px solid var(--bb-border-soft, #f3f4f6);
  border-radius: 16px;
  display: flex;
  gap: 16px;
  justify-content: space-between;
  padding: 16px;
  transition: box-shadow 0.2s ease;
}

.accounts-card:hover {
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}

.accounts-card__head {
  align-items: center;
  display: flex;
  flex: 1 1 auto;
  gap: 12px;
  min-width: 0;
}

.accounts-card__figures {
  display: flex;
  flex-shrink: 0;
  gap: 32px;
}

.accounts-card__networth {
  text-align: right;
}

.accounts-grid .accounts-card {
  align-items: stretch;
  flex-direction: column;
}

.accounts-grid .accounts-card__head {
  align-items: flex-start;
}

.accounts-grid .accounts-card__figures {
  gap: 16px;
  justify-content: space-between;
}

.accounts-figure-label {
  color: #9ca3af;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  margin-bottom: 2px;
  text-transform: uppercase;
}

.accounts-badge {
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  white-space: nowrap;
}

.accounts-badge.is-good { background: #dcfce7; color: #166534; }
.accounts-badge.is-warn { background: #fef3c7; color: #92400e; }
.accounts-badge.is-bad { background: #fee2e2; color: #991b1b; }

.accounts-usage {
  background: #e5e7eb;
  border-radius: 9999px;
  height: 6px;
  margin: 8px 0 4px;
  overflow: hidden;
}

.accounts-usage__bar {
  border-radius: 9999px;
  display: block;
  height: 100%;
}

.accounts-usage__bar.is-good { background: #22c55e; }
.accounts-usage__bar.is-warn { background: #f59e0b; }
.accounts-usage__bar.is-bad { background: #ef4444; }

@media (max-width: 900px) {
  .accounts-card {
    align-items: stretch;
    flex-direction: column;
  }

  .accounts-card__figures {
    justify-content: space-between;
  }
}
</style>

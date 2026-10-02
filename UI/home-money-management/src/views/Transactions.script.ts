import axios, { getAllPages } from '@/services/api';
import { defineComponent } from 'vue';
import { getCategoryStyle } from '@/constants/categoryStyles';
import { getStoredSession } from '@/services/session';
import AppHeader from '@/components/AppHeader.vue';

interface Transaction {
  id: number;
  transaction_type: string;
  category: string;
  date: string;
  title: string;
  total: number;
  account_id?: string;
  from_account_id?: string;
  to_account_id?: string;
}

interface Account {
  id: number;
  account_name: string;
}

export default defineComponent({
  name: 'Transactions',
  components: { AppHeader },
  data() {
    return {
      userData: { user: {} } as any,
      transactions: [] as Transaction[],
      accounts: [] as Account[],
      filterAccount: '' as string,
      filterCategory: '' as string,
      filterPeriod: '30' as string,
      sortBy: '-date' as string,
      currentPage: 1,
      itemsPerPage: 10,
      searchQuery: '' as string,
      periodOptions: [
        { title: 'Last 7 Days', value: '7' },
        { title: 'Last 30 Days', value: '30' },
        { title: 'Last 90 Days', value: '90' },
      ],
    };
  },
  computed: {
    accountFilterOptions(): Array<{ title: string; value: string }> {
      return [{ title: 'All Accounts', value: '' }, ...this.accounts.map((a) => ({ title: a.account_name, value: String(a.id) }))];
    },
    categoryFilterOptions(): Array<{ title: string; value: string }> {
      const cats = [...new Set(this.transactions.map((t) => t.category).filter(Boolean))].sort();
      return [{ title: 'All Categories', value: '' }, ...cats.map((c) => ({ title: c, value: c }))];
    },
    filteredTransactions(): Transaction[] {
      let list = [...this.transactions];
      const now = new Date();
      const days = parseInt(this.filterPeriod || '30', 10);
      const cutout = new Date(now);
      cutout.setDate(cutout.getDate() - days);
      list = list.filter((t) => {
        const d = new Date(t.date);
        if (isNaN(d.getTime())) return false;
        return d >= cutout;
      });
      if (this.filterAccount) {
        list = list.filter((t) => {
          if (t.transaction_type === 'Transfer') {
            return String(t.from_account_id) === this.filterAccount || String(t.to_account_id) === this.filterAccount;
          }
          return String(t.account_id) === this.filterAccount;
        });
      }
      if (this.filterCategory) {
        list = list.filter((t) => t.category === this.filterCategory);
      }
      if (this.searchQuery.trim()) {
        const q = this.searchQuery.trim().toLowerCase();
        list = list.filter((t) =>
          (t.title || '').toLowerCase().includes(q) ||
          (t.category || '').toLowerCase().includes(q)
        );
      }
      const [key, order] = this.sortBy.startsWith('-') ? [this.sortBy.slice(1), -1] : [this.sortBy, 1];
      list.sort((a, b) => {
        const av = (a as any)[key];
        const bv = (b as any)[key];
        if (typeof av === 'string' && typeof bv === 'string') return order * av.localeCompare(bv);
        if (typeof av === 'number' && typeof bv === 'number') return order * (av - bv);
        const da = new Date(av).getTime();
        const db = new Date(bv).getTime();
        return order * (da - db);
      });
      return list;
    },
    paginatedTransactions(): Transaction[] {
      const start = (this.currentPage - 1) * this.itemsPerPage;
      return this.filteredTransactions.slice(start, start + this.itemsPerPage);
    },
    totalPages(): number {
      return Math.max(1, Math.ceil(this.filteredTransactions.length / this.itemsPerPage));
    },
    pageStart(): number {
      if (this.filteredTransactions.length === 0) return 0;
      return (this.currentPage - 1) * this.itemsPerPage + 1;
    },
    pageEnd(): number {
      return Math.min(this.currentPage * this.itemsPerPage, this.filteredTransactions.length);
    },
    visiblePages(): number[] {
      const total = this.totalPages;
      const cur = this.currentPage;
      const pages: number[] = [];
      const start = Math.max(1, cur - 2);
      const end = Math.min(total, cur + 2);
      for (let i = start; i <= end; i++) pages.push(i);
      return pages;
    },
    filteredIncomeTotal(): number {
      return this.filteredTransactions
        .filter((t) => t.transaction_type === 'Income')
        .reduce((acc, t) => acc + (Number(t.total) || 0), 0);
    },
    filteredExpenseTotal(): number {
      return this.filteredTransactions
        .filter((t) => t.transaction_type === 'Expense')
        .reduce((acc, t) => acc + Math.abs(Number(t.total) || 0), 0);
    },
    filteredNet(): number {
      return this.filteredIncomeTotal - this.filteredExpenseTotal;
    },
  },
  watch: {
    filterAccount: { handler() { this.currentPage = 1; } },
    filterCategory: { handler() { this.currentPage = 1; } },
    filterPeriod: { handler() { this.currentPage = 1; } },
    searchQuery: { handler() { this.currentPage = 1; } },
  },
  mounted() {
    const session = getStoredSession();
    if (session) this.userData.user = session.user;
    if (!this.userData?.user?.username) {
      this.$router.replace('/');
      return;
    }
    this.getTransactions();
    this.getAccounts();
  },
  methods: {
    getTransactions() {
      const username = this.userData?.user?.username;
      if (!username) return;
      getAllPages<Transaction>(`/transactions/retrieve/${username}/0/0/0`, (data) => data.results)
        .then((items) => { this.transactions = items; })
        .catch((err) => console.error('Transactions fetch error:', err));
    },
    getAccounts() {
      const username = this.userData?.user?.username;
      if (!username) return;
      axios.get(`/accounts/details/${username}/0`)
        .then((res) => { this.accounts = res.data || []; })
        .catch((err) => console.error('Accounts fetch error:', err));
    },
    getAccountName(t: Transaction): string {
      if (t.transaction_type === 'Transfer') {
        const fromId = t.from_account_id ? this.accounts.find((a) => a.id === Number(t.from_account_id))?.account_name : null;
        const toId = t.to_account_id ? this.accounts.find((a) => a.id === Number(t.to_account_id))?.account_name : null;
        if (fromId && toId) return `From ${fromId} to ${toId}`;
        return fromId || toId || '-';
      }
      const id = Number(t.account_id);
      const acc = this.accounts.find((a) => a.id === id);
      return acc?.account_name || '-';
    },
    formatDate(dateStr: string): string {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    },
    getCategoryStyle,
    resetFilters() {
      this.filterAccount = '';
      this.filterCategory = '';
      this.filterPeriod = '30';
      this.currentPage = 1;
    },
    exportTransactions() {
      const rows = this.filteredTransactions.map((t) => ({
        Date: this.formatDate(t.date),
        Description: t.title,
        Category: t.category,
        Account: this.getAccountName(t),
        Amount: t.transaction_type === 'Income' ? t.total : t.transaction_type === 'Expense' ? -Math.abs(t.total) : t.total,
      }));
      const headers = ['Date', 'Description', 'Category', 'Account', 'Amount'];
      const csv = [headers.join(','), ...rows.map((r) => headers.map((h) => `"${String(r[h as keyof typeof r]).replace(/"/g, '""')}"`).join(','))].join('\n');
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `transactions-${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(a.href);
    },
  },
});

import axios from '@/services/api';
import { defineComponent } from 'vue';
import { getCategoryColor } from '@/constants/categoryStyles';
import { getStoredSession } from '@/services/session';

interface AnalyticsData {
  start_date: string;
  end_date: string;
  kpis: {
    total_income: number;
    total_income_pct_change: number;
    total_expenses: number;
    total_expenses_pct_change: number;
    net_savings: number;
    net_savings_pct_change: number;
    savings_rate: number;
    savings_rate_pct_change: number;
  };
  monthly_income_expenses: Array<{ month: string; label: string; income: number; expense: number }>;
  net_worth: number;
  net_worth_change: number;
  spending_by_category: Array<{ month: string; label: string; categories: Record<string, number> }>;
  top_categories: Array<{ category: string; amount: number }>;
  smart_insights: { message: string; tags: string[] };
}

const CATEGORY_CHART_COLORS = ['#4CAF50', '#8b5cf6', '#06b6d4', '#f59e0b', '#6366f1'];

export default defineComponent({
  name: 'Reports',
  data() {
    return {
      userData: { user: {} } as any,
      searchQuery: '' as string,
      analytics: null as AnalyticsData | null,
      dateStart: '' as string,
      dateEnd: '' as string,
      showDateMenu: false as boolean,
      categoryColors: CATEGORY_CHART_COLORS,
    };
  },
  computed: {
    dateRangeLabel(): string {
      if (this.analytics?.start_date && this.analytics?.end_date) {
        const s = new Date(this.analytics.start_date);
        const e = new Date(this.analytics.end_date);
        return `${s.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} - ${e.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
      }
      const now = new Date();
      const first = new Date(now.getFullYear(), now.getMonth(), 1);
      const last = new Date(now.getFullYear(), now.getMonth() + 1, 0);
      return `${first.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} - ${last.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
    },
    kpiCards(): Array<{ key: string; label: string; display: string; pct: number; barClass: string; barWidth: string }> {
      const k = this.analytics?.kpis;
      if (!k) return [];
      const maxIncome = Math.max(k.total_income || 1, 1);
      const maxExp = Math.max(k.total_expenses || 1, 1);
      const maxNet = Math.max(Math.abs(k.net_savings) || 1, 1);
      return [
        {
          key: 'income',
          label: 'Total Income',
          display: `$${(k.total_income || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
          pct: k.total_income_pct_change ?? 0,
          barClass: 'bg-brand-primary',
          barWidth: `${Math.min(100, ((k.total_income || 0) / maxIncome) * 100)}%`,
        },
        {
          key: 'expenses',
          label: 'Total Expenses',
          display: `$${(k.total_expenses || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
          pct: k.total_expenses_pct_change ?? 0,
          barClass: 'bg-red-400',
          barWidth: `${Math.min(100, ((k.total_expenses || 0) / maxExp) * 100)}%`,
        },
        {
          key: 'net',
          label: 'Net Savings',
          display: `$${(k.net_savings || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
          pct: k.net_savings_pct_change ?? 0,
          barClass: 'bg-emerald-500',
          barWidth: `${Math.min(100, Math.max(0, ((k.net_savings || 0) / maxNet) * 50 + 50))}%`,
        },
        {
          key: 'savings_rate',
          label: 'Savings Rate',
          display: `${(k.savings_rate ?? 0).toFixed(1)}%`,
          pct: k.savings_rate_pct_change ?? 0,
          barClass: 'bg-amber-500',
          barWidth: `${Math.min(100, (k.savings_rate ?? 0) / 100 * 100)}%`,
        },
      ];
    },
    monthlyData(): AnalyticsData['monthly_income_expenses'] {
      return this.analytics?.monthly_income_expenses ?? [];
    },
    maxChartVal(): number {
      let m = 0;
      for (const d of this.monthlyData) {
        m = Math.max(m, d.income || 0, d.expense || 0);
      }
      return m || 1;
    },
    netWorth(): number {
      return this.analytics?.net_worth ?? 0;
    },
    netWorthChange(): number {
      return this.analytics?.net_worth_change ?? 0;
    },
    netWorthPath(): string {
      const data = this.monthlyData;
      if (data.length < 2) return 'M0,35 L100,35';
      const points = data.map((d, i) => {
        const x = (i / (data.length - 1)) * 100;
        const total = (d.income || 0) - (d.expense || 0);
        const y = 35 - (total / (this.maxChartVal || 1)) * 25;
        return `${x},${Math.max(5, Math.min(35, y))}`;
      });
      return 'M' + points.join(' L');
    },
    netWorthAreaPath(): string {
      const data = this.monthlyData;
      if (data.length < 2) return '';
      const path = this.netWorthPath;
      return path + ' L100,40 L0,40 Z';
    },
    spendingByCategory(): AnalyticsData['spending_by_category'] {
      return this.analytics?.spending_by_category ?? [];
    },
    categoryLegend(): string[] {
      const cats = new Set<string>();
      for (const m of this.spendingByCategory) {
        for (const c of Object.keys(m.categories || {})) cats.add(c);
      }
      return Array.from(cats);
    },
    topCategories(): AnalyticsData['top_categories'] {
      return this.analytics?.top_categories ?? [];
    },
    maxTopCategory(): number {
      const tc = this.topCategories;
      if (tc.length === 0) return 1;
      return Math.max(...tc.map((t) => t.amount), 1);
    },
    smartInsights(): { message: string; tags: string[] } {
      return this.analytics?.smart_insights ?? { message: 'Loading your financial insights...', tags: [] };
    },
  },
  mounted() {
    const session = getStoredSession();
    if (session) this.userData.user = session.user;
    if (!this.userData?.user?.username) {
      this.$router.replace('/');
      return;
    }
    this.fetchAnalytics();
  },
  methods: {
    fetchAnalytics() {
      const username = this.userData?.user?.username;
      if (!username) return;
      const params: Record<string, string> = {};
      if (this.dateStart) params.start_date = this.dateStart;
      if (this.dateEnd) params.end_date = this.dateEnd;
      axios
        .get(`/reports/analytics/${username}/`, { params })
        .then((res) => {
          this.analytics = res.data;
          if (res.data?.start_date && res.data?.end_date) {
            this.dateStart = res.data.start_date;
            this.dateEnd = res.data.end_date;
          }
        })
        .catch((err) => console.error('Reports fetch error:', err));
    },
    barHeight(val: number): string {
      const max = this.maxChartVal;
      const pct = max > 0 ? (val / max) * 100 : 0;
      return `${Math.min(100, Math.max(5, pct))}%`;
    },
    categoryBarHeight(m: { categories: Record<string, number> }, cat: string): string {
      const cats = m.categories || {};
      const total = Object.values(cats).reduce((a, b) => a + b, 0) || 1;
      const amt = cats[cat] || 0;
      return `${(amt / total) * 100}%`;
    },
    topCategoryWidth(tc: { amount: number }): string {
      const max = this.maxTopCategory;
      return `${(tc.amount / max) * 100}%`;
    },
    getCategoryColor,
    applyDateRange() {
      this.showDateMenu = false;
      this.fetchAnalytics();
    },
    goToProfile() {
      this.$router.push('/profile');
    },
    exportReport() {
      const data = this.analytics;
      if (!data) return;
      const lines = [
        'Financial Analytics Report',
        `Period: ${data.start_date} to ${data.end_date}`,
        '',
        'KPIs',
        `Total Income,$${data.kpis.total_income}`,
        `Total Expenses,$${data.kpis.total_expenses}`,
        `Net Savings,$${data.kpis.net_savings}`,
        `Savings Rate,${data.kpis.savings_rate}%`,
        '',
        'Smart Insights',
        data.smart_insights.message,
      ];
      const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `financial-analytics-${data.start_date}.csv`;
      a.click();
      URL.revokeObjectURL(a.href);
    },
  },
});

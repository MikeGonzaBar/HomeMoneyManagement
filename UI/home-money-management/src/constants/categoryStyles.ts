/**
 * Canonical category styles - shared between TableData and PieChart.
 * Each category has a unique color and icon.
 */
export const CATEGORY_STYLES: Record<string, { icon: string; color: string }> = {
  'Salary': { icon: 'mdi-cash', color: '#2E7D32' },
  'Awards': { icon: 'mdi-trophy', color: '#F57C00' },
  'Investments': { icon: 'mdi-chart-line', color: '#1565C0' },
  'Gifts': { icon: 'mdi-gift', color: '#C2185B' },
  'Account Transfer': { icon: 'mdi-bank-transfer', color: '#6A1B9A' },
  'Balance Transfer': { icon: 'mdi-swap-horizontal', color: '#4527A0' },
  'Money Transfer': { icon: 'mdi-cash-multiple', color: '#283593' },
  'Transfer': { icon: 'mdi-arrow-left-right', color: '#3949AB' },
  'Bills and utilities': { icon: 'mdi-lightning-bolt', color: '#E65100' },
  'Education': { icon: 'mdi-school', color: '#00695C' },
  'Entertainment': { icon: 'mdi-movie', color: '#00838F' },
  'Food and drinks': { icon: 'mdi-food', color: '#5D4037' },
  'Insurance': { icon: 'mdi-shield', color: '#455A64' },
  'Loans': { icon: 'mdi-currency-usd', color: '#C62828' },
  'Medical': { icon: 'mdi-medical-bag', color: '#D84315' },
  'Shopping': { icon: 'mdi-shopping', color: '#7B1FA2' },
  'Transportation': { icon: 'mdi-car', color: '#00796B' },
  'Others': { icon: 'mdi-dots-horizontal', color: '#757575' },
  'Income': { icon: 'mdi-cash', color: '#10B981' },
};

const FALLBACK = { icon: 'mdi-tag', color: '#616161' };

export function getCategoryStyle(category: string): { icon: string; color: string } {
  return CATEGORY_STYLES[category] || FALLBACK;
}

export function getCategoryColor(category: string): string {
  return getCategoryStyle(category).color;
}

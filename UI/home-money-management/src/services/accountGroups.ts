/**
 * Pure grouping / health rules for the Accounts page.
 *
 * Kept free of Vue so the grouping, subtotal and badge rules that drive the
 * page can be checked without mounting the view. See accountGroups.check.mjs.
 *
 * Balance contract follows the API (`API/account/models.py::net_worth_value`):
 * `total` is the balance for assets, *available* credit for credit cards and
 * the *amount owed* for loans/mortgages.
 */
import { toMoneyNumber } from './money.ts'

export interface AccountLike {
  id: number
  account_name: string
  account_type: string
  bank: string
  total: number
  credit_limit?: number | null
}

export type GroupKey = 'cash' | 'savings' | 'investments' | 'credit' | 'loans' | 'other'

/** Page ordering. Groups with no accounts are dropped at render time. */
export const ACCOUNT_GROUPS: ReadonlyArray<{ key: GroupKey; label: string }> = [
  { key: 'cash', label: 'Cash & checking' },
  { key: 'savings', label: 'Savings' },
  { key: 'investments', label: 'Investments' },
  { key: 'credit', label: 'Credit cards' },
  { key: 'loans', label: 'Loans' },
  { key: 'other', label: 'Other' },
]

/** One icon per group, shared by the Accounts page and the dashboard summary. */
export const GROUP_ICONS: Readonly<Record<GroupKey, string>> = {
  cash: 'mdi-wallet-outline',
  savings: 'mdi-piggy-bank-outline',
  investments: 'mdi-chart-line',
  credit: 'mdi-credit-card-outline',
  loans: 'mdi-bank-transfer',
  other: 'mdi-bank',
}

const CREDIT_TYPES = new Set(['crédito', 'credit'])
const DEBT_TYPES = new Set(['loan', 'mortgage'])

/** "Savings Account" / "Credit Card" -> "Savings" / "Credit". */
export function normalizeType(accountType?: string): string {
  return (accountType ?? '').replace(/\s+(Account|Card)$/i, '').trim()
}

export function groupKeyFor(accountType?: string): GroupKey {
  const type = normalizeType(accountType).toLowerCase()
  if (type === 'savings') return 'savings'
  if (CREDIT_TYPES.has(type)) return 'credit'
  if (DEBT_TYPES.has(type)) return 'loans'
  if (type === 'investment' || type === 'retirement') return 'investments'
  if (['débito', 'debit', 'checking', 'cash', 'efectivo'].includes(type)) return 'cash'
  return 'other'
}

/**
 * What the account adds to net worth (mirrors `Account.net_worth_value`).
 * A credit card without a recorded limit contributes 0 — the API makes the
 * same call, and disagreeing here would break the dashboard totals.
 */
export function netWorthContribution(account: AccountLike): number {
  const total = toMoneyNumber(account.total)
  const type = normalizeType(account.account_type).toLowerCase()
  if (CREDIT_TYPES.has(type)) {
    const limit = toMoneyNumber(account.credit_limit)
    return limit > 0 ? -(limit - total) : 0
  }
  if (DEBT_TYPES.has(type)) return -total
  return total
}

/** Fraction of the limit currently used (0..1), or null when not applicable. */
export function creditUtilization(account: AccountLike): number | null {
  const type = normalizeType(account.account_type).toLowerCase()
  if (!CREDIT_TYPES.has(type)) return null
  const limit = toMoneyNumber(account.credit_limit)
  if (limit <= 0) return null
  const ratio = (limit - toMoneyNumber(account.total)) / limit
  return Math.min(Math.max(ratio, 0), 1)
}

export type HealthTone = 'good' | 'warn' | 'bad'

export interface HealthBadge {
  label: string
  tone: HealthTone
}

/**
 * Exceptions worth flagging: credit utilization tiers (>=50% warn, >=80% high)
 * and a negative balance on a non-liability. Healthy assets get no badge.
 */
export function healthBadge(account: AccountLike): HealthBadge | null {
  const utilization = creditUtilization(account)
  if (utilization !== null) {
    const percent = Math.round(utilization * 100)
    const tone: HealthTone = utilization >= 0.8 ? 'bad' : utilization >= 0.5 ? 'warn' : 'good'
    return { label: `${percent}% used`, tone }
  }
  if (toMoneyNumber(account.total) < 0) return { label: 'Overdrawn', tone: 'bad' }
  return null
}

export type AccountGroupKey = GroupKey | 'all'

export function filterAccounts(
  accounts: AccountLike[],
  search?: string,
  group: AccountGroupKey = 'all',
): AccountLike[] {
  const query = (search ?? '').trim().toLowerCase()
  return accounts.filter((account) => {
    if (group !== 'all' && groupKeyFor(account.account_type) !== group) return false
    if (!query) return true
    return `${account.account_name} ${account.bank} ${account.account_type}`.toLowerCase().includes(query)
  })
}

export type AccountSort = 'name' | '-name' | 'networth' | '-networth' | 'bank' | '-bank'

/** Stable sort; ties keep the order the API returned them in. */
export function sortAccounts(accounts: AccountLike[], sort: AccountSort): AccountLike[] {
  const descending = sort.startsWith('-')
  const key = descending ? sort.slice(1) : sort
  const direction = descending ? -1 : 1
  return [...accounts].sort((a, b) => {
    if (key === 'networth') {
      return (netWorthContribution(a) - netWorthContribution(b)) * direction
    }
    const left = (key === 'bank' ? a.bank : a.account_name).toLowerCase()
    const right = (key === 'bank' ? b.bank : b.account_name).toLowerCase()
    return left.localeCompare(right) * direction
  })
}

/** Extra rows the dashboard needs that the Accounts page has no reason to show. */
export interface SnapshotAccount extends AccountLike {
  statement_snapshot?: { statement_date?: string; positions?: Array<{ investment_id?: string; name?: string; total?: number; capital?: number }> } | null
  credit_card_statement_snapshot?: {
    statement_date?: string
    summary?: { deferred_balance?: number }
    deferred_purchases?: Array<{ source_key?: string; merchant?: string; remaining_balance?: number; installment_number?: number; installment_count?: number }>
  } | null
  retirement_metadata?: { institution?: string; statement_date?: string; breakdown?: { subaccounts?: Record<string, number> } } | null
}

export interface CardDebt {
  /** Sum of every card's limit. 0 when no card has a recorded limit. */
  limit: number
  /** limit - available credit, per card, floored at 0. */
  used: number
  /** Cards actually contributing (i.e. those with a limit). */
  cards: number
}

/**
 * Card debt for the top-of-dashboard. A card with no recorded limit is skipped
 * entirely — same call the API makes in `net_worth_value`, so the number here
 * can never disagree with the Accounts page.
 */
export function cardDebt(accounts: SnapshotAccount[]): CardDebt {
  return accounts.reduce<CardDebt>((debt, account) => {
    const limit = toMoneyNumber(account.credit_limit)
    if (groupKeyFor(account.account_type) !== 'credit' || limit <= 0) return debt
    const used = limit - toMoneyNumber(account.total)
    return { limit: debt.limit + limit, used: debt.used + Math.max(used, 0), cards: debt.cards + 1 }
  }, { limit: 0, used: 0, cards: 0 })
}

/**
 * Money you could spend right now: checking + savings + cash on hand. Excludes
 * investments, and deliberately excludes cards (their `total` is *available*
 * credit, not money in the bank).
 */
export function availableCash(accounts: SnapshotAccount[]): number {
  return accounts
    .filter((account) => ['cash', 'savings'].includes(groupKeyFor(account.account_type)))
    .reduce((total, account) => total + toMoneyNumber(account.total), 0)
}

/** Balance held in investment + retirement accounts. */
export function investmentsTotal(accounts: SnapshotAccount[]): number {
  return accounts
    .filter((account) => groupKeyFor(account.account_type) === 'investments')
    .reduce((total, account) => total + toMoneyNumber(account.total), 0)
}

export interface FlowTransaction {
  transaction_type: string
  total: number | string
  date: string
}

export interface MonthFlow {
  income: number
  expense: number
  net: number
}

const monthKey = (date: string | Date): string => {
  const parsed = typeof date === 'string' ? new Date(date) : date
  if (isNaN(parsed.getTime())) return ''
  return `${parsed.getFullYear()}-${parsed.getMonth()}`
}

/**
 * Income / expense for the calendar month containing `at`, with transfers
 * excluded from both (they are neither). Falls back to the whole list when no
 * transaction carries a parseable date, so a bad date never blanks the cards.
 */
export function monthFlow(transactions: FlowTransaction[], at: Date = new Date()): MonthFlow {
  const scoped = transactions.filter((transaction) => monthKey(transaction.date) === monthKey(at))
  const source = scoped.length > 0 ? scoped : transactions
  let income = 0
  let expense = 0
  for (const transaction of source) {
    const amount = toMoneyNumber(transaction.total)
    if (transaction.transaction_type === 'Income') income += amount
    else if (transaction.transaction_type === 'Expense') expense += Math.abs(amount)
  }
  return { income, expense, net: income - expense }
}

export interface DashboardSnapshot {
  netWorth: number
  availableCash: number
  card: CardDebt
  investments: number
  flow: MonthFlow
}

/** Everything the dashboard's top area renders, in one call. */
export function dashboardSnapshot(
  accounts: SnapshotAccount[],
  transactions: FlowTransaction[],
  at: Date = new Date(),
): DashboardSnapshot {
  return {
    netWorth: accounts.reduce((total, account) => total + netWorthContribution(account), 0),
    availableCash: availableCash(accounts),
    card: cardDebt(accounts),
    investments: investmentsTotal(accounts),
    flow: monthFlow(transactions, at),
  }
}

export interface InstitutionSection {
  bank: string
  accounts: AccountLike[]
  subtotal: number
}

export interface AccountGroup {
  key: GroupKey
  label: string
  accounts: AccountLike[]
  subtotal: number
  institutions: InstitutionSection[]
}

const sumContributions = (accounts: AccountLike[]): number =>
  accounts.reduce((total, account) => total + netWorthContribution(account), 0)

/**
 * Buckets into the fixed page groups, preserving the input order inside each
 * group. Institutions are always computed (alphabetically) so the view can
 * switch layouts without recomputing totals.
 */
export function groupAccounts(accounts: AccountLike[]): AccountGroup[] {
  const buckets = new Map<GroupKey, AccountLike[]>()
  for (const account of accounts) {
    const key = groupKeyFor(account.account_type)
    const bucket = buckets.get(key)
    if (bucket) bucket.push(account)
    else buckets.set(key, [account])
  }

  const groups: AccountGroup[] = []
  for (const { key, label } of ACCOUNT_GROUPS) {
    const members = buckets.get(key)
    if (!members || members.length === 0) continue

    const byBank = new Map<string, AccountLike[]>()
    for (const account of members) {
      const bank = account.bank?.trim() || 'Other'
      const bankBucket = byBank.get(bank)
      if (bankBucket) bankBucket.push(account)
      else byBank.set(bank, [account])
    }

    groups.push({
      key,
      label,
      accounts: members,
      subtotal: sumContributions(members),
      institutions: [...byBank.entries()]
        .map(([bank, bankAccounts]) => ({
          bank,
          accounts: bankAccounts,
          subtotal: sumContributions(bankAccounts),
        }))
        .sort((a, b) => a.bank.localeCompare(b.bank)),
    })
  }
  return groups
}

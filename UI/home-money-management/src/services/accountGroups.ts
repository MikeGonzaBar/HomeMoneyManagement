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

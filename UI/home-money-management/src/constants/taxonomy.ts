/**
 * Canonical transaction categories, transaction types and account types — the
 * single source of truth for the UI.
 *
 * These mirror the API's canonical lists:
 *   - categories:    `CANONICAL_CATEGORIES` in `API/bankstatements/services.py`
 *   - transaction types: `Transaction.TRANSACTION_TYPES` in `API/transaction/models.py`
 *   - account types: the "Allowed account/product types" list in the extraction prompt
 *
 * Import from here instead of re-declaring these lists inside individual views
 * or components, so the statement importer, the transaction editor, budgets and
 * recurring items cannot drift apart.
 */

/** Every transaction category the API may emit or accept, in display order. */
export const CATEGORIES = [
  // Income
  'Salary',
  'Awards',
  'Investments',
  'Gifts',
  // Transfers
  'Account Transfer',
  'Balance Transfer',
  'Money Transfer',
  'Transfer',
  // Cash movements whose other account is outside the tracked account set
  'External cash adjustment',
  // Expense
  'Bills and utilities',
  'Education',
  'Entertainment',
  'Food and drinks',
  'Insurance',
  'Loans',
  'Medical',
  'Shopping',
  'Transportation',
  // Other / retirement
  'Others',
  'Retirement contribution',
  'Investment return',
  'Retirement fee',
  'Retirement interest',
];

/** Categories that only ever appear on retirement-statement movements. */
export const RETIREMENT_CATEGORIES = [
  'Retirement contribution',
  'Investment return',
  'Retirement fee',
  'Retirement interest',
];

/** Expense categories offered when creating a monthly budget. */
export const BUDGET_CATEGORIES = [
  'Bills and utilities',
  'Education',
  'Entertainment',
  'Food and drinks',
  'Insurance',
  'Investments',
  'Loans',
  'Medical',
  'Others',
  'Shopping',
  'Transportation',
];

/** Categories offered when creating a recurring item. */
export const RECURRING_CATEGORIES = [
  'Bills and utilities',
  'Entertainment',
  'Food and drinks',
  'Insurance',
  'Investments',
  'Loans',
  'Money Transfer',
  'Others',
  'Salary',
  'Transportation',
  'Transfer',
];

/** Canonical transaction types. Mirrors `Transaction.TRANSACTION_TYPES`. */
export const TRANSACTION_TYPES: Array<{ title: string; value: string }> = [
  { title: 'Income', value: 'Income' },
  { title: 'Expense', value: 'Expense' },
  { title: 'Transfer', value: 'Transfer' },
  { title: 'External cash adjustment - in', value: 'External Deposit' },
  { title: 'External cash adjustment - out', value: 'External Withdrawal' },
];

/** Transaction types offered for a recurring item. */
export const RECURRING_TRANSACTION_TYPES = ['Income', 'Expense', 'Transfer'];

/**
 * Canonical account types. `value` is what the API stores; `title` is the
 * label shown in the UI. The Spanish values (`Débito`, `Efectivo`) are kept
 * because they are what existing accounts already use and what the API's
 * `normalize_account_type` produces for debit/cash. The credit-card synonyms
 * ("Crédito"/"Credit") are intentionally not listed — the API normalizes them
 * to "Credit Card", so offering them separately would be a duplicate.
 */
export const ACCOUNT_TYPES: Array<{ title: string; value: string }> = [
  { title: 'Checking', value: 'Checking' },
  { title: 'Savings', value: 'Savings' },
  { title: 'Credit Card', value: 'Credit Card' },
  { title: 'Debit', value: 'Débito' },
  { title: 'Cash', value: 'Efectivo' },
  { title: 'Investment', value: 'Investment' },
  { title: 'Retirement', value: 'Retirement' },
  { title: 'Loan', value: 'Loan' },
  { title: 'Mortgage', value: 'Mortgage' },
  { title: 'Business', value: 'Business' },
  { title: 'Other', value: 'Other' },
];

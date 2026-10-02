// Runnable check for the Import Review row-classification rules.
//   node src/services/importReviewStatus.check.mjs
// Fails loudly if the "needs review" rules that drive the progress counts break.
import assert from 'node:assert/strict';
import { rowStatus, summarizeRows } from './importReviewStatus.ts';

// A plain expense needs no attention.
assert.equal(rowStatus({ transaction_type: 'Expense' }), 'ready');

// Transfers are unresolved until both ends are set to different accounts.
assert.equal(rowStatus({ transaction_type: 'Transfer' }), 'needs_review');
assert.equal(rowStatus({ transaction_type: 'Transfer', from_account_id: '1' }), 'needs_review');
assert.equal(
  rowStatus({ transaction_type: 'Transfer', from_account_id: '1', to_account_id: '1' }),
  'needs_review',
);
assert.equal(
  rowStatus({ transaction_type: 'Transfer', from_account_id: '1', to_account_id: '2' }),
  'ready',
);

// Multi-product transfers map through products instead of accounts.
assert.equal(
  rowStatus({ transaction_type: 'Transfer', source_product_id: 'p1' }),
  'ready',
);

// Historical decisions win over the transfer rule.
assert.equal(rowStatus({ transaction_type: 'Transfer', status: 'skipped' }), 'skipped');
assert.equal(rowStatus({ transaction_type: 'Transfer', status: 'imported' }), 'imported');
assert.equal(rowStatus({ linked_transaction_id: 9 }), 'linked');

// The 21/35 style summary: 3 rows, 1 blocker, 1 duplicate.
const summary = summarizeRows([
  { transaction_type: 'Expense' },
  { transaction_type: 'Expense', possible_matches: [{ id: 1 }] },
  { transaction_type: 'Transfer' },
]);
assert.deepEqual(summary, { resolved: 2, actionRequired: 1, duplicates: 1 });

// Empty batch must not divide by zero or drift.
assert.deepEqual(summarizeRows([]), { resolved: 0, actionRequired: 0, duplicates: 0 });

console.log('importReviewStatus: all checks passed');

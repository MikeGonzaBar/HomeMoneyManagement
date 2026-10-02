/**
 * Pure review-row classification for the Import Review workspace.
 *
 * Kept free of Vue so the "needs review" rules that drive the sticky progress
 * counts can be checked without mounting the view. See importReviewStatus.check.mjs.
 */

export interface ReviewRow {
  transaction_type?: string;
  status?: string;
  from_account_id?: string | null;
  to_account_id?: string | null;
  source_product_id?: string | null;
  linked_transaction_id?: number | null;
  possible_matches?: unknown[];
}

export type RowStatus = 'needs_review' | 'ready' | 'imported' | 'skipped' | 'linked';

/** A transfer is unresolved until it has two different ends. */
export function rowNeedsReview(row: ReviewRow): boolean {
  return row.transaction_type === 'Transfer'
    && (!row.from_account_id || !row.to_account_id || row.from_account_id === row.to_account_id)
    && !row.source_product_id;
}

export function rowStatus(row: ReviewRow): RowStatus {
  if (row.status === 'imported') return 'imported';
  if (row.status === 'skipped') return 'skipped';
  if (row.status === 'linked' || row.linked_transaction_id) return 'linked';
  if (rowNeedsReview(row)) return 'needs_review';
  return 'ready';
}

export interface ReviewSummary {
  resolved: number;
  actionRequired: number;
  duplicates: number;
}

export function summarizeRows(rows: ReviewRow[]): ReviewSummary {
  const summary: ReviewSummary = { resolved: 0, actionRequired: 0, duplicates: 0 };
  for (const row of rows) {
    if (rowStatus(row) === 'needs_review') summary.actionRequired += 1;
    else summary.resolved += 1;
    if ((row.possible_matches?.length || 0) > 0) summary.duplicates += 1;
  }
  return summary;
}

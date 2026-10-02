import { reactive } from 'vue';
import axios from '@/services/api';
import { getStoredSession } from '@/services/session';

export type StatementStatus = 'pending' | 'processing' | 'completed' | 'failed';

interface TrackedStatement {
  id: number;
  filename: string;
  polls: number;
  nextPollAt: number;
}

export interface StatementNotification {
  id: number;
  statementId: number;
  filename: string;
  status: 'queued' | 'completed' | 'failed';
  message: string;
  reviewBatchId?: number | null;
}

const trackedStatements = reactive<TrackedStatement[]>([]);
const notifications = reactive<StatementNotification[]>([]);
let pollTimer: ReturnType<typeof setTimeout> | null = null;
let trackingUsername: string | null = null;

function storageKey(): string | null {
  const username = getStoredSession()?.user.username;
  return username ? `bank-statement-tracking:${username}` : null;
}

function persist(): void {
  const key = storageKey();
  if (!key) return;
  localStorage.setItem(key, JSON.stringify(trackedStatements.map(({ id, filename }) => ({ id, filename }))));
}

function notify(item: Omit<StatementNotification, 'id'>): void {
  notifications.push({ ...item, id: Date.now() + Math.floor(Math.random() * 1000) });
}

function removeTracked(statementId: number): void {
  const index = trackedStatements.findIndex((item) => item.id === statementId);
  if (index >= 0) trackedStatements.splice(index, 1);
  persist();
}

function schedule(): void {
  if (pollTimer) clearTimeout(pollTimer);
  if (!trackedStatements.length) {
    pollTimer = null;
    return;
  }
  const nextAt = Math.min(...trackedStatements.map((item) => item.nextPollAt));
  pollTimer = setTimeout(poll, Math.max(250, nextAt - Date.now()));
}

async function poll(): Promise<void> {
  if (!getStoredSession()) {
    trackedStatements.splice(0);
    notifications.splice(0);
    schedule();
    return;
  }
  const now = Date.now();
  const due = trackedStatements.filter((item) => item.nextPollAt <= now);
  await Promise.all(due.map(async (item) => {
    try {
      const response = await axios.get(`/bank-statements/details/${item.id}/`);
      const statement = response.data.statement;
      if (statement.processing_status === 'completed') {
        removeTracked(item.id);
        notify({
          statementId: item.id, filename: item.filename, status: 'completed',
          reviewBatchId: statement.review_batch_id,
          message: `${item.filename} is ready to review.`,
        });
        return;
      }
      if (statement.processing_status === 'failed') {
        removeTracked(item.id);
        notify({
          statementId: item.id, filename: item.filename, status: 'failed',
          message: statement.error_message || `${item.filename} could not be processed.`,
        });
        return;
      }
      item.polls += 1;
      item.nextPollAt = Date.now() + (item.polls < 10 ? 3000 : 10000);
    } catch {
      // Keep the job tracked across short API/container restarts, backing off
      // rather than treating an unavailable status endpoint as a failure.
      item.polls += 1;
      item.nextPollAt = Date.now() + 10000;
    }
  }));
  schedule();
}

export function startStatementTracking(): void {
  const key = storageKey();
  const username = getStoredSession()?.user.username ?? null;
  if (trackingUsername !== username) {
    trackedStatements.splice(0);
    notifications.splice(0);
    trackingUsername = username;
  }
  if (!key) {
    if (pollTimer) clearTimeout(pollTimer);
    pollTimer = null;
    return;
  }
  if (key && !trackedStatements.length) {
    try {
      const saved = JSON.parse(localStorage.getItem(key) || '[]');
      if (Array.isArray(saved)) {
        saved.forEach((item) => {
          if (Number.isInteger(item?.id) && typeof item.filename === 'string') {
            trackedStatements.push({ id: item.id, filename: item.filename, polls: 0, nextPollAt: Date.now() });
          }
        });
      }
    } catch {
      localStorage.removeItem(key);
    }
  }
  schedule();
}

export async function resumeRecentStatementTracking(): Promise<void> {
  const username = getStoredSession()?.user.username;
  if (!username) return;
  try {
    const response = await axios.get(`/bank-statements/user/${username}/?page_size=100`);
    const statements = response.data.statements || response.data.results || [];
    statements
      .filter((statement: { processing_status?: StatementStatus }) => statement.processing_status === 'pending' || statement.processing_status === 'processing')
      .forEach((statement: { id: number; original_filename: string }) => trackBankStatement({ id: statement.id, filename: statement.original_filename }, false));
  } catch {
    // Existing persisted IDs will resume when the API is reachable again.
  }
}

export function trackBankStatement(statement: { id: number; filename: string }, announce = true): void {
  if (!trackedStatements.some((item) => item.id === statement.id)) {
    trackedStatements.push({ id: statement.id, filename: statement.filename, polls: 0, nextPollAt: Date.now() + 3000 });
    persist();
    if (announce) {
      notify({ statementId: statement.id, filename: statement.filename, status: 'queued', message: `${statement.filename} was uploaded and is being processed. You can keep using the app.` });
    }
  }
  schedule();
}

export function dismissStatementNotification(notificationId: number): void {
  const index = notifications.findIndex((item) => item.id === notificationId);
  if (index >= 0) notifications.splice(index, 1);
}

export function activeStatementCount(): number {
  return trackedStatements.length;
}

export { notifications, trackedStatements };

import Database from 'better-sqlite3'
import { randomUUID } from 'node:crypto'
import { DB_PATH } from './db-config'
import { logger } from './logger'

export interface BranchRecord {
  branch_id: string
  thread_id: string
  parent_branch_id: string | null
  fork_message_index: number
  created_at: string
}

let _db: Database.Database | null = null

function getDb(): Database.Database {
  if (!_db) {
    _db = new Database(DB_PATH)
    _db.pragma('journal_mode = WAL')
    _db.pragma('foreign_keys = ON')
    _db.exec(`
      CREATE TABLE IF NOT EXISTS thread_branches (
        branch_id TEXT PRIMARY KEY,
        thread_id TEXT NOT NULL,
        parent_branch_id TEXT,
        fork_message_index INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (thread_id) REFERENCES threads(thread_id) ON DELETE CASCADE
      )
    `)
    _db.exec(`CREATE INDEX IF NOT EXISTS idx_thread_branches_thread_id ON thread_branches(thread_id)`)
    logger.thread.info('Branch store initialized', { path: DB_PATH })
  }
  return _db
}

/** スレッドに紐づく非 main 分岐一覧を created_at 昇順で取得 */
export function getBranches(threadId: string): BranchRecord[] {
  const db = getDb()
  return db.prepare(
    'SELECT * FROM thread_branches WHERE thread_id = ? ORDER BY created_at ASC',
  ).all(threadId) as BranchRecord[]
}

/** 指定した branchId が指定した threadId に属しているかを確認 */
export function branchBelongsToThread(threadId: string, branchId: string): boolean {
  const db = getDb()
  const row = db.prepare(
    'SELECT 1 FROM thread_branches WHERE thread_id = ? AND branch_id = ?',
  ).get(threadId, branchId) as { 1: number } | undefined
  return !!row
}

/** 分岐レコードを新規作成（branch_id は UUID で採番） */
export function createBranch(params: {
  threadId: string
  parentBranchId: string
  forkMessageIndex: number
}): BranchRecord {
  const db = getDb()
  const branchId = randomUUID()
  db.prepare(`
    INSERT INTO thread_branches (branch_id, thread_id, parent_branch_id, fork_message_index)
    VALUES (?, ?, ?, ?)
  `).run(branchId, params.threadId, params.parentBranchId, params.forkMessageIndex)
  const row = db.prepare('SELECT * FROM thread_branches WHERE branch_id = ?').get(branchId) as BranchRecord
  logger.thread.info('Branch created', { threadId: params.threadId, branchId })
  return row
}

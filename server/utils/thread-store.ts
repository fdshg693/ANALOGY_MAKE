import Database from 'better-sqlite3'
import { DB_PATH } from './db-config'
import { logger } from './logger'

export interface SearchSettings {
  enabled: boolean
  depth: 'basic' | 'advanced'
  maxResults: number
}

export type ResponseMode = 'ai' | 'echo'

export interface ThreadSettings {
  granularity: 'concise' | 'standard' | 'detailed'
  customInstruction: string
  search: SearchSettings
  responseMode: ResponseMode
  systemPromptOverride: string
}

export const DEFAULT_SEARCH_SETTINGS: SearchSettings = {
  enabled: true,
  depth: 'basic',
  maxResults: 3,
}

export const DEFAULT_SETTINGS: ThreadSettings = {
  granularity: 'standard',
  customInstruction: '',
  search: { ...DEFAULT_SEARCH_SETTINGS },
  responseMode: 'ai',
  systemPromptOverride: '',
}

interface ThreadRecord {
  thread_id: string
  title: string
  created_at: string  // ISO 8601
  updated_at: string  // ISO 8601
}

let _db: Database.Database | null = null

function getDb(): Database.Database {
  if (!_db) {
    _db = new Database(DB_PATH)
    _db.pragma('journal_mode = WAL')
    _db.exec(`
      CREATE TABLE IF NOT EXISTS threads (
        thread_id TEXT PRIMARY KEY,
        title TEXT NOT NULL DEFAULT '新しいチャット',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
      )
    `)
    try {
      _db.exec(`ALTER TABLE threads ADD COLUMN settings TEXT NOT NULL DEFAULT '{}'`)
    } catch {
      // カラム既存なら無視（SQLite は IF NOT EXISTS をサポートしない）
    }
    logger.thread.info('Database initialized', { path: DB_PATH, mode: 'WAL' })
  }
  return _db
}

/** スレッド一覧を更新日時降順で取得 */
export function getThreads(): ThreadRecord[] {
  const db = getDb()
  return db.prepare('SELECT * FROM threads ORDER BY updated_at DESC').all() as ThreadRecord[]
}

/** スレッドを新規登録（既存なら updated_at のみ更新） */
export function upsertThread(threadId: string, title?: string): void {
  const db = getDb()
  db.prepare(`
    INSERT INTO threads (thread_id, title)
    VALUES (?, ?)
    ON CONFLICT(thread_id) DO UPDATE SET updated_at = datetime('now')
  `).run(threadId, title ?? '新しいチャット')
  logger.thread.info('Thread upserted', { threadId })
}

/** スレッドタイトルを更新 */
export function updateThreadTitle(threadId: string, title: string): void {
  const db = getDb()
  db.prepare("UPDATE threads SET title = ?, updated_at = datetime('now') WHERE thread_id = ?").run(title, threadId)
  logger.thread.info('Thread title updated', { threadId, title })
}

/** スレッドの現在のタイトルを取得（存在しなければ null） */
export function getThreadTitle(threadId: string): string | null {
  const db = getDb()
  const row = db.prepare('SELECT title FROM threads WHERE thread_id = ?').get(threadId) as { title: string } | undefined
  return row?.title ?? null
}

/** スレッド設定を取得（未設定ならデフォルト値） */
export function getThreadSettings(threadId: string): ThreadSettings {
  const db = getDb()
  const row = db.prepare('SELECT settings FROM threads WHERE thread_id = ?').get(threadId) as { settings: string } | undefined
  if (!row?.settings || row.settings === '{}') return { ...DEFAULT_SETTINGS, search: { ...DEFAULT_SEARCH_SETTINGS } }
  try {
    const parsed = JSON.parse(row.settings) as Partial<ThreadSettings>
    return {
      ...DEFAULT_SETTINGS,
      ...parsed,
      search: { ...DEFAULT_SEARCH_SETTINGS, ...(parsed.search ?? {}) },
    }
  } catch {
    return { ...DEFAULT_SETTINGS, search: { ...DEFAULT_SEARCH_SETTINGS } }
  }
}

/** スレッド設定を更新 */
export function updateThreadSettings(threadId: string, settings: ThreadSettings): void {
  const db = getDb()
  db.prepare("UPDATE threads SET settings = ?, updated_at = datetime('now') WHERE thread_id = ?")
    .run(JSON.stringify(settings), threadId)
  logger.thread.info('Thread settings updated', { threadId })
}

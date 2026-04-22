import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createRequire } from 'node:module'
import { makeThreadSettings } from '../fixtures/settings'

// CJS モジュールを vitest のモック解決を回避して取得
const _require = createRequire(import.meta.url)
const RealDatabase = _require('better-sqlite3')

vi.mock('node:fs', () => ({
  mkdirSync: vi.fn(),
  appendFileSync: vi.fn(),
}))

let mockDb: any

async function importFresh() {
  vi.resetModules()
  vi.doMock('node:fs', () => ({ mkdirSync: vi.fn(), appendFileSync: vi.fn() }))
  vi.doMock('better-sqlite3', () => ({
    default: function () { return mockDb },
  }))
  return await import('../../server/utils/thread-store')
}

describe('thread-settings', () => {
  beforeEach(() => {
    mockDb = new RealDatabase(':memory:')
  })

  it('getThreadSettings — スレッドが存在しない場合はデフォルト設定を返す', async () => {
    const { getThreadSettings, DEFAULT_SETTINGS, DEFAULT_SEARCH_SETTINGS } = await importFresh()
    const settings = getThreadSettings('nonexistent-thread')
    expect(settings).toEqual(DEFAULT_SETTINGS)
    expect(settings.granularity).toBe('standard')
    expect(settings.customInstruction).toBe('')
    expect(settings.search).toEqual(DEFAULT_SEARCH_SETTINGS)
    expect(settings.responseMode).toBe('ai')
    expect(settings.systemPromptOverride).toBe('')
  })

  it('DEFAULT_SEARCH_SETTINGS — 既定値は enabled=true, depth=basic, maxResults=3', async () => {
    const { DEFAULT_SEARCH_SETTINGS } = await importFresh()
    expect(DEFAULT_SEARCH_SETTINGS).toEqual({ enabled: true, depth: 'basic', maxResults: 3 })
  })

  it('getThreadSettings — スレッドが存在するが settings が空 {} の場合はデフォルト設定を返す', async () => {
    const { upsertThread, getThreadSettings, DEFAULT_SETTINGS } = await importFresh()
    upsertThread('thread-1', 'テスト')
    const settings = getThreadSettings('thread-1')
    expect(settings).toEqual(DEFAULT_SETTINGS)
  })

  it('updateThreadSettings + getThreadSettings — 設定を保存・取得できる', async () => {
    const { upsertThread, updateThreadSettings, getThreadSettings } = await importFresh()
    upsertThread('thread-1', 'テスト')
    const newSettings = makeThreadSettings({
      granularity: 'detailed',
      customInstruction: 'テスト指示',
    })
    updateThreadSettings('thread-1', newSettings)
    const retrieved = getThreadSettings('thread-1')
    expect(retrieved).toEqual(newSettings)
  })

  it('updateThreadSettings — concise を設定して取得できる', async () => {
    const { upsertThread, updateThreadSettings, getThreadSettings } = await importFresh()
    upsertThread('thread-1', 'テスト')
    updateThreadSettings('thread-1', makeThreadSettings({
      granularity: 'concise',
    }))
    expect(getThreadSettings('thread-1').granularity).toBe('concise')
  })

  it('updateThreadSettings — detailed を設定して取得できる', async () => {
    const { upsertThread, updateThreadSettings, getThreadSettings } = await importFresh()
    upsertThread('thread-1', 'テスト')
    updateThreadSettings('thread-1', makeThreadSettings({
      granularity: 'detailed',
    }))
    expect(getThreadSettings('thread-1').granularity).toBe('detailed')
  })

  it('updateThreadSettings — search 設定を保存・取得できる', async () => {
    const { upsertThread, updateThreadSettings, getThreadSettings } = await importFresh()
    upsertThread('thread-1', 'テスト')
    const search = { enabled: false, depth: 'advanced' as const, maxResults: 7 }
    updateThreadSettings('thread-1', makeThreadSettings({
      search,
    }))
    const retrieved = getThreadSettings('thread-1')
    expect(retrieved.search).toEqual(search)
  })

  it('updateThreadSettings — responseMode=echo と systemPromptOverride を保存・取得できる', async () => {
    const { upsertThread, updateThreadSettings, getThreadSettings } = await importFresh()
    upsertThread('thread-1', 'テスト')
    updateThreadSettings('thread-1', makeThreadSettings({
      responseMode: 'echo',
      systemPromptOverride: 'デバッグ用前置き',
    }))
    const retrieved = getThreadSettings('thread-1')
    expect(retrieved.responseMode).toBe('echo')
    expect(retrieved.systemPromptOverride).toBe('デバッグ用前置き')
  })

  it('getThreadSettings — responseMode / systemPromptOverride を持たない旧 JSON でもデフォルトが補われる', async () => {
    const { getThreadSettings } = await importFresh()
    getThreadSettings('dummy')
    const legacyJson = JSON.stringify({
      granularity: 'standard',
      customInstruction: '',
      search: { enabled: true, depth: 'basic', maxResults: 3 },
    })
    mockDb.prepare(
      "INSERT INTO threads (thread_id, title, settings) VALUES (?, ?, ?)"
    ).run('thread-legacy-r', 'Legacy Response', legacyJson)
    const settings = getThreadSettings('thread-legacy-r')
    expect(settings.responseMode).toBe('ai')
    expect(settings.systemPromptOverride).toBe('')
  })

  it('getThreadSettings — 後方互換: search フィールドを持たない旧 JSON でもデフォルトがマージされる', async () => {
    const { getThreadSettings, DEFAULT_SEARCH_SETTINGS } = await importFresh()
    // テーブル初期化
    getThreadSettings('dummy')
    const legacyJson = JSON.stringify({ granularity: 'detailed', customInstruction: '旧設定' })
    mockDb.prepare(
      "INSERT INTO threads (thread_id, title, settings) VALUES (?, ?, ?)"
    ).run('thread-legacy', 'Legacy', legacyJson)
    const settings = getThreadSettings('thread-legacy')
    expect(settings.granularity).toBe('detailed')
    expect(settings.customInstruction).toBe('旧設定')
    expect(settings.search).toEqual(DEFAULT_SEARCH_SETTINGS)
  })

  it('getThreadSettings — 部分的な search フィールドでもデフォルトがマージされる', async () => {
    const { getThreadSettings } = await importFresh()
    getThreadSettings('dummy')
    const partialJson = JSON.stringify({
      granularity: 'standard',
      customInstruction: '',
      search: { depth: 'advanced' },
    })
    mockDb.prepare(
      "INSERT INTO threads (thread_id, title, settings) VALUES (?, ?, ?)"
    ).run('thread-partial', 'Partial', partialJson)
    const settings = getThreadSettings('thread-partial')
    expect(settings.search).toEqual({ enabled: true, depth: 'advanced', maxResults: 3 })
  })

  it('getThreadSettings — settings カラムに不正な JSON がある場合はデフォルト設定を返す', async () => {
    const { getThreadSettings, DEFAULT_SETTINGS } = await importFresh()
    // getDb() を呼び出してテーブルを初期化
    getThreadSettings('dummy')
    // テーブル初期化後に直接不正な JSON を挿入
    mockDb.prepare(
      "INSERT INTO threads (thread_id, title, settings) VALUES (?, ?, ?)"
    ).run('thread-bad', 'Bad JSON', '{invalid json!!!}')
    const settings = getThreadSettings('thread-bad')
    expect(settings).toEqual(DEFAULT_SETTINGS)
  })

  it('updateThreadSettings — customInstruction を正しく保持する', async () => {
    const { upsertThread, updateThreadSettings, getThreadSettings } = await importFresh()
    upsertThread('thread-1', 'テスト')
    const instruction = 'ユーザーに対して丁寧語で回答してください。専門用語は避けてください。'
    updateThreadSettings('thread-1', makeThreadSettings({
      customInstruction: instruction,
    }))
    const retrieved = getThreadSettings('thread-1')
    expect(retrieved.customInstruction).toBe(instruction)
    expect(retrieved.granularity).toBe('standard')
  })
})

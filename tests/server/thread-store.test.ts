import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createRequire } from 'node:module'

// CJS モジュールを vitest のモック解決を回避して取得
const _require = createRequire(import.meta.url)
const RealDatabase = _require('better-sqlite3')

vi.mock('node:fs', () => ({
  mkdirSync: vi.fn(),
}))

let mockDb: any

async function importFresh() {
  vi.resetModules()
  vi.doMock('node:fs', () => ({ mkdirSync: vi.fn() }))
  vi.doMock('better-sqlite3', () => ({
    default: function () { return mockDb },
  }))
  return await import('../../server/utils/thread-store')
}

describe('thread-store', () => {
  beforeEach(() => {
    mockDb = new RealDatabase(':memory:')
  })

  it('getThreads — 空の場合は空配列を返す', async () => {
    const { getThreads } = await importFresh()
    expect(getThreads()).toEqual([])
  })

  it('upsertThread — 新規スレッドを登録して取得できる', async () => {
    const { upsertThread, getThreads } = await importFresh()
    upsertThread('thread-1', 'テストタイトル')
    const threads = getThreads()
    expect(threads).toHaveLength(1)
    expect(threads[0].thread_id).toBe('thread-1')
    expect(threads[0].title).toBe('テストタイトル')
  })

  it('upsertThread — デフォルトタイトル', async () => {
    const { upsertThread, getThreads } = await importFresh()
    upsertThread('thread-1')
    const threads = getThreads()
    expect(threads[0].title).toBe('新しいチャット')
  })

  it('upsertThread — 既存スレッドはタイトルを保持', async () => {
    const { upsertThread, getThreads } = await importFresh()
    upsertThread('thread-1', '元のタイトル')
    upsertThread('thread-1', '新しいタイトル')
    const threads = getThreads()
    expect(threads[0].title).toBe('元のタイトル')
  })

  it('updateThreadTitle — タイトルを変更できる', async () => {
    const { upsertThread, updateThreadTitle, getThreadTitle } = await importFresh()
    upsertThread('thread-1', '元のタイトル')
    updateThreadTitle('thread-1', '更新後タイトル')
    expect(getThreadTitle('thread-1')).toBe('更新後タイトル')
  })

  it('getThreadTitle — 存在するスレッドのタイトルを返す', async () => {
    const { upsertThread, getThreadTitle } = await importFresh()
    upsertThread('thread-1', 'テストタイトル')
    expect(getThreadTitle('thread-1')).toBe('テストタイトル')
  })

  it('getThreadTitle — 存在しないスレッドには null を返す', async () => {
    const { getThreadTitle } = await importFresh()
    expect(getThreadTitle('nonexistent')).toBeNull()
  })

  it('getThreads — updated_at 降順でソートされる', async () => {
    const { upsertThread, updateThreadTitle, getThreads } = await importFresh()
    upsertThread('thread-1', 'スレッド1')
    upsertThread('thread-2', 'スレッド2')
    updateThreadTitle('thread-1', 'スレッド1更新')
    const threads = getThreads()
    expect(threads[0].thread_id).toBe('thread-1')
    expect(threads[1].thread_id).toBe('thread-2')
  })
})

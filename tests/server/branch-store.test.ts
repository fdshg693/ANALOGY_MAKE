import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createRequire } from 'node:module'

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
  const threadStore = await import('../../server/utils/thread-store')
  const branchStore = await import('../../server/utils/branch-store')
  return { ...threadStore, ...branchStore }
}

describe('branch-store', () => {
  beforeEach(() => {
    mockDb = new RealDatabase(':memory:')
  })

  it('getBranches — 存在しない threadId では空配列を返す', async () => {
    const { getBranches, upsertThread } = await importFresh()
    // thread-store 側でテーブル作成を先に走らせる（FK のため thread を先に用意）
    upsertThread('dummy-thread', 'dummy')
    expect(getBranches('nonexistent')).toEqual([])
  })

  it('createBranch — 新規分岐を作成し、全フィールドが埋まったレコードを返す', async () => {
    const { createBranch, upsertThread } = await importFresh()
    upsertThread('thread-1', 'テスト')
    const branch = createBranch({
      threadId: 'thread-1',
      parentBranchId: 'main',
      forkMessageIndex: 3,
    })
    expect(typeof branch.branch_id).toBe('string')
    expect(branch.branch_id.length).toBeGreaterThan(0)
    expect(branch.thread_id).toBe('thread-1')
    expect(branch.parent_branch_id).toBe('main')
    expect(branch.fork_message_index).toBe(3)
    expect(typeof branch.created_at).toBe('string')
    expect(branch.created_at.length).toBeGreaterThan(0)
  })

  it('getBranches — create 後は作成したレコード 1 件を返す', async () => {
    const { createBranch, getBranches, upsertThread } = await importFresh()
    upsertThread('thread-1', 'テスト')
    const created = createBranch({
      threadId: 'thread-1',
      parentBranchId: 'main',
      forkMessageIndex: 2,
    })
    const list = getBranches('thread-1')
    expect(list).toHaveLength(1)
    expect(list[0].branch_id).toBe(created.branch_id)
    expect(list[0].fork_message_index).toBe(2)
  })

  it('branchBelongsToThread — create 後の branchId に対して true', async () => {
    const { createBranch, branchBelongsToThread, upsertThread } = await importFresh()
    upsertThread('thread-1', 'テスト')
    const created = createBranch({
      threadId: 'thread-1',
      parentBranchId: 'main',
      forkMessageIndex: 0,
    })
    expect(branchBelongsToThread('thread-1', created.branch_id)).toBe(true)
  })

  it('branchBelongsToThread — 未知の branchId には false', async () => {
    const { branchBelongsToThread, upsertThread } = await importFresh()
    upsertThread('thread-1', 'テスト')
    expect(branchBelongsToThread('thread-1', 'unknown-uuid')).toBe(false)
  })

  it("branchBelongsToThread — 'main' は thread_branches に存在しないので false", async () => {
    const { branchBelongsToThread, upsertThread } = await importFresh()
    upsertThread('thread-1', 'テスト')
    expect(branchBelongsToThread('thread-1', 'main')).toBe(false)
  })

  it('getBranches — 複数作成時に created_at 昇順で全件返す', async () => {
    const { createBranch, getBranches, upsertThread } = await importFresh()
    upsertThread('thread-1', 'テスト')
    const a = createBranch({ threadId: 'thread-1', parentBranchId: 'main', forkMessageIndex: 1 })
    const b = createBranch({ threadId: 'thread-1', parentBranchId: 'main', forkMessageIndex: 2 })
    const c = createBranch({ threadId: 'thread-1', parentBranchId: a.branch_id, forkMessageIndex: 3 })

    const list = getBranches('thread-1')
    expect(list).toHaveLength(3)
    // created_at 昇順 (= 挿入順) を期待
    const ids = list.map((r) => r.branch_id)
    expect(ids).toEqual([a.branch_id, b.branch_id, c.branch_id])
    expect(list.map((r) => r.fork_message_index)).toEqual([1, 2, 3])
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'

vi.stubGlobal('ref', ref)

declare var __NUXT_CLIENT__: boolean | undefined
globalThis.__NUXT_CLIENT__ = false

const mockLocalStorage = {
  getItem: vi.fn().mockReturnValue(null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
}
vi.stubGlobal('localStorage', mockLocalStorage)

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

vi.stubGlobal('crypto', { randomUUID: () => 'new-thread-uuid' })

async function importFresh() {
  vi.resetModules()
  return await import('~/app/composables/useThreads')
}

describe('useThreads', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLocalStorage.getItem.mockReturnValue(null)
    globalThis.__NUXT_CLIENT__ = false
  })

  it('初期状態', async () => {
    const { useThreads } = await importFresh()
    const { threads, activeThreadId, isLoadingThreads } = useThreads()
    expect(threads.value).toEqual([])
    expect(activeThreadId.value).toBe('')
    expect(isLoadingThreads.value).toBe(false)
  })

  it('loadThreads — 正常系', async () => {
    const { useThreads } = await importFresh()
    const { threads, isLoadingThreads, loadThreads } = useThreads()

    mockFetch.mockResolvedValue({
      json: () => Promise.resolve({
        threads: [
          { threadId: 'id-1', title: 'スレッド1', createdAt: '2025-01-01', updatedAt: '2025-01-02' },
        ],
      }),
    })

    await loadThreads()

    expect(threads.value).toHaveLength(1)
    expect(threads.value[0].threadId).toBe('id-1')
    expect(isLoadingThreads.value).toBe(false)
  })

  it('loadThreads — 失敗時は空リストのまま', async () => {
    const { useThreads } = await importFresh()
    const { threads, isLoadingThreads, loadThreads } = useThreads()

    mockFetch.mockRejectedValue(new Error('Network error'))

    await loadThreads()

    expect(threads.value).toEqual([])
    expect(isLoadingThreads.value).toBe(false)
  })

  it('createNewThread — 新しいスレッドを先頭に追加', async () => {
    const { useThreads } = await importFresh()
    const { threads, activeThreadId, createNewThread } = useThreads()

    const newId = createNewThread()

    expect(newId).toBe('new-thread-uuid')
    expect(activeThreadId.value).toBe('new-thread-uuid')
    expect(threads.value).toHaveLength(1)
    expect(threads.value[0].threadId).toBe('new-thread-uuid')
    expect(threads.value[0].title).toBe('新しいチャット')
  })

  it('createNewThread — クライアント側で localStorage に保存', async () => {
    globalThis.__NUXT_CLIENT__ = true
    const { useThreads } = await importFresh()
    const { createNewThread } = useThreads()

    createNewThread()

    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('analogy-threadId', 'new-thread-uuid')
    globalThis.__NUXT_CLIENT__ = false
  })

  it('setActiveThread — activeThreadId を設定', async () => {
    const { useThreads } = await importFresh()
    const { activeThreadId, setActiveThread } = useThreads()

    setActiveThread('target-id')

    expect(activeThreadId.value).toBe('target-id')
  })

  it('setActiveThread — クライアント側で localStorage に保存', async () => {
    globalThis.__NUXT_CLIENT__ = true
    const { useThreads } = await importFresh()
    const { setActiveThread } = useThreads()

    setActiveThread('target-id')

    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('analogy-threadId', 'target-id')
    globalThis.__NUXT_CLIENT__ = false
  })

  it('initActiveThread — localStorage からアクティブスレッドを復元', async () => {
    globalThis.__NUXT_CLIENT__ = true
    mockLocalStorage.getItem.mockReturnValue('stored-id')
    const { useThreads } = await importFresh()
    const { activeThreadId, initActiveThread } = useThreads()

    initActiveThread()

    expect(activeThreadId.value).toBe('stored-id')
    globalThis.__NUXT_CLIENT__ = false
  })

  it('initActiveThread — localStorage に値がない場合は変更なし', async () => {
    globalThis.__NUXT_CLIENT__ = true
    mockLocalStorage.getItem.mockReturnValue(null)
    const { useThreads } = await importFresh()
    const { activeThreadId, initActiveThread } = useThreads()

    initActiveThread()

    expect(activeThreadId.value).toBe('')
    globalThis.__NUXT_CLIENT__ = false
  })

  it('updateLocalTitle — 既存スレッドのタイトルを更新', async () => {
    const { useThreads } = await importFresh()
    const { threads, updateLocalTitle } = useThreads()

    threads.value = [
      { threadId: 'id-1', title: '元のタイトル', createdAt: '', updatedAt: '' },
    ]

    updateLocalTitle('id-1', '新しいタイトル')

    expect(threads.value[0].title).toBe('新しいタイトル')
  })

  it('updateLocalTitle — 存在しないスレッドは無視', async () => {
    const { useThreads } = await importFresh()
    const { threads, updateLocalTitle } = useThreads()

    threads.value = [
      { threadId: 'id-1', title: '元のタイトル', createdAt: '', updatedAt: '' },
    ]

    updateLocalTitle('nonexistent', '新しいタイトル')

    expect(threads.value[0].title).toBe('元のタイトル')
  })
})

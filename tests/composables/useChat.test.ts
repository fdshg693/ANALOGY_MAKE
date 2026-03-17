import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'

// Nuxt の auto-import を模倣
vi.stubGlobal('ref', ref)

// import.meta.client は vitest.config.ts の define で
// (globalThis.__NUXT_CLIENT__ ?? false) に置換される
declare var __NUXT_CLIENT__: boolean | undefined
globalThis.__NUXT_CLIENT__ = false

// localStorage のモック
const mockLocalStorage = {
  getItem: vi.fn().mockReturnValue(null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
}
vi.stubGlobal('localStorage', mockLocalStorage)

// parseSSEStream をモック
vi.mock('../../app/utils/sse-parser', () => ({
  parseSSEStream: vi.fn(),
}))

// fetch をモック
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// crypto.randomUUID をモック
vi.stubGlobal('crypto', { randomUUID: () => 'mock-uuid' })

import { useChat } from '~/app/composables/useChat'
import { parseSSEStream } from '~/app/utils/sse-parser'

describe('useChat', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLocalStorage.getItem.mockReturnValue(null)
    globalThis.__NUXT_CLIENT__ = false
  })

  it('初期状態', () => {
    const { messages, isLoading, isStreaming, threadId } = useChat()

    expect(messages.value).toEqual([])
    expect(isLoading.value).toBe(false)
    expect(isStreaming.value).toBe(false)
    expect(threadId.value).toBe('mock-uuid')
  })

  it('sendMessage — 正常系', async () => {
    vi.mocked(parseSSEStream).mockImplementation(async (_stream, callbacks) => {
      callbacks.onToken('Hello')
      callbacks.onToken(' World')
      callbacks.onDone()
    })

    mockFetch.mockResolvedValue({
      ok: true,
      body: 'mock-stream',
    })

    const { messages, isLoading, isStreaming, sendMessage } = useChat()

    await sendMessage('テスト入力')

    expect(messages.value).toHaveLength(2)
    expect(messages.value[0].role).toBe('user')
    expect(messages.value[0].content).toBe('テスト入力')
    expect(messages.value[1].role).toBe('assistant')
    expect(messages.value[1].content).toBe('Hello World')
    expect(isLoading.value).toBe(false)
    expect(isStreaming.value).toBe(false)

    expect(mockFetch).toHaveBeenCalledWith('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'テスト入力', threadId: 'mock-uuid' }),
      signal: expect.any(AbortSignal),
    })
  })

  it('sendMessage — 空入力ガード', async () => {
    const { messages, sendMessage } = useChat()

    await sendMessage('')

    expect(messages.value).toEqual([])
    expect(mockFetch).not.toHaveBeenCalled()
  })

  it('sendMessage — SSE エラー', async () => {
    vi.mocked(parseSSEStream).mockImplementation(async (_stream, callbacks) => {
      callbacks.onError('API error')
    })

    mockFetch.mockResolvedValue({
      ok: true,
      body: 'mock-stream',
    })

    const { messages, isLoading, sendMessage } = useChat()

    await sendMessage('テスト')

    const assistantMsg = messages.value[1]
    expect(assistantMsg.content).toContain('⚠ エラーが発生しました: API error')
    expect(assistantMsg.isError).toBe(true)
    expect(isLoading.value).toBe(false)
  })

  it('sendMessage — 通信エラー', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'))

    const { messages, isLoading, sendMessage } = useChat()

    await sendMessage('テスト')

    const assistantMsg = messages.value[1]
    expect(assistantMsg.content).toContain('⚠ 通信エラーが発生しました')
    expect(assistantMsg.isError).toBe(true)
    expect(isLoading.value).toBe(false)
  })

  it('sendMessage — 空応答フォールバック', async () => {
    vi.mocked(parseSSEStream).mockImplementation(async (_stream, callbacks) => {
      callbacks.onDone()
    })

    mockFetch.mockResolvedValue({
      ok: true,
      body: 'mock-stream',
    })

    const { messages, sendMessage } = useChat()

    await sendMessage('テスト')

    const assistantMsg = messages.value[1]
    expect(assistantMsg.content).toBe('（応答を取得できませんでした）')
    expect(assistantMsg.isError).toBeUndefined()
  })

  it('abort — ストリーミング中の中断で部分テキストが保持される', async () => {
    vi.mocked(parseSSEStream).mockImplementation(async (_stream, callbacks) => {
      callbacks.onToken('部分テ')
      throw new DOMException('The operation was aborted.', 'AbortError')
    })

    mockFetch.mockResolvedValue({
      ok: true,
      body: 'mock-stream',
    })

    const { messages, isLoading, isStreaming, sendMessage } = useChat()

    await sendMessage('テスト')

    // 部分テキストが保持されている（エラー扱いではない）
    expect(messages.value[1].content).toBe('部分テ')
    expect(messages.value[1].isError).toBeUndefined()
    expect(isLoading.value).toBe(false)
    expect(isStreaming.value).toBe(false)
  })

  it('abort 関数が返される', () => {
    const result = useChat()
    expect(result.abort).toBeDefined()
    expect(typeof result.abort).toBe('function')
  })

  describe('threadId の永続化', () => {
    it('import.meta.client が false の場合、crypto.randomUUID で生成', () => {
      globalThis.__NUXT_CLIENT__ = false
      mockLocalStorage.getItem.mockReturnValue(null)

      const { threadId } = useChat()
      expect(threadId.value).toBe('mock-uuid')
    })

    it('import.meta.client が true で localStorage に threadId がない場合、新規生成して保存', () => {
      globalThis.__NUXT_CLIENT__ = true
      mockLocalStorage.getItem.mockReturnValue(null)

      const { threadId } = useChat()
      expect(threadId.value).toBe('mock-uuid')
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('analogy-threadId', 'mock-uuid')

      globalThis.__NUXT_CLIENT__ = false
    })

    it('import.meta.client が true で localStorage に threadId がある場合、復元', () => {
      globalThis.__NUXT_CLIENT__ = true
      mockLocalStorage.getItem.mockReturnValue('stored-thread-id')

      const { threadId } = useChat()
      expect(threadId.value).toBe('stored-thread-id')

      globalThis.__NUXT_CLIENT__ = false
    })
  })

  describe('履歴復元', () => {
    it('import.meta.client が true で localStorage に threadId がある場合、履歴を取得', async () => {
      globalThis.__NUXT_CLIENT__ = true
      mockLocalStorage.getItem.mockReturnValue('stored-thread-id')

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          messages: [
            { role: 'user', content: 'テスト' },
            { role: 'assistant', content: '回答' },
          ],
        }),
      })

      const { messages, isLoading } = useChat()

      // loadHistory is called but not awaited, so wait for it
      await vi.waitFor(() => {
        expect(isLoading.value).toBe(false)
      })

      expect(mockFetch).toHaveBeenCalledWith('/api/chat/history?threadId=stored-thread-id')
      expect(messages.value).toEqual([
        { role: 'user', content: 'テスト' },
        { role: 'assistant', content: '回答' },
      ])

      globalThis.__NUXT_CLIENT__ = false
    })

    it('履歴取得失敗時は空チャットで開始', async () => {
      globalThis.__NUXT_CLIENT__ = true
      mockLocalStorage.getItem.mockReturnValue('stored-thread-id')

      mockFetch.mockRejectedValue(new Error('Network error'))

      const { messages, isLoading } = useChat()

      await vi.waitFor(() => {
        expect(isLoading.value).toBe(false)
      })

      expect(messages.value).toEqual([])

      globalThis.__NUXT_CLIENT__ = false
    })
  })
})

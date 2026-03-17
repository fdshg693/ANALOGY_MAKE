import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'

// Nuxt の auto-import を模倣
vi.stubGlobal('ref', ref)

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
})

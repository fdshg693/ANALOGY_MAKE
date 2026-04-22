import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AIMessageChunk } from '@langchain/core/messages'

// Mock h3 functions
const mockEventStream = {
  push: vi.fn().mockResolvedValue(undefined),
  close: vi.fn().mockResolvedValue(undefined),
  send: vi.fn().mockResolvedValue(undefined),
  onClosed: vi.fn(),
}

vi.mock('h3', () => ({
  defineEventHandler: (handler: Function) => handler,
  readBody: vi.fn(),
  createError: (opts: { statusCode: number; statusMessage: string }) => {
    const error = new Error(opts.statusMessage) as Error & { statusCode: number; statusMessage: string }
    error.statusCode = opts.statusCode
    error.statusMessage = opts.statusMessage
    return error
  },
  createEventStream: vi.fn(() => mockEventStream),
}))

// Mock the analogy agent
const mockGraph = {
  stream: vi.fn(),
  getState: vi.fn().mockResolvedValue({ values: { messages: [] } }),
}

vi.mock('../../server/utils/analogy-agent', () => ({
  getAnalogyAgent: () => Promise.resolve(mockGraph),
}))

// Mock thread-store
vi.mock('../../server/utils/thread-store', () => ({
  upsertThread: vi.fn(),
  getThreadTitle: vi.fn().mockReturnValue('新しいチャット'),
  updateThreadTitle: vi.fn(),
  getThreadSettings: vi.fn().mockReturnValue({
    granularity: 'standard',
    customInstruction: '',
    search: { enabled: true, depth: 'basic', maxResults: 3 },
  }),
}))

vi.stubGlobal('useRuntimeConfig', () => ({ openaiApiKey: 'test-key', tavilyApiKey: 'test-tavily-key' }))

// Import handler after mocks are set up
import handler from '~/server/api/chat.post'
import { readBody } from 'h3'

describe('POST /api/chat', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('バリデーション', () => {
    it('message 欠落で 400 エラー', async () => {
      vi.mocked(readBody).mockResolvedValue({ threadId: 'test-id' })

      await expect(handler({} as any)).rejects.toMatchObject({
        statusCode: 400,
        statusMessage: 'message is required',
      })
    })

    it('threadId 欠落で 400 エラー', async () => {
      vi.mocked(readBody).mockResolvedValue({ message: 'hello' })

      await expect(handler({} as any)).rejects.toMatchObject({
        statusCode: 400,
        statusMessage: 'threadId is required',
      })
    })

    it('message が文字列でない場合に 400 エラー', async () => {
      vi.mocked(readBody).mockResolvedValue({ message: 123, threadId: 'test-id' })

      await expect(handler({} as any)).rejects.toMatchObject({
        statusCode: 400,
        statusMessage: 'message is required',
      })
    })
  })

  describe('正常系', () => {
    it('モックエージェントからのストリーム → SSE イベント形式', async () => {
      vi.mocked(readBody).mockResolvedValue({ message: 'test', threadId: 'thread-1' })

      // Create an async iterable that yields AIMessageChunk pairs
      const chunks = [
        [new AIMessageChunk({ content: 'Hello' }), { langgraph_node: 'caseSearch' }],
        [new AIMessageChunk({ content: ' World' }), { langgraph_node: 'caseSearch' }],
      ]

      mockGraph.stream.mockResolvedValue({
        async *[Symbol.asyncIterator]() {
          for (const chunk of chunks) {
            yield chunk
          }
        },
      })

      await handler({} as any)

      // Wait for the async IIFE to complete
      await vi.waitFor(() => {
        expect(mockEventStream.push).toHaveBeenCalledWith({
          event: 'done',
          data: '{}',
        })
      })

      expect(mockEventStream.push).toHaveBeenCalledWith({
        event: 'token',
        data: JSON.stringify({ content: 'Hello' }),
      })
      expect(mockEventStream.push).toHaveBeenCalledWith({
        event: 'token',
        data: JSON.stringify({ content: ' World' }),
      })
      expect(mockEventStream.close).toHaveBeenCalled()
      expect(mockEventStream.send).toHaveBeenCalled()
    })

    it('abstraction ノードの出力はストリーミングされない', async () => {
      vi.mocked(readBody).mockResolvedValue({ message: 'test', threadId: 'thread-1' })

      const chunks = [
        [new AIMessageChunk({ content: 'abstracted problem' }), { langgraph_node: 'abstraction' }],
        [new AIMessageChunk({ content: 'Here are the cases' }), { langgraph_node: 'caseSearch' }],
      ]

      mockGraph.stream.mockResolvedValue({
        async *[Symbol.asyncIterator]() {
          for (const chunk of chunks) {
            yield chunk
          }
        },
      })

      await handler({} as any)

      await vi.waitFor(() => {
        expect(mockEventStream.push).toHaveBeenCalledWith({
          event: 'done',
          data: '{}',
        })
      })

      // caseSearch node output is streamed
      expect(mockEventStream.push).toHaveBeenCalledWith({
        event: 'token',
        data: JSON.stringify({ content: 'Here are the cases' }),
      })

      // abstraction node output is NOT streamed
      const tokenCalls = mockEventStream.push.mock.calls.filter(
        (call: any) => call[0].event === 'token'
      )
      expect(tokenCalls).toHaveLength(1)
    })

    it('configurable に settings が含まれる', async () => {
      vi.mocked(readBody).mockResolvedValue({ message: 'test', threadId: 'thread-1' })

      const chunks = [
        [new AIMessageChunk({ content: 'test' }), { langgraph_node: 'caseSearch' }],
      ]

      mockGraph.stream.mockResolvedValue({
        async *[Symbol.asyncIterator]() {
          for (const chunk of chunks) {
            yield chunk
          }
        },
      })

      await handler({} as any)

      await vi.waitFor(() => {
        expect(mockEventStream.push).toHaveBeenCalledWith({
          event: 'done',
          data: '{}',
        })
      })

      expect(mockGraph.stream).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          configurable: expect.objectContaining({
            settings: {
              granularity: 'standard',
              customInstruction: '',
              search: { enabled: true, depth: 'basic', maxResults: 3 },
            },
          }),
        }),
      )
    })
  })

  describe('search_results SSE', () => {
    it('最終メッセージに searchResults があれば search_results イベントを送信', async () => {
      vi.mocked(readBody).mockResolvedValue({ message: 'test', threadId: 'thread-1' })

      const chunks = [
        [new AIMessageChunk({ content: 'ok' }), { langgraph_node: 'caseSearch' }],
      ]
      mockGraph.stream.mockResolvedValue({
        async *[Symbol.asyncIterator]() {
          for (const chunk of chunks) yield chunk
        },
      })
      const results = [{ title: 'A', url: 'https://a.test', content: 'a' }]
      mockGraph.getState.mockResolvedValue({
        values: {
          messages: [
            { type: 'human', content: 'q' },
            { type: 'ai', content: 'ok', additional_kwargs: { searchResults: results } },
          ],
        },
      })

      await handler({} as any)

      await vi.waitFor(() => {
        expect(mockEventStream.push).toHaveBeenCalledWith({
          event: 'done',
          data: '{}',
        })
      })

      expect(mockEventStream.push).toHaveBeenCalledWith({
        event: 'search_results',
        data: JSON.stringify({ results }),
      })
    })

    it('最終メッセージに searchResults が無ければ search_results イベントを送らない', async () => {
      vi.mocked(readBody).mockResolvedValue({ message: 'test', threadId: 'thread-1' })

      const chunks = [
        [new AIMessageChunk({ content: 'ok' }), { langgraph_node: 'caseSearch' }],
      ]
      mockGraph.stream.mockResolvedValue({
        async *[Symbol.asyncIterator]() {
          for (const chunk of chunks) yield chunk
        },
      })
      mockGraph.getState.mockResolvedValue({
        values: {
          messages: [
            { type: 'human', content: 'q' },
            { type: 'ai', content: 'ok' },
          ],
        },
      })

      await handler({} as any)

      await vi.waitFor(() => {
        expect(mockEventStream.push).toHaveBeenCalledWith({
          event: 'done',
          data: '{}',
        })
      })

      const searchCalls = mockEventStream.push.mock.calls.filter(
        (call: any) => call[0].event === 'search_results',
      )
      expect(searchCalls).toHaveLength(0)
    })

    it('エラー時は search_results イベントを送らない', async () => {
      vi.mocked(readBody).mockResolvedValue({ message: 'test', threadId: 'thread-1' })
      mockGraph.stream.mockRejectedValue(new Error('boom'))

      await handler({} as any)

      await vi.waitFor(() => {
        expect(mockEventStream.push).toHaveBeenCalledWith(
          expect.objectContaining({ event: 'error' }),
        )
      })

      const searchCalls = mockEventStream.push.mock.calls.filter(
        (call: any) => call[0].event === 'search_results',
      )
      expect(searchCalls).toHaveLength(0)
    })
  })

  describe('エラー系', () => {
    it('エージェント呼び出し失敗 → error イベント送信', async () => {
      vi.mocked(readBody).mockResolvedValue({ message: 'test', threadId: 'thread-1' })

      mockGraph.stream.mockRejectedValue(new Error('API key invalid'))

      await handler({} as any)

      // Wait for the async IIFE to complete
      await vi.waitFor(() => {
        expect(mockEventStream.push).toHaveBeenCalledWith({
          event: 'error',
          data: JSON.stringify({ message: 'API key invalid' }),
        })
      })

      expect(mockEventStream.close).toHaveBeenCalled()
      expect(mockEventStream.send).toHaveBeenCalled()
    })
  })
})

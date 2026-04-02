import { describe, it, expect, vi, beforeEach } from 'vitest'
import { HumanMessage, AIMessage } from '@langchain/core/messages'

// Mock h3 functions
vi.mock('h3', () => ({
  defineEventHandler: (handler: Function) => handler,
  getQuery: vi.fn(),
  createError: (opts: { statusCode: number; statusMessage: string }) => {
    const error = new Error(opts.statusMessage) as Error & { statusCode: number; statusMessage: string }
    error.statusCode = opts.statusCode
    error.statusMessage = opts.statusMessage
    return error
  },
}))

// Mock the analogy agent
const mockGraph = {
  getState: vi.fn(),
}

vi.mock('../../server/utils/analogy-agent', () => ({
  getAnalogyAgent: () => Promise.resolve(mockGraph),
}))

// Import handler after mocks are set up
import handler from '~/server/api/chat/history.get'
import { getQuery } from 'h3'

describe('GET /api/chat/history', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('threadId 欠落で 400 エラー', async () => {
    vi.mocked(getQuery).mockReturnValue({})

    await expect(handler({} as any)).rejects.toMatchObject({
      statusCode: 400,
      statusMessage: 'threadId is required',
    })
  })

  it('threadId が文字列でない場合に 400 エラー', async () => {
    vi.mocked(getQuery).mockReturnValue({ threadId: 123 as any })

    await expect(handler({} as any)).rejects.toMatchObject({
      statusCode: 400,
      statusMessage: 'threadId is required',
    })
  })

  it('チェックポイントにメッセージあり → 正しいフォーマットで返却', async () => {
    vi.mocked(getQuery).mockReturnValue({ threadId: 'thread-1' })

    mockGraph.getState.mockResolvedValue({
      values: {
        messages: [
          new HumanMessage('こんにちは'),
          new AIMessage('はい、こんにちは！'),
          new HumanMessage('質問です'),
          new AIMessage('回答です'),
        ],
      },
    })

    const result = await handler({} as any)

    expect(result).toEqual({
      messages: [
        { role: 'user', content: 'こんにちは' },
        { role: 'assistant', content: 'はい、こんにちは！' },
        { role: 'user', content: '質問です' },
        { role: 'assistant', content: '回答です' },
      ],
    })

    expect(mockGraph.getState).toHaveBeenCalledWith({
      configurable: { thread_id: 'thread-1' },
    })
  })

  it('チェックポイントが空 → 空配列を返却', async () => {
    vi.mocked(getQuery).mockReturnValue({ threadId: 'thread-1' })

    mockGraph.getState.mockResolvedValue({
      values: {},
    })

    const result = await handler({} as any)
    expect(result).toEqual({ messages: [] })
  })

  it('getState がエラー → 空配列を返却', async () => {
    vi.mocked(getQuery).mockReturnValue({ threadId: 'thread-1' })

    mockGraph.getState.mockRejectedValue(new Error('Database error'))

    const result = await handler({} as any)
    expect(result).toEqual({ messages: [] })
  })
})

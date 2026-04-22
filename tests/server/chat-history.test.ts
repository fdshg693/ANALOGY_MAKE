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

  it('type プロパティベースの型チェックでデシリアライズ後メッセージを正しく処理', async () => {
    vi.mocked(getQuery).mockReturnValue({ threadId: 'thread-1' })

    // チェックポイントからの復元を模倣:
    // type プロパティのみを持つプレーンオブジェクト（instanceof は通らない）
    const mockHumanMsg = {
      type: 'human',
      content: 'ユーザーメッセージ',
    }
    const mockAIMsg = {
      type: 'ai',
      content: 'AI応答メッセージ',
    }

    mockGraph.getState.mockResolvedValue({
      values: {
        messages: [mockHumanMsg, mockAIMsg],
      },
    })

    const result = await handler({} as any)

    expect(result).toEqual({
      messages: [
        { role: 'user', content: 'ユーザーメッセージ' },
        { role: 'assistant', content: 'AI応答メッセージ' },
      ],
    })
  })

  it('AI メッセージに additional_kwargs.searchResults がある場合、レスポンスに searchResults を含める', async () => {
    vi.mocked(getQuery).mockReturnValue({ threadId: 'thread-1' })

    const results = [
      { title: 'Doc A', url: 'https://example.com/a', content: 'A snippet' },
      { title: 'Doc B', url: 'https://example.com/b', content: 'B snippet' },
    ]
    mockGraph.getState.mockResolvedValue({
      values: {
        messages: [
          { type: 'human', content: '質問' },
          { type: 'ai', content: 'AI応答', additional_kwargs: { searchResults: results } },
        ],
      },
    })

    const result = await handler({} as any)

    expect(result).toEqual({
      messages: [
        { role: 'user', content: '質問' },
        { role: 'assistant', content: 'AI応答', searchResults: results },
      ],
    })
  })

  it('不正な形式の searchResults はフィルタアウトされる', async () => {
    vi.mocked(getQuery).mockReturnValue({ threadId: 'thread-1' })

    mockGraph.getState.mockResolvedValue({
      values: {
        messages: [
          { type: 'human', content: 'q' },
          {
            type: 'ai',
            content: 'a',
            additional_kwargs: {
              searchResults: [
                { title: 'ok', url: 'https://ok.test', content: 'ok snippet' },
                { title: 123, url: 'https://bad.test', content: 'bad' },
                { url: 'https://only-url.test' },
              ],
            },
          },
        ],
      },
    })

    const result = await handler({} as any)

    expect(result).toEqual({
      messages: [
        { role: 'user', content: 'q' },
        {
          role: 'assistant',
          content: 'a',
          searchResults: [{ title: 'ok', url: 'https://ok.test', content: 'ok snippet' }],
        },
      ],
    })
  })

  it('古い AI メッセージ（additional_kwargs なし）は searchResults フィールドを含まない', async () => {
    vi.mocked(getQuery).mockReturnValue({ threadId: 'thread-1' })

    mockGraph.getState.mockResolvedValue({
      values: {
        messages: [
          { type: 'human', content: 'q' },
          { type: 'ai', content: 'a' },
        ],
      },
    })

    const result = await handler({} as any)

    expect(result).toEqual({
      messages: [
        { role: 'user', content: 'q' },
        { role: 'assistant', content: 'a' },
      ],
    })
  })

  it('branchId 未指定 → main として raw threadId で getState が呼ばれる', async () => {
    vi.mocked(getQuery).mockReturnValue({ threadId: 'thread-1' })
    mockGraph.getState.mockResolvedValue({ values: { messages: [] } })

    await handler({} as any)

    expect(mockGraph.getState).toHaveBeenCalledWith({
      configurable: { thread_id: 'thread-1' },
    })
  })

  it('branchId=main → raw threadId で getState が呼ばれる', async () => {
    vi.mocked(getQuery).mockReturnValue({ threadId: 'thread-1', branchId: 'main' })
    mockGraph.getState.mockResolvedValue({ values: { messages: [] } })

    await handler({} as any)

    expect(mockGraph.getState).toHaveBeenCalledWith({
      configurable: { thread_id: 'thread-1' },
    })
  })

  it('非 main の branchId → ${threadId}::${branchId} で getState が呼ばれる', async () => {
    vi.mocked(getQuery).mockReturnValue({ threadId: 'thread-1', branchId: 'uuid-xyz' })
    mockGraph.getState.mockResolvedValue({ values: { messages: [] } })

    await handler({} as any)

    expect(mockGraph.getState).toHaveBeenCalledWith({
      configurable: { thread_id: 'thread-1::uuid-xyz' },
    })
  })

  it('type が human/ai 以外のメッセージはフィルタリングされる', async () => {
    vi.mocked(getQuery).mockReturnValue({ threadId: 'thread-1' })

    mockGraph.getState.mockResolvedValue({
      values: {
        messages: [
          { type: 'system', content: 'システムメッセージ' },
          { type: 'human', content: 'ユーザーメッセージ' },
          { type: 'tool', content: 'ツール結果' },
          { type: 'ai', content: 'AI応答' },
        ],
      },
    })

    const result = await handler({} as any)

    expect(result).toEqual({
      messages: [
        { role: 'user', content: 'ユーザーメッセージ' },
        { role: 'assistant', content: 'AI応答' },
      ],
    })
  })
})

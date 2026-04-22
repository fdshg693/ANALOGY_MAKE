import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock h3 functions
vi.mock('h3', () => ({
  defineEventHandler: (handler: Function) => handler,
  getRouterParam: vi.fn(),
  readBody: vi.fn(),
  createError: (opts: { statusCode: number; statusMessage: string }) => {
    const error = new Error(opts.statusMessage) as Error & { statusCode: number; statusMessage: string }
    error.statusCode = opts.statusCode
    error.statusMessage = opts.statusMessage
    return error
  },
}))

const DEFAULT_SEARCH_SETTINGS = { enabled: true, depth: 'basic' as const, maxResults: 3 }

// Mock thread-store
vi.mock('../../server/utils/thread-store', () => ({
  getThreadSettings: vi.fn().mockReturnValue({
    granularity: 'standard',
    customInstruction: '',
    search: { enabled: true, depth: 'basic', maxResults: 3 },
  }),
  updateThreadSettings: vi.fn(),
  DEFAULT_SEARCH_SETTINGS: { enabled: true, depth: 'basic', maxResults: 3 },
}))

import getHandler from '~/server/api/threads/[id]/settings.get'
import putHandler from '~/server/api/threads/[id]/settings.put'
import { getRouterParam, readBody } from 'h3'
import { getThreadSettings, updateThreadSettings } from '../../server/utils/thread-store'

describe('GET /api/threads/[id]/settings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('有効な thread ID で設定を返す', () => {
    vi.mocked(getRouterParam).mockReturnValue('thread-1')
    vi.mocked(getThreadSettings).mockReturnValue({ granularity: 'detailed', customInstruction: 'テスト' })

    const result = (getHandler as Function)({} as any)
    expect(getRouterParam).toHaveBeenCalledWith({}, 'id')
    expect(getThreadSettings).toHaveBeenCalledWith('thread-1')
    expect(result).toEqual({ granularity: 'detailed', customInstruction: 'テスト' })
  })

  it('id が欠落している場合は 400 エラーをスロー', () => {
    vi.mocked(getRouterParam).mockReturnValue(undefined)

    expect(() => (getHandler as Function)({} as any)).toThrow()
    try {
      (getHandler as Function)({} as any)
    } catch (error: any) {
      expect(error.statusCode).toBe(400)
      expect(error.statusMessage).toBe('id is required')
    }
  })
})

describe('PUT /api/threads/[id]/settings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('有効なデータで設定を保存して返す', async () => {
    vi.mocked(getRouterParam).mockReturnValue('thread-1')
    vi.mocked(readBody).mockResolvedValue({
      granularity: 'concise',
      customInstruction: 'テスト指示',
      search: { enabled: false, depth: 'advanced', maxResults: 5 },
    })

    const result = await (putHandler as Function)({} as any)
    expect(updateThreadSettings).toHaveBeenCalledWith('thread-1', {
      granularity: 'concise',
      customInstruction: 'テスト指示',
      search: { enabled: false, depth: 'advanced', maxResults: 5 },
    })
    expect(result).toEqual({
      granularity: 'concise',
      customInstruction: 'テスト指示',
      search: { enabled: false, depth: 'advanced', maxResults: 5 },
    })
  })

  it('無効な granularity の場合は standard にフォールバック', async () => {
    vi.mocked(getRouterParam).mockReturnValue('thread-1')
    vi.mocked(readBody).mockResolvedValue({ granularity: 'invalid-value', customInstruction: '' })

    const result = await (putHandler as Function)({} as any)
    expect(updateThreadSettings).toHaveBeenCalledWith('thread-1', {
      granularity: 'standard',
      customInstruction: '',
      search: DEFAULT_SEARCH_SETTINGS,
    })
    expect(result).toEqual({
      granularity: 'standard',
      customInstruction: '',
      search: DEFAULT_SEARCH_SETTINGS,
    })
  })

  it('customInstruction が 500 文字を超える場合は切り詰め', async () => {
    vi.mocked(getRouterParam).mockReturnValue('thread-1')
    const longInstruction = 'あ'.repeat(600)
    vi.mocked(readBody).mockResolvedValue({ granularity: 'standard', customInstruction: longInstruction })

    const result = await (putHandler as Function)({} as any)
    const expected = longInstruction.slice(0, 500)
    expect(updateThreadSettings).toHaveBeenCalledWith('thread-1', {
      granularity: 'standard',
      customInstruction: expected,
      search: DEFAULT_SEARCH_SETTINGS,
    })
    expect(result.customInstruction).toHaveLength(500)
  })

  it('search 省略時は DEFAULT_SEARCH_SETTINGS にフォールバック', async () => {
    vi.mocked(getRouterParam).mockReturnValue('thread-1')
    vi.mocked(readBody).mockResolvedValue({ granularity: 'standard', customInstruction: '' })
    const result = await (putHandler as Function)({} as any)
    expect(result.search).toEqual(DEFAULT_SEARCH_SETTINGS)
  })

  it('search.depth が不正な場合は basic にフォールバック', async () => {
    vi.mocked(getRouterParam).mockReturnValue('thread-1')
    vi.mocked(readBody).mockResolvedValue({
      granularity: 'standard',
      customInstruction: '',
      search: { enabled: true, depth: 'invalid', maxResults: 3 },
    })
    const result = await (putHandler as Function)({} as any)
    expect(result.search.depth).toBe('basic')
  })

  it('search.maxResults が範囲外 (0) の場合は 1 にクランプ', async () => {
    vi.mocked(getRouterParam).mockReturnValue('thread-1')
    vi.mocked(readBody).mockResolvedValue({
      granularity: 'standard',
      customInstruction: '',
      search: { enabled: true, depth: 'basic', maxResults: 0 },
    })
    const result = await (putHandler as Function)({} as any)
    expect(result.search.maxResults).toBe(1)
  })

  it('search.maxResults が範囲外 (11) の場合は 10 にクランプ', async () => {
    vi.mocked(getRouterParam).mockReturnValue('thread-1')
    vi.mocked(readBody).mockResolvedValue({
      granularity: 'standard',
      customInstruction: '',
      search: { enabled: true, depth: 'basic', maxResults: 11 },
    })
    const result = await (putHandler as Function)({} as any)
    expect(result.search.maxResults).toBe(10)
  })

  it('search.maxResults が非整数の場合は DEFAULT にフォールバック', async () => {
    vi.mocked(getRouterParam).mockReturnValue('thread-1')
    vi.mocked(readBody).mockResolvedValue({
      granularity: 'standard',
      customInstruction: '',
      search: { enabled: true, depth: 'basic', maxResults: 'abc' },
    })
    const result = await (putHandler as Function)({} as any)
    expect(result.search.maxResults).toBe(DEFAULT_SEARCH_SETTINGS.maxResults)
  })

  it('search.enabled が boolean でない場合は DEFAULT の true にフォールバック', async () => {
    vi.mocked(getRouterParam).mockReturnValue('thread-1')
    vi.mocked(readBody).mockResolvedValue({
      granularity: 'standard',
      customInstruction: '',
      search: { enabled: 'yes', depth: 'basic', maxResults: 3 },
    })
    const result = await (putHandler as Function)({} as any)
    expect(result.search.enabled).toBe(true)
  })

  it('id が欠落している場合は 400 エラーをスロー', async () => {
    vi.mocked(getRouterParam).mockReturnValue(undefined)

    await expect((putHandler as Function)({} as any)).rejects.toMatchObject({
      statusCode: 400,
      statusMessage: 'id is required',
    })
  })
})

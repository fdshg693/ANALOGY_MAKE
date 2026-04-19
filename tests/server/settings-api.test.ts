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

// Mock thread-store
vi.mock('../../server/utils/thread-store', () => ({
  getThreadSettings: vi.fn().mockReturnValue({ granularity: 'standard', customInstruction: '' }),
  updateThreadSettings: vi.fn(),
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
    vi.mocked(readBody).mockResolvedValue({ granularity: 'concise', customInstruction: 'テスト指示' })

    const result = await (putHandler as Function)({} as any)
    expect(updateThreadSettings).toHaveBeenCalledWith('thread-1', { granularity: 'concise', customInstruction: 'テスト指示' })
    expect(result).toEqual({ granularity: 'concise', customInstruction: 'テスト指示' })
  })

  it('無効な granularity の場合は standard にフォールバック', async () => {
    vi.mocked(getRouterParam).mockReturnValue('thread-1')
    vi.mocked(readBody).mockResolvedValue({ granularity: 'invalid-value', customInstruction: '' })

    const result = await (putHandler as Function)({} as any)
    expect(updateThreadSettings).toHaveBeenCalledWith('thread-1', { granularity: 'standard', customInstruction: '' })
    expect(result).toEqual({ granularity: 'standard', customInstruction: '' })
  })

  it('customInstruction が 500 文字を超える場合は切り詰め', async () => {
    vi.mocked(getRouterParam).mockReturnValue('thread-1')
    const longInstruction = 'あ'.repeat(600)
    vi.mocked(readBody).mockResolvedValue({ granularity: 'standard', customInstruction: longInstruction })

    const result = await (putHandler as Function)({} as any)
    const expected = longInstruction.slice(0, 500)
    expect(updateThreadSettings).toHaveBeenCalledWith('thread-1', { granularity: 'standard', customInstruction: expected })
    expect(result.customInstruction).toHaveLength(500)
  })

  it('id が欠落している場合は 400 エラーをスロー', async () => {
    vi.mocked(getRouterParam).mockReturnValue(undefined)

    await expect((putHandler as Function)({} as any)).rejects.toMatchObject({
      statusCode: 400,
      statusMessage: 'id is required',
    })
  })
})

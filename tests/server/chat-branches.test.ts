import { describe, it, expect, vi, beforeEach } from 'vitest'

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

vi.mock('../../server/utils/branch-store', () => ({
  getBranches: vi.fn().mockReturnValue([]),
}))

import { makeThreadSettings } from '../fixtures/settings'

vi.mock('../../server/utils/thread-store', () => ({
  getThreadSettings: vi.fn(),
  DEFAULT_SETTINGS: {
    granularity: 'standard',
    customInstruction: '',
    search: { enabled: true, depth: 'basic', maxResults: 3 },
    responseMode: 'ai',
    systemPromptOverride: '',
    activeBranchId: 'main',
  },
  DEFAULT_SEARCH_SETTINGS: { enabled: true, depth: 'basic', maxResults: 3 },
}))

import handler from '~/server/api/chat/branches.get'
import { getQuery } from 'h3'
import { getBranches } from '../../server/utils/branch-store'
import { getThreadSettings } from '../../server/utils/thread-store'

describe('GET /api/chat/branches', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(getThreadSettings).mockReturnValue(makeThreadSettings())
  })

  it('threadId 欠落で 400', async () => {
    vi.mocked(getQuery).mockReturnValue({})
    await expect(handler({} as any)).rejects.toMatchObject({
      statusCode: 400,
      statusMessage: 'threadId is required',
    })
  })

  it('threadId が文字列でない場合も 400', async () => {
    vi.mocked(getQuery).mockReturnValue({ threadId: 123 as any })
    await expect(handler({} as any)).rejects.toMatchObject({
      statusCode: 400,
      statusMessage: 'threadId is required',
    })
  })

  it('DB レコードなし → branches は main のみ、activeBranchId は settings から', async () => {
    vi.mocked(getQuery).mockReturnValue({ threadId: 'thread-1' })
    vi.mocked(getBranches).mockReturnValue([])
    vi.mocked(getThreadSettings).mockReturnValue(makeThreadSettings({ activeBranchId: 'main' }))

    const result = await handler({} as any)

    expect(result).toEqual({
      branches: [
        { branchId: 'main', parentBranchId: null, forkMessageIndex: null, createdAt: null },
      ],
      activeBranchId: 'main',
    })
  })

  it('DB レコード 2 件 → main に続けてマッピング済みの分岐が並ぶ', async () => {
    vi.mocked(getQuery).mockReturnValue({ threadId: 'thread-1' })
    vi.mocked(getBranches).mockReturnValue([
      {
        branch_id: 'uuid-a',
        thread_id: 'thread-1',
        parent_branch_id: 'main',
        fork_message_index: 2,
        created_at: '2026-01-01 00:00:00',
      },
      {
        branch_id: 'uuid-b',
        thread_id: 'thread-1',
        parent_branch_id: 'uuid-a',
        fork_message_index: 4,
        created_at: '2026-01-02 00:00:00',
      },
    ])
    vi.mocked(getThreadSettings).mockReturnValue(makeThreadSettings({ activeBranchId: 'uuid-a' }))

    const result = await handler({} as any)

    expect(result).toEqual({
      branches: [
        { branchId: 'main', parentBranchId: null, forkMessageIndex: null, createdAt: null },
        {
          branchId: 'uuid-a',
          parentBranchId: 'main',
          forkMessageIndex: 2,
          createdAt: '2026-01-01 00:00:00',
        },
        {
          branchId: 'uuid-b',
          parentBranchId: 'uuid-a',
          forkMessageIndex: 4,
          createdAt: '2026-01-02 00:00:00',
        },
      ],
      activeBranchId: 'uuid-a',
    })
  })

  it('getThreadSettings は要求された threadId で呼ばれる', async () => {
    vi.mocked(getQuery).mockReturnValue({ threadId: 'thread-xyz' })
    vi.mocked(getBranches).mockReturnValue([])
    await handler({} as any)
    expect(getThreadSettings).toHaveBeenCalledWith('thread-xyz')
    expect(getBranches).toHaveBeenCalledWith('thread-xyz')
  })
})

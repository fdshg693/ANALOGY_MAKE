import { describe, it, expect, vi, beforeEach } from 'vitest'
import { HumanMessage, AIMessage } from '@langchain/core/messages'

// Mock h3 functions
vi.mock('h3', () => ({
  defineEventHandler: (handler: Function) => handler,
  readBody: vi.fn(),
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
  updateState: vi.fn().mockResolvedValue(undefined),
}

vi.mock('../../server/utils/analogy-agent', () => ({
  getAnalogyAgent: () => Promise.resolve(mockGraph),
  // fork.post.ts は deriveCurrentStep(newMessages) を呼ぶ。
  // ここでは fork 側の制御に集中し、簡易実装で置換。
  deriveCurrentStep: vi.fn().mockImplementation((msgs: any[]) => {
    if (!msgs || msgs.length === 0) return 'initial'
    return 'initial'
  }),
}))

// Mock branch-store
vi.mock('../../server/utils/branch-store', () => ({
  getBranches: vi.fn().mockReturnValue([]),
  branchBelongsToThread: vi.fn().mockReturnValue(true),
  createBranch: vi.fn().mockReturnValue({
    branch_id: 'new-uuid',
    thread_id: 'thread-1',
    parent_branch_id: 'main',
    fork_message_index: 2,
    created_at: '2026-01-01 00:00:00',
  }),
}))

// Mock thread-store
import { makeThreadSettings } from '../fixtures/settings'

vi.mock('../../server/utils/thread-store', () => ({
  getThreadSettings: vi.fn(),
  updateThreadSettings: vi.fn(),
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

vi.stubGlobal('useRuntimeConfig', () => ({ openaiApiKey: 'test-key', tavilyApiKey: 'test-tavily-key' }))

import handler from '~/server/api/chat/fork.post'
import { readBody } from 'h3'
import { branchBelongsToThread, createBranch } from '../../server/utils/branch-store'
import { getThreadSettings, updateThreadSettings } from '../../server/utils/thread-store'

describe('POST /api/chat/fork', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(branchBelongsToThread).mockReturnValue(true)
    vi.mocked(getThreadSettings).mockReturnValue(makeThreadSettings())
    vi.mocked(createBranch).mockReturnValue({
      branch_id: 'new-uuid',
      thread_id: 'thread-1',
      parent_branch_id: 'main',
      fork_message_index: 2,
      created_at: '2026-01-01 00:00:00',
    })
    mockGraph.getState.mockResolvedValue({
      values: {
        messages: [
          new HumanMessage('q1'),
          new AIMessage('a1'),
          new HumanMessage('q2'),
          new AIMessage('a2'),
        ],
        abstractedProblem: 'abstracted',
      },
    })
  })

  describe('バリデーション', () => {
    it('threadId 欠落で 400', async () => {
      vi.mocked(readBody).mockResolvedValue({ fromBranchId: 'main', forkMessageIndex: 0 })
      await expect(handler({} as any)).rejects.toMatchObject({
        statusCode: 400,
        statusMessage: 'threadId is required',
      })
    })

    it('fromBranchId 欠落で 400', async () => {
      vi.mocked(readBody).mockResolvedValue({ threadId: 'thread-1', forkMessageIndex: 0 })
      await expect(handler({} as any)).rejects.toMatchObject({
        statusCode: 400,
        statusMessage: 'fromBranchId is required',
      })
    })

    it('forkMessageIndex が負数で 400', async () => {
      vi.mocked(readBody).mockResolvedValue({
        threadId: 'thread-1',
        fromBranchId: 'main',
        forkMessageIndex: -1,
      })
      await expect(handler({} as any)).rejects.toMatchObject({
        statusCode: 400,
        statusMessage: 'forkMessageIndex must be a non-negative integer',
      })
    })

    it('forkMessageIndex が非整数で 400', async () => {
      vi.mocked(readBody).mockResolvedValue({
        threadId: 'thread-1',
        fromBranchId: 'main',
        forkMessageIndex: 1.5,
      })
      await expect(handler({} as any)).rejects.toMatchObject({
        statusCode: 400,
        statusMessage: 'forkMessageIndex must be a non-negative integer',
      })
    })

    it('fromBranchId が非 main かつ branchBelongsToThread=false で 400', async () => {
      vi.mocked(branchBelongsToThread).mockReturnValue(false)
      vi.mocked(readBody).mockResolvedValue({
        threadId: 'thread-1',
        fromBranchId: 'unknown-uuid',
        forkMessageIndex: 0,
      })
      await expect(handler({} as any)).rejects.toMatchObject({
        statusCode: 400,
        statusMessage: 'fromBranchId does not belong to threadId',
      })
    })

    it('forkMessageIndex が親メッセージ数を超える → 400', async () => {
      vi.mocked(readBody).mockResolvedValue({
        threadId: 'thread-1',
        fromBranchId: 'main',
        forkMessageIndex: 99,
      })
      await expect(handler({} as any)).rejects.toMatchObject({
        statusCode: 400,
        statusMessage: 'forkMessageIndex out of range',
      })
    })
  })

  describe('正常系', () => {
    it('main から fork: updateState は thread-1::new-uuid で呼ばれ、スライスされた messages が渡る', async () => {
      vi.mocked(readBody).mockResolvedValue({
        threadId: 'thread-1',
        fromBranchId: 'main',
        forkMessageIndex: 2,
      })

      const result = await handler({} as any)

      expect(mockGraph.updateState).toHaveBeenCalledTimes(1)
      const [cfg, values] = mockGraph.updateState.mock.calls[0]
      expect(cfg).toEqual({ configurable: { thread_id: 'thread-1::new-uuid' } })
      expect((values as any).messages).toHaveLength(2)
      expect((values as any).currentStep).toBe('initial')
      expect((values as any).abstractedProblem).toBe('abstracted')

      expect(updateThreadSettings).toHaveBeenCalledTimes(1)
      const [tid, settings] = vi.mocked(updateThreadSettings).mock.calls[0]
      expect(tid).toBe('thread-1')
      expect((settings as any).activeBranchId).toBe('new-uuid')

      expect(result).toEqual({ branchId: 'new-uuid', activeBranchId: 'new-uuid' })
    })

    it('fromBranchId が main の場合は branchBelongsToThread を呼ばない', async () => {
      vi.mocked(readBody).mockResolvedValue({
        threadId: 'thread-1',
        fromBranchId: 'main',
        forkMessageIndex: 0,
      })
      await handler({} as any)
      expect(branchBelongsToThread).not.toHaveBeenCalled()
    })
  })
})

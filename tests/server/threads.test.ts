import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock h3 functions
vi.mock('h3', () => ({
  defineEventHandler: (handler: Function) => handler,
}))

// Mock thread-store
const mockGetThreads = vi.fn()

vi.mock('../../server/utils/thread-store', () => ({
  getThreads: (...args: any[]) => mockGetThreads(...args),
}))

import handler from '~/server/api/threads.get'

describe('GET /api/threads', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('スレッド一覧を返す', async () => {
    mockGetThreads.mockReturnValue([
      { thread_id: 'id-1', title: 'スレッド1', created_at: '2025-01-01 00:00:00', updated_at: '2025-01-02 00:00:00' },
      { thread_id: 'id-2', title: 'スレッド2', created_at: '2025-01-01 00:00:00', updated_at: '2025-01-01 12:00:00' },
    ])

    const result = await handler({} as any)

    expect(result).toEqual({
      threads: [
        { threadId: 'id-1', title: 'スレッド1', createdAt: '2025-01-01 00:00:00', updatedAt: '2025-01-02 00:00:00' },
        { threadId: 'id-2', title: 'スレッド2', createdAt: '2025-01-01 00:00:00', updatedAt: '2025-01-01 12:00:00' },
      ]
    })
  })

  it('スレッドがない場合は空配列を返す', async () => {
    mockGetThreads.mockReturnValue([])

    const result = await handler({} as any)

    expect(result).toEqual({ threads: [] })
  })
})

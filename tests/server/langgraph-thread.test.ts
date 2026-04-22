import { describe, it, expect } from 'vitest'
import { toLangGraphThreadId, MAIN_BRANCH_ID } from '../../server/utils/langgraph-thread'

describe('langgraph-thread', () => {
  describe('MAIN_BRANCH_ID', () => {
    it("定数は 'main' である", () => {
      expect(MAIN_BRANCH_ID).toBe('main')
    })
  })

  describe('toLangGraphThreadId', () => {
    it('branchId 未指定 → 生の threadId を返す', () => {
      expect(toLangGraphThreadId('thread-1')).toBe('thread-1')
    })

    it("branchId='main' → 生の threadId を返す", () => {
      expect(toLangGraphThreadId('thread-1', 'main')).toBe('thread-1')
    })

    it('非 main の branchId → ${threadId}::${branchId} を返す', () => {
      expect(toLangGraphThreadId('thread-1', 'uuid-xyz')).toBe('thread-1::uuid-xyz')
    })

    it('空文字でない任意の UUID でも同様に結合する', () => {
      expect(toLangGraphThreadId('t', 'abc-123')).toBe('t::abc-123')
    })
  })
})

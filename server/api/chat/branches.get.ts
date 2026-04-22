import { defineEventHandler, getQuery, createError } from 'h3'
import { getBranches } from '../../utils/branch-store'
import { getThreadSettings } from '../../utils/thread-store'
import { MAIN_BRANCH_ID } from '../../utils/langgraph-thread'

export interface BranchView {
  branchId: string
  parentBranchId: string | null
  forkMessageIndex: number | null
  createdAt: string | null
}

export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const threadId = query.threadId

  if (!threadId || typeof threadId !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'threadId is required' })
  }

  const records = getBranches(threadId)
  const branches: BranchView[] = [
    { branchId: MAIN_BRANCH_ID, parentBranchId: null, forkMessageIndex: null, createdAt: null },
    ...records.map((r) => ({
      branchId: r.branch_id,
      parentBranchId: r.parent_branch_id,
      forkMessageIndex: r.fork_message_index,
      createdAt: r.created_at,
    })),
  ]

  const settings = getThreadSettings(threadId)
  return {
    branches,
    activeBranchId: settings.activeBranchId,
  }
})

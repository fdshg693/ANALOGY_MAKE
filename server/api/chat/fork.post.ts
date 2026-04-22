import { defineEventHandler, readBody, createError } from 'h3'
import type { BaseMessage } from '@langchain/core/messages'
import { getAnalogyAgent, deriveCurrentStep } from '../../utils/analogy-agent'
import { getThreadSettings, updateThreadSettings } from '../../utils/thread-store'
import { createBranch, branchBelongsToThread } from '../../utils/branch-store'
import { MAIN_BRANCH_ID, toLangGraphThreadId } from '../../utils/langgraph-thread'
import { logger } from '../../utils/logger'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  if (!body.threadId || typeof body.threadId !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'threadId is required' })
  }
  if (typeof body.fromBranchId !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'fromBranchId is required' })
  }
  if (!Number.isInteger(body.forkMessageIndex) || body.forkMessageIndex < 0) {
    throw createError({ statusCode: 400, statusMessage: 'forkMessageIndex must be a non-negative integer' })
  }

  const { threadId, fromBranchId, forkMessageIndex } = body as {
    threadId: string
    fromBranchId: string
    forkMessageIndex: number
  }

  if (fromBranchId !== MAIN_BRANCH_ID && !branchBelongsToThread(threadId, fromBranchId)) {
    throw createError({ statusCode: 400, statusMessage: 'fromBranchId does not belong to threadId' })
  }

  const agent = await getAnalogyAgent()

  const parentThreadId = toLangGraphThreadId(threadId, fromBranchId)
  const parentSnapshot = await agent.getState({ configurable: { thread_id: parentThreadId } })
  const parentMessages = (parentSnapshot?.values?.messages ?? []) as BaseMessage[]
  if (forkMessageIndex > parentMessages.length) {
    throw createError({
      statusCode: 400,
      statusMessage: 'forkMessageIndex out of range',
    })
  }
  const newMessages = parentMessages.slice(0, forkMessageIndex)

  const branch = createBranch({ threadId, parentBranchId: fromBranchId, forkMessageIndex })

  const newThreadId = toLangGraphThreadId(threadId, branch.branch_id)
  const newCurrentStep = deriveCurrentStep(newMessages)
  const parentAbstracted = (parentSnapshot?.values?.abstractedProblem ?? '') as string

  await agent.updateState(
    { configurable: { thread_id: newThreadId } },
    {
      messages: newMessages,
      currentStep: newCurrentStep,
      abstractedProblem: parentAbstracted,
    },
  )

  const settings = getThreadSettings(threadId)
  updateThreadSettings(threadId, { ...settings, activeBranchId: branch.branch_id })

  logger.chat.info('Branch forked', {
    threadId,
    fromBranchId,
    newBranchId: branch.branch_id,
    forkMessageIndex,
    copiedMessages: newMessages.length,
    newCurrentStep,
  })

  return {
    branchId: branch.branch_id,
    activeBranchId: branch.branch_id,
  }
})

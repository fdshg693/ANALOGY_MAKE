import { defineEventHandler, getQuery, createError } from 'h3'
import { HumanMessage, AIMessage } from '@langchain/core/messages'
import { getAnalogyAgent } from '../../utils/analogy-agent'
import { logger } from '../../utils/logger'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const threadId = query.threadId

  if (!threadId || typeof threadId !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'threadId is required' })
  }

  logger.history.info('History requested', { threadId })

  try {
    const agent = await getAnalogyAgent()
    const snapshot = await agent.getState({ configurable: { thread_id: threadId } })

    const rawMessages = snapshot?.values?.messages
    if (!rawMessages || !Array.isArray(rawMessages)) {
      return { messages: [] }
    }

    const messages = rawMessages
      .filter((msg: unknown) => msg instanceof HumanMessage || msg instanceof AIMessage)
      .map((msg: HumanMessage | AIMessage) => ({
        role: msg instanceof HumanMessage ? 'user' as const : 'assistant' as const,
        content: typeof msg.content === 'string' ? msg.content : '',
      }))

    logger.history.info('History loaded', { threadId, messageCount: messages.length })

    return { messages }
  } catch (e) {
    logger.history.warn('History load failed', { threadId, error: e instanceof Error ? e.message : 'Unknown error' })
    return { messages: [] }
  }
})

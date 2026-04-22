import { defineEventHandler, getQuery, createError } from 'h3'
import { getAnalogyAgent } from '../../utils/analogy-agent'
import { logger } from '../../utils/logger'

interface CheckpointMessage {
  type: string
  content: unknown
  additional_kwargs?: Record<string, unknown>
}

function isChatMessage(msg: unknown): msg is CheckpointMessage & { type: 'human' | 'ai' } {
  return (
    typeof msg === 'object' &&
    msg !== null &&
    'type' in msg &&
    ((msg as CheckpointMessage).type === 'human' || (msg as CheckpointMessage).type === 'ai')
  )
}

interface SearchResult {
  title: string
  url: string
  content: string
}

function extractSearchResults(additionalKwargs: Record<string, unknown> | undefined): SearchResult[] {
  const raw = additionalKwargs?.searchResults
  if (!Array.isArray(raw)) return []
  return raw
    .filter(
      (r): r is SearchResult =>
        typeof r === 'object' &&
        r !== null &&
        typeof (r as { title?: unknown }).title === 'string' &&
        typeof (r as { url?: unknown }).url === 'string' &&
        typeof (r as { content?: unknown }).content === 'string',
    )
    .map((r) => ({ title: r.title, url: r.url, content: r.content }))
}

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

    logger.history.info('Raw messages from snapshot', {
      threadId,
      count: rawMessages.length,
      types: rawMessages.map((m: any) => m?.constructor?.name ?? typeof m),
    })

    const messages = rawMessages
      .filter(isChatMessage)
      .map((msg) => {
        const base = {
          role: msg.type === 'human' ? 'user' as const : 'assistant' as const,
          content: typeof msg.content === 'string' ? msg.content : '',
        }
        if (msg.type === 'ai') {
          const searchResults = extractSearchResults(msg.additional_kwargs)
          if (searchResults.length > 0) {
            return { ...base, searchResults }
          }
        }
        return base
      })

    if (rawMessages.length !== messages.length) {
      logger.history.warn('Messages filtered out', {
        threadId,
        rawCount: rawMessages.length,
        filteredCount: messages.length,
      })
    }

    logger.history.info('History loaded', { threadId, messageCount: messages.length })

    return { messages }
  } catch (e) {
    logger.history.warn('History load failed', { threadId, error: e instanceof Error ? e.message : 'Unknown error' })
    return { messages: [] }
  }
})

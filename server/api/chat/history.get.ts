import { defineEventHandler, getQuery, createError } from 'h3'
import { HumanMessage, AIMessage } from '@langchain/core/messages'
import { getAnalogyAgent } from '../../utils/analogy-agent'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const threadId = query.threadId

  if (!threadId || typeof threadId !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'threadId is required' })
  }

  try {
    const agent = await getAnalogyAgent()
    // getState() is typed as `never` in langchain's ReactAgent (marked @internal),
    // but works at runtime via LangGraph's CompiledStateGraph
    const snapshot = await (agent as any).getState({ configurable: { thread_id: threadId } })

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

    return { messages }
  } catch {
    return { messages: [] }
  }
})

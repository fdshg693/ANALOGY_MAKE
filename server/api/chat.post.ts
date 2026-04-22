import { createEventStream, readBody, createError, defineEventHandler } from 'h3'
import { AIMessageChunk, HumanMessage } from '@langchain/core/messages'
import { getAnalogyAgent } from '../utils/analogy-agent'
import { upsertThread, getThreadTitle, updateThreadTitle, getThreadSettings } from '../utils/thread-store'
import { logger } from '../utils/logger'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  if (!body.message || typeof body.message !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'message is required' })
  }
  if (!body.threadId || typeof body.threadId !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'threadId is required' })
  }

  logger.chat.info('Request received', { threadId: body.threadId, messageLength: body.message.length })

  const agent = await getAnalogyAgent()
  const eventStream = createEventStream(event)

  void (async () => {
    try {
      upsertThread(body.threadId)

      const settings = getThreadSettings(body.threadId)

      const stream = await agent.stream(
        { messages: [new HumanMessage(body.message)] },
        {
          configurable: { thread_id: body.threadId, settings },
          streamMode: "messages",
        },
      )

      logger.chat.info('Streaming started', { threadId: body.threadId })

      let fullResponse = ''

      const STREAMED_NODES = new Set(["caseSearch", "solution", "followUp"])

      for await (const [chunk, metadata] of stream) {
        if (
          chunk instanceof AIMessageChunk &&
          typeof chunk.content === "string" &&
          chunk.content &&
          STREAMED_NODES.has(metadata?.langgraph_node)
        ) {
          fullResponse += chunk.content
          await eventStream.push({
            event: 'token',
            data: JSON.stringify({ content: chunk.content }),
          })
        }
      }

      logger.chat.info('Streaming completed', { threadId: body.threadId, responseLength: fullResponse.length })

      try {
        const finalSnapshot = await agent.getState({
          configurable: { thread_id: body.threadId },
        })
        const finalMessages = finalSnapshot?.values?.messages
        const lastMessage = Array.isArray(finalMessages)
          ? finalMessages[finalMessages.length - 1]
          : undefined
        const searchResults = (lastMessage as { additional_kwargs?: { searchResults?: unknown } } | undefined)
          ?.additional_kwargs?.searchResults
        if (Array.isArray(searchResults) && searchResults.length > 0) {
          await eventStream.push({
            event: 'search_results',
            data: JSON.stringify({ results: searchResults }),
          })
        }
      } catch (e) {
        logger.chat.warn('search_results snapshot read failed', {
          threadId: body.threadId,
          error: e instanceof Error ? e.message : 'Unknown error',
        })
      }

      await eventStream.push({
        event: 'done',
        data: '{}',
      })

      // タイトル自動生成（初回メッセージのみ）
      const currentTitle = getThreadTitle(body.threadId)
      if (currentTitle === '新しいチャット' || currentTitle === null) {
        void generateTitle(body.threadId, body.message, fullResponse)
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Unknown error'
      logger.chat.error('Streaming failed', { threadId: body.threadId, error: message })
      await eventStream.push({
        event: 'error',
        data: JSON.stringify({ message }),
      })
    } finally {
      await eventStream.close()
    }
  })()

  eventStream.onClosed(async () => {
    await eventStream.close()
  })

  return eventStream.send()
})

async function generateTitle(threadId: string, userMessage: string, aiResponse: string): Promise<void> {
  try {
    logger.chat.info('Title generation started', { threadId })
    const { ChatOpenAI } = await import('@langchain/openai')
    const config = useRuntimeConfig()
    const model = new ChatOpenAI({
      model: 'gpt-4.1-mini',
      temperature: 0,
      maxTokens: 30,
      apiKey: config.openaiApiKey,
    })
    const result = await model.invoke([
      { role: 'system', content: '以下の会話の内容を10文字以内の日本語タイトルにしてください。タイトルのみ出力してください。' },
      { role: 'user', content: `ユーザー: ${userMessage}\nAI: ${aiResponse.slice(0, 200)}` },
    ])
    const title = (result.content as string).trim().slice(0, 30)
    if (title) {
      updateThreadTitle(threadId, title)
      logger.chat.info('Title generated', { threadId, title })
    }
  } catch (e) {
    logger.chat.warn('Title generation failed', { threadId, error: e instanceof Error ? e.message : 'Unknown error' })
  }
}

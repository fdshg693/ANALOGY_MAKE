import { createEventStream, readBody, createError, defineEventHandler } from 'h3'
import { AIMessageChunk } from '@langchain/core/messages'
import { getAnalogyAgent } from '../utils/analogy-agent'
import { upsertThread, getThreadTitle, updateThreadTitle } from '../utils/thread-store'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  if (!body.message || typeof body.message !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'message is required' })
  }
  if (!body.threadId || typeof body.threadId !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'threadId is required' })
  }

  const agent = await getAnalogyAgent()
  const eventStream = createEventStream(event)

  void (async () => {
    try {
      upsertThread(body.threadId)

      const stream = await agent.stream(
        { messages: [{ role: "user", content: body.message }] },
        {
          configurable: { thread_id: body.threadId },
          streamMode: "messages",
        },
      )

      let fullResponse = ''

      for await (const [chunk, _metadata] of stream) {
        if (chunk instanceof AIMessageChunk && typeof chunk.content === 'string' && chunk.content) {
          fullResponse += chunk.content
          await eventStream.push({
            event: 'token',
            data: JSON.stringify({ content: chunk.content }),
          })
        }
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
    }
  } catch {
    // タイトル生成失敗はサイレントに無視
  }
}

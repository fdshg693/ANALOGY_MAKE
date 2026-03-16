import { createEventStream } from 'h3'
import { AIMessageChunk } from '@langchain/core/messages'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  if (!body.message || typeof body.message !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'message is required' })
  }
  if (!body.threadId || typeof body.threadId !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'threadId is required' })
  }

  const agent = getAnalogyAgent()
  const eventStream = createEventStream(event)

  void (async () => {
    try {
      const stream = await agent.stream(
        { messages: [{ role: "user", content: body.message }] },
        {
          configurable: { thread_id: body.threadId },
          streamMode: "messages",
        },
      )

      for await (const [chunk, _metadata] of stream) {
        if (chunk instanceof AIMessageChunk && typeof chunk.content === 'string' && chunk.content) {
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

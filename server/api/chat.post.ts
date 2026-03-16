export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  if (!body.message || typeof body.message !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'message is required' })
  }
  if (!body.threadId || typeof body.threadId !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'threadId is required' })
  }

  const agent = getAnalogyAgent()

  const result = await agent.invoke(
    { messages: [{ role: "user", content: body.message }] },
    { configurable: { thread_id: body.threadId } },
  )

  const lastMessage = result.messages[result.messages.length - 1]

  return {
    message: {
      role: 'assistant' as const,
      content: lastMessage.content as string,
    },
  }
})

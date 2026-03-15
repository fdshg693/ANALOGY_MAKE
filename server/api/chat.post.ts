export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  if (!body.messages?.length) {
    throw createError({ statusCode: 400, statusMessage: 'messages is required' })
  }

  const lastMessage = body.messages[body.messages.length - 1]

  if (lastMessage.role !== 'user') {
    throw createError({ statusCode: 400, statusMessage: 'Last message must be from user' })
  }

  // モック応答（後続タスクでLangChain連携に差し替え）
  return {
    message: {
      role: 'assistant' as const,
      content: `「${lastMessage.content}」を受け取りました。\n\nこれはモック応答です。後続タスクでAIによるアナロジー思考に置き換わります。`,
    },
  }
})

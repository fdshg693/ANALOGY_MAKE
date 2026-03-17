import { parseSSEStream } from '../utils/sse-parser'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  isError?: boolean
}

export function useChat() {
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const isStreaming = ref(false)
  const threadId = ref(crypto.randomUUID())

  async function sendMessage(input: string): Promise<void> {
    if (!input) return

    messages.value.push({ role: 'user', content: input })
    isLoading.value = true
    isStreaming.value = false

    const assistantMessage: Message = { role: 'assistant', content: '' }
    messages.value.push(assistantMessage)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, threadId: threadId.value }),
      })

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`)
      }

      let firstToken = true

      await parseSSEStream(response.body, {
        onToken(content) {
          if (firstToken) {
            isStreaming.value = true
            firstToken = false
          }
          assistantMessage.content += content
        },
        onDone() {},
        onError(message) {
          const errorText = `\n\n⚠ エラーが発生しました: ${message}`
          if (assistantMessage.content) {
            assistantMessage.content += errorText
          } else {
            assistantMessage.content = errorText.trimStart()
          }
          assistantMessage.isError = true
        },
      })

      if (!assistantMessage.content && !assistantMessage.isError) {
        assistantMessage.content = '（応答を取得できませんでした）'
      }
    } catch (error) {
      console.error('Chat error:', error)
      if (!assistantMessage.isError) {
        const errorText = '\n\n⚠ 通信エラーが発生しました。もう一度お試しください。'
        if (assistantMessage.content) {
          assistantMessage.content += errorText
        } else {
          assistantMessage.content = errorText.trimStart()
        }
        assistantMessage.isError = true
      }
    } finally {
      isLoading.value = false
      isStreaming.value = false
    }
  }

  return { messages, isLoading, isStreaming, threadId, sendMessage }
}

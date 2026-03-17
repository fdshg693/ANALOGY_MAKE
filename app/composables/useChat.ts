import { parseSSEStream } from '../utils/sse-parser'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  isError?: boolean
}

const THREAD_ID_KEY = 'analogy-threadId'

function getOrCreateThreadId(): string {
  if (import.meta.client) {
    const stored = localStorage.getItem(THREAD_ID_KEY)
    if (stored) return stored
  }
  const id = crypto.randomUUID()
  if (import.meta.client) {
    localStorage.setItem(THREAD_ID_KEY, id)
  }
  return id
}

export function useChat() {
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const isStreaming = ref(false)
  const threadId = ref(getOrCreateThreadId())
  let abortController: AbortController | null = null

  async function loadHistory(): Promise<void> {
    isLoading.value = true
    try {
      const res = await fetch(`/api/chat/history?threadId=${threadId.value}`)
      if (!res.ok) return
      const data = await res.json()
      if (data.messages?.length) {
        messages.value = data.messages
      }
    } catch {
      // 取得失敗時は空チャットで開始
    } finally {
      isLoading.value = false
    }
  }

  if (import.meta.client && localStorage.getItem(THREAD_ID_KEY)) {
    loadHistory()
  }

  async function sendMessage(input: string): Promise<void> {
    if (!input) return

    messages.value.push({ role: 'user', content: input })
    isLoading.value = true
    isStreaming.value = false

    const assistantMessage: Message = { role: 'assistant', content: '' }
    messages.value.push(assistantMessage)

    try {
      abortController = new AbortController()

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, threadId: threadId.value }),
        signal: abortController.signal,
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
      if (error instanceof DOMException && error.name === 'AbortError') {
        return
      }
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

  function abort(): void {
    abortController?.abort()
  }

  return { messages, isLoading, isStreaming, threadId, sendMessage, abort }
}

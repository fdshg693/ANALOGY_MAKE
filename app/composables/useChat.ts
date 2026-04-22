import { parseSSEStream } from '../utils/sse-parser'

export interface SearchResult {
  title: string
  url: string
  content: string
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
  isError?: boolean
  searchResults?: SearchResult[]
}

export function useChat() {
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const isStreaming = ref(false)
  const threadId = ref('')
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

  async function sendMessage(input: string): Promise<void> {
    if (!input) return
    if (!threadId.value) return

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
        onSearchResults(results) {
          const validated: SearchResult[] = results
            .filter(
              (r): r is SearchResult =>
                typeof r === 'object' &&
                r !== null &&
                typeof (r as { title?: unknown }).title === 'string' &&
                typeof (r as { url?: unknown }).url === 'string' &&
                typeof (r as { content?: unknown }).content === 'string',
            )
            .map((r) => ({ title: r.title, url: r.url, content: r.content }))
          if (validated.length > 0) {
            assistantMessage.searchResults = validated
          }
        },
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

  function switchThread(newThreadId: string): void {
    if (isStreaming.value) {
      abort()
    }
    messages.value = []
    threadId.value = newThreadId
    loadHistory()
  }

  return { messages, isLoading, isStreaming, threadId, sendMessage, abort, switchThread, loadHistory }
}

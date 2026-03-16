<script setup lang="ts">
interface Message {
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<Message[]>([])
const isLoading = ref(false)
const isStreaming = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const threadId = ref(crypto.randomUUID())

async function sendMessage(input: string) {
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

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      const events = buffer.split('\n\n')
      buffer = events.pop()!

      for (const eventStr of events) {
        if (!eventStr.trim()) continue

        const lines = eventStr.split('\n')
        let eventType = ''
        let data = ''

        for (const line of lines) {
          if (line.startsWith('event: ')) eventType = line.slice(7)
          if (line.startsWith('data: ')) data = line.slice(6)
        }

        if (eventType === 'token' && data) {
          if (!isStreaming.value) isStreaming.value = true
          const parsed = JSON.parse(data)
          assistantMessage.content += parsed.content
        }
      }
    }

    if (!assistantMessage.content) {
      assistantMessage.content = '（応答を取得できませんでした）'
    }
  } catch (error) {
    console.error('Chat error:', error)
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg?.role === 'assistant' && !lastMsg.content) {
      messages.value.pop()
    }
  } finally {
    isLoading.value = false
    isStreaming.value = false
  }
}

watch(
  () => {
    const len = messages.value.length
    const last = messages.value[len - 1]
    return `${len}:${last?.content.length ?? 0}`
  },
  async () => {
    await nextTick()
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  },
)
</script>

<template>
  <div class="chat-page">
    <header class="chat-header">
      <h1>Analogy AI</h1>
    </header>

    <main class="chat-messages" ref="messagesContainer">
      <ChatMessage
        v-for="(msg, i) in messages"
        :key="i"
        :role="msg.role"
        :content="msg.content"
      />
      <div v-if="isLoading && !isStreaming" class="loading-indicator">
        考え中...
      </div>
    </main>

    <ChatInput :disabled="isLoading" @send="sendMessage" />
  </div>
</template>

<style scoped>
.chat-page {
  height: 100dvh;
  display: flex;
  flex-direction: column;
  background: #fafafa;
}

.chat-header {
  padding: 0.75rem 1rem;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.chat-header h1 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
}

.loading-indicator {
  align-self: flex-start;
  padding: 0.75rem 1rem;
  color: #6b7280;
  font-style: italic;
}
</style>

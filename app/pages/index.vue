<script setup lang="ts">
interface Message {
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<Message[]>([])
const isLoading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const threadId = ref(crypto.randomUUID())

async function sendMessage(input: string) {
  if (!input) return

  messages.value.push({ role: 'user', content: input })
  isLoading.value = true

  try {
    const data = await $fetch('/api/chat', {
      method: 'POST',
      body: { message: input, threadId: threadId.value },
    })
    messages.value.push(data.message)
  } catch (error) {
    console.error('Chat error:', error)
  } finally {
    isLoading.value = false
  }
}

watch(
  () => messages.value.length,
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
      <div v-if="isLoading" class="loading-indicator">
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

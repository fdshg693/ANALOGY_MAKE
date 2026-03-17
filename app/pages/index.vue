<script setup lang="ts">
import { useChat } from '~/composables/useChat'

const { messages, isLoading, isStreaming, sendMessage } = useChat()
const messagesContainer = ref<HTMLElement | null>(null)

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
        :is-error="msg.isError"
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

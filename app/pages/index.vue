<script setup lang="ts">
import { useChat } from '~/composables/useChat'
import { useThreads } from '~/composables/useThreads'

const { messages, isLoading, isStreaming, sendMessage, abort, switchThread } = useChat()
const {
  threads, activeThreadId, isLoadingThreads,
  loadThreads, createNewThread, setActiveThread, initActiveThread,
} = useThreads()

const messagesContainer = ref<HTMLElement | null>(null)

// 初期化
onMounted(async () => {
  initActiveThread()
  await loadThreads()
  if (activeThreadId.value) {
    switchThread(activeThreadId.value)
  } else {
    handleNewThread()
  }
})

function handleSelectThread(threadId: string) {
  setActiveThread(threadId)
  switchThread(threadId)
}

function handleNewThread() {
  const newId = createNewThread()
  switchThread(newId)
}

async function handleSend(content: string) {
  await sendMessage(content)
  await loadThreads()
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
  <div class="app-layout">
    <ThreadSidebar
      :threads="threads"
      :active-thread-id="activeThreadId"
      :is-loading="isLoadingThreads"
      @select-thread="handleSelectThread"
      @new-thread="handleNewThread"
    />
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

      <ChatInput
        :disabled="isLoading"
        :is-streaming="isStreaming"
        @send="handleSend"
        @abort="abort"
      />
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100dvh;
}

.chat-page {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fafafa;
  min-width: 0;
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

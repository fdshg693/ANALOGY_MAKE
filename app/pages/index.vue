<script setup lang="ts">
import { useChat } from '~/composables/useChat'
import { useThreads } from '~/composables/useThreads'
import { useSettings } from '~/composables/useSettings'
import { useBranches, MAIN_BRANCH_ID } from '~/composables/useBranches'
import type { EditMode } from '~/components/ChatInput.vue'

const { messages, isLoading, isStreaming, sendMessage, abort, switchThread } = useChat()
const {
  threads, activeThreadId, isLoadingThreads,
  loadThreads, createNewThread, setActiveThread, initActiveThread,
} = useThreads()
const { settings, isSaving, loadSettings, saveSettings } = useSettings()
const { branches, activeBranchId, loadBranches, setActiveBranch, fork } = useBranches()
const showSettings = ref(false)
const editMode = ref<EditMode | null>(null)

const messagesContainer = ref<HTMLElement | null>(null)

onMounted(async () => {
  initActiveThread()
  await loadThreads()
  if (activeThreadId.value) {
    await loadBranches(activeThreadId.value)
    switchThread(activeThreadId.value, activeBranchId.value)
    loadSettings(activeThreadId.value)
  } else {
    handleNewThread()
  }
})

async function handleSelectThread(threadId: string) {
  setActiveThread(threadId)
  editMode.value = null
  await loadBranches(threadId)
  switchThread(threadId, activeBranchId.value)
  loadSettings(threadId)
}

async function handleNewThread() {
  const newId = createNewThread()
  editMode.value = null
  await loadBranches(newId)
  switchThread(newId, MAIN_BRANCH_ID)
  loadSettings(newId)
}

async function handleSend(content: string) {
  await sendMessage(content)
  await loadThreads()
}

function handleStartEdit(messageIndex: number) {
  const msg = messages.value[messageIndex]
  if (!msg || msg.role !== 'user') return
  editMode.value = { messageIndex, originalText: msg.content }
}

function handleCancelEdit() {
  editMode.value = null
}

async function handleSubmitEdit(payload: { messageIndex: number, newText: string }) {
  const threadId = activeThreadId.value
  if (!threadId) return
  const fromBranchId = activeBranchId.value
  const forkMessageIndex = payload.messageIndex

  editMode.value = null

  try {
    await fork({ threadId, fromBranchId, forkMessageIndex })
  } catch (e) {
    console.error('Fork failed:', e)
    return
  }

  switchThread(threadId, activeBranchId.value)
  await sendMessage(payload.newText)
  await loadThreads()
}

async function handleChangeBranch(newBranchId: string) {
  const threadId = activeThreadId.value
  if (!threadId) return
  editMode.value = null
  await setActiveBranch(threadId, newBranchId)
  switchThread(threadId, newBranchId)
}

function branchForkIndexSet() {
  const s = new Set<number>()
  for (const b of branches.value) {
    if (b.forkMessageIndex !== null) s.add(b.forkMessageIndex)
  }
  return s
}

const forkIndices = computed(() => branchForkIndexSet())

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
        <button class="settings-toggle" @click="showSettings = !showSettings">
          &#9881;
        </button>
      </header>

      <SettingsPanel
        v-if="showSettings"
        :settings="settings"
        :is-saving="isSaving"
        @update:settings="settings = $event"
        @save="saveSettings"
      />

      <main class="chat-messages" ref="messagesContainer">
        <template v-for="(msg, i) in messages" :key="i">
          <ChatMessage
            :role="msg.role"
            :content="msg.content"
            :is-error="msg.isError"
            :is-streaming="isStreaming && i === messages.length - 1"
            :editable="msg.role === 'user' && !isStreaming"
            @start-edit="handleStartEdit(i)"
          >
            <template #branch-nav>
              <BranchNavigator
                v-if="msg.role === 'user' && forkIndices.has(i)"
                :branches="branches"
                :active-branch-id="activeBranchId"
                :fork-message-index="i"
                @change-branch="handleChangeBranch"
              />
            </template>
          </ChatMessage>
          <SearchResultsList
            v-if="msg.role === 'assistant' && msg.searchResults?.length"
            :results="msg.searchResults"
          />
        </template>
        <div v-if="isLoading && !isStreaming" class="loading-indicator">
          考え中...
        </div>
      </main>

      <ChatInput
        :disabled="isLoading"
        :is-streaming="isStreaming"
        :edit-mode="editMode"
        @send="handleSend"
        @abort="abort"
        @submit-edit="handleSubmitEdit"
        @cancel-edit="handleCancelEdit"
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
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.settings-toggle {
  background: none;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  padding: 0.375rem 0.625rem;
  font-size: 1.125rem;
  cursor: pointer;
  color: #6b7280;
  transition: background 0.15s;
}

.settings-toggle:hover {
  background: #f3f4f6;
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

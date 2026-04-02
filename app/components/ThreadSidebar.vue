<script setup lang="ts">
import type { Thread } from '../composables/useThreads'

defineProps<{
  threads: Thread[]
  activeThreadId: string
  isLoading: boolean
}>()

const emit = defineEmits<{
  selectThread: [threadId: string]
  newThread: []
}>()
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h2>スレッド</h2>
      <button class="new-thread-btn" @click="emit('newThread')">
        + 新規
      </button>
    </div>
    <div class="thread-list">
      <div v-if="isLoading" class="loading">読み込み中...</div>
      <button
        v-for="thread in threads"
        :key="thread.threadId"
        class="thread-item"
        :class="{ active: thread.threadId === activeThreadId }"
        @click="emit('selectThread', thread.threadId)"
      >
        <span class="thread-title">{{ thread.title }}</span>
      </button>
      <div v-if="!isLoading && threads.length === 0" class="empty">
        スレッドがありません
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 240px;
  min-width: 240px;
  background: #f9fafb;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
}

.new-thread-btn {
  padding: 0.25rem 0.75rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: #fff;
  background: #3b82f6;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}

.new-thread-btn:hover {
  background: #2563eb;
}

.thread-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.thread-item {
  display: block;
  width: 100%;
  padding: 0.625rem 0.75rem;
  margin-bottom: 2px;
  text-align: left;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
  color: #374151;
  font-size: 0.875rem;
}

.thread-item:hover {
  background: #e5e7eb;
}

.thread-item.active {
  background: #dbeafe;
  color: #1d4ed8;
  font-weight: 500;
}

.thread-title {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.loading,
.empty {
  padding: 1rem;
  text-align: center;
  color: #9ca3af;
  font-size: 0.8125rem;
}
</style>

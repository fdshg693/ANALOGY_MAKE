<script setup lang="ts">
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps<{
  role: 'user' | 'assistant'
  content: string
  isError?: boolean
}>()

const renderedHtml = computed(() => {
  if (props.role !== 'assistant') return ''
  const html = marked.parse(props.content) as string
  if (import.meta.client) {
    return DOMPurify.sanitize(html)
  }
  return html
})
</script>

<template>
  <div class="chat-message" :class="[role, { error: isError }]">
    <span class="role-label">{{ role === 'user' ? 'You' : 'AI' }}</span>
    <div v-if="role === 'assistant'" class="message-content markdown-body" v-html="renderedHtml"></div>
    <div v-else class="message-content">{{ content }}</div>
  </div>
</template>

<style scoped>
.chat-message {
  display: flex;
  flex-direction: column;
  max-width: 80%;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 0.75rem;
}

.chat-message.user {
  align-self: flex-end;
  background-color: #dbeafe;
  color: #1e3a5f;
}

.chat-message.assistant {
  align-self: flex-start;
  background-color: #f3f4f6;
  color: #1f2937;
}

.chat-message.error {
  background-color: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.role-label {
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
  opacity: 0.7;
}

.message-content {
  line-height: 1.5;
}

.chat-message.user .message-content {
  white-space: pre-wrap;
}

.message-content.markdown-body :deep(h1),
.message-content.markdown-body :deep(h2),
.message-content.markdown-body :deep(h3) {
  margin-top: 0.75rem;
  margin-bottom: 0.25rem;
  font-weight: 600;
  line-height: 1.3;
}

.message-content.markdown-body :deep(h1) { font-size: 1.25rem; }
.message-content.markdown-body :deep(h2) { font-size: 1.1rem; }
.message-content.markdown-body :deep(h3) { font-size: 1rem; }

.message-content.markdown-body :deep(p) {
  margin: 0.5rem 0;
}

.message-content.markdown-body :deep(ul),
.message-content.markdown-body :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.message-content.markdown-body :deep(li) {
  margin: 0.25rem 0;
}

.message-content.markdown-body :deep(strong) {
  font-weight: 600;
}

.message-content.markdown-body :deep(code) {
  background-color: rgba(0, 0, 0, 0.06);
  padding: 0.15rem 0.35rem;
  border-radius: 0.25rem;
  font-size: 0.9em;
  font-family: 'Consolas', 'Monaco', monospace;
}

.message-content.markdown-body :deep(pre) {
  background-color: rgba(0, 0, 0, 0.06);
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 0.5rem 0;
}

.message-content.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
}

.message-content.markdown-body :deep(blockquote) {
  border-left: 3px solid #d1d5db;
  padding-left: 0.75rem;
  margin: 0.5rem 0;
  color: #6b7280;
}

.message-content.markdown-body :deep(> :first-child) {
  margin-top: 0;
}

.message-content.markdown-body :deep(> :last-child) {
  margin-bottom: 0;
}
</style>

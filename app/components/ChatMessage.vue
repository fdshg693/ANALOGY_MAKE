<script setup lang="ts">
defineProps<{
  role: 'user' | 'assistant'
  content: string
  isError?: boolean
}>()
</script>

<template>
  <div class="chat-message" :class="[role, { error: isError }]">
    <span class="role-label">{{ role === 'user' ? 'You' : 'AI' }}</span>
    <div class="message-content">{{ content }}</div>
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
  white-space: pre-wrap;
  line-height: 1.5;
}
</style>

<script setup lang="ts">
defineProps<{
  disabled: boolean
}>()

const emit = defineEmits<{
  send: [content: string]
}>()

const input = ref('')

function handleSubmit() {
  if (!input.value.trim()) return
  emit('send', input.value.trim())
  input.value = ''
}
</script>

<template>
  <form class="chat-input" @submit.prevent="handleSubmit">
    <input
      v-model="input"
      type="text"
      placeholder="メッセージを入力..."
      :disabled="disabled"
    />
    <button type="submit" :disabled="disabled || !input.trim()">
      送信
    </button>
  </form>
</template>

<style scoped>
.chat-input {
  display: flex;
  gap: 0.5rem;
  padding: 1rem;
  border-top: 1px solid #e5e7eb;
  background: #fff;
}

.chat-input input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 1rem;
  outline: none;
}

.chat-input input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.chat-input button {
  padding: 0.75rem 1.5rem;
  background-color: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  cursor: pointer;
}

.chat-input button:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}
</style>

<script setup lang="ts">
import type { ThreadSettings, SearchSettings } from '~/composables/useSettings'

const props = defineProps<{
  settings: ThreadSettings
  isSaving: boolean
}>()

const emit = defineEmits<{
  'update:settings': [value: ThreadSettings]
  'save': []
}>()

const granularityOptions: { value: ThreadSettings['granularity']; label: string }[] = [
  { value: 'concise', label: '簡潔' },
  { value: 'standard', label: '標準' },
  { value: 'detailed', label: '詳細' },
]

const responseModeOptions: { value: ThreadSettings['responseMode']; label: string }[] = [
  { value: 'ai', label: 'AI' },
  { value: 'echo', label: 'エコー' },
]

const isDev = import.meta.dev

function selectGranularity(value: ThreadSettings['granularity']) {
  emit('update:settings', { ...props.settings, granularity: value })
}

function selectResponseMode(value: ThreadSettings['responseMode']) {
  emit('update:settings', { ...props.settings, responseMode: value })
}

function updateCustomInstruction(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:settings', { ...props.settings, customInstruction: target.value })
}

function updateSystemPromptOverride(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:settings', { ...props.settings, systemPromptOverride: target.value })
}

function updateSearch(patch: Partial<SearchSettings>) {
  emit('update:settings', {
    ...props.settings,
    search: { ...props.settings.search, ...patch },
  })
}

const searchDepthOptions: { value: SearchSettings['depth']; label: string }[] = [
  { value: 'basic', label: 'basic' },
  { value: 'advanced', label: 'advanced' },
]

const maxResultsOptions = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
</script>

<template>
  <div class="settings-panel">
    <div class="settings-section">
      <label class="settings-label">回答粒度:</label>
      <div class="granularity-buttons">
        <button
          v-for="option in granularityOptions"
          :key="option.value"
          :class="['granularity-btn', { active: settings.granularity === option.value }]"
          @click="selectGranularity(option.value)"
        >
          {{ option.label }}
        </button>
      </div>
    </div>

    <div class="settings-section">
      <label class="settings-label">カスタム指示:</label>
      <textarea
        class="custom-instruction"
        :value="settings.customInstruction"
        placeholder="例: 英語で回答して"
        rows="3"
        @input="updateCustomInstruction"
      />
    </div>

    <div class="settings-section">
      <label class="settings-label">Web検索:</label>
      <div class="search-row">
        <label class="search-toggle">
          <input
            type="checkbox"
            :checked="settings.search.enabled"
            @change="updateSearch({ enabled: ($event.target as HTMLInputElement).checked })"
          >
          <span>有効</span>
        </label>

        <select
          class="search-select"
          :value="settings.search.depth"
          :disabled="!settings.search.enabled"
          @change="updateSearch({ depth: ($event.target as HTMLSelectElement).value as SearchSettings['depth'] })"
        >
          <option v-for="opt in searchDepthOptions" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>

        <select
          class="search-select"
          :value="settings.search.maxResults"
          :disabled="!settings.search.enabled"
          @change="updateSearch({ maxResults: Number(($event.target as HTMLSelectElement).value) })"
        >
          <option v-for="n in maxResultsOptions" :key="n" :value="n">{{ n }}件</option>
        </select>
      </div>
    </div>

    <div class="settings-section">
      <label class="settings-label">応答モード:</label>
      <div class="granularity-buttons">
        <button
          v-for="opt in responseModeOptions"
          :key="opt.value"
          :class="['granularity-btn', { active: settings.responseMode === opt.value }]"
          @click="selectResponseMode(opt.value)"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>

    <div v-if="isDev" class="settings-section">
      <label class="settings-label">システムプロンプト上書き（開発のみ）:</label>
      <textarea
        class="custom-instruction"
        :value="settings.systemPromptOverride"
        placeholder="各ノードのシステムプロンプト先頭に追記されます"
        rows="4"
        @input="updateSystemPromptOverride"
      />
    </div>

    <div class="settings-actions">
      <button
        class="save-btn"
        :disabled="isSaving"
        @click="emit('save')"
      >
        {{ isSaving ? '保存中...' : '保存' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.settings-panel {
  padding: 0.75rem 1rem;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.settings-section {
  margin-bottom: 0.75rem;
}

.settings-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.375rem;
}

.granularity-buttons {
  display: flex;
  gap: 0.5rem;
}

.granularity-btn {
  padding: 0.375rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: #f3f4f6;
  color: #374151;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.granularity-btn:hover {
  background: #e5e7eb;
}

.granularity-btn.active {
  background: #3b82f6;
  color: #fff;
  border-color: #3b82f6;
}

.custom-instruction {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-family: inherit;
  resize: vertical;
  box-sizing: border-box;
}

.custom-instruction:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px #3b82f6;
}

.search-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.search-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: #374151;
  cursor: pointer;
}

.search-select {
  padding: 0.25rem 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: #fff;
  color: #374151;
  font-size: 0.875rem;
  font-family: inherit;
}

.search-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px #3b82f6;
}

.search-select:disabled {
  background: #f3f4f6;
  color: #9ca3af;
  cursor: not-allowed;
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
}

.save-btn {
  padding: 0.375rem 1rem;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.15s;
}

.save-btn:hover {
  background: #2563eb;
}

.save-btn:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}
</style>

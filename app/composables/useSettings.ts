export interface SearchSettings {
  enabled: boolean
  depth: 'basic' | 'advanced'
  maxResults: number
}

export type ResponseMode = 'ai' | 'echo'

export interface ThreadSettings {
  granularity: 'concise' | 'standard' | 'detailed'
  customInstruction: string
  search: SearchSettings
  responseMode: ResponseMode
  systemPromptOverride: string
  activeBranchId: string
}

const DEFAULT_SEARCH_SETTINGS: SearchSettings = {
  enabled: true,
  depth: 'basic',
  maxResults: 3,
}

const DEFAULT_SETTINGS: ThreadSettings = {
  granularity: 'standard',
  customInstruction: '',
  search: { ...DEFAULT_SEARCH_SETTINGS },
  responseMode: 'ai',
  systemPromptOverride: '',
  activeBranchId: 'main',
}

export function useSettings() {
  const settings = ref<ThreadSettings>({ ...DEFAULT_SETTINGS })
  const isSaving = ref(false)
  let currentThreadId = ''

  async function loadSettings(threadId: string): Promise<void> {
    currentThreadId = threadId
    if (!threadId) {
      settings.value = { ...DEFAULT_SETTINGS }
      return
    }
    try {
      const data = await $fetch<ThreadSettings>(`/api/threads/${threadId}/settings`)
      settings.value = data
    } catch {
      settings.value = { ...DEFAULT_SETTINGS }
    }
  }

  async function saveSettings(): Promise<void> {
    if (!currentThreadId) return
    isSaving.value = true
    try {
      await $fetch(`/api/threads/${currentThreadId}/settings`, {
        method: 'PUT',
        body: settings.value,
      })
    } finally {
      isSaving.value = false
    }
  }

  return { settings, isSaving, loadSettings, saveSettings }
}

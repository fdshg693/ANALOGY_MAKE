export interface ThreadSettings {
  granularity: 'concise' | 'standard' | 'detailed'
  customInstruction: string
}

const DEFAULT_SETTINGS: ThreadSettings = {
  granularity: 'standard',
  customInstruction: '',
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

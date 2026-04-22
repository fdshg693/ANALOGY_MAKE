import { DEFAULT_SETTINGS, DEFAULT_SEARCH_SETTINGS } from '../../server/utils/thread-store'
import type { ThreadSettings } from '../../server/utils/thread-store'

export function makeThreadSettings(override: Partial<ThreadSettings> = {}): ThreadSettings {
  return {
    ...DEFAULT_SETTINGS,
    ...override,
    search: { ...DEFAULT_SEARCH_SETTINGS, ...(override.search ?? {}) },
  }
}

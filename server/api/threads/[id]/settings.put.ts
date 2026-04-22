import { defineEventHandler, getRouterParam, readBody, createError } from 'h3'
import { updateThreadSettings, DEFAULT_SEARCH_SETTINGS } from '../../../utils/thread-store'
import type { ThreadSettings, SearchSettings, ResponseMode } from '../../../utils/thread-store'
import { MAIN_BRANCH_ID } from '../../../utils/langgraph-thread'
import { branchBelongsToThread } from '../../../utils/branch-store'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id is required' })
  const body = await readBody(event)
  const validGranularity = ['concise', 'standard', 'detailed']
  const granularity = validGranularity.includes(body.granularity) ? body.granularity : 'standard'
  const customInstruction = typeof body.customInstruction === 'string' ? body.customInstruction.slice(0, 500) : ''

  const rawSearch = body.search as Partial<SearchSettings> | undefined
  const parsedMax = Number(rawSearch?.maxResults)
  const search: SearchSettings = {
    enabled: typeof rawSearch?.enabled === 'boolean' ? rawSearch.enabled : DEFAULT_SEARCH_SETTINGS.enabled,
    depth: rawSearch?.depth === 'advanced' ? 'advanced' : 'basic',
    maxResults: Number.isInteger(parsedMax)
      ? Math.min(10, Math.max(1, parsedMax))
      : DEFAULT_SEARCH_SETTINGS.maxResults,
  }

  const responseMode: ResponseMode = body.responseMode === 'echo' ? 'echo' : 'ai'

  const isDev = process.env.NODE_ENV !== 'production'
  const systemPromptOverride = isDev && typeof body.systemPromptOverride === 'string'
    ? body.systemPromptOverride.slice(0, 2000)
    : ''

  const rawActiveBranchId = typeof body.activeBranchId === 'string' ? body.activeBranchId : MAIN_BRANCH_ID
  const activeBranchId =
    rawActiveBranchId === MAIN_BRANCH_ID || branchBelongsToThread(id, rawActiveBranchId)
      ? rawActiveBranchId
      : MAIN_BRANCH_ID

  const settings: ThreadSettings = {
    granularity,
    customInstruction,
    search,
    responseMode,
    systemPromptOverride,
    activeBranchId,
  }
  updateThreadSettings(id, settings)
  return settings
})

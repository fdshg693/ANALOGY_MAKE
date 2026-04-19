import { defineEventHandler, getRouterParam, readBody, createError } from 'h3'
import { updateThreadSettings } from '../../../utils/thread-store'
import type { ThreadSettings } from '../../../utils/thread-store'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id is required' })
  const body = await readBody(event)
  const validGranularity = ['concise', 'standard', 'detailed']
  const granularity = validGranularity.includes(body.granularity) ? body.granularity : 'standard'
  const customInstruction = typeof body.customInstruction === 'string' ? body.customInstruction.slice(0, 500) : ''
  const settings: ThreadSettings = { granularity, customInstruction }
  updateThreadSettings(id, settings)
  return settings
})

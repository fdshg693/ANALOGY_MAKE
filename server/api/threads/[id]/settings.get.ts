import { defineEventHandler, getRouterParam, createError } from 'h3'
import { getThreadSettings } from '../../../utils/thread-store'

export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id is required' })
  return getThreadSettings(id)
})

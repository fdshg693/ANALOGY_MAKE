import { defineEventHandler } from 'h3'
import { getThreads } from '../utils/thread-store'

export default defineEventHandler(() => {
  const threads = getThreads()
  return {
    threads: threads.map(t => ({
      threadId: t.thread_id,
      title: t.title,
      createdAt: t.created_at,
      updatedAt: t.updated_at,
    }))
  }
})

export interface SSECallbacks {
  onToken: (content: string) => void
  onDone: () => void
  onError: (message: string) => void
  onSearchResults?: (results: unknown[]) => void
}

export async function parseSSEStream(
  stream: ReadableStream<Uint8Array>,
  callbacks: SSECallbacks,
): Promise<void> {
  const reader = stream.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    const events = buffer.split('\n\n')
    buffer = events.pop()!

    for (const eventStr of events) {
      if (!eventStr.trim()) continue

      const lines = eventStr.split('\n')
      let eventType = ''
      let data = ''

      for (const line of lines) {
        if (line.startsWith('event: ')) eventType = line.slice(7)
        if (line.startsWith('data: ')) data = line.slice(6)
      }

      if (eventType === 'token' && data) {
        const parsed = JSON.parse(data)
        callbacks.onToken(parsed.content)
      }

      if (eventType === 'search_results' && data) {
        const parsed = JSON.parse(data)
        callbacks.onSearchResults?.(Array.isArray(parsed.results) ? parsed.results : [])
      }

      if (eventType === 'done') {
        callbacks.onDone()
        return
      }

      if (eventType === 'error' && data) {
        const parsed = JSON.parse(data)
        callbacks.onError(parsed.message)
        return
      }
    }
  }
}

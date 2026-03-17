import { describe, it, expect, vi } from 'vitest'
import { parseSSEStream, type SSECallbacks } from '~/app/utils/sse-parser'

function createSSEStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk))
      }
      controller.close()
    },
  })
}

function createCallbacks(): SSECallbacks & {
  onToken: ReturnType<typeof vi.fn>
  onDone: ReturnType<typeof vi.fn>
  onError: ReturnType<typeof vi.fn>
} {
  return {
    onToken: vi.fn(),
    onDone: vi.fn(),
    onError: vi.fn(),
  }
}

describe('parseSSEStream', () => {
  // 正常系
  describe('正常系', () => {
    it('基本フロー: token → done', async () => {
      const stream = createSSEStream([
        'event: token\ndata: {"content":"Hello"}\n\n',
        'event: done\ndata: {}\n\n',
      ])
      const cb = createCallbacks()

      await parseSSEStream(stream, cb)

      expect(cb.onToken).toHaveBeenCalledOnce()
      expect(cb.onToken).toHaveBeenCalledWith('Hello')
      expect(cb.onDone).toHaveBeenCalledOnce()
      expect(cb.onError).not.toHaveBeenCalled()
    })

    it('複数トークン', async () => {
      const stream = createSSEStream([
        'event: token\ndata: {"content":"A"}\n\n',
        'event: token\ndata: {"content":"B"}\n\n',
        'event: token\ndata: {"content":"C"}\n\n',
        'event: done\ndata: {}\n\n',
      ])
      const cb = createCallbacks()

      await parseSSEStream(stream, cb)

      expect(cb.onToken).toHaveBeenCalledTimes(3)
      expect(cb.onToken).toHaveBeenNthCalledWith(1, 'A')
      expect(cb.onToken).toHaveBeenNthCalledWith(2, 'B')
      expect(cb.onToken).toHaveBeenNthCalledWith(3, 'C')
      expect(cb.onDone).toHaveBeenCalledOnce()
    })

    it('1チャンクに複数イベント', async () => {
      const stream = createSSEStream([
        'event: token\ndata: {"content":"A"}\n\nevent: token\ndata: {"content":"B"}\n\nevent: done\ndata: {}\n\n',
      ])
      const cb = createCallbacks()

      await parseSSEStream(stream, cb)

      expect(cb.onToken).toHaveBeenCalledTimes(2)
      expect(cb.onToken).toHaveBeenNthCalledWith(1, 'A')
      expect(cb.onToken).toHaveBeenNthCalledWith(2, 'B')
      expect(cb.onDone).toHaveBeenCalledOnce()
    })
  })

  // バッファ分割
  describe('バッファ分割', () => {
    it('イベントがチャンク境界で分断', async () => {
      const stream = createSSEStream([
        'event: tok',
        'en\ndata: {"content":"Hi"}\n\nevent: done\ndata: {}\n\n',
      ])
      const cb = createCallbacks()

      await parseSSEStream(stream, cb)

      expect(cb.onToken).toHaveBeenCalledWith('Hi')
      expect(cb.onDone).toHaveBeenCalledOnce()
    })

    it('data行が途中で分断', async () => {
      const stream = createSSEStream([
        'event: token\ndata: {"con',
        'tent":"World"}\n\nevent: done\ndata: {}\n\n',
      ])
      const cb = createCallbacks()

      await parseSSEStream(stream, cb)

      expect(cb.onToken).toHaveBeenCalledWith('World')
      expect(cb.onDone).toHaveBeenCalledOnce()
    })
  })

  // エラー系
  describe('エラー系', () => {
    it('error イベント受信', async () => {
      const stream = createSSEStream([
        'event: error\ndata: {"message":"Server error"}\n\n',
      ])
      const cb = createCallbacks()

      await parseSSEStream(stream, cb)

      expect(cb.onError).toHaveBeenCalledOnce()
      expect(cb.onError).toHaveBeenCalledWith('Server error')
      expect(cb.onDone).not.toHaveBeenCalled()
    })

    it('途中テキスト後の error', async () => {
      const stream = createSSEStream([
        'event: token\ndata: {"content":"A"}\n\n',
        'event: token\ndata: {"content":"B"}\n\n',
        'event: error\ndata: {"message":"Timeout"}\n\n',
      ])
      const cb = createCallbacks()

      await parseSSEStream(stream, cb)

      expect(cb.onToken).toHaveBeenCalledTimes(2)
      expect(cb.onError).toHaveBeenCalledWith('Timeout')
      expect(cb.onDone).not.toHaveBeenCalled()
    })
  })

  // エッジケース
  describe('エッジケース', () => {
    it('ストリーム終端（done なし）', async () => {
      const stream = createSSEStream([
        'event: token\ndata: {"content":"partial"}\n\n',
      ])
      const cb = createCallbacks()

      await parseSSEStream(stream, cb)

      expect(cb.onToken).toHaveBeenCalledWith('partial')
      expect(cb.onDone).not.toHaveBeenCalled()
      expect(cb.onError).not.toHaveBeenCalled()
    })

    it('空のイベント文字列はスキップ', async () => {
      const stream = createSSEStream([
        '\n\n\n\nevent: token\ndata: {"content":"ok"}\n\nevent: done\ndata: {}\n\n',
      ])
      const cb = createCallbacks()

      await parseSSEStream(stream, cb)

      expect(cb.onToken).toHaveBeenCalledOnce()
      expect(cb.onToken).toHaveBeenCalledWith('ok')
      expect(cb.onDone).toHaveBeenCalledOnce()
    })
  })
})

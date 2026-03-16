# ver4 実装計画: ストリーミングレスポンス対応

## 技術方針

| 項目 | 選定 |
|---|---|
| サーバー→クライアント通信 | SSE（Server-Sent Events） |
| サーバー側SSE | H3 `createEventStream`（h3 v1.15.6 で利用可能） |
| LangGraph ストリーミング | `agent.stream()` + `streamMode: "messages"` |
| クライアント側SSE受信 | `fetch` + `ReadableStream`（POST のため `EventSource` は使用不可） |

## 変更ファイル一覧

| ファイル | 変更内容 |
|---|---|
| `server/api/chat.post.ts` | SSEストリーミングに全面書き換え |
| `app/pages/index.vue` | fetch → SSE受信に変更、ストリーミング状態管理 |

## I1: サーバー側 — SSEストリーミング応答 (`server/api/chat.post.ts`)

### 変更概要

`agent.invoke()` → `agent.stream()` に変更し、トークンを SSE イベントとして逐次送信する。

### 実装詳細

```typescript
import { createEventStream } from 'h3'
import { AIMessageChunk } from '@langchain/core/messages'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  // バリデーション（既存と同じ）
  if (!body.message || typeof body.message !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'message is required' })
  }
  if (!body.threadId || typeof body.threadId !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'threadId is required' })
  }

  const agent = getAnalogyAgent()
  const eventStream = createEventStream(event)

  // ストリーミング処理を非同期で開始
  const streamTask = (async () => {
    try {
      const stream = await agent.stream(
        { messages: [{ role: "user", content: body.message }] },
        {
          configurable: { thread_id: body.threadId },
          streamMode: "messages",
        },
      )

      for await (const [chunk, _metadata] of stream) {
        // AIMessageChunk のテキストコンテンツのみを送信
        if (chunk instanceof AIMessageChunk && typeof chunk.content === 'string' && chunk.content) {
          await eventStream.push({
            event: 'token',
            data: JSON.stringify({ content: chunk.content }),
          })
        }
      }

      // 完了イベント
      await eventStream.push({
        event: 'done',
        data: '{}',
      })
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Unknown error'
      await eventStream.push({
        event: 'error',
        data: JSON.stringify({ message }),
      })
    } finally {
      await eventStream.close()
    }
  })()

  // クライアント切断時のクリーンアップ
  eventStream.onClosed(async () => {
    await eventStream.close()
  })

  return eventStream.send()
})
```

### SSE イベント仕様

| event | data | 説明 |
|---|---|---|
| `token` | `{"content": "..."}` | トークン1つ分のテキスト |
| `done` | `{}` | ストリーミング正常完了 |
| `error` | `{"message": "..."}` | エラー発生 |

### MemorySaver との整合性

- `agent.stream()` は内部で LangGraph のチェックポイント機構を通るため、ストリーミング完了時に会話履歴が MemorySaver に自動保存される
- 既存の `thread_id` ベースのセッション管理はそのまま機能する

## I2: クライアント側 — SSE受信とリアルタイム表示 (`app/pages/index.vue`)

### 変更概要

`$fetch` による一括取得を、`fetch` + `ReadableStream` による SSE 受信に変更する。

### 実装詳細

`sendMessage` 関数を以下に書き換える:

```typescript
async function sendMessage(input: string) {
  if (!input) return

  messages.value.push({ role: 'user', content: input })
  isLoading.value = true

  // 空の assistant メッセージを先に追加（ストリーミングで埋めていく）
  const assistantMessage: Message = { role: 'assistant', content: '' }
  messages.value.push(assistantMessage)

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: input, threadId: threadId.value }),
    })

    if (!response.ok || !response.body) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // SSE イベントは "\n\n" で区切られる
      const events = buffer.split('\n\n')
      buffer = events.pop()! // 未完成のイベントをバッファに残す

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
          assistantMessage.content += parsed.content
        }
        // 'done' と 'error' はループ終了で自然に処理される
      }
    }

    // ストリーミング後にコンテンツが空の場合のフォールバック
    if (!assistantMessage.content) {
      assistantMessage.content = '（応答を取得できませんでした）'
    }
  } catch (error) {
    console.error('Chat error:', error)
    // ストリーミング中にエラーが起きた場合、空メッセージを除去
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg.role === 'assistant' && !lastMsg.content) {
      messages.value.pop()
    }
  } finally {
    isLoading.value = false
  }
}
```

### ポイント

- **空メッセージの先行追加**: assistant メッセージオブジェクトを先に配列に入れ、同じ参照の `.content` を更新することで Vue のリアクティビティが動作する
- **ローディング表示**: `isLoading` が true の間は「考え中...」が表示されるが、assistant メッセージが追加された時点でそのメッセージ自体が表示されるため、ストリーミング開始後は自然にテキストが現れる
  - ただし、ストリーミング開始までの待機中（`fetch` の応答待ち）は引き続き「考え中...」が表示される
- **SSE パーサー**: `EventSource` は GET 専用のため、POST リクエストでは `fetch` + 手動パースが必要

### ローディング表示の改善

現在の「考え中...」表示は `v-if="isLoading"` で制御されている。ストリーミング中は空の assistant メッセージが表示されるため、以下の調整を行う:

```html
<div v-if="isLoading && !isStreaming" class="loading-indicator">
  考え中...
</div>
```

`isStreaming` フラグを追加し、最初のトークン受信時に `true` にする。これにより:
- 送信直後〜最初のトークン受信: 「考え中...」表示
- ストリーミング中: テキストが逐次表示（「考え中...」は非表示）

```typescript
const isStreaming = ref(false)

// sendMessage 内:
// 最初のトークン受信時
if (eventType === 'token' && data) {
  if (!isStreaming.value) isStreaming.value = true
  // ...
}

// finally ブロック内:
isStreaming.value = false
```

## 実装順序

1. **R1** — 自動スクロールのリファクタリング（REFACTOR.md 参照）
2. **I1** — サーバー側 SSE ストリーミング
3. **I2** — クライアント側 SSE 受信
4. **動作確認** — ブラウザでストリーミング表示、会話の継続、エラー時の挙動を確認

# ver7 実装計画

## 実装順序

1. テスト基盤のセットアップ
2. SSEパーサーの切り出し（リファクタリング）
3. `chat.post.ts` の明示的インポート追加（リファクタリング）
4. SSEパーサーのユニットテスト
5. サーバーAPIハンドラのテスト

---

## 1. テスト基盤のセットアップ

### 1-1. パッケージインストール

```bash
pnpm add -D vitest happy-dom
```

- `vitest` — テストランナー
- `happy-dom` — DOM環境（ver7では未使用だが、後続バージョンの composable テスト用に導入しておく）

### 1-2. `vitest.config.ts` 新規作成（プロジェクトルート）

```typescript
import { defineConfig } from 'vitest/config'
import { resolve } from 'path'

export default defineConfig({
  test: {
    environment: 'node',
  },
  resolve: {
    alias: {
      '~': resolve(__dirname, '.'),
    },
  },
})
```

- `environment: 'node'` — SSEパーサーもサーバーハンドラもNode環境で十分
- `~` エイリアス — Nuxt の `~` パス解決をテストでも有効にする

### 1-3. `package.json` にスクリプト追加

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

---

## 2. SSEパーサーの切り出し

### 2-1. `app/utils/sse-parser.ts` 新規作成

```typescript
export interface SSECallbacks {
  onToken: (content: string) => void
  onDone: () => void
  onError: (message: string) => void
}

/**
 * ReadableStream から SSE イベントを読み取り、コールバックで通知する。
 * 正常完了（done イベント受信）またはエラー（error イベント受信）で return する。
 * ストリーム終端に達した場合もそのまま return する。
 */
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
```

### 2-2. `app/pages/index.vue` の修正

`sendMessage()` 内のSSEパース処理（35〜87行目）を `parseSSEStream()` 呼び出しに置き換える。

変更後の `sendMessage()` の try ブロック内（fetch 成功後）:

```typescript
import { parseSSEStream } from '~/utils/sse-parser'

// response.ok && response.body チェック後:
let firstToken = true

await parseSSEStream(response.body, {
  onToken(content) {
    if (firstToken) {
      isStreaming.value = true
      firstToken = false
    }
    assistantMessage.content += content
  },
  onDone() {
    // 何もしない（finally で isLoading/isStreaming をリセット）
  },
  onError(message) {
    const errorText = `\n\n⚠ エラーが発生しました: ${message}`
    if (assistantMessage.content) {
      assistantMessage.content += errorText
    } else {
      assistantMessage.content = errorText.trimStart()
    }
    assistantMessage.isError = true
  },
})
```

空レスポンスチェック（89〜91行目）と catch/finally ブロックはそのまま維持。

**注意**: 元コードの `streamDone` フラグと二重ループ脱出パターンは不要になる。`parseSSEStream` 内部で `done`/`error` イベント受信時に `return` するため、同等の制御フローが関数内で完結する。

---

## 3. `chat.post.ts` の明示的インポート追加

`server/api/chat.post.ts` の先頭に以下のインポートを追加（既存の `createEventStream` import を拡張）:

```typescript
// 変更前
import { createEventStream } from 'h3'

// 変更後
import { createEventStream, readBody, createError, defineEventHandler } from 'h3'
import { getAnalogyAgent } from '../utils/analogy-agent'
```

コード本体は変更なし。

---

## 4. SSEパーサーのユニットテスト

### 4-1. `tests/utils/sse-parser.test.ts` 新規作成

ヘルパー: テスト用に SSE 形式の文字列から ReadableStream を生成する関数を用意する。

```typescript
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
```

### テストケース

#### 正常系
1. **基本フロー: token → done**
   - 入力: `["event: token\ndata: {\"content\":\"Hello\"}\n\n", "event: done\ndata: {}\n\n"]`
   - 検証: `onToken("Hello")` が1回、`onDone()` が1回呼ばれる

2. **複数トークン**
   - 入力: token イベント3つ + done
   - 検証: `onToken` が3回呼ばれ、引数が各トークンの content と一致

3. **1チャンクに複数イベント**
   - 入力: `["event: token\ndata: {\"content\":\"A\"}\n\nevent: token\ndata: {\"content\":\"B\"}\n\nevent: done\ndata: {}\n\n"]`
   - 検証: 全イベントが正しくパースされる

#### バッファ分割
4. **イベントがチャンク境界で分断**
   - 入力: `["event: tok", "en\ndata: {\"content\":\"Hi\"}\n\nevent: done\ndata: {}\n\n"]`
   - 検証: バッファリングにより正しくパースされる

5. **data 行が途中で分断**
   - 入力: data の JSON が2チャンクに分かれるケース
   - 検証: バッファリングにより正しくパースされる

#### エラー系
6. **error イベント受信**
   - 入力: `["event: error\ndata: {\"message\":\"Server error\"}\n\n"]`
   - 検証: `onError("Server error")` が呼ばれ、`onDone` は呼ばれない

7. **途中テキスト後の error**
   - 入力: token 2つ + error
   - 検証: `onToken` が2回呼ばれた後、`onError` が呼ばれる

#### エッジケース
8. **ストリーム終端（done なし）**
   - 入力: token のみでストリーム close
   - 検証: `onDone` も `onError` も呼ばれずに関数が return する

9. **空のイベント文字列（`\n\n` の連続）**
   - 入力: 空イベントを含むストリーム
   - 検証: 空イベントはスキップされ、有効なイベントのみ処理される

---

## 5. サーバーAPIハンドラのテスト

### 5-1. `tests/server/chat.test.ts` 新規作成

### モック戦略

- `../utils/analogy-agent` モジュールを `vi.mock()` でモック
  - `getAnalogyAgent()` がモックエージェントを返すようにする
  - モックエージェントの `stream()` メソッドは async generator を返す
- h3 の関数は実際のものを使用（`readBody` のみイベントオブジェクトを自前構築してモック）

### h3 イベントのモック

テスト用に最小限の h3 イベントを構築するヘルパーを用意する:

```typescript
import { createEvent } from 'h3'
import { Readable } from 'stream'
import { IncomingMessage, ServerResponse } from 'http'

function createMockEvent(body: Record<string, unknown>) {
  const json = JSON.stringify(body)
  const req = new IncomingMessage(/* ... */)
  // ... body を含む最小限の h3 Event を構築
}
```

※ h3 のイベント構築方法はテスト実装時に最適な方法を選定する。`createEvent` や直接の `readBody` モックなど、いくつかのアプローチを検討。

### テストケース

#### バリデーション
1. **message 欠落で 400 エラー**
   - 入力: `{ threadId: "test-id" }`（message なし）
   - 検証: statusCode 400 のエラーが throw される

2. **threadId 欠落で 400 エラー**
   - 入力: `{ message: "hello" }`（threadId なし）
   - 検証: statusCode 400 のエラーが throw される

3. **message が文字列でない場合に 400 エラー**
   - 入力: `{ message: 123, threadId: "test-id" }`
   - 検証: statusCode 400 のエラーが throw される

#### 正常系
4. **モックエージェントからのストリーム → SSE イベント形式**
   - モック: `agent.stream()` が `AIMessageChunk` を yield する async generator を返す
   - 検証: `eventStream.push()` が `{ event: 'token', data: '{"content":"..."}' }` 形式で呼ばれ、最後に `{ event: 'done', data: '{}' }` が送信される

#### エラー系
5. **エージェント呼び出し失敗 → error イベント送信**
   - モック: `agent.stream()` が例外を throw
   - 検証: `eventStream.push()` が `{ event: 'error', data: '{"message":"..."}' }` 形式で呼ばれ、`eventStream.close()` が呼ばれる

---

## ファイル変更一覧

| 操作 | ファイル | 内容 |
|---|---|---|
| 新規 | `vitest.config.ts` | Vitest 設定 |
| 新規 | `app/utils/sse-parser.ts` | SSEパーサーユーティリティ |
| 新規 | `tests/utils/sse-parser.test.ts` | SSEパーサーテスト |
| 新規 | `tests/server/chat.test.ts` | サーバーAPIテスト |
| 修正 | `app/pages/index.vue` | SSEパース処理を `parseSSEStream()` 呼び出しに置換 |
| 修正 | `server/api/chat.post.ts` | 明示的インポート追加 |
| 修正 | `package.json` | devDependencies 追加、test スクリプト追加 |

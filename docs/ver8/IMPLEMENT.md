# ver8 実装計画

## 1. `app/composables/useChat.ts` の新設

### エクスポートする型

```typescript
export interface Message {
  role: 'user' | 'assistant'
  content: string
  isError?: boolean
}
```

現在 `index.vue` 内で定義されている `Message` インターフェースをそのまま移動する。

### composable の API

```typescript
export function useChat() {
  const messages: Ref<Message[]>
  const isLoading: Ref<boolean>
  const isStreaming: Ref<boolean>
  const threadId: Ref<string>

  async function sendMessage(input: string): Promise<void>

  return { messages, isLoading, isStreaming, threadId, sendMessage }
}
```

### `sendMessage` の実装

`index.vue` の現在の `sendMessage` 関数をそのまま移植する。変更点なし:

1. 空入力ガード
2. ユーザーメッセージ＋空 assistant メッセージを `messages` に追加
3. `isLoading = true`, `isStreaming = false`
4. `fetch('/api/chat', ...)` で POST
5. `parseSSEStream` でコールバック処理（onToken / onDone / onError）
6. 初回トークンで `isStreaming = true`
7. エラー時は途中テキスト保持＋エラーメッセージ付記
8. `finally` で `isLoading = false`, `isStreaming = false`

import 文: `parseSSEStream` を相対パス `../utils/sse-parser` からインポートする。

> **パスエイリアスに関する注意**: `vitest.config.ts` の `~` エイリアスはプロジェクトルートを指すが、Nuxt の `~` は `app/` ディレクトリを指す。composable（`app/composables/`）から `~/utils/sse-parser` と書くと、Nuxt では `app/utils/sse-parser` に正しく解決されるが、vitest では `{root}/utils/sse-parser` に解決されてテストが失敗する。相対パス `../utils/sse-parser` を使うことで両環境で正しく解決される。

## 2. `index.vue` の修正

### 変更後の `<script setup>` ブロック（約10行）

```typescript
import { useChat } from '~/composables/useChat'

const { messages, isLoading, isStreaming, sendMessage } = useChat()
const messagesContainer = ref<HTMLElement | null>(null)

watch(
  () => {
    const len = messages.value.length
    const last = messages.value[len - 1]
    return `${len}:${last?.content.length ?? 0}`
  },
  async () => {
    await nextTick()
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  },
)
```

### 変更内容

- `Message` インターフェース定義を削除（composable からエクスポート）
- リアクティブ状態の宣言を削除（`useChat()` から取得）
- `sendMessage` 関数を削除（composable から取得）
- `parseSSEStream` の import を削除（composable 内部で使用）
- `threadId` は `useChat` 内部で生成。`index.vue` では使用しないため destructure しない
- テンプレート・スタイルは変更なし（既存のバインディングがそのまま動作する）

### 残るもの

- `messagesContainer` ref（DOM 参照、UI の関心事）
- auto-scroll の `watch`（UI の関心事）
- テンプレート（変更なし）
- スタイル（変更なし）

## 3. `tests/composables/useChat.test.ts` の新設

### テスト環境

- vitest の `environment: 'node'` で実行（Vue の `ref` は Node.js で動作する）
- `fetch` はグローバルモック（`vi.stubGlobal`）
- `parseSSEStream` はモジュールモック（composable の相対インポートの解決先パスでモック）

### モック戦略

```typescript
// parseSSEStream をモックし、コールバックを手動で呼び出す
// パスは composable 内の相対インポートの解決先と一致させる
vi.mock('../../../app/utils/sse-parser', () => ({
  parseSSEStream: vi.fn(),
}))
```

`parseSSEStream` のモックは、呼び出し時にコールバック引数を取得し、テスト内から `onToken` / `onDone` / `onError` を手動で発火する。これにより SSE ストリームの各シナリオを制御できる。

```typescript
// fetch のモック
vi.stubGlobal('fetch', vi.fn())

// crypto.randomUUID のモック — テストの再現性のため beforeEach で常にモックする
vi.stubGlobal('crypto', { randomUUID: () => 'mock-uuid' })
```

### テストケース

1. **初期状態**: `messages` が空、`isLoading` / `isStreaming` が `false`、`threadId` が存在する
2. **sendMessage — 正常系**:
   - ユーザーメッセージと空 assistant メッセージが追加される
   - `isLoading` が `true` になる
   - `fetch` が正しいパラメータで呼ばれる
   - `parseSSEStream` のコールバック経由でトークンが追加される
   - 初回トークンで `isStreaming` が `true` になる
   - 完了後 `isLoading` / `isStreaming` が `false` に戻る
3. **sendMessage — 空入力ガード**: 空文字列で呼ぶと何も起きない
4. **sendMessage — SSE エラー**: `onError` コールバック発火時にエラーメッセージが付記され、`isError` が設定される
5. **sendMessage — 通信エラー**: `fetch` が reject した場合のエラーハンドリング
6. **sendMessage — 空応答フォールバック**: コンテンツなし＋エラーなしの場合にフォールバックメッセージが設定される

## 4. 実装順序

1. `app/composables/useChat.ts` を作成（`index.vue` からロジックを移植）
2. `index.vue` を修正（composable を使用するように変更）
3. 動作確認（既存の振る舞いが保持されていること）
4. `tests/composables/useChat.test.ts` を作成
5. 全テスト実行（既存テスト + 新テスト）

## 5. 注意事項

- `ChatMessage.vue` の Props（`role`, `content`, `isError`）は `Message` 型のフィールドと一致しているが、Props は独自に `defineProps` で定義されており、`Message` 型を直接参照していない。そのため `Message` 型の移動による影響はない
- `sendMessage` 内の `assistantMessage` への直接ミューテーション（`assistantMessage.content += content`）は Vue のリアクティビティの仕組み上、`messages` 配列の要素への参照を保持して更新するパターン。composable に移植してもこの挙動は変わらない

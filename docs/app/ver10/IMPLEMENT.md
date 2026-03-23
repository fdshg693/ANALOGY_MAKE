# ver10 実装計画

事前リファクタリング不要（MemorySaver→SqliteSaverはドロップイン置換のため）

## 1. パッケージ追加

```bash
pnpm add @langchain/langgraph-checkpoint-sqlite
```

`@langchain/langgraph-checkpoint-sqlite` は内部で `better-sqlite3` に依存する。peer dependency として `better-sqlite3` の追加インストールが必要な場合は対応する。

## 2. サーバー側: チェックポインター差し替え

### `server/utils/analogy-agent.ts`

**変更内容**: `MemorySaver` → `SqliteSaver` に置き換え。`setup()` が非同期の可能性があるため、`getAnalogyAgent()` を async 化する。

```typescript
// Before
import { MemorySaver } from "@langchain/langgraph"
let _agent: ... | null = null
export function getAnalogyAgent() {
  if (!_agent) {
    const checkpointer = new MemorySaver()
    _agent = createAgent({ ..., checkpointer })
  }
  return _agent
}

// After
import { SqliteSaver } from "@langchain/langgraph-checkpoint-sqlite"
import { mkdirSync } from "node:fs"

const DB_PATH = "./data/langgraph-checkpoints.db"
let _agent: ... | null = null

export async function getAnalogyAgent() {
  if (!_agent) {
    mkdirSync("./data", { recursive: true })
    const checkpointer = SqliteSaver.fromConnString(DB_PATH)
    await checkpointer.setup()  // テーブル自動作成
    _agent = createAgent({ ..., checkpointer })
  }
  return _agent
}
```

- `SqliteSaver.fromConnString()` は `better-sqlite3` ベースのため同期処理
- `setup()` はインターフェース上 `async` のため `await` する（`better-sqlite3` が同期なので実質即時解決だが、型安全のため）
- `mkdirSync` で `data/` ディレクトリを初回起動時に自動作成
- **破壊的変更**: `getAnalogyAgent()` が async になるため、呼び出し元 (`chat.post.ts`, `chat/history.get.ts`) も `await` が必要

### `server/api/chat.post.ts` への影響

```typescript
// Before
const agent = getAnalogyAgent()

// After
const agent = await getAnalogyAgent()
```

既に async ハンドラ内のため、`await` 追加のみ

## 3. 会話履歴取得API

### `server/api/chat/history.get.ts`（新規）

**目的**: ページリロード後に過去のメッセージをUIに復元するためのエンドポイント

```
GET /api/chat/history?threadId=xxx
```

**レスポンス**:
```json
{
  "messages": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

**実装方針**:
- `await getAnalogyAgent()` で取得したエージェントの `getState({ configurable: { thread_id } })` を呼び出し、チェックポイントからメッセージ一覧を取得
- `HumanMessage` → `role: 'user'`、`AIMessage` → `role: 'assistant'` にマッピング
- threadId が存在しない・チェックポイントが空の場合は `{ messages: [] }` を返す（エラーにしない）
- `threadId` のバリデーション（必須・文字列型チェック、400エラー）

**`getState()` の返り値**: `createAgent` (from `langchain`) は LangGraph の `CompiledStateGraph` を返す。`getState({ configurable: { thread_id } })` は `StateSnapshot` を返し、`snapshot.values.messages` に `BaseMessage[]` が格納される。`BaseMessage` のサブクラス（`HumanMessage` / `AIMessage`）を `instanceof` で判定してロールをマッピングする。threadId が未知の場合は `values` が空オブジェクトになるため、`values?.messages` の存在チェックが必要

## 4. フロントエンド: threadId の永続化と履歴復元

### `app/composables/useChat.ts`

**変更1: threadId の localStorage 永続化**

```typescript
// Before
const threadId = ref(crypto.randomUUID())

// After
const THREAD_ID_KEY = 'analogy-threadId'

function getOrCreateThreadId(): string {
  if (import.meta.client) {
    const stored = localStorage.getItem(THREAD_ID_KEY)
    if (stored) return stored
  }
  const id = crypto.randomUUID()
  if (import.meta.client) {
    localStorage.setItem(THREAD_ID_KEY, id)
  }
  return id
}

const threadId = ref(getOrCreateThreadId())
```

- SSR時: `crypto.randomUUID()` で生成（fetchには使われないため問題なし）
- クライアント: localStorage から復元 or 新規生成して保存
- **ハイドレーション安全性**: `threadId` は `index.vue` で destructure されておらず（`{ messages, isLoading, isStreaming, sendMessage, abort }` のみ取得）、テンプレートに一切バインドされないため、SSR/クライアント間の値不一致はハイドレーションエラーを引き起こさない。Nuxt 4 デフォルトでSSR有効だが問題なし

**変更2: ページロード時の会話履歴復元**

```typescript
async function loadHistory(): Promise<void> {
  isLoading.value = true  // 履歴取得中は送信ボタンを無効化（競合防止）
  try {
    const res = await fetch(`/api/chat/history?threadId=${threadId.value}`)
    if (!res.ok) return
    const data = await res.json()
    if (data.messages?.length) {
      messages.value = data.messages
    }
  } catch {
    // 取得失敗時は空チャットで開始（エラー表示不要）
  } finally {
    isLoading.value = false
  }
}

// localStorage に threadId が存在する場合のみ履歴を取得
if (import.meta.client && localStorage.getItem(THREAD_ID_KEY)) {
  loadHistory()
}
```

- localStorage に threadId がある場合のみ API を呼ぶ（初回訪問時は呼ばない）
- **競合状態の防止**: `isLoading = true` を設定することで、履歴取得完了前のメッセージ送信を防ぐ（`ChatInput` の `disabled` が連動）。これにより `loadHistory()` 完了後に `messages.value` が上書きされる競合を回避
- 取得失敗時はサイレントに無視し、空チャットで開始

## 5. 設定ファイル更新

### `.gitignore`

SQLite データベースファイルを除外（Nuxt が生成する `.data/` とは別のドットなしディレクトリ）:

```
data/
```

### `nuxt.config.ts`

`better-sqlite3` はネイティブモジュールのため、Nuxt のバンドルから除外する設定が必要になる可能性がある:

```typescript
// 必要な場合のみ追加
nitro: {
  externals: {
    external: ['better-sqlite3'],
  },
}
```

`better-sqlite3` はネイティブバイナリ (`.node` ファイル) を含むため、Nitro のバンドルから除外する必要がある。ビルドエラーが発生した場合に対応する。

## 6. テスト

### 既存テストへの影響

- `tests/server/chat.test.ts`: `getAnalogyAgent` はモック済みのため、チェックポインター変更の影響なし。ただし `getAnalogyAgent` が async 化するため、モックの返り値を `Promise.resolve(mockAgent)` に変更する必要あり
- `tests/composables/useChat.test.ts`: `threadId` の初期化ロジック変更に伴うテスト修正が必要

### `tests/composables/useChat.test.ts` の修正

- `localStorage` のモック追加（`vi.stubGlobal` で `getItem` / `setItem` をスタブ）
- `import.meta.client` のモック: テスト環境（Node）では `false` になるため、`getOrCreateThreadId` は常に `crypto.randomUUID()` を呼ぶパスに入る。既存の `初期状態` テスト（`crypto.randomUUID` を `'mock-uuid'` でスタブ済み）はそのまま通る。localStorage パスのテストには `vi.stubGlobal` で `import.meta.client = true` を設定する
- テストケース追加:
  - localStorage に threadId がない → 新規生成して localStorage に保存
  - localStorage に threadId がある → そこから復元
  - 履歴取得 → messages に反映

### `tests/server/chat-history.test.ts`（新規）

- `getAnalogyAgent` のモック（`getState` メソッドを追加）
- テストケース:
  - threadId 欠落で 400 エラー
  - チェックポイントにメッセージあり → 正しいフォーマットで返却
  - チェックポイントが空 → `{ messages: [] }` を返却
  - `getState` がエラー → `{ messages: [] }` を返却

## 変更ファイル一覧

| ファイル | 変更種別 | 概要 |
|---|---|---|
| `package.json` | 修正 | `@langchain/langgraph-checkpoint-sqlite` 追加 |
| `server/utils/analogy-agent.ts` | 修正 | MemorySaver → SqliteSaver |
| `server/api/chat/history.get.ts` | **新規** | 会話履歴取得API |
| `app/composables/useChat.ts` | 修正 | threadId永続化 + 履歴ロード |
| `.gitignore` | 修正 | `data/` 追加 |
| `tests/composables/useChat.test.ts` | 修正 | localStorage テスト追加 |
| `tests/server/chat-history.test.ts` | **新規** | 履歴APIテスト |
| `nuxt.config.ts` | 修正（必要時） | ネイティブモジュール除外設定 |

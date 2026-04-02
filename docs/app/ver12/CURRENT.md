# ver12 完了時点のコード現況

ver11（複数スレッド管理）を経て、Tavily Search によるWeb検索連携を追加した状態。エージェントがステップ3（類似事例の提示）でWeb検索を活用し、LLM内部知識と統合して事例を提示できる。UIに変更はない。

## 依存パッケージバージョン

| パッケージ | バージョン |
|---|---|
| nuxt | ^4.4.2 |
| vue | ^3.5.30 |
| vue-router | ^5.0.3 |
| @langchain/core | ^1.1.32 |
| @langchain/openai | ^1.2.13 |
| @langchain/langgraph | ^1.2.2 |
| @langchain/langgraph-checkpoint-sqlite | ^1.0.1 |
| @langchain/tavily | ^1.2.0 |
| langchain | ^1.2.32 |
| better-sqlite3 | ^12.8.0 |
| marked | ^17.0.4 |
| dompurify | ^3.3.3 |
| vitest（dev） | ^4.1.0 |
| happy-dom（dev） | ^20.8.4 |
| @types/better-sqlite3（dev） | ^7.6.13 |
| dotenv（dev） | ^17.3.1 |
| tsx（dev） | ^4.21.0 |

`package.json` に `pnpm.onlyBuiltDependencies: ["better-sqlite3"]` を指定（ネイティブモジュールのビルド許可）。

## ファイル詳細

### `app/app.vue`（7行）

- `<NuxtRouteAnnouncer />` と `<NuxtPage />` を配置するルートレイアウト

### `app/composables/useChat.ts`（116行）

- `Message` インターフェース（`{ role: 'user' | 'assistant', content: string, isError?: boolean }`）をエクスポート
- `useChat()` composable をエクスポート。戻り値: `{ messages, isLoading, isStreaming, threadId, sendMessage, abort, switchThread, loadHistory }`
- リアクティブ状態:
  - `messages: Ref<Message[]>` — チャット履歴
  - `isLoading: Ref<boolean>` — 送信〜応答完了 or 履歴ロード中の全体ローディング
  - `isStreaming: Ref<boolean>` — 初回トークン受信〜ストリーム完了のストリーミング状態
  - `threadId: Ref<string>` — 初期値は空文字列。外部から `switchThread()` で設定
- `threadId` の初期化と永続化は `useThreads` composable が担当。`useChat` は `threadId` を受動的に受け取るのみ
- `threadId` 未設定時（空文字列）は `sendMessage()` が早期リターンするガード
- `loadHistory()` を公開関数としてエクスポート
- `switchThread(newThreadId)` — ストリーミング中なら `abort()` で自動中断、`messages` リセット、`threadId` 設定、`loadHistory()` 呼び出し
- `abortController: AbortController | null` — モジュールスコープの非リアクティブ変数
- `parseSSEStream` は相対パス `../utils/sse-parser` でインポート

### `app/composables/useThreads.ts`（86行）

- `Thread` インターフェース（`{ threadId, title, createdAt, updatedAt }`）をエクスポート
- `useThreads()` composable をエクスポート。戻り値: `{ threads, activeThreadId, isLoadingThreads, loadThreads, createNewThread, setActiveThread, initActiveThread, updateLocalTitle }`
- モジュールスコープのシングルトン状態: `threads`, `activeThreadId`, `isLoadingThreads`
- `ACTIVE_THREAD_KEY = 'analogy-threadId'` を localStorage キーとして使用
- `createNewThread()`: `crypto.randomUUID()` でID生成、楽観的に `threads` 先頭に追加、localStorage に保存
- `import.meta.client` ガードで SSR 安全性を確保

### `app/components/ThreadSidebar.vue`（130行）

- Props: `threads: Thread[]`, `activeThreadId: string`, `isLoading: boolean`
- Emits: `selectThread(threadId)`, `newThread()`
- サイドバー（幅 240px 固定）、ヘッダー（「スレッド」+ 「+ 新規」ボタン）、スレッド一覧（ボタンリスト）
- アクティブスレッド: 青背景（`#dbeafe`）で視覚的に区別

### `app/pages/index.vue`（133行）

- 2カラムレイアウト: `ThreadSidebar` + チャットエリア（`display: flex`, `height: 100dvh`）
- `useChat()` と `useThreads()` を統合利用
- 初期化フロー（`onMounted`）:
  1. `initActiveThread()` — localStorage からアクティブスレッドID復元
  2. `loadThreads()` — サーバーからスレッド一覧取得
  3. `activeThreadId` があれば `switchThread()` で会話履歴ロード、なければ `handleNewThread()` で新規作成
- 自動スクロール: `watch` で `messages.length` と最終メッセージの `content.length` を結合監視

### `app/utils/sse-parser.ts`（53行）

- `SSECallbacks` インターフェース: `onToken(content)`, `onDone()`, `onError(message)`
- `parseSSEStream(stream, callbacks): Promise<void>` — `ReadableStream` を消費しSSEイベントをコールバックで通知

### `app/components/ChatMessage.vue`（139行）

- Props: `role`, `content`, `isError?`
- assistant メッセージのみ `marked.parse()` → `DOMPurify.sanitize()` でリッチ HTML 生成

### `app/components/ChatInput.vue`（約85行）

- Props: `{ disabled, isStreaming }`
- Emits: `send(content)`, `abort()`
- ストリーミング中は赤色「停止」ボタン、通常時は青色「送信」ボタン

### `server/api/chat.post.ts`（92行）

- `POST /api/chat` SSE ストリーミングエンドポイント
- `upsertThread(body.threadId)` でスレッドメタデータ登録・更新
- ストリーム完了後にタイトル自動生成（`generateTitle()`、非同期・非ブロッキング）
- `generateTitle()`: `ChatOpenAI`（gpt-4.1-mini, temperature: 0, maxTokens: 30）で10文字以内の日本語タイトル生成
- ストリーミングフィルタ: `chunk instanceof AIMessageChunk && typeof chunk.content === 'string' && chunk.content` — ツール呼び出し時の `ToolMessage` や配列型 `content` を除外する防御的実装

### `server/api/threads.get.ts`（14行）

- `GET /api/threads` スレッド一覧取得エンドポイント
- `getThreads()` を呼び出し、`thread_id` → `threadId` などキャメルケースに変換して返却

### `server/api/chat/history.get.ts`（36行）

- `GET /api/chat/history?threadId=xxx` 会話履歴取得エンドポイント
- `(agent as any).getState()` で LangGraph チェックポイントからスナップショット取得

### `server/utils/analogy-agent.ts`（42行）— ver12 更新

- `getAnalogyAgent()`: シングルトンパターンで LangChain エージェントを初期化・保持
- `SqliteSaver.fromConnString("./data/langgraph-checkpoints.db")`
- `TavilySearch`（`@langchain/tavily`）をツールとして条件付きで追加:
  - `config.tavilyApiKey` が truthy の場合のみ `TavilySearch` インスタンスを生成（`maxResults: 3`）
  - キー未設定時は `tools: []` でフォールバック（ver11 と同等の動作）
- コンストラクタのパラメータ名は `tavilyApiKey`（`apiKey` ではない）

### `server/utils/analogy-prompt.ts`（34行）— ver12 更新

- `ANALOGY_SYSTEM_PROMPT` 定数。5ステップのアナロジー思考対話フロー
- ステップ3にWeb検索ツール活用の指示を追加:
  - `tavily_search` ツールを使って関連事例や最新情報を検索することを強く推奨
  - 検索結果から得られた実在の事例を優先的に取り上げ、内部知識と組み合わせる旨を記載
  - ReActエージェントの自律判断に委ねるため、プロンプトでの「必ず」は厳密な強制ではない

### `server/utils/thread-store.ts`（59行）

- `better-sqlite3` を直接インポートしてスレッドメタデータを CRUD 操作
- シングルトンパターンで DB 接続を管理（`getDb()`）、WAL モード
- `getThreads()`, `upsertThread()`, `updateThreadTitle()`, `getThreadTitle()`
- DB パス: `./data/langgraph-checkpoints.db`（LangGraph チェックポインターと同一ファイル）

### `nuxt.config.ts`（14行）— ver12 更新

- `compatibilityDate: '2025-07-15'`
- `runtimeConfig.openaiApiKey`, `runtimeConfig.tavilyApiKey`（ver12 追加）
- `nitro.externals.external: ['better-sqlite3']`

### `vitest.config.ts`（16行）

- `environment: 'node'`
- `define: { 'import.meta.client': 'globalThis.__NUXT_CLIENT__' }`

### `.env.example`（3行）— ver12 更新

- `OPENAI_API_KEY`、`NUXT_OPENAI_API_KEY`、`NUXT_TAVILY_API_KEY`（ver12 追加）の3行

### テストファイル

| ファイル | テストケース | 備考 |
|---|---|---|
| `tests/composables/useChat.test.ts` | switchThread 含む | |
| `tests/composables/useThreads.test.ts` | useThreads 全機能 | `importFresh` パターン |
| `tests/server/thread-store.test.ts` | CRUD 8ケース | `createRequire` で CJS モック回避 |
| `tests/server/threads.test.ts` | threads API | |
| `tests/server/chat.test.ts`（141行） | chat API 5ケース | ver12 で `tavilyApiKey` をruntimeConfigスタブに追加 |
| `tests/server/chat-history.test.ts` | history API 5ケース | |
| `tests/utils/sse-parser.test.ts` | SSE パーサー 9ケース | |

### その他

- `experiments/_shared.ts`, `01-basic-connection.ts`, `02-memory-management.ts`, `03-analogy-prompt.ts`: 実験スクリプト

## API 契約

### `POST /api/chat`

**リクエスト:**

```json
{ "message": "string", "threadId": "string" }
```

**レスポンス:** SSE ストリーム（`Content-Type: text/event-stream`）

| event | data | 説明 |
|---|---|---|
| `token` | `{"content": "..."}` | トークン1つ分のテキスト |
| `done` | `{}` | ストリーミング正常完了 |
| `error` | `{"message": "..."}` | エラー発生 |

**副作用:**
- `upsertThread()` でスレッドメタデータを登録・更新
- タイトルが「新しいチャット」の場合、ストリーム完了後に非同期でタイトル自動生成
- Tavily Search ツールが有効な場合、エージェントの自律判断によりWeb検索が実行される可能性あり

### `GET /api/chat/history`

```
GET /api/chat/history?threadId=<uuid>
```

**レスポンス:**

```json
{
  "messages": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

### `GET /api/threads`

**レスポンス:**

```json
{
  "threads": [
    {
      "threadId": "uuid",
      "title": "新しいチャット",
      "createdAt": "2025-03-24T00:00:00",
      "updatedAt": "2025-03-24T00:00:00"
    }
  ]
}
```

- 更新日時降順でソート済み

## データベーススキーマ

### threads テーブル

```sql
CREATE TABLE IF NOT EXISTS threads (
  thread_id TEXT PRIMARY KEY,
  title TEXT NOT NULL DEFAULT '新しいチャット',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
)
```

- LangGraph チェックポインター（`langgraph-checkpoints.db`）と同一 DB ファイルに格納
- WAL モードで並行読み取り対応

## 技術的な決定事項

### 継続中の決定事項

- **ストリーミング方式**: h3 `createEventStream` + LangChain `agent.stream()` による SSE
- **SSE パーサーの分離**: `parseSSEStream()` を `app/utils/sse-parser.ts` に切り出し
- **composable 設計**: `useChat()`（メッセージ・通信）と `useThreads()`（スレッド一覧・アクティブ管理）で責務分離
- **AbortController による応答中断**
- **リアクティビティ戦略**: 空の assistant メッセージオブジェクトを先に追加し、同一参照の `.content` を更新
- **会話メモリの永続化**: LangGraph チェックポイント機構により SQLite に自動保存
- **Markdown レンダリング**: `marked` + `DOMPurify`、`import.meta.client` ガード
- **h3 明示的インポート**: auto-import 非依存（Vitest モック設定を簡潔に）
- **テスト環境**: Vitest `environment: 'node'`
- **ネイティブモジュール除外**: `nitro.externals.external: ['better-sqlite3']`
- **楽観的 UI 更新**: `createNewThread()` でサーバー通信なしに即座にスレッドをリストに追加
- **タイトル自動生成**: `generateTitle()` で gpt-4.1-mini を使い10文字以内の日本語タイトルを非同期生成
- **better-sqlite3 の直接依存**: pnpm の厳密な依存解決による
- **thread-store のシングルトン DB**: LangGraph チェックポインターと同一 DB ファイルを共有
- **CJS モジュールテスト**: `createRequire(import.meta.url)` で vitest のモック解決を回避
- **composable テストの importFresh**: モジュールスコープ状態をテスト間で分離

### ver12 で追加

- **Tavily Search の条件付き統合**: `config.tavilyApiKey` が truthy の場合のみツールを追加し、未設定時はツールなしでフォールバック。Tavily は補助機能であり、キー未設定でもアプリは LLM 内部知識のみで動作する
- **コンストラクタパラメータの違い**: `@langchain/tavily@^1.2.0` のコンストラクタは `tavilyApiKey`（`apiKey` ではない）
- **プロンプトによるツール活用推奨**: ステップ3でWeb検索を「必ず」使うよう記述しているが、ReActエージェントの自律判断に依存するため厳密な強制ではない。検索実行を強制する仕組みが必要になった場合は、ver13 の LangGraph ステートマシン移行で「事例検索ノード」として実装予定
- **ストリーミングフィルタの防御的実装**: `instanceof AIMessageChunk` で `ToolMessage` を除外、`typeof chunk.content === 'string'` で配列型コンテンツ（`tool_use` ブロック含む）も除外。実環境での検証は未実施（ISSUES/app/low に登録済み）

## ISSUES 管理

### low（低優先度）

| ファイル | 内容 |
|---|---|
| `analogy-prompt-categories.md` | アナロジープロンプトへのバイオミミクリー等の例示カテゴリ追加 |
| `react-agent-getstate-type-safety.md` | `ReactAgent.getState()` の `as any` 回避策の検討 |
| `streaming.md` | ストリーミング中の不完全 Markdown 表示の改善 |
| `streaming-tool-call-compatibility.md` | Tavily ツール呼び出し時のストリーミング互換性検証（ver12 追加） |
| `syntax-highlight.md` | コードブロックのシンタックスハイライト |
| `vitest-nuxt-test-utils.md` | `@nuxt/test-utils` 導入（エイリアス解決・auto-import モック統一） |

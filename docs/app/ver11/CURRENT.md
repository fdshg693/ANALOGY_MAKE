# ver11 完了時点のコード現況

ver10（SQLite 会話履歴永続化）を経て、複数スレッド管理機能を導入した状態。サイドバーUIによるスレッド一覧表示・切り替え・新規作成、およびタイトル自動生成が可能。

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
- **threadId 管理の変更（ver10→ver11）**:
  - ver10: `getOrCreateThreadId()` で localStorage から復元 or 新規生成
  - ver11: `threadId` の初期化と永続化は `useThreads` composable が担当。`useChat` は `threadId` を受動的に受け取るのみ
  - `threadId` 未設定時（空文字列）は `sendMessage()` が早期リターンするガード追加
- **履歴復元**: `loadHistory()` を公開関数としてエクスポート（ver10 では内部関数）
- **スレッド切り替え**: `switchThread(newThreadId)` — ストリーミング中なら `abort()` で自動中断、`messages` リセット、`threadId` 設定、`loadHistory()` 呼び出し
- `abortController: AbortController | null` — モジュールスコープの非リアクティブ変数
- `parseSSEStream` は相対パス `../utils/sse-parser` でインポート

### `app/composables/useThreads.ts`（86行）— ver11 新規

- `Thread` インターフェース（`{ threadId, title, createdAt, updatedAt }`）をエクスポート
- `useThreads()` composable をエクスポート。戻り値: `{ threads, activeThreadId, isLoadingThreads, loadThreads, createNewThread, setActiveThread, initActiveThread, updateLocalTitle }`
- **モジュールスコープのシングルトン状態**:
  - `threads: Ref<Thread[]>` — スレッド一覧
  - `activeThreadId: Ref<string>` — 現在アクティブなスレッドID
  - `isLoadingThreads: Ref<boolean>` — スレッド一覧ロード中フラグ
- `ACTIVE_THREAD_KEY = 'analogy-threadId'` を localStorage キーとして使用
- `loadThreads()`: `GET /api/threads` からスレッド一覧取得。失敗時はサイレント無視
- `createNewThread()`: `crypto.randomUUID()` でID生成、楽観的に `threads` 先頭に追加、localStorage に保存。新IDを返す
- `setActiveThread(threadId)`: `activeThreadId` 更新 + localStorage 保存
- `initActiveThread()`: localStorage から `activeThreadId` を復元
- `updateLocalTitle(threadId, title)`: ローカルのスレッドタイトルを更新
- `import.meta.client` ガードで SSR 安全性を確保

### `app/components/ThreadSidebar.vue`（130行）— ver11 新規

- Props: `threads: Thread[]`, `activeThreadId: string`, `isLoading: boolean`
- Emits: `selectThread(threadId)`, `newThread()`
- テンプレート: サイドバー（幅 240px 固定）、ヘッダー（「スレッド」+ 「+ 新規」ボタン）、スレッド一覧（ボタンリスト）
- アクティブスレッド: 青背景（`#dbeafe`）で視覚的に区別
- スレッドタイトル: `text-overflow: ellipsis` で省略表示
- ローディング中・空状態の表示対応

### `app/pages/index.vue`（133行）

- 2カラムレイアウト: `ThreadSidebar` + チャットエリア（`display: flex`, `height: 100dvh`）
- `useChat()` と `useThreads()` を統合利用
- 初期化フロー（`onMounted`）:
  1. `initActiveThread()` — localStorage からアクティブスレッドID復元
  2. `loadThreads()` — サーバーからスレッド一覧取得
  3. `activeThreadId` があれば `switchThread()` で会話履歴ロード、なければ `handleNewThread()` で新規作成
- `handleSelectThread(threadId)`: `setActiveThread()` + `switchThread()`
- `handleNewThread()`: `createNewThread()` + `switchThread()`
- `handleSend(content)`: `sendMessage()` + `loadThreads()` 再取得（タイトル更新反映のため）
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
- ver11 追加: `upsertThread(body.threadId)` でスレッドメタデータ登録・更新
- ver11 追加: ストリーム完了後にタイトル自動生成（`generateTitle()`、非同期・非ブロッキング）
- `generateTitle()`: `ChatOpenAI`（gpt-4.1-mini, temperature: 0, maxTokens: 30）で10文字以内の日本語タイトル生成。`useRuntimeConfig()` 経由で API キー取得。タイトルが「新しいチャット」または null の場合のみ実行

### `server/api/threads.get.ts`（14行）— ver11 新規

- `GET /api/threads` スレッド一覧取得エンドポイント
- `getThreads()` を呼び出し、`thread_id` → `threadId` などキャメルケースに変換して返却

### `server/api/chat/history.get.ts`（36行）

- `GET /api/chat/history?threadId=xxx` 会話履歴取得エンドポイント
- `(agent as any).getState()` で LangGraph チェックポイントからスナップショット取得

### `server/utils/thread-store.ts`（59行）— ver11 新規

- `better-sqlite3` を直接インポートしてスレッドメタデータを CRUD 操作
- シングルトンパターンで DB 接続を管理（`getDb()`）
- WAL モードで並行読み取り対応
- `getThreads()`: 更新日時降順でスレッド一覧取得
- `upsertThread(threadId, title?)`: 新規登録 or `updated_at` 更新（`ON CONFLICT DO UPDATE`）
- `updateThreadTitle(threadId, title)`: タイトル更新
- `getThreadTitle(threadId)`: タイトル取得（存在しなければ null）
- DB パス: `./data/langgraph-checkpoints.db`（LangGraph チェックポインターと同一ファイル）

### `server/utils/analogy-agent.ts`（32行）

- `getAnalogyAgent()`: シングルトンパターンで LangChain エージェントを初期化・保持
- `SqliteSaver.fromConnString("./data/langgraph-checkpoints.db")`

### `server/utils/analogy-prompt.ts`（31行）

- `ANALOGY_SYSTEM_PROMPT` 定数。5ステップのアナロジー思考対話フロー

### `nuxt.config.ts`（13行）

- `compatibilityDate: '2025-07-15'`
- `runtimeConfig.openaiApiKey`
- `nitro.externals.external: ['better-sqlite3']`

### `vitest.config.ts`（16行）

- `environment: 'node'`
- `define: { 'import.meta.client': 'globalThis.__NUXT_CLIENT__' }`

### テストファイル

| ファイル | テストケース | 備考 |
|---|---|---|
| `tests/composables/useChat.test.ts` | switchThread 含む | ver11 で threadId 関連テスト更新 |
| `tests/composables/useThreads.test.ts` | useThreads 全機能 | ver11 新規、`importFresh` パターン |
| `tests/server/thread-store.test.ts` | CRUD 8ケース | ver11 新規、`createRequire` で CJS モック回避 |
| `tests/server/threads.test.ts` | threads API | ver11 新規 |
| `tests/server/chat.test.ts` | chat API 5ケース | ver11 で thread-store モック追加 |
| `tests/server/chat-history.test.ts` | history API 5ケース | |
| `tests/utils/sse-parser.test.ts` | SSE パーサー 9ケース | |

### その他

- `experiments/_shared.ts`, `01-basic-connection.ts`, `02-memory-management.ts`, `03-analogy-prompt.ts`: 実験スクリプト
- `.env.example`: 環境変数テンプレート

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

**副作用（ver11 追加）:**
- `upsertThread()` でスレッドメタデータを登録・更新
- タイトルが「新しいチャット」の場合、ストリーム完了後に非同期でタイトル自動生成

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

### `GET /api/threads` — ver11 新規

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

### threads テーブル（ver11 新規）

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

### ver10 から継続

- **ストリーミング方式**: h3 `createEventStream` + LangChain `agent.stream()` による SSE
- **SSE パーサーの分離**: `parseSSEStream()` を `app/utils/sse-parser.ts` に切り出し
- **composable 設計**: `useChat()` がチャットのリアクティブ状態と通信ロジックを一元管理
- **AbortController による応答中断**
- **リアクティビティ戦略**: 空の assistant メッセージオブジェクトを先に追加し、同一参照の `.content` を更新
- **会話メモリの永続化**: LangGraph チェックポイント機構により SQLite に自動保存
- **Markdown レンダリング**: `marked` + `DOMPurify`、`import.meta.client` ガード
- **h3 明示的インポート**: auto-import 非依存（Vitest モック設定を簡潔に）
- **テスト環境**: Vitest `environment: 'node'`
- **ネイティブモジュール除外**: `nitro.externals.external: ['better-sqlite3']`

### ver11 で追加

- **スレッド管理の分離**: `useChat`（メッセージ・通信）と `useThreads`（スレッド一覧・アクティブ管理）で責務分離。`useChat` は threadId を受動的に受け取り、`useThreads` がスレッドのライフサイクルを管理
- **threadId の管理主体変更**: ver10 では `useChat` 内で localStorage 管理。ver11 では `useThreads` が localStorage 管理を担当、`useChat` は `switchThread()` 経由で threadId を設定されるのみ
- **楽観的 UI 更新**: `createNewThread()` でサーバー通信なしに即座にスレッドをリストに追加。サーバーへの登録は初回メッセージ送信時の `upsertThread()` で実行
- **タイトル自動生成**: `generateTitle()` で gpt-4.1-mini を使い10文字以内の日本語タイトルを非同期生成。`void` で fire-and-forget。クライアントへの反映は次回 `loadThreads()` 呼び出し時
- **better-sqlite3 の直接依存**: pnpm の厳密な依存解決により、トランジティブ依存（`@langchain/langgraph-checkpoint-sqlite` 経由）では直接インポート不可のため、直接依存に追加
- **thread-store のシングルトン DB**: `getDb()` で遅延初期化、テーブル作成を含む。LangGraph チェックポインターと同一 DB ファイルを共有
- **CJS モジュールテスト**: `better-sqlite3` は CJS モジュールのため、テストでは `createRequire(import.meta.url)` で vitest のモック解決を回避
- **composable テストの importFresh**: `useThreads` のモジュールスコープ状態をテスト間で分離するため、`vi.importActual` で毎回フレッシュインポート

## ISSUES 管理

### low（低優先度）

| ファイル | 内容 |
|---|---|
| `analogy-prompt-categories.md` | アナロジープロンプトへのバイオミミクリー等の例示カテゴリ追加 |
| `react-agent-getstate-type-safety.md` | `ReactAgent.getState()` の `as any` 回避策の検討 |
| `streaming.md` | ストリーミング中の不完全 Markdown 表示の改善 |
| `syntax-highlight.md` | コードブロックのシンタックスハイライト |
| `vitest-nuxt-test-utils.md` | `@nuxt/test-utils` 導入（エイリアス解決・auto-import モック統一） |

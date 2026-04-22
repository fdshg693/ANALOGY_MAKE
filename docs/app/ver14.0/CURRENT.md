# ver14.0 完了時点のコード現況

ver12（Tavily Search連携）、ver13.1（サーバーサイドログ追加）を経て、`createReactAgent`（単一エージェント + 単一プロンプト）を LangGraph `StateGraph` によるマルチノード構成に置き換えた状態。Router パターンにより、各 API 呼び出しが `graph.stream()` で統一され、`currentStep` に基づいてノードが条件分岐する。フロントエンドに変更はない。

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

### `app/app.vue`（6行）

- `<NuxtRouteAnnouncer />` と `<NuxtPage />` を配置するルートレイアウト

### `app/composables/useChat.ts`（117行）

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

### `app/components/ThreadSidebar.vue`（131行）

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

### `app/utils/sse-parser.ts`（54行）

- `SSECallbacks` インターフェース: `onToken(content)`, `onDone()`, `onError(message)`
- `parseSSEStream(stream, callbacks): Promise<void>` — `ReadableStream` を消費しSSEイベントをコールバックで通知

### `app/components/ChatMessage.vue`（139行）

- Props: `role`, `content`, `isError?`
- assistant メッセージのみ `marked.parse()` → `DOMPurify.sanitize()` でリッチ HTML 生成

### `app/components/ChatInput.vue`（86行）

- Props: `{ disabled, isStreaming }`
- Emits: `send(content)`, `abort()`
- ストリーミング中は赤色「停止」ボタン、通常時は青色「送信」ボタン

### `server/utils/analogy-agent.ts`（182行）— ver14.0 全面書き換え

LangGraph `StateGraph` によるマルチノード構成のアナロジー思考ワークフロー。

#### ステート定義（`AnalogyState`）

```typescript
const AnalogyState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: messagesStateReducer,
    default: () => [],
  }),
  currentStep: Annotation<string>({
    reducer: (_prev, next) => next,
    default: () => "initial",
  }),
  abstractedProblem: Annotation<string>({
    reducer: (_prev, next) => next,
    default: () => "",
  }),
})
```

#### ステップ遷移

| currentStep | 意味 | 次に実行されるノード |
|---|---|---|
| `initial` | 新規スレッド、課題未入力 | abstraction → caseSearch |
| `awaiting_selection` | 事例提示済み、ユーザー選択待ち | solution |
| `completed` | 解決策提示済み | followUp |

#### グラフ構造

```
START ──→ [routeByStep: conditional edge]
              │
              ├── currentStep === "initial"
              │       ↓
              │   abstraction ──→ caseSearch ──→ END
              │
              ├── currentStep === "awaiting_selection"
              │       ↓
              │   solution ──→ END
              │
              └── currentStep === "completed"
                      ↓
                  followUp ──→ END
```

#### ノード関数

- `abstractionNode` — ユーザーの具体的課題を抽象概念に変換。`abstractedProblem` に格納。メッセージ履歴には追加しない（`caseSearchNode` が統合応答を生成するため）
- `caseSearchNode` — `performSearch()` で Tavily Web検索を実行し、抽象化結果とともに LLM に類似事例の提示を依頼。コンテキスト情報はシステムプロンプト末尾に統合。`currentStep` を `"awaiting_selection"` に更新
- `solutionNode` — ユーザー選択事例に基づく解決策生成。`currentStep` を `"completed"` に更新
- `followUpNode` — 解決策提示後の追加質問に応答。`currentStep` は更新しない（`"completed"` を維持し、後続も `followUpNode` にルーティング）

#### Tavily Search 呼び出し（`performSearch` 関数）

- ノードロジック内で直接呼び出し（ツールとしてではない）。Web検索の実行が確実になる
- `config.tavilyApiKey` が truthy の場合のみ実行、未設定時は空文字列を返す
- `maxResults: 3`
- エラー時はサイレントに空文字列を返し、LLM 内部知識のみで動作を継続

#### ユーティリティ関数

- `getRuntimeConfig()` — `useRuntimeConfig()` の結果をモジュールスコープ変数にキャッシュ。ノード関数からはキャッシュを参照（リクエストコンテキスト外での動作を保証）
- `getModel()` — `ChatOpenAI` インスタンスを都度生成（gpt-5.4, temperature: 0.7）

#### シングルトン

- `getAnalogyAgent()`: `CompiledStateGraph` をシングルトンで保持
- `SqliteSaver.fromConnString("./data/langgraph-checkpoints.db")` でチェックポインターを初期化
- `mkdirSync("./data", { recursive: true })` で `data/` ディレクトリを保証

### `server/utils/analogy-prompt.ts`（55行）— ver14.0 全面書き換え

既存の `ANALOGY_SYSTEM_PROMPT`（単一プロンプト）を削除し、ノード別の4プロンプトに分割。

| 定数名 | 用途 | 概要 |
|---|---|---|
| `ABSTRACTION_PROMPT` | abstractionNode | 課題の抽象化（固有名詞・分野を除去、1〜2文で簡潔に） |
| `CASE_SEARCH_PROMPT` | caseSearchNode | 類似事例の提示（3〜5個、異分野から、Web検索結果を優先） |
| `SOLUTION_PROMPT` | solutionNode | 解決策の提案（原理説明 + 適用方法 + 実現可能性） |
| `FOLLOWUP_PROMPT` | followUpNode | フォローアップ対応（詳細説明、別事例での再検討） |

全プロンプト共通ルール: 日本語で出力。`[内部コンテキスト]` の情報はそのまま出力せず自然な文章に組み込む。

### `server/utils/logger.ts`（15行）— ver13.1 追加

- モジュール別プレフィックス付きロガーユーティリティ
- `console.log` / `console.warn` / `console.error` ベース（外部ライブラリ不使用）
- 4モジュール: `logger.agent`, `logger.chat`, `logger.thread`, `logger.history`
- 各モジュールから明示的にインポートして使用

### `server/api/chat.post.ts`（110行）— ver14.0 更新

- `POST /api/chat` SSE ストリーミングエンドポイント
- `upsertThread(body.threadId)` でスレッドメタデータ登録・更新
- ストリーム完了後にタイトル自動生成（`generateTitle()`、非同期・非ブロッキング）
- `generateTitle()`: `ChatOpenAI`（gpt-5.4, temperature: 0, maxTokens: 30）で10文字以内の日本語タイトル生成
- **ストリーミングフィルタ（ver14.0 変更点）**:
  - `STREAMED_NODES = new Set(["caseSearch", "solution", "followUp"])` — ホワイトリスト方式
  - `metadata?.langgraph_node` でノードを識別し、`abstraction` ノードの出力をフィルタリング
  - `AIMessageChunk` かつ文字列 content かつ `STREAMED_NODES` に含まれるノードの出力のみストリーミング
  - ver12 のツール検出ログ分岐を削除（Tavily がツールでなくなったため `ToolMessage` は発生しない）
- 入力は `new HumanMessage(body.message)` に変更（`StateGraph` の `messages` フィールドが `BaseMessage[]` を要求するため）

### `server/api/threads.get.ts`（15行）

- `GET /api/threads` スレッド一覧取得エンドポイント
- `getThreads()` を呼び出し、`thread_id` → `threadId` などキャメルケースに変換して返却

### `server/api/chat/history.get.ts`（40行）— ver14.0 更新

- `GET /api/chat/history?threadId=xxx` 会話履歴取得エンドポイント
- `graph.getState()` で LangGraph チェックポイントからスナップショット取得
- ver14.0 で `(agent as any).getState()` の `as any` キャストを除去（`CompiledStateGraph` が `getState()` を公開しているため型安全に呼び出し可能）
- `snapshot.values` には `messages`, `currentStep`, `abstractedProblem` が含まれるが、`messages` のみを使用
- `HumanMessage` と `AIMessage` のみ抽出し `{ role, content }` 形式に変換

### `server/utils/thread-store.ts`（64行）

- `better-sqlite3` を直接インポートしてスレッドメタデータを CRUD 操作
- シングルトンパターンで DB 接続を管理（`getDb()`）、WAL モード
- `getThreads()`, `upsertThread()`, `updateThreadTitle()`, `getThreadTitle()`
- DB パス: `./data/langgraph-checkpoints.db`（LangGraph チェックポインターと同一ファイル）

### `nuxt.config.ts`（14行）

- `compatibilityDate: '2025-07-15'`
- `runtimeConfig.openaiApiKey`, `runtimeConfig.tavilyApiKey`
- `nitro.externals.external: ['better-sqlite3']`

### `vitest.config.ts`（16行）

- `environment: 'node'`
- `define: { 'import.meta.client': 'globalThis.__NUXT_CLIENT__' }`

### `.env.example`（3行）

- `OPENAI_API_KEY`、`NUXT_OPENAI_API_KEY`、`NUXT_TAVILY_API_KEY` の3行

### テストファイル

| ファイル | 行数 | テストケース数 | 備考 |
|---|---|---|---|
| `tests/utils/sse-parser.test.ts` | 168 | 10 | SSE パーサー |
| `tests/composables/useChat.test.ts` | 240 | 11 | switchThread 含む |
| `tests/composables/useThreads.test.ts` | 165 | 14 | `importFresh` パターン |
| `tests/server/thread-store.test.ts` | 85 | 7 | `createRequire` で CJS モック回避 |
| `tests/server/threads.test.ts` | 46 | 2 | threads API |
| `tests/server/chat.test.ts` | 180 | 8 | ver14.0 で `langgraph_node` メタデータ付きモックに更新、abstraction フィルタテスト追加 |
| `tests/server/chat-history.test.ts` | 102 | 5 | ver14.0 で `mockAgent` → `mockGraph` に更新 |

合計: 986行、57テストケース

### その他

- `experiments/_shared.ts`, `01-basic-connection.ts`, `02-memory-management.ts`: 実験スクリプト
- `experiments/03-analogy-prompt.ts` は ver14.0 以前に削除済み（`createReactAgent` ベースのスクリプトが不要になったため）

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
- `caseSearchNode` 内で Tavily Search が有効な場合、Web検索が実行される（ノードロジックとして確実に実行、プロンプト依存ではない）

**ストリーミングされるノード:**
- `caseSearch`, `solution`, `followUp` — ユーザーに表示する応答を生成するノード
- `abstraction` — フィルタリングされ、ユーザーには表示されない（内部処理のみ）

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

ステートの `messages`, `currentStep`, `abstractedProblem` のうち `messages` のみ返却。`HumanMessage` と `AIMessage` のみ抽出（`SystemMessage` 等は除外）。

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

### LangGraph チェックポイントステート

ver14.0 で保存されるステート構造:

| フィールド | 型 | 用途 |
|---|---|---|
| `messages` | `BaseMessage[]` | 会話メッセージ履歴（`messagesStateReducer` で自動追記） |
| `currentStep` | `string` | 対話フローの現在ステップ（`"initial"`, `"awaiting_selection"`, `"completed"`） |
| `abstractedProblem` | `string` | 抽象化された課題テキスト |

既存の `createReactAgent` ベースのチェックポイントデータとは互換性がない（ステート構造が異なるため）。`data/` ディレクトリの削除が必要。

## 技術的な決定事項

### 継続中の決定事項

- **ストリーミング方式**: h3 `createEventStream` + LangGraph `graph.stream()` による SSE（`streamMode: "messages"`）
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
- **タイトル自動生成**: `generateTitle()` で gpt-5.4 を使い10文字以内の日本語タイトルを非同期生成
- **better-sqlite3 の直接依存**: pnpm の厳密な依存解決による
- **thread-store のシングルトン DB**: LangGraph チェックポインターと同一 DB ファイルを共有
- **CJS モジュールテスト**: `createRequire(import.meta.url)` で vitest のモック解決を回避
- **composable テストの importFresh**: モジュールスコープ状態をテスト間で分離

### ver14.0 で追加

- **Router パターンの採用**: ROUGH_PLAN では `interrupt` 機構を想定していたが、`interrupt()` はノード関数を最初から再実行する（LLM 二重呼び出しのコスト・不一致リスク）、`interruptAfter` は `updateState` + `stream(null)` という異なる API フローが必要。Router パターンでは各 API 呼び出しが `graph.stream(input, config)` で統一され、実装がシンプル
- **StateGraph によるマルチノード構成**: `createReactAgent`（単一エージェント + 単一プロンプト）から、4ノード（abstraction, caseSearch, solution, followUp）の StateGraph に移行。フローの再現性と制御性が向上
- **ノード別プロンプト分割**: 単一の `ANALOGY_SYSTEM_PROMPT` を4つの専用プロンプトに分割。各ノードの役割を厳密に限定
- **Tavily Search のノード内直接呼び出し**: ツールとしてではなくノードロジック内で `tavily.invoke({ query })` を直接呼び出し。Web検索の実行が確実になる（プロンプト依存から脱却）
- **ストリーミングフィルタのホワイトリスト方式**: `metadata?.langgraph_node` に基づき、`STREAMED_NODES` に含まれるノードの出力のみストリーミング。`abstraction` ノードの出力がクライアントに送信されることを防止
- **`useRuntimeConfig()` のキャッシュ**: ノード関数がリクエストコンテキスト外で実行される可能性があるため、初期化時に結果をモジュールスコープ変数にキャッシュ
- **`as any` キャストの除去**: `CompiledStateGraph` が `getState()` を公開しており、型安全に呼び出し可能

### ver14.0 で削除

- **`createReactAgent` ベースのエージェント構成**: `StateGraph` に完全移行
- **単一の `ANALOGY_SYSTEM_PROMPT`**: ノード別プロンプトに分割
- **Tavily Search のツール統合**: ノード内直接呼び出しに変更（`ToolMessage` は発生しなくなった）
- **ツール検出ログ分岐**: `ToolMessage` が発生しなくなったため不要
- **実験スクリプト `03-analogy-prompt.ts`**: `createReactAgent` ベースのため不要

## ISSUES 管理

### low（低優先度）

| ファイル | 内容 |
|---|---|
| `analogy-prompt-categories.md` | アナロジープロンプトへのバイオミミクリー等の例示カテゴリ追加 |
| `streaming.md` | ストリーミング中の不完全 Markdown 表示の改善 |
| `syntax-highlight.md` | コードブロックのシンタックスハイライト |
| `vitest-nuxt-test-utils.md` | `@nuxt/test-utils` 導入（エイリアス解決・auto-import モック統一） |

### ver14.0 で解決済み（削除）

| ファイル | 内容 | 解決理由 |
|---|---|---|
| `streaming-tool-call-compatibility.md` | Tavily ツール呼び出し時のストリーミング互換性 | Tavily がツールでなくなった |
| `react-agent-getstate-type-safety.md` | `ReactAgent.getState()` の `as any` 回避策 | `CompiledStateGraph` で型安全に呼び出し可能 |

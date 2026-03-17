# ver10 完了時点のコード現況

ver9（composable 切り出し + 応答中断機能）を経て、SQLite による会話履歴永続化を導入した状態。サーバー再起動・ページリロード後も会話を継続可能。

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
| marked | ^17.0.4 |
| dompurify | ^3.3.3 |
| vitest（dev） | ^4.1.0 |
| happy-dom（dev） | ^20.8.4 |
| dotenv（dev） | ^17.3.1 |
| tsx（dev） | ^4.21.0 |

`package.json` に `pnpm.onlyBuiltDependencies: ["better-sqlite3"]` を指定（ネイティブモジュールのビルド許可）。

## ファイル詳細

### `app/app.vue`（7行）

- `<NuxtRouteAnnouncer />` と `<NuxtPage />` を配置するルートレイアウト

### `app/composables/useChat.ts`（125行）

- `Message` インターフェース（`{ role: 'user' | 'assistant', content: string, isError?: boolean }`）をエクスポート
- `useChat()` composable をエクスポート。戻り値: `{ messages, isLoading, isStreaming, threadId, sendMessage, abort }`
- リアクティブ状態:
  - `messages: Ref<Message[]>` — チャット履歴
  - `isLoading: Ref<boolean>` — 送信〜応答完了 or 履歴ロード中の全体ローディング
  - `isStreaming: Ref<boolean>` — 初回トークン受信〜ストリーム完了のストリーミング状態
  - `threadId: Ref<string>` — `getOrCreateThreadId()` で初期化（localStorage 復元 or 新規生成）
- **threadId 永続化**:
  - `THREAD_ID_KEY = 'analogy-threadId'` を localStorage キーとして使用
  - `getOrCreateThreadId()`: `import.meta.client` が true の場合 localStorage から復元を試み、なければ `crypto.randomUUID()` で生成して localStorage に保存。SSR 時は UUID を生成するのみ（通信には使われない）
  - ハイドレーション安全: `threadId` はテンプレートにバインドされないため SSR/クライアント間の値不一致は問題なし
- **履歴復元**:
  - `loadHistory()`: `GET /api/chat/history?threadId=...` から会話履歴を取得し `messages.value` に設定
  - `isLoading = true` で履歴取得中の送信を防止（競合状態回避）
  - localStorage に threadId が存在する場合のみ呼び出し（初回訪問時は呼ばない）
  - 取得失敗時はサイレントに無視し空チャットで開始
- `abortController: AbortController | null` — モジュールスコープの非リアクティブ変数。`sendMessage` 呼び出しごとに新規生成し、`fetch` の `signal` に渡す
- `abort()` — `abortController?.abort()` を呼び出す。`catch` ブロックで `AbortError` を判定し、中断時は `return`（エラー扱いにしない）。`finally` ブロックは必ず実行されるため `isLoading` / `isStreaming` のリセットは保証される。部分テキストはそのまま保持
- `sendMessage()`:
  1. 空入力ガード
  2. ユーザーメッセージ＋空 assistant メッセージを `messages` に追加
  3. `abortController` を生成し `fetch('/api/chat', { signal })` で POST
  4. `parseSSEStream` でコールバック処理（onToken / onDone / onError）
  5. 初回トークンで `isStreaming = true`
  6. エラー時は途中テキスト保持＋エラーメッセージ付記、`isError = true`
  7. `finally` で `isLoading = false`, `isStreaming = false`
- `parseSSEStream` は相対パス `../utils/sse-parser` でインポート（Nuxt と vitest のエイリアス不整合を回避）

### `app/pages/index.vue`（約85行）

- チャットページ。`useChat()` から `{ messages, isLoading, isStreaming, sendMessage, abort }` を取得
- `messagesContainer: ref<HTMLElement | null>` — スクロール制御用 DOM 参照
- 自動スクロール: `watch` で `messages.length` と最終メッセージの `content.length` を結合した文字列を監視 → `nextTick` 後にスクロール
- ローディング表示: `isLoading && !isStreaming` の間のみ「考え中...」を表示
- コンポーネント接続:
  - `<ChatMessage v-for="(msg, i) in messages" :key="i" :role :content :is-error>`
  - `<ChatInput :disabled="isLoading" :is-streaming="isStreaming" @send="sendMessage" @abort="abort">`

### `app/utils/sse-parser.ts`（53行）

- `SSECallbacks` インターフェースをエクスポート: `onToken(content)`, `onDone()`, `onError(message)`
- `parseSSEStream(stream, callbacks): Promise<void>` をエクスポート
- `ReadableStream` を `getReader()` + `TextDecoder({ stream: true })` で消費
- `\n\n` でイベント境界を分割、バッファリングでチャンク跨ぎのイベントを再構成
- `event:` / `data:` 行をパースし、`token` / `done` / `error` イベントに応じたコールバック呼び出し
- `done` / `error` 受信時に `return` して関数終了

### `app/components/ChatMessage.vue`（139行）

- Props: `role`（`'user' | 'assistant'`）, `content`（`string`）, `isError?`（`boolean`）
- `renderedHtml` computed: assistant メッセージのみ `marked.parse()` → `DOMPurify.sanitize()` でリッチ HTML 生成（`import.meta.client` ガードで SSR 回避）
- テンプレート: assistant は `v-html`、user はテキスト補間
- スタイル: ユーザー=右寄せ青系、AI=左寄せグレー、エラー=薄赤。`:deep()` で Markdown タイポグラフィ適用。最大幅 80%

### `app/components/ChatInput.vue`（約85行）

- Props: `{ disabled: boolean, isStreaming: boolean }`
- Emits: `send(content: string)`, `abort()`
- `<form @submit.prevent="handleSubmit">` でフォーム送信ハンドリング
- ボタンは `v-if="isStreaming"` で条件分岐:
  - ストリーミング中: 赤色「停止」ボタン（`type="button"`, `@click="emit('abort')"`, 常にクリック可能）
  - 通常時: 青色「送信」ボタン（`type="submit"`, `disabled` 時・空入力時は無効）
- 内部状態: `input = ref('')`、送信後にクリア

### `server/api/chat.post.ts`（57行）

- `POST /api/chat` SSE ストリーミングエンドポイント
- h3 関数と `getAnalogyAgent` を明示的にインポート（auto-import 非依存）
- リクエスト: `{ message: string, threadId: string }`（バリデーションあり、400 エラー）
- `const agent = await getAnalogyAgent()` で非同期取得
- h3 `createEventStream` で SSE レスポンス構築。ストリーム消費を async IIFE で実行（`void` で明示的に無視）
- `agent.stream()` を `streamMode: "messages"` で呼び出し、`AIMessageChunk` のテキスト content を `token` イベントとして送信
- 完了時 `done`、エラー時 `error` イベント送信後ストリーム close

### `server/api/chat/history.get.ts`（36行）— ver10 新規

- `GET /api/chat/history?threadId=xxx` 会話履歴取得エンドポイント
- h3 関数（`defineEventHandler`, `getQuery`, `createError`）と `HumanMessage`, `AIMessage` を明示的にインポート
- `threadId` バリデーション（必須・文字列型チェック、400 エラー）
- `(agent as any).getState({ configurable: { thread_id } })` で LangGraph チェックポイントからスナップショットを取得
  - `ReactAgent.getState()` は `@internal` で `never` 型のため `as any` で型アサーション（ISSUES/low に記録済み）
- `snapshot.values.messages` から `HumanMessage` / `AIMessage` をフィルタし `{ role, content }` にマッピング
- チェックポイントが空 or エラー時は `{ messages: [] }` を返却（エラーレスポンスにしない）

### `server/utils/analogy-agent.ts`（32行）

- `getAnalogyAgent()` を async 関数としてエクスポート。シングルトンパターンで LangChain エージェントを初期化・保持
- `SqliteSaver.fromConnString("./data/langgraph-checkpoints.db")` でチェックポインターを生成
- `mkdirSync("./data", { recursive: true })` で DB ディレクトリを初回起動時に自動作成
- `ChatOpenAI`（gpt-4.1-mini, temperature 0.7）、`createAgent({ model, tools: [], systemPrompt, checkpointer })`
- `SqliteSaver.setup()` は protected のため明示呼び出し不要（checkpointing 時に自動実行）

### `server/utils/analogy-prompt.ts`（31行）

- `ANALOGY_SYSTEM_PROMPT` 定数。5ステップのアナロジー思考対話フロー（課題受取→抽象化→類似事例提示→選択→解決策提案）。ステップ2・3を1応答にまとめるルール、日本語応答ルール

### `nuxt.config.ts`（12行）

- `compatibilityDate: '2025-07-15'`
- `devtools: { enabled: true }`
- `runtimeConfig.openaiApiKey`
- `nitro.externals.external: ['better-sqlite3']` — ネイティブモジュールを Nitro バンドルから除外

### `vitest.config.ts`（16行）

- `environment: 'node'`
- `resolve.alias` で `~` をプロジェクトルートにマッピング
- `define: { 'import.meta.client': 'globalThis.__NUXT_CLIENT__' }` — テスト時に `import.meta.client` を `globalThis.__NUXT_CLIENT__` にコンパイル時置換

### `tests/composables/useChat.test.ts`（251行）

- `useChat` composable のユニットテスト（11テストケース）
- モック: `parseSSEStream`（モジュールモック）、`fetch`（`vi.stubGlobal`）、`crypto.randomUUID`（`vi.stubGlobal`）、`ref`（実 Vue の `ref` をスタブ注入）、`localStorage`（`getItem` / `setItem` / `removeItem`）
- `globalThis.__NUXT_CLIENT__` で `import.meta.client` を制御
- カバレッジ:
  - 初期状態（各 ref のデフォルト値）
  - 正常系（2トークン追加、fetch パラメータ + `signal: AbortSignal` の検証、フラグリセット）
  - 空入力ガード
  - SSE `onError` コールバック → エラーメッセージ付記 + `isError`
  - 通信エラー（fetch reject）→ エラーハンドリング
  - 空応答フォールバック
  - abort 中断 → 部分テキスト保持、`isError` なし、フラグリセット
  - `abort` 関数の存在確認
  - threadId 永続化（SSR時 / クライアント新規生成 / クライアント復元の3ケース）
  - 履歴復元（正常取得 / 取得失敗の2ケース）

### `tests/server/chat.test.ts`（132行）

- `chat.post.ts` ハンドラのテスト（5テストケース）
- h3 関数を `vi.mock('h3')` でモック、`getAnalogyAgent` もモジュールモック（`Promise.resolve(mockAgent)` を返却）
- カバレッジ: バリデーション（message/threadId 欠落、型エラー）、正常系（2チャンク → token + done）、エラー系（agent 失敗 → error イベント）

### `tests/server/chat-history.test.ts`（102行）— ver10 新規

- `history.get.ts` ハンドラのテスト（5テストケース）
- h3 関数を `vi.mock('h3')` でモック、`getAnalogyAgent` もモジュールモック（`mockAgent.getState` を含む）
- カバレッジ:
  - threadId 欠落で 400 エラー
  - threadId が文字列でない場合に 400 エラー
  - チェックポイントにメッセージあり → `{ role, content }` フォーマットで返却
  - チェックポイントが空 → `{ messages: [] }` を返却
  - `getState` がエラー → `{ messages: [] }` を返却

### `tests/utils/sse-parser.test.ts`（167行）

- `parseSSEStream` のユニットテスト（9テストケース）
- 実 `ReadableStream` + `TextEncoder` でテストストリームを構築
- カバレッジ: 正常系（基本フロー・複数トークン・1チャンク内複数イベント）、バッファ分割（イベント境界・data 行途中）、エラー系（error イベント・途中テキスト後 error）、エッジケース（done なし終端・空イベントスキップ）

### その他

- `experiments/_shared.ts`（7行）: 実験スクリプト共通の `ChatOpenAI` 初期化
- `experiments/01-basic-connection.ts`（28行）: 基本接続テスト
- `experiments/02-memory-management.ts`（36行）: メモリ管理検証
- `docs/DEV_NOTES.md`（25行）: 環境変数・シングルトン・typecheck の注意点
- `.env.example`（2行）: `OPENAI_API_KEY` / `NUXT_OPENAI_API_KEY` テンプレート

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

### `GET /api/chat/history` — ver10 新規

**リクエスト:**

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

- threadId が未知・チェックポイントが空・エラー時はすべて `{ messages: [] }` を返却（エラーレスポンスにしない）
- threadId 欠落・型不正の場合のみ 400 エラー

## 技術的な決定事項

- **ストリーミング方式**: h3 `createEventStream` + LangChain `agent.stream()` による SSE。POST リクエストに対する SSE レスポンスのため、`EventSource` API は使用不可（GET 専用）。クライアントは `fetch` + `parseSSEStream()` で受信
- **SSE パーサーの分離**: `parseSSEStream()` を `app/utils/sse-parser.ts` に切り出し、Vue に依存しない純粋な async 関数。コールバック（`onToken` / `onDone` / `onError`）でイベント通知、`done` / `error` 受信時に `return`
- **ストリーム並行処理**: `chat.post.ts` ではエージェントのストリーム消費（async IIFE）と `eventStream.send()` を並行実行
- **composable 設計**: `useChat()` がチャットのリアクティブ状態と通信ロジックを一元管理。`index.vue` は UI の関心事（DOM 参照・自動スクロール・コンポーネント接続）のみ担当
- **AbortController による応答中断**: `sendMessage` 呼び出しごとに `AbortController` を生成し `fetch` の `signal` に渡す。`abort()` で `abortController.abort()` を呼び出すと、`parseSSEStream` 内の `reader.read()` が `AbortError` を throw。`catch` で `AbortError` を判定し `return`（エラー扱いにしない）。`finally` は必ず実行されるためフラグリセットは保証。部分受信テキストはそのまま保持
- **停止ボタンの UI 切り替え**: `ChatInput` が `isStreaming` prop で状態を受け取り、`v-if` で送信/停止ボタンを排他的に切り替え。停止ボタンは `type="button"`（フォーム送信防止）、赤色（`#ef4444`）で視覚的に区別、常にクリック可能（disabled にしない）
- **リアクティビティ戦略**: 空の assistant メッセージオブジェクトを先に `messages` 配列に追加し、同一参照の `.content` を更新することで Vue のリアクティビティが動作
- **自動スクロール監視**: `messages.length` と最終メッセージの `content.length` を結合監視 → ストリーミング中のスクロール追従
- **会話メモリの永続化**: LangGraph チェックポイント機構により会話履歴が SQLite に自動保存。`SqliteSaver.fromConnString()` でチェックポインター生成。`thread_id` でセッション識別。`setup()` は protected で内部自動実行
- **threadId の永続化**: クライアント側で `localStorage` に保存。ページリロード時に復元し、`GET /api/chat/history` で会話履歴をロード
- **履歴取得の競合防止**: `loadHistory()` 実行中は `isLoading = true` を設定し、`ChatInput` の `disabled` と連動して送信を防止
- **getState() の型アサーション**: `ReactAgent.getState()` が `@internal`（`never` 型）のため `(agent as any).getState()` で回避。ランタイムでは LangGraph の `CompiledStateGraph` 経由で正常動作
- **import.meta.client のテスト対応**: `vitest.config.ts` の `define` で `import.meta.client` を `globalThis.__NUXT_CLIENT__` にコンパイル時置換。テスト側で `globalThis.__NUXT_CLIENT__` を切り替えて分岐テスト可能
- **エージェント初期化**: シングルトンパターン。`getAnalogyAgent()` は async 関数（将来の拡張性のため）
- **API キー管理**: Nuxt `runtimeConfig` 経由。`NUXT_OPENAI_API_KEY` 環境変数から自動取得
- **SSE エラーハンドリング**: クライアント側で2つのエラー経路を統一処理（`onError` コールバック + `catch` ブロック）。`!isError` ガードで二重エラー防止
- **エラー時の途中テキスト保持**: ストリーミング途中のエラーでは既受信テキストを破棄せず、末尾に改行付きでエラーメッセージを付記
- **Markdown レンダリング**: `marked`（同期パース）+ `DOMPurify`（XSS 対策）を computed で実行。`import.meta.client` ガードで SSR 回避。`:deep()` で `v-html` 子要素にスタイル適用。assistant メッセージのみ適用
- **h3 明示的インポート**: auto-import 非依存にすることで Vitest からのモック設定を簡潔に
- **テストにおける h3 モック**: `vi.mock('h3')` 方式採用。ハンドラ関数を直接呼び出し
- **composable テストのモック戦略**: `parseSSEStream` はモジュールモック、`fetch` / `crypto.randomUUID` / `localStorage` は `vi.stubGlobal`、`ref` は実 Vue の `ref` をスタブ注入
- **composable の相対パスインポート**: Nuxt の `~` と vitest の `~` エイリアス不整合を回避するため、`../utils/sse-parser` の相対パスを使用
- **テスト環境**: Vitest `environment: 'node'`。`happy-dom` は導入済みだが現テストは全て Node 環境で実行
- **ネイティブモジュール除外**: `nuxt.config.ts` の `nitro.externals.external: ['better-sqlite3']` で Nitro バンドルから除外

## ISSUES 管理

### high（高優先度）

なし

### low（低優先度）

| ファイル | 内容 |
|---|---|
| `analogy-prompt-categories.md` | アナロジープロンプトへのバイオミミクリー等の例示カテゴリ追加 |
| `react-agent-getstate-type-safety.md` | `ReactAgent.getState()` の `as any` 回避策の検討 |
| `streaming.md` | ストリーミング中の不完全 Markdown 表示の改善 |
| `syntax-highlight.md` | コードブロックのシンタックスハイライト |
| `vitest-nuxt-test-utils.md` | `@nuxt/test-utils` 導入（エイリアス解決・auto-import モック統一） |

### 解決済み（ver8〜ver9で対応）

| 元ファイル | 内容 | 対応バージョン |
|---|---|---|
| `index-vue-composable.md` | `index.vue` のロジックを composable へ切り出し | ver8 |
| `response-cancel.md` | 応答の中断・キャンセル機能 | ver9 |

## REQUESTS 管理

| ファイル | 内容 |
|---|---|
| `special/category_switch.md` | カテゴリ別の AI 指示切り替え |
| `special/flow_automation.md` | Claude Agent SDK によるワークフロー自動化 |
| `special/version_flow.md` | バージョン管理ワークフロー |
| `unknown/deploy.md` | デプロイ計画 |

## 未実装の課題

- `ReactAgent.getState()` の型安全なアクセス方法（現在は `as any` で回避）
- コードブロックのシンタックスハイライト（`highlight.js` 等の導入検討）
- ストリーミング中の不完全 Markdown の表示崩れ対策（体感上は軽微）
- アナロジープロンプトへのバイオミミクリー等の例示カテゴリ追加の検討
- `@nuxt/test-utils` の導入（Nuxt エイリアス解決・auto-import モック統一）
- フロントエンドコンポーネントテスト・E2E テスト

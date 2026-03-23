# ver7 完了時点のコード現況

自動テスト基盤（Vitest）を導入し、SSE パーサーをユーティリティに切り出してテスト可能にした状態。サーバー API ハンドラのバリデーション・ストリーミングテストも整備済み。

## 依存パッケージバージョン

| パッケージ | バージョン |
|---|---|
| nuxt | ^4.4.2 |
| vue | ^3.5.30 |
| vue-router | ^5.0.3 |
| @langchain/core | ^1.1.32 |
| @langchain/openai | ^1.2.13 |
| @langchain/langgraph | ^1.2.2 |
| langchain | ^1.2.32 |
| marked | ^17.0.4 |
| dompurify | ^3.3.3 |
| vitest（dev） | ^4.1.0 |
| happy-dom（dev） | ^20.8.4 |
| dotenv（dev） | ^17.3.1 |
| tsx（dev） | ^4.21.0 |

## ファイル詳細

### `app/app.vue`（6行）

- `<NuxtRouteAnnouncer />` と `<NuxtPage />` を配置するルートレイアウト

### `app/pages/index.vue`（152行）

- チャットページ。以下のリアクティブ状態を管理:
  - `messages: ref<Message[]>` — チャット履歴
  - `isLoading: ref<boolean>` — 送信〜応答完了までの全体ローディング状態
  - `isStreaming: ref<boolean>` — 最初のトークン受信〜ストリーム完了までのストリーミング状態
  - `messagesContainer: ref<HTMLElement | null>` — スクロール制御用 DOM 参照
  - `threadId: ref<string>` — `crypto.randomUUID()` でページロード時に生成
- `Message` インターフェース: `{ role: 'user' | 'assistant', content: string, isError?: boolean }`
- `sendMessage()`:
  1. ユーザーメッセージと空の assistant メッセージを `messages` に追加
  2. `/api/chat` に POST → `parseSSEStream()` で SSE イベントを処理
  3. `onToken`: 初回トークンで `isStreaming = true`、assistant メッセージの `content` を逐次追加
  4. `onDone`: 何もしない（finally でフラグリセット）
  5. `onError`: エラーテキストを assistant メッセージに付記（途中テキストがあれば末尾に改行付きで追加、なければエラーテキストのみ）、`isError = true` を設定
  6. ストリーム完了後にコンテンツが空かつ `isError` でない場合はフォールバックメッセージを設定
  7. `catch` ブロック: `parseSSEStream` 外の通信エラーを処理（`!isError` ガードで二重エラー防止）
- ローディング表示: `isLoading && !isStreaming` の間のみ「考え中...」を表示
- 自動スクロール: `watch` で `messages.length` と最終メッセージの `content.length` を結合した文字列を監視 → `nextTick` 後にスクロール

### `app/utils/sse-parser.ts`（53行）

- `SSECallbacks` インターフェースをエクスポート:
  - `onToken(content: string)` — トークン受信時
  - `onDone()` — ストリーム正常完了時
  - `onError(message: string)` — エラーイベント受信時
- `parseSSEStream(stream: ReadableStream<Uint8Array>, callbacks: SSECallbacks): Promise<void>` をエクスポート:
  - `ReadableStream` を `getReader()` で消費し、`TextDecoder` でデコード
  - `\n\n` でイベント境界を分割、バッファリングでチャンク跨ぎのイベントを正しく再構成
  - `event:` 行と `data:` 行をパースし、イベント種別に応じたコールバックを呼び出す
  - `done` / `error` イベント受信時に `return` して関数を終了（呼び出し元のループ脱出パターンが不要になる）
  - ストリーム終端（`reader.read()` が `done: true`）でもそのまま return

### `app/components/ChatMessage.vue`（138行）

- Props: `role`（`'user' | 'assistant'`）, `content`（`string`）, `isError?`（`boolean`）
- `renderedHtml` computed:
  - `role === 'assistant'` の場合のみ `marked.parse()` → `DOMPurify.sanitize()` でリッチ HTML 生成
  - `import.meta.client` ガードで SSR 時の DOMPurify エラーを回避
  - `content` prop の変更ごとに computed 再評価 → ストリーミング中もリアルタイムレンダリング
- テンプレート: assistant は `v-html`、user は テキスト補間で表示
- スタイル:
  - ユーザーメッセージ: 右寄せ・青系背景（`#dbeafe`）、`white-space: pre-wrap`
  - AI メッセージ: 左寄せ・グレー背景（`#f3f4f6`）
  - エラーメッセージ: 薄赤背景・暗赤テキスト・赤ボーダー
  - Markdown タイポグラフィ: `:deep()` で見出し・段落・リスト・コード・ブロッククォート等のスタイル適用
  - 最大幅 80%

### `app/components/ChatInput.vue`（70行）

- Props: `disabled: boolean`、Emits: `send: [content: string]`
- `@submit.prevent` でフォーム送信をハンドリング。空入力・disabled 時は送信不可
- 送信後に入力欄をクリア

### `server/api/chat.post.ts`（57行）

- `POST /api/chat` SSE ストリーミングエンドポイント
- h3 関数（`createEventStream`, `readBody`, `createError`, `defineEventHandler`）と `getAnalogyAgent` を明示的にインポート（auto-import 非依存）
- リクエスト: `{ message: string, threadId: string }`（バリデーションあり、400 エラー）
- h3 の `createEventStream` を使用して SSE レスポンスを構築
- ストリーム消費を async IIFE で実行し、戻り値を `void` で明示的に無視
- LangChain の `agent.stream()` を `streamMode: "messages"` で呼び出し
- `AIMessageChunk` のテキスト content をトークン単位で `token` イベントとして送信
- 完了時に `done` イベント、エラー時に `error` イベントを送信後、ストリームを close
- `eventStream.onClosed()` でクライアント切断時のクリーンアップ

### `server/utils/analogy-agent.ts`（28行）

- `getAnalogyAgent()` 関数をエクスポート。シングルトンパターンで LangChain エージェントを初期化・保持
- `ChatOpenAI`（gpt-4.1-mini, temperature 0.7）を `useRuntimeConfig().openaiApiKey` で初期化
- `MemorySaver` をチェックポインターとして使用し、`createAgent({ model, tools: [], systemPrompt, checkpointer })` でエージェントを生成

### `server/utils/analogy-prompt.ts`（31行）

- `ANALOGY_SYSTEM_PROMPT` 定数をエクスポート
- 5ステップのアナロジー思考対話フロー定義:
  1. 課題の受け取り
  2. 抽象化（具体→構造的問題への再定義）
  3. 類似事例の提示（他分野から3〜5個）
  4. 事例の選択（ユーザーが選択）
  5. 解決策の提案（選択事例の原理を元課題に適用）
- ステップ2と3を1応答にまとめるルール、日本語応答ルールを含む

### `vitest.config.ts`（13行）

- `environment: 'node'` — 現テストは全て Node 環境で実行
- `resolve.alias` で `~` をプロジェクトルートにマッピング（Nuxt の `~` パス解決をテスト時にも有効化）

### `tests/utils/sse-parser.test.ts`（167行）

- `parseSSEStream` のユニットテスト（9テストケース）
- テストヘルパー:
  - `createSSEStream(chunks: string[])` — 文字列配列から `ReadableStream<Uint8Array>` を生成
  - `createCallbacks()` — `vi.fn()` で `onToken` / `onDone` / `onError` のモックコールバックを生成
- テストカバレッジ:
  - 正常系: 基本フロー（token → done）、複数トークン、1チャンク内の複数イベント
  - バッファ分割: イベントがチャンク境界で分断、data 行の途中分断
  - エラー系: error イベント受信、途中テキスト後の error
  - エッジケース: done なしのストリーム終端、空イベント文字列のスキップ

### `tests/server/chat.test.ts`（132行）

- `chat.post.ts` ハンドラの統合テスト（5テストケース）
- モック戦略（候補B採用）: h3 関数をすべて `vi.mock('h3')` でモック、ハンドラ関数を直接呼び出し
  - `readBody` — 固定値を返すモック
  - `createEventStream` — `{ push: vi.fn(), close: vi.fn(), send: vi.fn(), onClosed: vi.fn() }` を返すモック
  - `defineEventHandler` — 受け取ったハンドラ関数をそのまま返す（透過）
  - `createError` — 実際の Error オブジェクト生成
- `getAnalogyAgent` モジュールも `vi.mock()` でモック（パスは `../../server/utils/analogy-agent`）
- テストカバレッジ:
  - バリデーション: message 欠落、threadId 欠落、message が文字列でない場合の 400 エラー
  - 正常系: モックエージェントが `AIMessageChunk` を yield → token イベント送信 → done イベント送信
  - エラー系: `agent.stream()` 失敗 → error イベント送信 → ストリーム close

### `nuxt.config.ts`（8行）

- `compatibilityDate: '2025-07-15'`、`devtools: { enabled: true }`
- `runtimeConfig.openaiApiKey: ''` — `NUXT_OPENAI_API_KEY` 環境変数から自動マッピング

### `experiments/_shared.ts`（7行）

- `dotenv/config` で `.env` を自動読み込み
- `ChatOpenAI` を `gpt-4.1-mini` / temperature 0.7 で初期化しエクスポート（実験スクリプト共通）

### `experiments/01-basic-connection.ts`（28行）

- LangChain から OpenAI API を呼び出す3形式の基本接続テスト

### `experiments/02-memory-management.ts`（36行）

- MemorySaver（LangGraph チェックポイント）による会話メモリ管理の検証スクリプト

### `docs/DEV_NOTES.md`（25行）

- 環境変数の使い分け、エージェントシングルトンと HMR の注意点、typecheck 既知警告について記載

### `.env.example`（2行）

- `OPENAI_API_KEY`（実験用）と `NUXT_OPENAI_API_KEY`（Nuxt サーバー用）のテンプレート

## ISSUES 管理

### high（高優先度）

なし（すべて対応済み）

| 元ファイル | 内容 | 状態 |
|---|---|---|
| `auto-test.md` | 自動テスト導入 | ver7 で対応済み・削除 |

### low（低優先度）

| ファイル | 内容 |
|---|---|
| `response-cancel.md` | 応答の中断・キャンセル機能 |
| `index-vue-composable.md` | `index.vue` のロジックを composable へ切り出し |
| `analogy-prompt-categories.md` | アナロジープロンプトへのバイオミミクリー等の例示カテゴリ追加 |
| `streaming.md` | ストリーミング中の不完全 Markdown 表示の改善 |
| `syntax-highlight.md` | コードブロックのシンタックスハイライト |

## REQUESTS 管理

| ファイル | 内容 |
|---|---|
| `special/category_switch.md` | カテゴリ別の AI 指示切り替え |
| `special/version_flow.md` | バージョン管理ワークフロー |
| `unknown/deploy.md` | デプロイ計画 |

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

## 技術的な決定事項

- **ストリーミング方式**: h3 `createEventStream` + LangChain `agent.stream()` による SSE。POST リクエストに対する SSE レスポンスのため、`EventSource` API は使用不可（GET 専用）。クライアントは `fetch` + `parseSSEStream()` ユーティリティで受信する
- **SSE パーサーの分離**: `parseSSEStream()` を `app/utils/sse-parser.ts` に切り出し、Vue（ref 等）に依存しない純粋な async 関数として実装。コールバック（`onToken` / `onDone` / `onError`）でイベントを通知し、`done` / `error` 受信時に `return` する設計。これにより旧実装の `streamDone` フラグ・二重ループ脱出パターンが不要になった
- **ストリーム並行処理**: `chat.post.ts` ではエージェントのストリーム消費（async IIFE）と `eventStream.send()` を並行実行。IIFE の戻り値は `void` で明示的に無視
- **リアクティビティ戦略**: 空の assistant メッセージオブジェクトを先に `messages` 配列に追加し、同一参照の `.content` を更新することで Vue のリアクティビティが動作する
- **自動スクロール監視**: `messages.length` のみでなく最終メッセージの `content.length` も監視することで、ストリーミング中のスクロール追従を実現
- **会話メモリ**: `agent.stream()` でも LangGraph チェックポイント機構を通るため、ストリーミング完了時に会話履歴が MemorySaver に自動保存される。`thread_id` でセッションを識別
- **エージェント初期化**: シングルトンパターン。モジュールスコープ変数で保持し、`getAnalogyAgent()` で遅延初期化
- **API キー管理**: Nuxt `runtimeConfig` 経由。`NUXT_OPENAI_API_KEY` 環境変数から自動取得
- **SSE エラーハンドリング**: クライアント側で2つのエラー経路を統一処理。`parseSSEStream` の `onError` コールバック（サーバー側エラー）と `catch` ブロック（ネットワーク障害等）の両方で assistant メッセージに `isError` フラグを設定しエラーテキストを表示。`!isError` ガードで二重エラー防止
- **エラー時の途中テキスト保持**: ストリーミング途中でエラーが発生した場合、既に受信済みのテキストを破棄せず、末尾に改行付きでエラーメッセージを付記する
- **Markdown レンダリング**: `marked`（同期パース）+ `DOMPurify`（XSS 対策）を `ChatMessage.vue` の computed で実行。ストリーミング中もリアルタイムでリッチ表示が更新される
- **Markdown の適用範囲**: assistant メッセージのみ `v-html` + Markdown レンダリング。user メッセージはテキスト補間でプレーンテキスト表示
- **DOMPurify の SSR ガード**: `import.meta.client` で SSR 時の DOM 依存エラーを回避
- **Markdown スタイルの scoped 適用**: `:deep()` セレクタで `v-html` 子要素に Markdown タイポグラフィスタイルを適用
- **chat.post.ts の明示的インポート**: h3 関数（`createEventStream`, `readBody`, `createError`, `defineEventHandler`）と `getAnalogyAgent` を明示的にインポート。auto-import に依存しないことで、Vitest から直接 import してテストする際のモック設定が簡潔になる
- **テストにおける h3 モック**: `vi.mock('h3')` で h3 関数全体をモックし、ハンドラ関数を直接呼び出す方式を採用。`createEvent` + `IncomingMessage` を手組みする方式と比較して、テストがシンプルで保守しやすい
- **テスト環境**: Vitest の `environment: 'node'` で実行。DOM が不要なテスト（SSE パーサー、サーバーハンドラ）のみのため十分。`happy-dom` は後続バージョンの composable テスト用に導入済み

## 未実装の課題

- コードブロックのシンタックスハイライト（`highlight.js` 等の導入検討）
- ストリーミング中の不完全 Markdown の表示崩れ対策（体感上は軽微）
- 応答の中断・キャンセル機能
- composable への切り出し（`index.vue` のロジック分離、低優先度）
- アナロジープロンプトへのバイオミミクリー等の例示カテゴリ追加の検討
- フロントエンドコンポーネントテスト・E2E テスト

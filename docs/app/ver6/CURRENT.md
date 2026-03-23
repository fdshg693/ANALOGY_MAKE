# ver6 完了時点のコード現況

AI 応答の Markdown レンダリングを導入し、リスト・見出し・太字・コードブロック等をリッチテキストで表示する状態。

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
| dotenv（dev） | ^17.3.1 |
| tsx（dev） | ^4.21.0 |

## ファイル詳細

### `app/app.vue`（6行）

- `<NuxtRouteAnnouncer />` と `<NuxtPage />` を配置するルートレイアウト

### `app/pages/index.vue`（183行）

- チャットページ。以下のリアクティブ状態を管理:
  - `messages: ref<Message[]>` — チャット履歴
  - `isLoading: ref<boolean>` — 送信〜応答完了までの全体ローディング状態
  - `isStreaming: ref<boolean>` — 最初のトークン受信〜ストリーム完了までのストリーミング状態
  - `messagesContainer: ref<HTMLElement | null>` — スクロール制御用 DOM 参照
  - `threadId: ref<string>` — `crypto.randomUUID()` でページロード時に生成
- `Message` インターフェース: `{ role: 'user' | 'assistant', content: string, isError?: boolean }`
  - `isError` フラグでエラーメッセージを通常メッセージと区別
- `sendMessage()`:
  1. ユーザーメッセージと空の assistant メッセージを `messages` に追加
  2. `/api/chat` に POST → `ReadableStream` から SSE イベントを手動パース
  3. `token` イベント: assistant メッセージの `content` を逐次追加（同一オブジェクト参照を更新）
  4. `done` イベント: フラグ変数 `streamDone` を `true` に設定し `for` ループを `break`、外側の `while` ループも脱出
  5. `error` イベント: エラーテキストを assistant メッセージに付記（途中テキストがあれば末尾に改行付きで追加、なければエラーテキストのみ）、`isError = true` を設定し `streamDone` でループ脱出
  6. ストリーム完了後にコンテンツが空かつ `isError` でない場合はフォールバックメッセージを設定
  7. `catch` ブロック: SSE `error` イベントで未処理の場合のみ通信エラーメッセージを設定（`!assistantMessage.isError` ガードで二重エラー防止）
- ローディング表示: `isLoading && !isStreaming` の間のみ「考え中...」を表示
- 自動スクロール: `watch` で `messages.length` と最終メッセージの `content.length` を結合した文字列を監視 → `nextTick` 後にスクロール

### `app/components/ChatMessage.vue`（139行）

- Props: `role`（`'user' | 'assistant'`）, `content`（`string`）, `isError?`（`boolean`）
- `renderedHtml` computed:
  - `role === 'assistant'` の場合のみ `marked.parse()` で Markdown → HTML 変換し、`DOMPurify.sanitize()` でサニタイズして返す
  - `import.meta.client` ガードで SSR 時の DOMPurify エラーを回避
  - `content` prop の変更ごとに computed が再評価されるため、ストリーミング中もリアルタイムレンダリング
- テンプレート:
  - assistant メッセージ: `v-html="renderedHtml"` + `markdown-body` クラスでリッチ表示
  - user メッセージ: `{{ content }}` テキスト補間でプレーンテキスト表示
  - `v-if` / `v-else` で分岐
- ロールラベル表示（"You" / "AI"）
- ルート要素に `:class="[role, { error: isError }]"` で動的クラスを付与
- スタイル:
  - ユーザーメッセージ: 右寄せ・青系背景（`#dbeafe`）、`white-space: pre-wrap` で改行保持
  - AI メッセージ: 左寄せ・グレー背景（`#f3f4f6`）
  - エラーメッセージ: 薄赤背景（`#fef2f2`）・暗赤テキスト（`#991b1b`）・赤ボーダー（`#fecaca`）
  - Markdown タイポグラフィ（`:deep()` で `v-html` 子要素に scoped CSS 適用）:
    - 見出し（h1〜h3）: サイズ・ウェイト・マージン設定
    - 段落（p）: 上下 0.5rem マージン
    - リスト（ul/ol/li）: 左パディング 1.5rem、アイテム間 0.25rem マージン
    - インラインコード（code）: 薄灰背景・角丸・等幅フォント
    - コードブロック（pre）: 薄灰背景・角丸・横スクロール対応、内部 code の背景リセット
    - ブロッククォート（blockquote）: 左ボーダー・パディング・グレーテキスト
    - 先頭・末尾要素のマージン除去（メッセージバブル内の余白調整）
  - 最大幅 80%

### `app/components/ChatInput.vue`（70行）

- Props: `disabled: boolean`、Emits: `send: [content: string]`
- `@submit.prevent` でフォーム送信をハンドリング。空入力・disabled 時は送信不可
- 送信後に入力欄をクリア

### `server/api/chat.post.ts`（56行）

- `POST /api/chat` SSE ストリーミングエンドポイント
- リクエスト: `{ message: string, threadId: string }`（バリデーションあり、400 エラー）
- h3 の `createEventStream` を使用して SSE レスポンスを構築
- ストリーム消費を async IIFE で実行し、戻り値を `void` で明示的に無視（`eventStream.send()` と並行動作）
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

### `nuxt.config.ts`（8行）

- `compatibilityDate: '2025-07-15'`、`devtools: { enabled: true }`
- `runtimeConfig.openaiApiKey: ''` — `NUXT_OPENAI_API_KEY` 環境変数から自動マッピング

### `experiments/_shared.ts`（7行）

- `dotenv/config` で `.env` を自動読み込み
- `ChatOpenAI` を `gpt-4.1-mini` / temperature 0.7 で初期化しエクスポート（実験スクリプト共通）

### `experiments/01-basic-connection.ts`（28行）

- LangChain から OpenAI API を呼び出す3形式（文字列 / メッセージ配列 / オブジェクト）の基本接続テスト

### `experiments/02-memory-management.ts`（36行）

- MemorySaver（LangGraph チェックポイント）による会話メモリ管理の検証スクリプト
- `createAgent` + `thread_id` で会話を識別

### `docs/DEV_NOTES.md`（24行）

- 環境変数の使い分け（`OPENAI_API_KEY` は実験用、`NUXT_OPENAI_API_KEY` は Nuxt サーバー用）
- エージェントシングルトンと HMR の注意点
- `npx nuxi typecheck` の vue-router volar 既知警告について記載

### `.env.example`（2行）

- `OPENAI_API_KEY=sk-your-key-here`（実験スクリプト用）
- `NUXT_OPENAI_API_KEY=sk-your-key-here`（Nuxt サーバー用）

## ISSUES 管理

### high（高優先度）

| ファイル | 内容 | 状態 |
|---|---|---|
| `markdown-rendering.md` | Markdown レンダリング導入 | ver6 で対応済み |
| `auto-test.md` | 自動テスト導入 | 未着手 |

### low（低優先度）

| ファイル | 内容 |
|---|---|
| `response-cancel.md` | 応答の中断・キャンセル機能 |
| `sse-parser-extraction.md` | SSE パーサーのユーティリティ切り出し |
| `index-vue-composable.md` | `index.vue` のロジックを composable へ切り出し |
| `analogy-prompt-categories.md` | アナロジープロンプトへのバイオミミクリー等の例示カテゴリ追加 |
| `streaming.md` | ストリーミング中の不完全 Markdown 表示の改善 |
| `syntax-highlight.md` | コードブロックのシンタックスハイライト |

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

- **ストリーミング方式**: h3 `createEventStream` + LangChain `agent.stream()` による SSE。POST リクエストに対する SSE レスポンスのため、`EventSource` API は使用不可（GET 専用）。クライアントは `fetch` + `ReadableStream` + 手動 SSE パーサーで受信する
- **ストリーム並行処理**: `chat.post.ts` ではエージェントのストリーム消費（async IIFE）と `eventStream.send()` を並行実行。IIFE の戻り値は `void` で明示的に無視
- **リアクティビティ戦略**: 空の assistant メッセージオブジェクトを先に `messages` 配列に追加し、同一参照の `.content` を更新することで Vue のリアクティビティが動作する
- **自動スクロール監視**: `messages.length` のみでなく最終メッセージの `content.length` も監視することで、ストリーミング中のスクロール追従を実現
- **会話メモリ**: `agent.stream()` でも LangGraph チェックポイント機構を通るため、ストリーミング完了時に会話履歴が MemorySaver に自動保存される。`thread_id` でセッションを識別
- **エージェント初期化**: シングルトンパターン。モジュールスコープ変数で保持し、`getAnalogyAgent()` で遅延初期化
- **API キー管理**: Nuxt `runtimeConfig` 経由。`NUXT_OPENAI_API_KEY` 環境変数から自動取得
- **SSE エラーハンドリング**: クライアント側で2つのエラー経路を統一処理。SSE `error` イベント（サーバー側エラー）と `catch` ブロック（ネットワーク障害等）の両方で、assistant メッセージに `isError` フラグを設定しエラーテキストを表示する。`!isError` ガードで二重エラー防止
- **ストリーム完了制御**: `done` イベント受信時にフラグ変数 `streamDone` で `for` ループと `while` ループの二重ループを脱出。`ReadableStream` の終了のみに依存せず、明示的に完了を確定する
- **エラー時の途中テキスト保持**: ストリーミング途中でエラーが発生した場合、既に受信済みのテキストを破棄せず、末尾に改行付きでエラーメッセージを付記する
- **Markdown レンダリング**: `marked`（同期パース）+ `DOMPurify`（XSS 対策）を `ChatMessage.vue` の computed で実行。`content` prop の変更ごとに再評価されるため、ストリーミング中もリアルタイムでリッチ表示が更新される
- **Markdown の適用範囲**: assistant メッセージのみ `v-html` + Markdown レンダリング。user メッセージはテキスト補間でプレーンテキスト表示を維持
- **DOMPurify の SSR ガード**: `import.meta.client` で SSR 時の DOM 依存エラーを回避。初回 SSR では messages 配列が空のため実質的に呼ばれないが、安全策として明示ガード
- **Markdown スタイルの scoped 適用**: `v-html` で挿入される子要素は scoped CSS が直接適用されないため、`:deep()` セレクタで Markdown タイポグラフィスタイルを適用

## 未実装の課題

- コードブロックのシンタックスハイライト（`highlight.js` 等の導入検討）
- ストリーミング中の不完全 Markdown の表示崩れ対策（体感上は軽微）
- 応答の中断・キャンセル機能
- SSE パーサーのユーティリティ切り出し（現在 `index.vue` 内に手動実装、使用箇所が1か所のため先送り）
- composable への切り出し（`index.vue` のロジック分離、低優先度）
- アナロジープロンプトへのバイオミミクリー等の例示カテゴリ追加の検討
- 自動テストの導入

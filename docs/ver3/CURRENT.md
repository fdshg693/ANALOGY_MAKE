# ver3 完了時点のコード現況

## プロジェクト概要

アナロジー思考AIアシスタントのチャットアプリ。Nuxt 4 + Vue 3 構成。
チャットUIから LangChain エージェント経由で OpenAI API を呼び出し、5ステップのアナロジー思考フローに基づくAI応答を得られる状態。会話履歴はサーバー側 MemorySaver でセッション単位に管理される。

## 技術スタック

| 項目 | 内容 |
|---|---|
| フレームワーク | Nuxt 4.4.2 / Vue 3.5.30 |
| ルーティング | Vue Router 5.0.3（Nuxt auto-routing） |
| 言語 | TypeScript |
| スタイル | Scoped CSS（外部CSSライブラリなし） |
| バックエンド | Nuxt Server API Routes |
| AI連携 | LangChain.js（`@langchain/core` ^1.1.32, `@langchain/openai` ^1.2.13, `langchain` ^1.2.32） |
| エージェント/メモリ | LangGraph（`@langchain/langgraph` ^1.2.2）— MemorySaver による会話メモリ管理 |
| LLMモデル | gpt-4.1-mini（temperature: 0.7） |
| パッケージマネージャ | pnpm |

## ディレクトリ構成

```
app/
├── app.vue                  # ルートレイアウト（NuxtPage によるルーティング）
├── pages/
│   └── index.vue            # チャットページ（メインUI + threadId 管理）
└── components/
    ├── ChatMessage.vue      # メッセージ1件の表示コンポーネント
    └── ChatInput.vue        # 入力欄 + 送信ボタンコンポーネント
server/
├── utils/
│   ├── analogy-prompt.ts    # アナロジー思考システムプロンプト定数
│   └── analogy-agent.ts     # エージェント初期化（シングルトン）
└── api/
    └── chat.post.ts         # POST /api/chat（LangChain エージェント呼び出し）
experiments/
├── _shared.ts               # 共通設定（ChatOpenAI初期化、dotenv読み込み）
├── 01-basic-connection.ts   # 基本接続確認（3形式の呼び出しテスト）
└── 02-memory-management.ts  # 会話メモリ管理の検証（MemorySaver）
docs/
├── MASTER_PLAN.md           # 概要設計
├── DEV_NOTES.md             # 開発メモ（環境変数・HMR・既知警告）
├── ver1/ ... ver3/          # 各バージョンの計画・実装・現況ドキュメント
.env.example                 # 環境変数テンプレート（OPENAI_API_KEY, NUXT_OPENAI_API_KEY）
```

## ファイル詳細

### `app/app.vue`（6行）

- `<NuxtRouteAnnouncer />` と `<NuxtPage />` を配置するルートレイアウト

### `app/pages/index.vue`（99行）

- チャットページ。`messages` / `isLoading` / `threadId` のリアクティブ状態管理
- `threadId` は `crypto.randomUUID()` でページロード時に生成
- `sendMessage()` で `/api/chat` に `{ message, threadId }` を POST → レスポンスの `message` を `messages` に追加
- `watch` + `nextTick` による自動スクロール
- `100dvh` flex column レイアウト（ヘッダー / メッセージ領域 / 入力欄）

### `app/components/ChatMessage.vue`（48行）

- Props: `role`（`'user' | 'assistant'`）, `content`（`string`）
- ユーザーメッセージ: 右寄せ・青系背景、AIメッセージ: 左寄せ・グレー背景
- `white-space: pre-wrap` で改行保持

### `app/components/ChatInput.vue`（70行）

- Props: `disabled`、Emits: `send`
- `@submit.prevent` でフォーム送信をハンドリング。空入力は送信不可
- 送信後に入力欄をクリア

### `server/utils/analogy-prompt.ts`（31行）

- `ANALOGY_SYSTEM_PROMPT` 定数をエクスポート
- 5ステップのアナロジー思考対話フロー定義:
  1. 課題の受け取り
  2. 抽象化（具体→構造的問題への再定義）
  3. 類似事例の提示（他分野から3〜5個）
  4. 事例の選択（ユーザーが選択）
  5. 解決策の提案（選択事例の原理を元課題に適用）
- ステップ2と3を1応答にまとめるルール、日本語応答ルールを含む

### `server/utils/analogy-agent.ts`（28行）

- `getAnalogyAgent()` 関数をエクスポート。シングルトンパターンで LangChain エージェントを初期化・保持
- `ChatOpenAI`（gpt-4.1-mini, temperature 0.7）を `useRuntimeConfig().openaiApiKey` で初期化
- `MemorySaver` をチェックポインターとして使用し、`createAgent({ model, tools: [], systemPrompt, checkpointer })` でエージェントを生成

### `server/api/chat.post.ts`（26行）

- `POST /api/chat` エンドポイント
- リクエスト: `{ message: string, threadId: string }`（バリデーションあり、400 エラー）
- `getAnalogyAgent()` でエージェントを取得し、`agent.invoke()` に `{ configurable: { thread_id } }` を渡して呼び出し
- レスポンス: `{ message: { role: 'assistant', content: string } }`

### `nuxt.config.ts`（8行）

- `compatibilityDate: '2025-07-15'`、`devtools: { enabled: true }`
- `runtimeConfig.openaiApiKey: ''` — `NUXT_OPENAI_API_KEY` 環境変数から自動マッピング

### `experiments/_shared.ts`（8行）

- `dotenv/config` で `.env` を自動読み込み
- `ChatOpenAI` を `gpt-4.1-mini` / temperature 0.7 で初期化しエクスポート（実験スクリプト用）

### `experiments/01-basic-connection.ts`（28行）

- LangChain から OpenAI API を呼び出す3形式の基本接続テスト

### `experiments/02-memory-management.ts`（36行）

- MemorySaver（LangGraph チェックポイント）による会話メモリ管理の検証スクリプト
- `createAgent` + `thread_id` で会話を識別

### `docs/DEV_NOTES.md`（24行）

- 環境変数の使い分け（`OPENAI_API_KEY` は実験用、`NUXT_OPENAI_API_KEY` は Nuxt サーバー用）
- エージェントシングルトンと HMR の注意点（API キー変更時はサーバー再起動が必要）
- `npx nuxi typecheck` の vue-router volar 既知警告について記載

### `.env.example`（2行）

- `OPENAI_API_KEY=sk-your-key-here`（実験スクリプト用）
- `NUXT_OPENAI_API_KEY=sk-your-key-here`（Nuxt サーバー用）

## 技術的な決定事項

- **会話メモリ**: MemorySaver（LangGraph チェックポイント）方式。`thread_id` でセッションを識別。インメモリのためサーバー再起動で会話履歴はリセットされる
- **エージェント初期化**: シングルトンパターン。モジュールスコープ変数で保持し、`getAnalogyAgent()` で遅延初期化
- **`createAgent` API**: `systemPrompt` パラメータでシステムプロンプトを渡す（`langchain` v1.2.32）
- **API キー管理**: Nuxt `runtimeConfig` 経由。`NUXT_OPENAI_API_KEY` 環境変数から自動取得
- **API 契約**: クライアントは最新メッセージのみ送信（`{ message, threadId }`）。会話履歴はサーバー側 MemorySaver が管理

## 既知の注意点

- `createAgent` のパラメータ名は `systemPrompt`（`prompt` ではない）
- API キーの変更後はサーバー再起動が必要（シングルトンの再初期化のため）
- `npx nuxi typecheck` で vue-router volar 関連の既知警告が出るが、ビルド・実行に影響なし

## 未実装の課題

- ストリーミングレスポンス対応（現状は全文生成後に一括返却）
- エラー時のUI上のフィードバック（現状は `console.error` のみ）
- アナロジープロンプトへのバイオミミクリー等の例示カテゴリ追加の検討
- 永続的な会話履歴ストレージ（現状はインメモリのため再起動でリセット）
- 本番デプロイ時の環境変数・セキュリティ設定

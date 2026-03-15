# ver2 完了時点のコード現況

## プロジェクト概要

アナロジー思考AIアシスタントのチャットアプリ。Nuxt 4 + Vue 3 構成。
ver2 では **LangChain + OpenAI API の実験フェーズ** を実施。`experiments/` ディレクトリに検証スクリプトを追加し、API接続・会話メモリ・アナロジープロンプトの動作を確認済み。
チャットUI + モックAPI（ver1）はそのまま維持。

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
│   └── index.vue            # チャットページ（メインUI）
└── components/
    ├── ChatMessage.vue      # メッセージ1件の表示コンポーネント
    └── ChatInput.vue        # 入力欄 + 送信ボタンコンポーネント
server/
└── api/
    └── chat.post.ts         # POST /api/chat モックエンドポイント（AI連携は未統合）
experiments/
├── _shared.ts               # 共通設定（ChatOpenAI初期化、dotenv読み込み）
├── 01-basic-connection.ts   # 基本接続確認（3形式の呼び出しテスト）
├── 02-memory-management.ts  # 会話メモリ管理の比較検証（アプローチA/B）
└── 03-analogy-prompt.ts     # アナロジー思考プロンプトの検証（5ステップフロー）
docs/
├── MASTER_PLAN.md           # 概要設計
├── ver1/
│   ├── ROUGH_PLAN.md        # タスク概要
│   ├── REFACTOR.md          # リファクタリング計画
│   ├── IMPLEMENT.md         # 実装計画
│   └── CURRENT.md           # ver1 完了時のコード現況
└── ver2/
    ├── ROUGH_PLAN.md        # タスク概要
    ├── REFACTOR.md          # リファクタリング計画
    ├── IMPLEMENT.md         # 実装計画
    ├── MEMO.md              # 実装メモ・確認事項
    └── CURRENT.md           # 本ファイル
.env.example                 # 環境変数テンプレート（OPENAI_API_KEY）
```

## ver2 で追加・変更されたファイル

### `experiments/_shared.ts`（新規・8行）

- `dotenv/config` で `.env` を自動読み込み
- `ChatOpenAI` を `gpt-4.1-mini` / temperature 0.7 で初期化し、`model` としてエクスポート
- `OPENAI_API_KEY` は `ChatOpenAI` が環境変数から自動取得

### `experiments/01-basic-connection.ts`（新規・28行）

LangChain から OpenAI API を呼び出す3形式の基本接続テスト：
1. 文字列で直接呼び出し
2. `SystemMessage` + `HumanMessage` クラスの配列
3. `{ role, content }` オブジェクト形式

`usage_metadata` によるトークン使用量の取得も確認。

### `experiments/02-memory-management.ts`（新規・83行）

会話履歴の保持方法を2アプローチで比較検証：
- **アプローチA（手動管理）**: `ChatPromptTemplate` の `placeholder` に手動で `BaseMessage[]` を渡す。LCEL チェーン構成
- **アプローチB（MemorySaver）**: `langchain` の `createAgent` + `@langchain/langgraph` の `MemorySaver` でサーバー側自動保持。`thread_id` で会話を識別

→ **アプローチB を採用決定**（ver3 で統合予定）

### `experiments/03-analogy-prompt.ts`（新規・77行）

5ステップのアナロジー思考フローを実現するシステムプロンプトの検証：
- `ANALOGY_SYSTEM_PROMPT` 定数にフロー定義（ステップ1〜5 + ルール）
- 新幹線トンネル騒音問題をテストケースに3ターンの対話を実行
- ステップ2（抽象化）と3（類似事例）の1応答へのまとめ出力を確認

### `.env.example`（新規・1行）

- `OPENAI_API_KEY=sk-your-key-here` のテンプレート

### `package.json`（変更）

- **dependencies 追加**: `@langchain/core`, `@langchain/openai`, `@langchain/langgraph`, `langchain`
- **devDependencies 追加**: `dotenv`, `tsx`
- **scripts 追加**: `exp:basic`, `exp:memory`, `exp:analogy`

## ver1 から変更なしのファイル

### `app/app.vue`（6行）

- `<NuxtRouteAnnouncer />` と `<NuxtPage />` を配置するルートレイアウト

### `app/pages/index.vue`（98行）

- チャットページ。`messages` / `isLoading` のリアクティブ状態管理
- `sendMessage()` で `/api/chat` に POST → レスポンスを `messages` に追加
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

### `server/api/chat.post.ts`（21行）

- `POST /api/chat` のモックエンドポイント
- `messages` の受信・バリデーション → エコー型のモック応答を返す
- **LangChain 統合は未実施**（ver3 で対応予定）

## 実験結果サマリ

| 実験 | 結果 | 備考 |
|---|---|---|
| 01-basic-connection | 成功 | 3形式すべて正常。トークン使用量も取得可 |
| 02-memory-management | 成功 | A/B 両方動作。**アプローチB（MemorySaver）を採用** |
| 03-analogy-prompt | 成功 | 5ステップフロー成立。カワセミは自動では挙がらず、プロンプト改善余地あり |

## 技術的な決定事項

- **会話メモリ**: MemorySaver（LangGraph チェックポイント）方式を採用。`createAgent` + `thread_id` で管理
- **`createAgent` API**: `langchain` v1.2.32 の `createAgent({ model, tools, prompt, checkpointer })` で正常動作を確認

## 未実装・次バージョン以降の課題

- `server/api/chat.post.ts` への LangChain + MemorySaver 統合
- アナロジープロンプトにバイオミミクリー等の例示カテゴリ追加の検討
- `02-memory-management.ts` のアプローチA コード削除（整理）
- エラー時のUI上のフィードバック（現状は `console.error` のみ）
- CLI からの同一ロジック実行

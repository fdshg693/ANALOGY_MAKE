# ver1 完了時点のコード現況

## プロジェクト概要

アナロジー思考AIアシスタントのチャットアプリ。Nuxt 4 + Vue 3 構成。
ver1 では **チャットUI + モックAPI** を実装済み。AI連携（LangChain / OpenAI）は未実装。

## 技術スタック

| 項目 | 内容 |
|---|---|
| フレームワーク | Nuxt 4.4.2 / Vue 3.5.30 |
| ルーティング | Vue Router 5.0.3（Nuxt auto-routing） |
| 言語 | TypeScript |
| スタイル | Scoped CSS（外部CSSライブラリなし） |
| バックエンド | Nuxt Server API Routes |
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
    └── chat.post.ts         # POST /api/chat モックエンドポイント
docs/
├── MASTER_PLAN.md           # 概要設計
└── ver1/
    ├── ROUGH_PLAN.md        # タスク概要
    ├── REFACTOR.md          # リファクタリング計画
    ├── IMPLEMENT.md         # 実装計画
    └── CURRENT.md           # 本ファイル
```

## 各ファイルの状態

### `app/app.vue`

- `<NuxtRouteAnnouncer />` と `<NuxtPage />` を配置するだけのルートレイアウト
- 初期状態の `<NuxtWelcome />` から書き換え済み

### `app/pages/index.vue`

チャットページ。以下の機能を実装済み：

- **状態管理**: `messages: ref<Message[]>` と `isLoading: ref<boolean>` で管理
- **`sendMessage(input)`**: ユーザーメッセージを追加 → `/api/chat` に POST → レスポンスを追加
- **自動スクロール**: `messages.length` を `watch` し、`nextTick` 後に最下部へスクロール
- **レイアウト**: `100dvh` の flex column。ヘッダー / メッセージ領域（スクロール可能）/ 入力欄 の3段構成
- **ローディング表示**: `isLoading` 中は「考え中...」を表示

### `app/components/ChatMessage.vue`

- Props: `role`（`'user' | 'assistant'`）, `content`（`string`）
- ロールラベル（You / AI）とメッセージ本文を表示
- ユーザーメッセージは右寄せ・青系背景、AIメッセージは左寄せ・グレー背景
- `white-space: pre-wrap` で改行を保持

### `app/components/ChatInput.vue`

- Props: `disabled`（`boolean`）
- Emits: `send`（`content: string`）
- `<form>` の `@submit.prevent` でハンドリング。空入力は送信不可
- 送信後に入力欄をクリア
- `disabled` 時はボタン・入力欄ともに無効化

### `server/api/chat.post.ts`

- `POST /api/chat` エンドポイント
- リクエスト: `{ messages: Array<{ role, content }> }`
- バリデーション: `messages` が空でないこと、最後のメッセージが `user` ロールであること
- レスポンス: ユーザーの最新メッセージをエコーするモック応答を返す
  - 形式: `「{入力}」を受け取りました。\n\nこれはモック応答です。...`

## 未実装・次バージョン以降の課題

- LangChain によるプロンプトチェーン構築
- OpenAI API 連携（アナロジー思考の5ステップフロー）
- CLI からの同一ロジック実行
- エラー時のUI上のフィードバック（現状は `console.error` のみ）

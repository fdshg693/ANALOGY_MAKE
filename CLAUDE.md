# ANALOGY_MAKE - アナロジー思考AIアシスタント

## プロジェクト概要

ユーザーの課題に対し、アナロジー思考（異分野の類似事例から着想を得る手法）をAIが補助するチャットアプリ。
課題の抽象化 → 他分野の類似事例の提示 → ユーザー選択 → 解決策の提案、という5ステップの対話フローを実現する。

## 技術スタック

| 項目 | 内容 |
|---|---|
| フレームワーク | Nuxt 4 / Vue 3 |
| 言語 | TypeScript |
| スタイル | Scoped CSS（外部CSSライブラリなし） |
| バックエンド | Nuxt Server API Routes |
| AI連携 | LangChain.js + OpenAI API (gpt-4.1-mini, temperature 0.7) |
| メモリ | LangGraph MemorySaver（インメモリ、再起動でリセット） |
| テスト | Vitest 4（happy-dom 導入済み、現テストは Node 環境で実行） |
| パッケージマネージャ | pnpm |

## ディレクトリ構成

- `app/` — フロントエンド（Vue コンポーネント、ページ）
  - `composables/` — Composables（状態管理・ロジック）
- `server/` — バックエンド（API Routes、ユーティリティ）
- `tests/` — 自動テスト（Vitest）
- `experiments/` — 実験スクリプト（tsx で実行）
- `ISSUES/` — 課題管理（優先度別: `high/`, `low/`）
- `REQUESTS/` — 機能リクエスト（分類別: `special/`, `unknown/`）
- `docs/` — ドキュメント（バージョン別管理）
  - `MASTER_PLAN.md` — 概要設計
  - `DEV_NOTES.md` — 開発メモ
  - `ver{N}/` — バージョン別ドキュメント

## バージョン管理規則

各バージョンフォルダ `docs/ver{N}/` の構成:
- `ROUGH_PLAN.md` — タスク概要
- `REFACTOR.md` — リファクタリング計画
- `IMPLEMENT.md` — 実装計画
- `MEMO.md` — 実装メモ・残課題
- `CURRENT.md` — そのバージョン完了時のコード現況（CLAUDE.md と重複しない内容のみ）

## 開発上の注意

- `createAgent` のパラメータ名は `systemPrompt`（`prompt` ではない）
- APIキーの変更後はサーバー再起動が必要（シングルトンの再初期化のため）
- 環境変数: `OPENAI_API_KEY`（実験用）、`NUXT_OPENAI_API_KEY`（Nuxtサーバー用）
- `npx nuxi typecheck` で vue-router volar 関連の既知警告あり（ビルド・実行に影響なし）

## やらないこと

- 認証・ユーザー管理
- 会話履歴の永続化（DBへの保存）
- RAG構成・事例データベース
- Web検索による最新事例の取得
- モバイル最適化
- 本番デプロイ

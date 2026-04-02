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
| メモリ | LangGraph SqliteSaver（SQLite永続化、@langchain/langgraph-checkpoint-sqlite） |
| テスト | Vitest 4（happy-dom 導入済み、現テストは Node 環境で実行） |
| パッケージマネージャ | pnpm |

## ディレクトリ構成

- `app/` — フロントエンド（Vue コンポーネント、ページ）
  - `composables/` — Composables（状態管理・ロジック）
- `server/` — バックエンド（API Routes、ユーティリティ）
- `tests/` — 自動テスト（Vitest）
- `experiments/` — 実験スクリプト（tsx で実行）
- `ISSUES/` — 課題管理（カテゴリ別 → 優先度別: `{category}/high/`, `medium/`, `low/`）
- `REQUESTS/` — 機能リクエスト（分類別: `workflow/` 等）
- `docs/` — ドキュメント（カテゴリ別 → バージョン別管理）
  - `{category}/MASTER_PLAN.md` — カテゴリごとの概要設計
  - `{category}/DEV_NOTES.md` — 開発メモ
  - `{category}/ver{N}/` — バージョン別ドキュメント

## バージョン管理規則

各バージョンフォルダ `docs/{category}/ver{N}/` の構成:
- `ROUGH_PLAN.md` — タスク概要
- `REFACTOR.md` — リファクタリング計画
- `IMPLEMENT.md` — 実装計画
- `MEMO.md` — 実装メモ・残課題
- `CURRENT.md` — そのバージョン完了時のコード現況（CLAUDE.md と重複しない内容のみ）

## カテゴリ管理

- 現在のカテゴリは `.claude/CURRENT_CATEGORY` に記載（1行のカテゴリ名のみ）
- 未設定時のフォールバック: `app`
- 利用可能カテゴリ: `app`（アプリ）, `infra`（インフラ）, `cicd`（CI/CD）, `util`（ユーティリティ）
- カテゴリ切り替え: `echo "{category}" > .claude/CURRENT_CATEGORY`
- 各SKILLは自動的に現在のカテゴリに対応するパスを参照する

## 開発上の注意

- `createAgent` のパラメータ名は `systemPrompt`（`prompt` ではない）
- `getAnalogyAgent()` は async 関数（呼び出し元で `await` が必要）
- APIキーの変更後はサーバー再起動が必要（シングルトンの再初期化のため）
- 環境変数: `OPENAI_API_KEY`（実験用）、`NUXT_OPENAI_API_KEY`（Nuxtサーバー用）
- `npx nuxi typecheck` で vue-router volar 関連の既知警告あり（ビルド・実行に影響なし）
- `data/` ディレクトリは SQLite データベースの保存先（`.gitignore` 済み）
- `better-sqlite3` は pnpm の厳密な依存解決により直接依存として追加済み（`thread-store.ts` での直接インポートのため）

## やらないこと

- 認証・ユーザー管理
- RAG構成・事例データベース
- Web検索による最新事例の取得
- モバイル最適化
- 本番デプロイ

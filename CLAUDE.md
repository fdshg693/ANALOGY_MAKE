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
| AI連携 | LangGraph StateGraph + LangChain.js + OpenAI API (gpt-5.4, temperature 0.7) + Tavily Search (@langchain/tavily) |
| メモリ | LangGraph SqliteSaver（SQLite永続化、@langchain/langgraph-checkpoint-sqlite） |
| テスト | Vitest 4（happy-dom 導入済み、現テストは Node 環境で実行） |
| パッケージマネージャ | pnpm（`packageManager: pnpm@10.26.2` で固定） |
| デプロイ先 | Azure App Service Free (F1, Linux)（Nitro preset: `node-server`） |
| CI/CD | GitHub Actions（`.github/workflows/deploy.yml`、main push 時に自動デプロイ） |
| IaC | Bicep（`infra/` に Azure リソース定義、`just deploy-infra` で手動デプロイ） |
| コマンドランナー | just（`Justfile` で Azure CLI 操作・インフラ管理をラップ） |

## ディレクトリ構成

- `app/` — フロントエンド（Vue コンポーネント、ページ）
  - `composables/` — Composables（状態管理・ロジック）
- `server/` — バックエンド（API Routes、ユーティリティ）
- `tests/` — 自動テスト（Vitest）
- `scripts/` — Python 自動化スクリプト（`claude_loop.py` + `claude_loop_lib/` パッケージ、詳細は `scripts/README.md`）
- `experiments/` — 実験スクリプト（tsx で実行）
- `.github/workflows/` — CI/CD（GitHub Actions）
- `ISSUES/` — 課題管理（カテゴリ別 → 優先度別: `{category}/high/`, `medium/`, `low/`）。`ISSUES/README.md` にフロントマター仕様（`status` / `assigned` / `reviewed_at`）を定義。`python scripts/issue_status.py` で分布確認、`python scripts/issue_worklist.py` で AI 向け着手候補を一覧取得。人間への依頼は `assigned: human` / `status: need_human_action` を付けて同ディレクトリに集約する（ver13.0 で `REQUESTS/AI` `REQUESTS/HUMAN` を廃止）
- `FEEDBACKS/` — ワークフローへのユーザーフィードバック（YAML frontmatter で対象ステップ指定、消費後 `done/` へ移動）
- `infra/` — Azure インフラ定義（Bicep テンプレート）
- `Justfile` — Azure CLI 運用コマンド（ログ確認・再起動・SSH 等）+ インフラ管理コマンド（デプロイ・プレビュー・削除）
- `docs/` — ドキュメント（カテゴリ別 → バージョン別管理）
  - `{category}/MASTER_PLAN.md` — カテゴリごとの概要設計
  - `{category}/DEV_NOTES.md` — 開発メモ
  - `{category}/ver{N}/` — バージョン別ドキュメント

## バージョン管理規則

バージョン形式: `ver{Major}.{Minor}`（例: `ver13.0`, `ver13.1`）
- **メジャーバージョン (X.0)**: 新機能追加・アーキテクチャ変更・MASTER_PLAN の新項目着手時
- **マイナーバージョン (X.Y, Y>0)**: バグ修正・既存機能改善・ISSUES対応

各バージョンフォルダ `docs/{category}/ver{X.Y}/` の構成:
- `ROUGH_PLAN.md` — タスク概要
- `REFACTOR.md` — リファクタリング計画
- `IMPLEMENT.md` — 実装計画
- `MEMO.md` — 実装メモ・残課題
- `CURRENT.md` — **メジャーバージョンのみ**: コード現況の完全版（CLAUDE.md と重複しない内容のみ）
- `CHANGES.md` — **マイナーバージョンのみ**: 前バージョンからの変更差分

※ 旧形式 (ver9〜ver12) は整数名のまま保持

## カテゴリ管理

- 現在のカテゴリは `.claude/CURRENT_CATEGORY` に記載（1行のカテゴリ名のみ）
- 未設定時のフォールバック: `app`
- 利用可能カテゴリ: `app`（アプリ）, `infra`（インフラ）, `cicd`（CI/CD）, `util`（ユーティリティ）
- カテゴリ切り替え: `echo "{category}" > .claude/CURRENT_CATEGORY`
- 各SKILLは自動的に現在のカテゴリに対応するパスを参照する

## 開発上の注意

- `getAnalogyAgent()` は async 関数（呼び出し元で `await` が必要）。戻り値は `CompiledStateGraph`（ver14.0 で `createReactAgent` から `StateGraph` に移行済み）
- APIキーの変更後はサーバー再起動が必要（シングルトンの再初期化のため）
- 環境変数: `OPENAI_API_KEY`（実験用）、`NUXT_OPENAI_API_KEY`（Nuxtサーバー用）、`NUXT_TAVILY_API_KEY`（Tavily Search用、未設定時はWeb検索なしで動作）
- `npx nuxi typecheck` で vue-router volar 関連の既知警告あり（ビルド・実行に影響なし）
- `data/` ディレクトリは SQLite データベースの保存先（`.gitignore` 済み）
- DB パスは `server/utils/db-config.ts` で一元管理（開発: `./data/`、本番: `/home/data/`）
- `better-sqlite3` は pnpm の厳密な依存解決により直接依存として追加済み（`thread-store.ts` での直接インポートのため）

## やらないこと

- 認証・ユーザー管理
- RAG構成・事例データベース
- モバイル最適化
- カスタムドメイン・SSL証明書管理・監視・バックアップ

# ver15.0 完了時点のコード現況

ver14.0（StateGraph マルチノード構成）〜 ver14.5（履歴フィルタリング修正）を経て、PHASE3 の動的設定システム基盤とAI回答粒度切り替え機能を追加した状態。スレッドごとに設定（回答粒度プリセット + カスタム指示）を保存し、各ノードのシステムプロンプトに動的注入する仕組みが完成。

- [CURRENT_backend.md](CURRENT_backend.md) — サーバーサイド（API Routes、エージェント、プロンプト、ストレージ）
- [CURRENT_frontend.md](CURRENT_frontend.md) — フロントエンド（コンポーネント、Composables、ユーティリティ）
- [CURRENT_tests.md](CURRENT_tests.md) — テストファイル一覧・テストケース数

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

`package.json` に `pnpm.onlyBuiltDependencies: ["better-sqlite3"]` を指定。

## 設定・構成ファイル

### `nuxt.config.ts`（15行）

- `compatibilityDate: '2025-07-15'`
- `runtimeConfig.openaiApiKey`, `runtimeConfig.tavilyApiKey`
- `nitro.externals.external: ['better-sqlite3']`

### `vitest.config.ts`（16行）

- `environment: 'node'`
- `define: { 'import.meta.client': 'globalThis.__NUXT_CLIENT__' }`

### `.env.example`（3行）

- `OPENAI_API_KEY`、`NUXT_OPENAI_API_KEY`、`NUXT_TAVILY_API_KEY`

## ISSUES 管理

### low（低優先度）

| ファイル | 内容 |
|---|---|
| `syntax-highlight.md` | コードブロックのシンタックスハイライト |
| `vitest-nuxt-test-utils.md` | `@nuxt/test-utils` 導入 |

### medium（中優先度）

| ファイル | 内容 |
|---|---|
| `動作確認便利化.md` | エコーモード・システムプロンプトカスタマイズ（PHASE3 項目4） |

### ver14.1〜14.5 で解決済み（削除）

| ファイル | 解決バージョン |
|---|---|
| `analogy-prompt-categories.md` | ver14.1 |
| `streaming.md` | ver14.2 |
| `履歴不具合.md` | ver14.3 |
| `テストモック脆弱性-isInstance.md` | ver14.5 |
| `履歴修正-実機確認.md` | ver15.0 時点で削除済み |

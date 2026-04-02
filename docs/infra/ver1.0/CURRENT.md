# ver1.0 コード現況

## DB パス管理

### server/utils/db-config.ts（11行）

DB パスとディレクトリ初期化を一元管理するモジュール。

- `NODE_ENV === 'production'` の場合: `/home/data/langgraph-checkpoints.db`（Azure App Service 永続ストレージ）
- それ以外: `./data/langgraph-checkpoints.db`（ローカル開発）
- モジュール読み込み時に `mkdirSync(DB_DIR, { recursive: true })` でディレクトリを自動作成
- `DB_PATH` を named export し、`analogy-agent.ts` と `thread-store.ts` から参照される

### server/utils/analogy-agent.ts（DB 関連部分）

- `import { DB_PATH } from "./db-config"` で DB パスを取得
- `SqliteSaver.fromConnString(DB_PATH)` で LangGraph チェックポイントを永続化
- 起動時に `console.log` で DB パスをログ出力

### server/utils/thread-store.ts（DB 関連部分）

- `import { DB_PATH } from './db-config'` で DB パスを取得
- `new Database(DB_PATH)` で better-sqlite3 の接続を初期化
- WAL モード有効化済み

## Nuxt ビルド設定

### nuxt.config.ts（15行）

- `nitro.preset: 'node-server'` — Azure App Service 向けの Node.js サーバーモード
- `nitro.externals.external: ['better-sqlite3']` — ネイティブモジュールをバンドル対象から除外
- `runtimeConfig.openaiApiKey` / `runtimeConfig.tavilyApiKey` — 環境変数経由で注入
- ビルド成果物: `.output/server/index.mjs`（App Service の起動コマンドに使用）

## CI/CD

### .github/workflows/deploy.yml（29行）

GitHub Actions ワークフロー。`main` ブランチへの push 時に自動実行。

| ステップ | 内容 |
|---|---|
| checkout | `actions/checkout@v4` |
| pnpm セットアップ | `pnpm/action-setup@v4`（`package.json` の `packageManager` フィールドからバージョン検出） |
| Node.js セットアップ | `actions/setup-node@v4`（Node 22、pnpm キャッシュ有効） |
| 依存インストール | `pnpm install --frozen-lockfile` |
| ビルド | `pnpm build` |
| デプロイ | `azure/webapps-deploy@v3`（Publish Profile 認証、`.output/` をデプロイ） |

認証方式: Publish Profile（`secrets.AZURE_WEBAPP_PUBLISH_PROFILE` に登録が必要）

### package.json（packageManager フィールド）

- `"packageManager": "pnpm@10.26.2"` — CI 上の `pnpm/action-setup@v4` がこのフィールドからバージョンを検出

## 運用ツール

### Justfile（25行）

Azure CLI 操作をラップするコマンドランナー。`az login` 済みが前提。

| コマンド | 説明 |
|---|---|
| `just logs` | Azure App Service のリアルタイムログ出力 |
| `just restart` | App Service の再起動 |
| `just env-list` | App Service の環境変数一覧をテーブル表示 |
| `just ssh` | App Service コンテナへの SSH 接続 |
| `just preview` | ローカルビルド + `node .output/server/index.mjs` で本番相当のプレビュー |

変数定義: `app_name := "analogy-make"`, `resource_group := "rg-analogy-make"`（実際のリソース名に要変更）

## Azure 環境の設定状況

### 手動設定が必要な項目（未実施）

以下はコードで管理されておらず、Azure CLI での手動操作が必要:

1. **リソース作成**: `az group create` → `az appservice plan create` → `az webapp create`
2. **環境変数設定**: `NUXT_OPENAI_API_KEY`, `NUXT_TAVILY_API_KEY` を App Service に登録
3. **起動コマンド設定**: `az webapp config set --startup-file "node .output/server/index.mjs"`
4. **GitHub Secrets**: Publish Profile を `AZURE_WEBAPP_PUBLISH_PROFILE` として登録

手順の詳細は `docs/infra/MASTER_PLAN/PHASE1.0.md` に記載。

## 未解決の課題

| ISSUE | 優先度 | 内容 |
|---|---|---|
| `ISSUES/infra/medium/verify-output-dir-azure.md` | Medium | `.output/` ディレクトリが Azure App Service と互換性があるか、初回デプロイ時に要検証 |
| `ISSUES/infra/low/azure-resource-docs.md` | Low | Azure リソース作成手順の独立ドキュメント化 |

## 技術的判断

### Nitro preset に `node-server` を採用

Azure App Service は Node.js ランタイムを直接実行するため、`node-server` プリセットが最適。Nuxt の SPA モードやスタティック生成は SSR + API Routes の要件に合わないため不採用。

### DB パスの環境切り替えに `NODE_ENV` を使用

Nuxt は本番ビルド時に `NODE_ENV=production` を設定するため、追加の環境変数なしでパスを切り替えられる。Azure App Service の `/home/data/` はデプロイで上書きされない永続ストレージであり、DB ファイルの安全な配置先となる。

### Publish Profile 認証を採用

Service Principal や OIDC と比較して設定が最もシンプル。個人プロジェクトの Free プランでは十分。Azure Portal からダウンロード → GitHub Secrets に登録するだけで完了。

### Justfile に `deploy` コマンドを含めない

デプロイは GitHub Actions で自動化されているため、手動デプロイコマンドの二重管理を避けた。`just preview` でローカルでの本番ビルド確認は可能。

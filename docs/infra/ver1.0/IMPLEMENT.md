# ver1.0 実装計画

## 前提: REFACTOR.md の R1 を先に適用済みとする

---

## I1: Nuxt ビルド設定の調整

### 対象ファイル

`nuxt.config.ts`

### 変更内容

Nitro の preset に `node-server` を追加する。

```typescript
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  runtimeConfig: {
    openaiApiKey: '',
    tavilyApiKey: '',
  },
  nitro: {
    preset: 'node-server',
    externals: {
      external: ['better-sqlite3'],
    },
  },
})
```

### 補足

- `nuxi dev` は preset に関係なく開発サーバーを起動するため、ローカル開発への影響なし
- `nuxt build` 実行時に `.output/server/index.mjs` が生成される（App Service の起動コマンドに使用）

---

## I2: SQLite パスの環境ベース切り替え

### 対象ファイル

`server/utils/db-config.ts`（R1 で新規作成済み）

### 変更内容

R1 で作成した `db-config.ts` 内で、`NODE_ENV` に基づきパスを切り替える:

- 開発環境 (`NODE_ENV !== 'production'`): `./data/langgraph-checkpoints.db`
- 本番環境 (`NODE_ENV === 'production'`): `/home/data/langgraph-checkpoints.db`

`/home/data/` は Azure App Service の永続ストレージ。デプロイで上書きされない。

### 既存ファイルの修正

| ファイル | 修正内容 |
|---|---|
| `server/utils/analogy-agent.ts` | `DB_PATH` 定義を削除、`import { DB_PATH } from './db-config'` に変更。`mkdirSync` 呼び出しを削除 |
| `server/utils/thread-store.ts` | 同上 |

---

## I3: GitHub Actions ワークフロー

### 新規ファイル

`.github/workflows/deploy.yml`

### 内容

```yaml
name: Deploy to Azure App Service

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm

      - run: pnpm install --frozen-lockfile

      - run: pnpm build

      - uses: azure/webapps-deploy@v3
        with:
          app-name: analogy-make  # 実際の名前に要変更
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
          package: .output/
```

### 補足

- `ubuntu-latest` でビルドするため、`better-sqlite3` のネイティブモジュールは Linux 向けにコンパイルされる（クロスプラットフォーム対応は CI 上のビルドで自動解決）
- `pnpm/action-setup@v4` は `package.json` の `packageManager` フィールドから pnpm バージョンを検出する。現在 `package.json` に `packageManager` フィールドがないため、追加が必要
- `--frozen-lockfile` で lockfile の整合性を保証
- `publish-profile` は手動で Azure Portal から取得し、GitHub Secrets に `AZURE_WEBAPP_PUBLISH_PROFILE` として登録する（本バージョンのスコープ外）

### package.json への追記

`packageManager` フィールドを追加する:

```json
{
  "packageManager": "pnpm@10.26.2"
}
```

---

## I4: Justfile

### 新規ファイル

`Justfile`

### 内容

```justfile
# Azure App Service 操作コマンド
# 前提: az login 済み

app_name := "analogy-make"
resource_group := "rg-analogy-make"

# ログ確認（リアルタイム）
logs:
    az webapp log tail --name {{app_name}} --resource-group {{resource_group}}

# 再起動
restart:
    az webapp restart --name {{app_name}} --resource-group {{resource_group}}

# 環境変数一覧
env-list:
    az webapp config appsettings list --name {{app_name}} --resource-group {{resource_group}} --output table

# SSH接続
ssh:
    az webapp ssh --name {{app_name}} --resource-group {{resource_group}}

# ローカルビルド + プレビュー
preview:
    pnpm build && node .output/server/index.mjs
```

### 補足

- `app_name` と `resource_group` は Justfile 冒頭の変数で定義。Azure リソース作成時に名前が変わった場合はここを修正する
- `deploy` コマンドは GitHub Actions で自動化されるため、Justfile には含めない（二重管理を避ける）

---

## I5: 動作確認チェックリスト

### 対象

MEMO.md に記載する（本バージョンの実装後に確認すべき手動ステップ）。

### チェック項目

1. **ローカルビルド確認**: `pnpm build` が成功し、`.output/server/index.mjs` が生成される
2. **ローカルプレビュー**: `just preview` または `node .output/server/index.mjs` でアプリが起動する
3. **Azure リソース作成**: PHASE1.0 の手順に従い az CLI でリソースを作成
4. **環境変数設定**: `NUXT_OPENAI_API_KEY` と `NUXT_TAVILY_API_KEY` を App Service に設定
5. **起動コマンド設定**: `az webapp config set --startup-file "node .output/server/index.mjs"` を実行
6. **GitHub Secrets 設定**: Publish Profile を `AZURE_WEBAPP_PUBLISH_PROFILE` として登録
7. **初回デプロイ**: `main` ブランチに push → GitHub Actions が成功
8. **動作確認**:
   - チャット UI が表示される
   - メッセージ送信 → AI 応答（ストリーミング）が動作する
   - スレッド作成・切り替えが動作する
   - サーバー再起動後も会話履歴が保持される

---

## 実装順序

1. R1（DB パス共通化）
2. I1（Nuxt ビルド設定）+ I2（SQLite パス切り替え）— R1 の適用と合わせて実施
3. I3（GitHub Actions）+ I4（Justfile）— 独立しているため並行可能
4. I5（チェックリストを MEMO.md に記載）

## リスク・不確実性

### `azure/webapps-deploy@v3` の `package` パラメータ

Nuxt の `.output/` ディレクトリ構造が Azure App Service の期待するフォーマットと合致するか、実際のデプロイ時に検証が必要。合致しない場合は zip デプロイ (`az webapp deploy --type zip`) への切り替えを検討する。

### `SqliteSaver.fromConnString` のパス解決

`@langchain/langgraph-checkpoint-sqlite` が絶対パス `/home/data/...` を正しく扱えるか、ライブラリの実装に依存する。`better-sqlite3` 自体は絶対パスをサポートしているため問題ない見込みだが、ラッパー側で相対パス前提の処理がある可能性は排除できない。

### pnpm の `packageManager` フィールド追加

`pnpm/action-setup@v4` が `packageManager` フィールドを必要とする。追加自体は単純だが、ローカル開発で pnpm バージョンの不一致警告が出る可能性がある。corepack が有効な環境では自動的に正しいバージョンが使用される。

### App Service 起動コマンドの設定

Azure App Service はデフォルトでは `npm start` を実行するが、本プロジェクトでは `node .output/server/index.mjs` が正しい起動コマンドとなる。Azure Portal または `az webapp config set --startup-file "node .output/server/index.mjs"` で設定が必要（手動操作、I5 のチェックリストに含む）。

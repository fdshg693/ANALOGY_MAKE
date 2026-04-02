# PHASE1.0: Azure App Service Free への初回デプロイ

## 概要

ANALOGY_MAKE を Azure App Service Free (F1, Linux) にデプロイし、
ブラウザからアクセスして動作する状態にする。

## 前提条件

- Azure アカウント（無料枠利用）
- GitHub リポジトリ（GitHub Actions 用）
- Azure CLI インストール済み
- just コマンドランナーインストール済み

## やること

### 1. Azure リソースの作成

- Resource Group の作成
- App Service Plan (Free F1, Linux) の作成
- Web App (Node.js 22 LTS) の作成

```
az group create --name rg-analogy-make --location japaneast
az appservice plan create --name plan-analogy-make --resource-group rg-analogy-make --sku F1 --is-linux
az webapp create --name analogy-make --resource-group rg-analogy-make --plan plan-analogy-make --runtime "NODE:22-lts"
```

※ `analogy-make` は一意な名前に要変更（`*.azurewebsites.net` のサブドメインになるため）

### 2. Nuxt ビルド設定の調整

- Nitro preset を `node-server` に設定（App Service 向け）
- 起動コマンド: `node .output/server/index.mjs`
- SQLite のデータパスを環境に応じて切り替え
  - 開発: `./data/` (既存のまま)
  - 本番: `/home/data/` (App Service の永続ストレージ)

### 3. better-sqlite3 のクロスプラットフォーム対応

- ローカル開発は Windows だが、App Service は Linux
- GitHub Actions (ubuntu-latest) でビルドすれば Linux 向けネイティブモジュールが生成される
- `pnpm install` + `nuxt build` を Linux 上で実行すれば問題なし

### 4. 環境変数の設定

```
az webapp config appsettings set \
  --name analogy-make \
  --resource-group rg-analogy-make \
  --settings \
    NUXT_OPENAI_API_KEY="sk-..." \
    NUXT_TAVILY_API_KEY="tvly-..."
```

### 5. GitHub Actions ワークフロー

`.github/workflows/deploy.yml` を作成:
- トリガー: `main` ブランチへの push
- ステップ: pnpm install → nuxt build → Azure App Service へデプロイ
- 認証: Azure publish profile をリポジトリの Secrets に登録

### 6. Justfile の作成

手動操作を Azure CLI でラップ:

```justfile
# デプロイ（手動）
deploy:
    pnpm build
    az webapp deploy ...

# ログ確認
logs:
    az webapp log tail --name analogy-make --resource-group rg-analogy-make

# 再起動
restart:
    az webapp restart --name analogy-make --resource-group rg-analogy-make

# 環境変数一覧
env-list:
    az webapp config appsettings list --name analogy-make --resource-group rg-analogy-make

# SSH接続
ssh:
    az webapp ssh --name analogy-make --resource-group rg-analogy-make
```

### 7. 動作確認

- `https://analogy-make.azurewebsites.net` にアクセスしてチャットUIが表示される
- メッセージ送信 → AI応答（ストリーミング）が動作する
- スレッド作成・切り替えが動作する
- サーバー再起動後も会話履歴が保持される（SQLite永続化確認）

## 技術的な注意点

### SQLite パス切り替え

App Service Free の `/home` ディレクトリは Azure Storage にマウントされた永続ストレージ。
アプリのルートディレクトリ（`/home/site/wwwroot/`）も `/home` 配下だが、
DB ファイルはデプロイで上書きされないよう `/home/data/` に配置する。

```typescript
// 例: 環境に応じたパス切り替え
const dbPath = process.env.NODE_ENV === 'production'
  ? '/home/data/analogy.db'
  : './data/analogy.db'
```

### コールドスタート

Free プランでは非アクティブ時にプロセスが停止する。
次回アクセス時に Node.js + Nuxt の起動が必要で、数秒〜十数秒のレイテンシが発生する。
個人利用なので許容する。

### GitHub Actions の認証

Publish Profile 方式（シンプル）:
1. Azure Portal → Web App → デプロイセンター → 発行プロファイルの取得
2. GitHub リポジトリ → Settings → Secrets → `AZURE_WEBAPP_PUBLISH_PROFILE` として登録

## やらないこと

- カスタムドメイン設定
- SSL証明書の管理（`*.azurewebsites.net` のデフォルトHTTPSを利用）
- バックアップ設定
- 監視・アラート設定
- ステージング環境

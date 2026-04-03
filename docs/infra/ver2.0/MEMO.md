# ver2.0 実装メモ

## 計画との乖離

なし。IMPLEMENT.md の計画通りに全ファイルを作成した。

## デプロイ前に確認すべき事項

### appCommandLine のパス

- ⏭️ **対応不要**
- `deploy.yml` が `package: .output/` で `.output/` の中身を wwwroot にデプロイするため、wwwroot 基準では `server/index.mjs` が正しい
- Bicep の `appCommandLine: 'node server/index.mjs'` は正しい設定
- CURRENT.md (ver1.0) の `node .output/server/index.mjs` はローカルプレビュー（`just preview`）向けの記述であり、Azure の起動コマンドとは文脈が異なる
- 実デプロイ後の検証は `ISSUES/infra/medium/verify-output-dir-azure.md` で引き続きトラッキング

### @secure() パラメータのプロンプト入力

- ⏭️ **対応不要**
- Azure CLI は `.bicepparam` に `@secure()` パラメータの値がない場合、デプロイ時にプロンプトで入力を求める（既知の動作）
- フォールバック手段（`--parameters openaiApiKey=xxx tavilyApiKey=yyy` インライン指定）も記載済み
- 実デプロイ時に確認する運用タスクであり、コード修正不要

## クローズした ISSUE

- ✅ `ISSUES/infra/low/azure-resource-docs.md` — Bicep テンプレート（infra/main.bicep 等）と Justfile コマンドがリソース作成手順の代替となったため、クローズ済み

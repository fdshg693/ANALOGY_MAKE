# ver2.0 実装メモ

## 計画との乖離

なし。IMPLEMENT.md の計画通りに全ファイルを作成した。

## デプロイ前に確認すべき事項

- **appCommandLine のパス**: `node server/index.mjs` を設定しているが、CURRENT.md (ver1.0) では `node .output/server/index.mjs` と記載されている箇所がある。deploy.yml が `package: .output/` で `.output/` の中身を wwwroot にデプロイするため `server/index.mjs` が正しいはずだが、初回デプロイ後に `just logs` で起動の成否を確認すること
- **@secure() パラメータのプロンプト入力**: `.bicepparam` に値を記載しない設計のため、`az deployment sub create` 実行時にプロンプトで入力を求められる想定。動作しない場合は `--parameters openaiApiKey=xxx tavilyApiKey=yyy` のインライン指定でフォールバック可能

## クローズ可能な ISSUE

- `ISSUES/infra/low/azure-resource-docs.md` — Bicep テンプレートがリソース作成手順の代替となるため、クローズ可能

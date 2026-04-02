# ver1.0 実装メモ

## 計画との乖離

なし。REFACTOR.md / IMPLEMENT.md の計画通りに実装。

## 動作確認チェックリスト（手動）

1. **ローカルビルド確認**: `pnpm build` が成功し、`.output/server/index.mjs` が生成される
2. **ローカルプレビュー**: `just preview` または `node .output/server/index.mjs` でアプリが起動する
3. **Azure リソース作成**: az CLI でリソースグループ・App Service を作成
4. **環境変数設定**: `NUXT_OPENAI_API_KEY` と `NUXT_TAVILY_API_KEY` を App Service に設定
5. **起動コマンド設定**: `az webapp config set --startup-file "node .output/server/index.mjs"` を実行
6. **GitHub Secrets 設定**: Publish Profile を `AZURE_WEBAPP_PUBLISH_PROFILE` として登録
7. **初回デプロイ**: `main` ブランチに push → GitHub Actions が成功
8. **動作確認**:
   - チャット UI が表示される
   - メッセージ送信 → AI 応答（ストリーミング）が動作する
   - スレッド作成・切り替えが動作する
   - サーバー再起動後も会話履歴が保持される

## 注意事項

- `deploy.yml` の `app-name: analogy-make` は実際の Azure App Service 名に合わせて変更が必要
- `Justfile` の `app_name` と `resource_group` も同様に実際のリソース名に合わせる
- `packageManager` フィールドを `package.json` に追加済み（`pnpm@10.26.2`）。ローカルの pnpm バージョンと合わない場合は corepack で管理推奨

## 残課題

- Azure リソースの作成手順のドキュメント化（docs/infra/ に別途作成を推奨）
- `.output/` ディレクトリ構造が Azure App Service と合致するかはデプロイ時に要検証（合致しない場合は zip デプロイに切り替え）

---

## wrap_up 対応結果（2026-04-03）

### 品質チェック

- `npx nuxi typecheck`: vue-router volar 既知警告のみ（型エラーなし）
- 未使用 import・変数: deploy.yml / Justfile / nuxt.config.ts / package.json を確認、問題なし

### 各項目の対応

| 項目 | 判断 | 理由 |
|---|---|---|
| 動作確認チェックリスト（全8項目） | ⏭️ 対応不要 | 手動確認前提。デプロイ時にユーザーが実施 |
| 注意事項: app-name / リソース名の変更 | ⏭️ 対応不要 | リソース名はユーザー決定事項。ドキュメントとして保持 |
| 注意事項: packageManager 追加済み | ✅ 対応完了 | package.json に `pnpm@10.26.2` 設定済みを確認 |
| 残課題: Azure リソース作成手順のドキュメント化 | 📋 先送り | ISSUES/infra/low に追加。PHASE1.0.md に最低限の手順あり |
| 残課題: .output/ ディレクトリ構造の検証 | 📋 先送り | ISSUES/infra/medium に追加。実デプロイ後でないと判断不能 |

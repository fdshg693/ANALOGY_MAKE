# ver2.1 変更内容

## 変更ファイル一覧

| ファイル | 種別 | 概要 |
|---|---|---|
| `.github/workflows/deploy.yml` | 修正 | ビルド後・デプロイ前にシンボリックリンクを実体に置換するステップを追加 |

## 変更内容の詳細

### `.github/workflows/deploy.yml` — シンボリックリンク実体化ステップ追加

**問題**: Nitro の `node-server` プリセットは、`.output/server/node_modules/` 内でパッケージの重複を避けるため、`.nitro/` ディレクトリに実体を配置しシンボリックリンクで参照する構造を取る。`azure/webapps-deploy@v3` は内部で ZIP デプロイを使用するが、ZIP アーカイブはシンボリックリンクを保持しない。そのため Azure 上でリンクが壊れ、`ERR_MODULE_NOT_FOUND: Cannot find package 'hookable'` などの 500 エラーが発生していた。

**修正内容**: `pnpm build` と `azure/webapps-deploy` の間に「Resolve symlinks for Azure deployment」ステップ（約20行）を追加。

- `find .output -type l` で全シンボリックリンクを列挙
- 各リンクの実体パスを `readlink -f` で取得
- リンクを削除し、実体をコピー（`cp -r`）で置換
- 壊れたリンク（実体が存在しない）はスキップして WARNING 出力
- 事後検証: 残存シンボリックリンクがあればエラー終了

## 技術的判断

### シンボリックリンク実体化をデプロイパイプラインで行う理由

**採用案**: deploy.yml でビルド後に全シンボリックリンクを実体に置換

- 全シンボリックリンクに一括対応（`hookable` だけでなく `uuid` 等も含む）
- 将来の依存追加・変更でリンクが増えても自動対応
- ローカル開発・ビルド設定への影響ゼロ
- 標準 POSIX コマンドのみ使用し、ubuntu-latest で確実に動作

**不採用案**:
- Nitro `externals.inline` で特定パッケージをバンドル → 対症療法であり、他のリンクに対応不可
- pnpm `--node-linker=hoisted` → pnpm 全体の挙動変更で副作用が広い
- `rsync -rL` で `.output/` を複製 → ディスク使用量が2倍になり不必要

## 対応 ISSUE

| ISSUE | ステータス |
|---|---|
| `ISSUES/infra/high/Actionデプロイ.md` | 修正済み（デプロイ検証後にクローズ予定） |
| `ISSUES/infra/medium/verify-output-dir-azure.md` | 本修正で対応（デプロイ検証後にクローズ予定） |

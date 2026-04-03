# ver2.1 実装計画

## 原因の詳細分析

### 問題の構造

Nitro の `node-server` プリセットは、バンドルしないパッケージ（externals）を `.output/server/node_modules/` に配置する。この際、同一パッケージの重複を避けるため、`.nitro/` ディレクトリ内にバージョン付きの実体を置き、各パッケージディレクトリをシンボリックリンクにする:

```
.output/server/node_modules/
├── .nitro/
│   ├── hookable@6.1.0/    ← 実体
│   └── uuid@11.1.0/       ← 実体
├── hookable/               ← シンボリックリンク → .nitro/hookable@6.1.0
├── uuid/                   ← シンボリックリンク → .nitro/uuid@11.1.0
└── unhead/
    └── node_modules/
        └── hookable/       ← シンボリックリンク → ../../.nitro/hookable@6.1.0
```

### なぜ Azure で壊れるか

`azure/webapps-deploy@v3` は内部で ZIP デプロイを使用する。ZIP アーカイブはシンボリックリンクを保持しないため、Azure 上ではリンクが壊れた状態（空ファイルまたは欠損）になり、`ERR_MODULE_NOT_FOUND` が発生する。

## 対処方針

### 採用: deploy.yml でシンボリックリンクを実体に置換

ビルド後・デプロイ前に、`.output/` 内の全シンボリックリンクを実体ファイル/ディレクトリに置換するステップを追加する。

**選定理由**:
- 全シンボリックリンクに対応（`hookable` だけでなく `uuid` 等も修正）
- 将来の依存追加・変更でシンボリックリンクが増えても自動対応
- Nitro のビルド設定を変更しないため、ローカル開発への影響ゼロ
- GitHub Actions（ubuntu-latest）で確実に動作する標準 POSIX コマンドのみ使用

**不採用案**:
- Nitro `externals.inline` で特定パッケージをバンドル → 対症療法であり、他のシンボリックリンクに対応できない
- pnpm `--node-linker=hoisted` → pnpm 全体の挙動が変わり、副作用が広い
- `rsync -rL` で `.output/` を複製 → ディスク使用量が2倍になり不必要

## 変更内容

### 1. `.github/workflows/deploy.yml`（既存ファイル修正）

`pnpm build` ステップと `azure/webapps-deploy` ステップの間に、シンボリックリンク実体化ステップを追加する。

**変更前**（24-30行）:
```yaml
      - run: pnpm build

      - uses: azure/webapps-deploy@v3
        with:
          app-name: analogy-make
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
          package: .output/
```

**変更後**:
```yaml
      - run: pnpm build

      - name: Resolve symlinks for Azure deployment
        run: |
          # Nitro creates symlinks in .output/server/node_modules/.nitro/ for deduplication.
          # Azure's ZIP deployment does not preserve symlinks, so replace them with copies.
          find .output -type l | while read -r link; do
            target=$(readlink -f "$link")
            if [ -z "$target" ] || [ ! -e "$target" ]; then
              echo "WARNING: broken symlink skipped: $link"
              continue
            fi
            rm "$link"
            if [ -d "$target" ]; then
              cp -r "$target" "$link"
            else
              cp "$target" "$link"
            fi
          done
          # Verify no symlinks remain
          remaining=$(find .output -type l | wc -l)
          if [ "$remaining" -gt 0 ]; then
            echo "ERROR: $remaining symlinks still remain in .output/"
            find .output -type l
            exit 1
          fi
          echo "All symlinks resolved successfully"

      - uses: azure/webapps-deploy@v3
        with:
          app-name: analogy-make
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
          package: .output/
```

**シンボリックリンク実体化スクリプトの動作**:
1. `find .output -type l` — `.output/` 配下の全シンボリックリンクを列挙
2. `readlink -f "$link"` — シンボリックリンクの絶対パス（実体）を取得
3. ガード: `target` が空または実体が存在しない場合は WARNING を出力してスキップ
4. `rm "$link"` — シンボリックリンクを削除
5. `cp -r "$target" "$link"` — 実体をシンボリックリンクの元の位置にコピー
6. 事後検証: 残存シンボリックリンクがあればエラー終了（ワークフロー失敗として検知）

## nuxt.config.ts の変更について

変更不要。今回の問題はビルド設定ではなくデプロイパイプラインに起因する。Nitro の `externals` 設定は正しく機能しており、`.output/` のローカル実行では問題が再現しない。シンボリックリンクの実体化はデプロイ時のみ必要であり、ビルド設定で対応すると他のシンボリックリンク（`uuid` 等）への対処が漏れるリスクがある。

## 検証方法

### ローカル検証

1. `pnpm build` を実行
2. `find .output -type l` でシンボリックリンクが存在することを確認（スクリプトの前提条件）
3. 上記の `find` スクリプトを手動実行
4. `find .output -type l` の出力が空であることを確認（シンボリックリンクが全て実体に置換された）
5. `node .output/server/index.mjs` で起動確認（`hookable` エラーが出ないこと）

### Azure 検証

1. 修正を `main` にプッシュ
2. GitHub Actions のワークフローが成功することを確認
3. `https://analogy-make.azurewebsites.net/` にアクセスし、500 エラーが解消されていることを確認
4. `just logs` でランタイムエラーが出ていないことを確認

## ISSUE 対応

- `ISSUES/infra/high/Actionデプロイ.md` — 修正対象。検証成功後にクローズ
- `ISSUES/infra/medium/verify-output-dir-azure.md` — `.output/` の Azure 互換性問題の一因がシンボリックリンクであることが判明。本修正で対応。検証成功後にクローズ

## 変更サマリ

| ファイル | 変更内容 | 追加行数 |
|---|---|---|
| `.github/workflows/deploy.yml` | シンボリックリンク実体化ステップ追加 | 約10行 |

変更対象ファイル: 1つ。小規模な修正。

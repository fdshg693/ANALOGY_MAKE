---
name: experiment_test
description: research workflow の実装前検証 step。experiments/ 配下で再現・性能・CLI 試行を行い EXPERIMENT.md を生成
disable-model-invocation: true
user-invocable: true
---

## コンテキスト

- カテゴリ: !`cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app`
- 最新バージョン番号: !`bash .claude/scripts/get_latest_version.sh`
- 今日の日付: !`date +%Y-%m-%d`

## 役割

`research` workflow の 4 step 目。`RESEARCH.md` の未解決点（特に「実装方式を実験で絞り込む」「長時間検証」「隔離環境での試行」）を実際に `experiments/` 配下でスクリプトを書いて検証し、結果を `docs/{カテゴリ}/ver{X.Y}/EXPERIMENT.md` に残す。

### `experiments/` ディレクトリ運用ルール

- 既存依存で足りるなら既存 `package.json` / `.venv` をそのまま使う
- 新しい依存が必要な場合は `experiments/{slug}/` 配下に閉じる（プロジェクトルートの依存を増やさない）
- 残すスクリプトは先頭コメントに以下 2 点を必ず書く:
  - `// 何を確かめるためか: ...`
  - `// いつ削除してよいか: ...`

詳細は `experiments/README.md` を参照。

### やらないこと

- production コード（`app/` / `server/` / `scripts/`）への変更
- 長時間コマンドの本 step 内での同期実行（5 分超）は **ver16.1 の deferred execution 機構が未実装のため本版では許容するが**、該当仮説は `未検証` として `EXPERIMENT.md` の「判断」に明記する
- **nested `claude` / `claude -r` / `claude -p` の subprocess 起動**: 本 step は `research` workflow 内で `claude -p` として同期実行されているため、そこから更に `claude` を呼ぶと (a) 親 workflow の `--session-id` と衝突し、(b) `research` workflow の観測バイアス（deferred 機構の挙動確認を deferred 未完のまま実施してしまう）、(c) 1 往復数十秒 × 複数発話で同期 5 分境界に達する、の 3 重リスクがある。該当仮説は実走させず `EXPERIMENT.md` の「判断」で **`未検証`** 扱いとし、deferred execution 経路が本番発動する次バージョン以降に先送りする（`experiments/{slug}/README.md` に先送り理由と再開手順草稿を残す）

## 手順

### 1. 仮説整理

- `RESEARCH.md` の「未解決点」から検証仮説を 1〜N 個抽出
- 各仮説に「再現手順」と「成功条件」を割り当てる

### 2. 実験スクリプト作成・実行

- `experiments/` 配下に追加（既存ファイルを壊さない）
- 実行ログは `EXPERIMENT.md` に貼る（コマンドと出力の前後 10 行程度）
- 規約に従い先頭コメントに「何を確かめるためか」「いつ削除してよいか」を記載

### 3. `EXPERIMENT.md` 出力

出力先: `docs/{カテゴリ}/ver{X.Y}/EXPERIMENT.md`

必須 4 節（見出しは固定）:

```markdown
# ver{X.Y} EXPERIMENT — {短い主題}

## 検証した仮説

- 箇条書きで各仮説を記載
- 仮説ごとに「成功条件」を併記

## 再現手順

- 実行コマンド / 前提条件 / 必要な環境変数 / 使用ファイル
- `experiments/{slug}/README.md` があればリンク

## 結果

- 実行出力（抜粋で OK）/ 性能値 / エラー内容
- 検証対象のバージョン・日付を明記

## 判断

- 実装方式の確定 / 却下 / 未確定
- 未確定の場合は理由と次アクションを明記
```

## 長時間コマンドの扱い（ver16.1 以降の拡張ポイント）

本 step 内では **同期実行に限定**。5 分を超える長時間コマンドを本 step で扱う必要が出た場合、ver16.1 の deferred execution 機構に委譲することを前提とし、本版では該当仮説は `未検証` として `EXPERIMENT.md` の「判断」に明記する。

## Git コミット

- `git add docs/{cat}/ver{X.Y}/EXPERIMENT.md experiments/`
- コミットメッセージ: `docs(ver{X.Y}): experiment_test 完了`
- **プッシュはしない**（後続 step でまとめて push）

---
name: issue_scout
description: 能動的に潜在課題を探索し、ISSUES/{カテゴリ}/ に新規 ISSUE を起票する opt-in workflow（--workflow scout で起動）
disable-model-invocation: true
user-invocable: true
---

## コンテキスト

- カテゴリ: !`cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app`
- 最新バージョン番号: !`bash .claude/scripts/get_latest_version.sh`
- 今日の日付: !`date +%Y-%m-%d`
- 既存 ISSUE 分布: !`python scripts/issue_status.py $(cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app)`

## 役割

能動探索専用の SKILL。対象カテゴリのコード・tests・docs・`RETROSPECTIVE.md`・`MASTER_PLAN.md`・既存 `ISSUES/` を読み、
潜在課題を **1 run あたり最大 3 件** の新規 ISSUE として起票する。

**やらないこと**:

- コード修正・テスト実行・リファクタリング
- ドキュメント更新（`docs/` 配下・`CLAUDE.md`・`README.md` 等）
- `.claude/` 配下の編集
- `docs/{cat}/ver*/` バージョンディレクトリの作成
- 既存 ISSUE の書き換え・status 変更
- 起票ゼロで価値ある候補が見つからなければそのまま終了する（形骸的起票をしない）

## 探索手順

### 1. 既存資産の棚卸し

以下を Read して現状把握する:

- `ISSUES/{cat}/**/*.md`（`done/` 配下も必ず含める — 重複検出の母集団）
- 直近 3 バージョンの `docs/{cat}/ver*/RETROSPECTIVE.md`（存在する場合）
- `docs/{cat}/MASTER_PLAN.md` と `docs/{cat}/MASTER_PLAN/PHASE*.md` の実装進捗表
- 直近メジャーバージョンの `docs/{cat}/ver{X.0}/CURRENT.md`（分割されていれば各 `CURRENT_*.md`）

### 2. 潜在課題の抽出

対象スコープ（カテゴリ単位で閉じる）:

- `util` カテゴリ → `scripts/` / `.claude/` / `ISSUES/util/` / `docs/util/`
- `app` カテゴリ → `app/` / `server/` / `ISSUES/app/` / `docs/app/`
- `infra` カテゴリ → `infra/` / `Justfile` / `ISSUES/infra/` / `docs/infra/`
- `cicd` カテゴリ → `.github/workflows/` / `ISSUES/cicd/` / `docs/cicd/`

**価値観点（3 軸。件数より質）**:

1. **壊れ兆候** — 例外握りつぶし / 未使用分岐 / dead code / TODO コメント長期滞留
2. **ドキュメント × 実装の乖離** — rule と実コードの食い違い / README 記載と挙動の差
3. **`RETROSPECTIVE.md` の「次ループ観察」未 ISSUE 化** — 前バージョンが観察扱いしたまま放置された事項

### 3. 重複排除 / 除外チェック（起票前ゲート）

起票前に以下で重複判定する:

1. **タイトル正規化比較** — 先頭 `#` 以降を lower + 非英数字除去 + NFKC 正規化。既存 ISSUE（`done/` 含む）と完全一致 → スキップ
2. **本文冒頭類似度** — 本文の最初の 50 文字を空白区切りで単語集合化し、Jaccard ≥ 0.5 → 重複扱いでスキップ
3. 重複ヒット時は該当パスをサマリに記録し、**起票しない**

## 起票ルール

### 件数上限

- **1 run あたり最大 3 件**（下限 0）。価値ある候補がなければゼロ起票で終了する

### frontmatter 既定

```yaml
---
status: raw
assigned: ai
priority: high | medium | low
reviewed_at: "YYYY-MM-DD"
---
```

- `priority` は **必須扱い**。配置先ディレクトリ `ISSUES/{cat}/{priority}/` と frontmatter の `priority` を必ず一致させる
- `reviewed_at` は文字列クオート必須（`issue_status.py` の date 変換警告回避）。値は本日日付（`date +%Y-%m-%d`）

### `ready / ai` への昇格条件（すべて満たす場合のみ許可）

- 症状の再現条件がファイルパス + 具体操作で書ける
- 影響範囲が 3 ファイル / 100 行以内で見積もれる
- 修正方向が `IMPLEMENT.md` なしで 1 段落で書ける

上記 3 点を満たせない小粒は **原則 `raw / ai`** で起票する。

### ファイル命名

- `ISSUES/{cat}/{priority}/{kebab-case-summary}.md`
- 既存 ISSUE と同規約（lower-case / 単語は `-` 区切り）

### 本文テンプレート

```markdown
---
status: raw
assigned: ai
priority: medium
reviewed_at: "2026-04-24"
---

# {kebab-case-summary の人間可読表現}

## 症状

（何が起きているか / どこで確認できるか — ファイルパス + 行番号で具体的に）

## 影響

（放置した場合の悪影響 / 誰が・いつ困るか）

## なぜ今見る価値があるか

（なぜ他の ISSUE より優先して検討対象にする価値があるか）

## 想定修正方向（任意）

（わかる範囲で。`ready / ai` に昇格する場合は必須）
```

## サマリ報告（run 終了時）

stdout に以下を出力:

```
issue_scout summary:
  起票件数: N
  起票パス:
    - ISSUES/{cat}/{priority}/xxx.md
    - ...
  重複でスキップ: M 件
    - ISSUES/{cat}/{priority}/既存.md とタイトル一致: 候補X
    - ...
```

## Git コミット

新規 ISSUE 起票のみをコミットする:

```
git add ISSUES/{cat}/
git commit -m "issues({cat}): issue_scout による能動起票 (N件)"
```

**プッシュはしない**（scout は起票専用で、後続フローが push 責任を持つ）。

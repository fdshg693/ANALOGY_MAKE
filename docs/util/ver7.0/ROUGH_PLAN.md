# ver7.0 ROUGH_PLAN — issue_worklist.py 導入（PHASE6.0 第 1 弾）

## ISSUE レビュー結果

util カテゴリの `status: review / assigned: ai` ISSUE を走査した。該当なし（書き換え対象 0 件）。

| 対象 | 結果 |
|---|---|
| `ISSUES/util/high/*.md` | 0 件 |
| `ISSUES/util/medium/*.md` | `issue-review-rewrite-verification.md` 1 件（`ready / ai` のため対象外） |
| `ISSUES/util/low/*.md` | 0 件 |

書き換え件数: 0 件（`review / ai` は存在しない）。

## ISSUE 状態サマリ

| 組み合わせ | high | medium | low |
|---|---|---|---|
| ready / ai | 0 | 1 | 0 |
| review / ai | 0 | 0 | 0 |
| need_human_action / human | 0 | 0 | 0 |
| raw / human | 0 | 0 | 0 |
| raw / ai | 0 | 0 | 0 |

## バージョン種別

**メジャー (7.0)** — `docs/util/MASTER_PLAN.md` の **PHASE6.0（未実装）** に着手するため。

判定根拠:
- `docs/util/MASTER_PLAN.md` 末尾の PHASE6.0 が唯一の未実装項目
- ver6.0 / ver6.1 の両 RETROSPECTIVE が PHASE6.0 を次の自然な一歩として推奨
- util カテゴリ内の消化可能な `ready / ai` ISSUE は 0 件（medium の 1 件は app / infra ワークフロー起動時にのみ消化される性質）

## 対象範囲（本バージョンのスコープ）

PHASE6.0 は 5 節（§1 抽出スクリプト / §2 SKILL 分離 / §3 `--workflow auto` / §4 retrospective 利用 / §5 文書化）から成る大規模フェーズ。ver7.0 では **§1 と §4 のみ** を切り出す。

### ver7.0 で対応する範囲

1. **§1 `scripts/issue_worklist.py` の新規作成**
   - `ISSUES/{category}/{high,medium,low}/*.md` を走査し、frontmatter の `status` / `assigned` を読んで、`status in {ready, review}` かつ `assigned == <指定値>` の ISSUE だけを返す CLI スクリプト
   - 既定は `.claude/CURRENT_CATEGORY` のカテゴリ、`assigned: ai`、`status: ready,review`
   - 出力フォーマット: `text`（人間可読）と `json`（機械可読）
2. **§4 `/retrospective` SKILL での利用手順追記**
   - `.claude/skills/retrospective/SKILL.md` に `issue_worklist.py` を使った次バージョン推奨の手順を記述
3. **ドキュメント整備**
   - `scripts/README.md` に `issue_worklist.py` の説明を追記
4. **テスト整備**
   - `tests/` 配下に `issue_worklist.py` のユニットテストを追加（正常系・フォールバック・カテゴリ指定）

### ver7.0 で対応しない範囲（後続バージョンへ持ち越し）

- **§2 `/issue_plan` SKILL 新設と `/split_plan` 責務縮小** → ver7.1 想定
- **§3 `scripts/claude_loop.py` への `--workflow auto` 導入** → ver7.2 想定
- **§5 のうち `meta_judge/WORKFLOW.md` の全体図更新のみ** → §2 / §3 と一体で行うのが自然なので ver7.1 以降（`retrospective/SKILL.md` への手順追記は本バージョン §4 として対応済み扱い）
- **`/quick_plan` SKILL の整理** → §2 と一体で ver7.1

ver7.0 の成果物は「まだ誰も呼んでいない単体スクリプト + `/retrospective` からの利用」にとどまる。既存ワークフロー（`claude_loop.yaml` / `claude_loop_quick.yaml`）・既存 SKILL（`/split_plan` 等）には触れない。

## スコープをここで切る理由

- §1 の `issue_worklist.py` は §2 の `/issue_plan` と §4 の `/retrospective` の **共通データソース**。先に単体スクリプトを検証・固定化しておけば、後続 §2 / §3 が frontmatter パース・ディレクトリ走査・出力仕様を心配せずに利用できる
- §2（SKILL 分離）と §3（`--workflow auto`）は `ROUGH_PLAN.md` frontmatter の `workflow` フィールドを介して密に結合する。同一バージョンで片方だけ入れると中途半端になるため、両方を ver7.1 で一体化するのが合理的
- ver7.0 は外部挙動変更ゼロ（新規スクリプト追加 + `/retrospective` 手順追記のみ）。既存ワークフロー実行に影響を与えない安全な足場固めに徹する

## 機能面でのユーザー体験

- `python scripts/issue_worklist.py` で、今の AI 担当 `ready` / `review` ISSUE 一覧を即座に取得できる
- `--format json` で機械可読出力が得られる（後続バージョンで SKILL が消費）
- `/retrospective` 実行時に、次バージョンで取り組める ISSUE を明示的に把握したうえで推奨を行える
- 既存 `/split_plan` / `/quick_plan` / `claude_loop.py` の挙動は従来通り（破壊的変更なし）

## 成否判定基準

- `python scripts/issue_worklist.py` が現在のカテゴリで `ready/ai` + `review/ai` の ISSUE 一覧を返す
- `python scripts/issue_worklist.py --format json` が機械可読 JSON を出力し、フィールド（`path`, `title`, `priority`, `status`, `assigned`, `reviewed_at`）を含む
- `python scripts/issue_worklist.py --category <X> --assigned <Y> --status <Z>` の組み合わせが CLI で解決できる
- 既存 `python scripts/issue_status.py` の動作に影響しない
- 追加テストがすべて通る
- `/retrospective` SKILL の手順に `issue_worklist.py` 呼び出しステップが含まれる

## 小規模タスク判定

以下のとおり、**小規模タスクではない**（フルワークフロー継続）:

| 条件 | 実態 |
|---|---|
| 変更ファイルが 3 つ以下 | ❌ 4 ファイル以上（`issue_worklist.py` 新規 + テスト新規 + `scripts/README.md` + `retrospective/SKILL.md`） |
| 追加行 100 行以下 | ❌ 150〜250 行程度の見込み（CLI + JSON 出力 + テスト多数） |
| 新規ファイル作成不要 | ❌ `issue_worklist.py` と対応テストが新規 |

→ `REFACTOR.md` の作成は事前リファクタリングの必要性次第で判断（IMPLEMENT 作成時に確認）。
→ `IMPLEMENT.md` は通常タスクとして実装詳細に踏み込む。

## 事前リファクタリング

未確定。以下は IMPLEMENT 検討時に確認する:

- `scripts/issue_status.py` の `_extract_status_assigned` / `VALID_STATUS` / `VALID_ASSIGNED` などの定数・ヘルパを `issue_worklist.py` から再利用したい。共通化するなら `scripts/claude_loop_lib/` への切り出しが候補
- `scripts/claude_loop_lib/frontmatter.py` はすでに共通化済みのため、追加切り出しは不要

共通化が「コードコピー回避」に留まり複雑化を招かないと判断できる場合のみ `REFACTOR.md` を作成する。単純な重複回避で足りるなら ROUGH_PLAN 本項に「事前リファクタリング不要」と確定させる。

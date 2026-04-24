---
workflow: full
source: master_plan
---

# ver15.4 PLAN_HANDOFF — 後続 step 向け引き継ぎ

## ISSUE レビュー結果

本 `/issue_plan` 実行時点で `ISSUES/util/` 配下に `status: review` / `assigned: ai` の ISSUE は **0 件** だった。直前バージョン ver15.3 の RETROSPECTIVE で review-phase 対象が出尽くしている状態のため、今回はレビューフェーズでの frontmatter 書き換えは発生していない（遷移件数 0 / 対象パスなし）。

## ISSUE 状態サマリ

`python scripts/issue_status.py util` 実行結果（`/issue_plan` 実行時点）:

| priority | ready/ai | review/ai | need_human_action/human | raw/human | raw/ai |
|---|---|---|---|---|---|
| high | 0 | 0 | 0 | 0 | 0 |
| medium | 2 | 0 | 0 | 0 | 0 |
| low | 2 | 0 | 0 | 0 | 2 |

`ready/ai` 4 件の内訳:

| path | priority | 本バージョン内の扱い |
|---|---|---|
| `ISSUES/util/medium/issue-review-rewrite-verification.md` | medium | 継続持ち越し（util 単体消化不能、`app` / `infra` 起動待ち） |
| `ISSUES/util/medium/plan-handoff-generation-followup.md` | medium | 本 `/issue_plan` 実行自体が観察材料 — run 後に判定 |
| `ISSUES/util/low/plan-handoff-frontmatter-drift.md` | low | 並走観察（本バージョンの ROUGH_PLAN.md / PLAN_HANDOFF.md 2 ファイル frontmatter drift 有無） |
| `ISSUES/util/low/plan-handoff-omission-tracking.md` | low | 並走観察（full バージョンのため quick 省略判断は本版では発生しない） |

`raw/ai` 2 件（ver14.0 持越し）は本バージョンでは触らない（運用中問題顕在化を待つ）。

## 選定理由・除外理由

### 選定: PHASE7.1 §4（run 単位通知）

根拠（優先度順）:

1. **PHASE7.1 唯一の未完走節**: §1 / §2 / §3 は ver15.0〜ver15.3 で実装済み、§4 のみ残。消化すれば PHASE7.1 全体が完走し、次に PHASE8.0 骨子検討へ進める道が開く。残す合理的な理由がない
2. **マイナー適合**: 通知実装（`scripts/claude_loop_lib/notify.py` 変更）と `claude_loop.py` の終了経路整理に領域が独立。新 PHASE 骨子作成・アーキテクチャ変更・新規外部ライブラリ導入のいずれにも該当しない
3. **ver15.3 FEEDBACK handoff の明示推奨**: `FEEDBACKS/handoff_ver15.3_to_next.md` の「着手推奨」として §4 が指定されている
4. **multi-loop 運用時の実害**: 現行の loop ごと通知は `--max-loops 2` 以上で完了把握がしづらい実害が PHASE7.1 §4 動機に明記されている

### 除外（その 1）: `ready/ai` の 4 件の ISSUE 消化を主軸にする

却下理由:

- `issue-review-rewrite-verification.md` は util 単体では消化不能（ver6.0 から繰り返し判定済み）
- 残 3 件（generation / drift / omission）は全て「次バージョンの実運用を観察して判定する」タイプの follow-up。本バージョンの `/issue_plan` 実行自体が観察材料となるため、専用バージョンを割くのは非効率
- ver15.3 RETROSPECTIVE §3 の代替案評価で既に却下済み

### 除外（その 2）: ver16.0（メジャー）で PHASE7.1 §4 + PHASE8.0 骨子を一括

却下理由:

- PHASE7.1 §4 は通知実装で独立しており、PHASE8.0 骨子作成と同時着手は scope 過大
- ver15.3 RETROSPECTIVE §3 で「PHASE8.0 骨子作成は §4 完了後に再判定」と明示されており、本バージョンで先取りする動機がない

### 除外（その 3）: loop 単位通知を残しつつ run 単位通知をオプトインで追加

却下理由:

- PHASE7.1 §4 の期待挙動が「loop ごとではなく、Python スクリプト全体が終了した時点で 1 回だけ出す」と断定形。設計意図は run 単位が default で loop 単位は廃止
- 二系統併存は `--no-notify` / `--dry-run` との優先順位判断を複雑化させ、tests も二重化する

## 関連 ISSUE / 関連ファイル / 前提条件

### 関連 ISSUE

- `ISSUES/util/medium/plan-handoff-generation-followup.md` — 本 `/issue_plan` 実行結果（`PLAN_HANDOFF.md` が実際に生成されたか）が判定材料。run 完了後、本ファイルの存在を確認した時点で `done/` 移動可否を判断する
- `ISSUES/util/low/plan-handoff-frontmatter-drift.md` — `ROUGH_PLAN.md` と本ファイルの frontmatter（`workflow: full` / `source: master_plan`）が一致しているかの観察対象
- `ISSUES/util/low/plan-handoff-omission-tracking.md` — 本バージョンは full のため省略判断の発火機会なし。次に quick を採用するバージョンまで観察継続

### 関連ファイル

- `scripts/claude_loop_lib/notify.py` — 通知 API 本体。`notify_completion(title, message)` を run サマリ対応に拡張予定
- `scripts/claude_loop.py` — 通知呼び出し位置。現行は loop ループ内で発火していると想定、終了経路（正常 / 例外 / SIGINT / timeout）を 1 箇所に収束させる改修対象
- `scripts/claude_loop_lib/logging_utils.py` — 所要時間フォーマットに `format_duration` が既にあるため、run サマリ生成で再利用可能
- `scripts/claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` / `claude_loop_scout.yaml` / `claude_loop_question.yaml` — 5 YAML 間で `command` / `defaults` セクションを同一に保つ規約（`.claude/rules/scripts.md` §3）あり、通知関連オプション追加時は全ファイル同期が必要
- `scripts/README.md` / `scripts/USAGE.md` — 通知仕様の一次資料。rule 側は scripts.md が要点のみ記述し、詳細は docs が優先
- `.claude/rules/scripts.md` — Python 3.10+ / PEP 604 型 / `pathlib.Path` / `argparse` / `print()` 禁止（`logging_utils` 使用）等の stable 規約

### 前提条件

- Python 3.10+ / 標準ライブラリ + PyYAML のみ（3rd-party 依存追加禁止）
- 通知バックエンドは Windows PowerShell toast（`notify.py` 現行実装）を基盤に拡張。完全な常駐表示が OS トースト仕様で難しい場合は、ログ出力 + beep の fallback を自動消滅しにくい形に強化する方向で許容
- `--no-notify` / `--dry-run` の既存セマンティクスは破壊しない

## 後続 step への注意点

### `/split_plan` 向け

- **中断経路の網羅性**: 正常終了 / 例外（非ゼロ終了コード） / SIGINT / timeout の 4 経路で通知発火点が 1 箇所に収束することを IMPLEMENT.md §タイムラインで明示し、リスク項目にも「経路漏れ」を 1 行入れる
- **Windows トースト永続化の調査項目**: `ToastTemplateType::ToastText02` の現行テンプレートが「人が閉じるまで残る」挙動を取れるか、取れない場合どの Template / Scenario（例: `reminder`）が必要かを IMPLEMENT.md の先頭タスクに置く。OS 依存の不確実性は PoC で先に潰す
- **fallback 方針の扱い**: ver15.3 の `notify.py` は toast 失敗時に beep + console print にフォールバック。run 単位化に伴い fallback 経路も run サマリを受け取る形に揃える必要があるため、分岐設計を IMPLEMENT.md に明記
- **plan_review_agent の活用**: full workflow なので review あり。OS トースト仕様の不確実性と中断経路網羅性は review の主要観点として扱ってもらう
- **5 YAML 同期**: 新規 CLI フラグを追加する場合は `claude_loop*.yaml` の 5 ファイルすべてに反映する規約（`.claude/rules/scripts.md` §3）を IMPLEMENT.md タイムラインに組み込む
- **tests の配置**: `scripts/tests/` に run サマリ生成・`--no-notify` 優先順位・中断経路のユニットテストを追加する前提。外部プロセス（PowerShell toast）呼び出しは mock で切る方針が妥当

### 共通

- **frontmatter drift 回避**: 本 `PLAN_HANDOFF.md` と `ROUGH_PLAN.md` の frontmatter（`workflow: full` / `source: master_plan`）は同値で重複保持している。後続 step で片側のみ更新しないこと（`plan-handoff-frontmatter-drift.md` ISSUE の観察対象）
- **仕分け方針の遵守**: 本 `ROUGH_PLAN.md` からは「ISSUE 状態サマリ」「選定理由・除外理由」を意図的に除去済み。`MEMO.md` / `IMPLEMENT.md` に逆流させないこと（ver15.3 自身の ROUGH_PLAN.md では重複が残った移行期の揺らぎがあった）
- **MASTER_PLAN 進捗表の更新**: 本節（§4）完了時は `docs/util/MASTER_PLAN/PHASE7.1.md` 進捗表を「実装済み（ver15.4）」に更新する（`/wrap_up` 相当のタイミング）

### `/retrospective` 向け（先行メモ）

- 本バージョンの `/issue_plan` 実行で `PLAN_HANDOFF.md` が生成されたか・frontmatter が drift していないかを記録し、`plan-handoff-generation-followup.md` / `plan-handoff-frontmatter-drift.md` の done 判定材料を残すこと
- PHASE7.1 完走判定後、次バージョンで PHASE8.0 骨子作成に着手するか、util 外カテゴリ（`app` / `infra` / `cicd`）の ISSUE 消化に移るかを §3 で整理する

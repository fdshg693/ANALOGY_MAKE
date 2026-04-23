# ver15.0 MEMO — `issue_scout` workflow 新設の実装メモ

## 実装サマリ

`IMPLEMENT.md` の計画通りに 12 件の成果物すべてを add-only で積んだ。`auto` / `full` / `quick` の挙動・自動選択ロジックには触っていない。

- `scripts/claude_loop_lib/workflow.py`: `SCOUT_YAML_FILENAME` 定数追加 / `RESERVED_WORKFLOW_VALUES` に `"scout"` 追加 / `resolve_workflow_value()` に分岐追加
- `scripts/claude_loop_scout.yaml`: 新規（1 ステップ `/issue_scout`、`command` / `defaults` は既存 3 YAML と完全一致）
- `scripts/claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml`: NOTE コメントの sync 対象リストに `claude_loop_scout.yaml` を追加（4-way sync）
- `.claude/skills/issue_scout/SKILL.md`: 新規（`claude_sync.py export → 編集 → import` 経由で配置）
- `scripts/tests/test_workflow.py`: `SCOUT_YAML_FILENAME` import / `test_resolve_scout_returns_scout_yaml_path` / `test_scout_yaml_uses_only_allowed_keys` を追加
- `scripts/tests/test_validation.py`: `TestValidateStartupExistingYamls.test_scout_yaml_passes` を追加
- `scripts/README.md`: 「scout（能動探索）」節を「フル/quick の使い分け」の直後に新規追加
- `scripts/USAGE.md`: 「YAML ワークフロー仕様」節末尾に scout YAML サンプルを追加（3 ファイル同期を 4 ファイル同期に更新）
- `ISSUES/README.md`: 「AI が起票するパス」節に `issue_scout` 起票時の既定値を追記
- `docs/util/MASTER_PLAN.md` / `docs/util/MASTER_PLAN/PHASE7.1.md`: §1 を「実装済み（ver15.0）」に更新

## 計画との乖離

なし。`IMPLEMENT.md` の設計判断（`--workflow scout` 一本、`--scout` フラグを追加しない、重複検出を SKILL 内ヒューリスティックに閉じる、カテゴリ単位スコープ）をそのまま踏襲。

SKILL 配置パスの表記だけ実態に合わせて調整した: IMPLEMENT.md / ROUGH_PLAN.md では `.claude/SKILLS/issue_scout/` と大文字で記載されているが、validation.py の skill 存在チェックが `.claude / "skills"`（小文字）を参照しているため、実ファイルは `.claude/skills/issue_scout/SKILL.md` に配置した。Windows 上は case-insensitive で問題なし。Linux 互換は本バージョン対象外（既存 SKILL 群と同じ配置パターン）。

## リスク検証結果

### R1 — `raw / ai` のノイズ化

**検証先送り**。初回 smoke test（`/wrap_up` SKILL 手順内で実施予定）の起票件数・内容を目視するまで評価不能。`ISSUES/util/medium/issue-scout-noise-risk.md` に独立 ISSUE として追加済み。`issue_plan` レビュー負荷が顕著に増えた場合は次バージョンで件数上限引き下げ・価値観点の再定義を検討する。

### R2 — 重複検出ヒューリスティックの閾値不明

**検証先送り**。Jaccard 0.5 / タイトル正規化一致の閾値が過検出/取りこぼしどちらに偏るかは、初回 run で既存 ISSUE（`done/` 含む）との照合を目視して確定する。`ISSUES/util/medium/issue-scout-noise-risk.md` にまとめて記載（R1 と同じ観察軸のため独立化せず同居）。

### R3 — `claude_sync.py` import 時の新規 SKILL 追加動作

**検証済み**。`python scripts/claude_sync.py export` → `.claude_sync/skills/issue_scout/SKILL.md` を新規作成 → `python scripts/claude_sync.py import` を実行した後、`ls .claude/skills/issue_scout/SKILL.md` で物理配置を確認（成功）。`python scripts/claude_loop.py --workflow scout --dry-run` も完走し、validation の skill 存在チェック（validation.py:272-281）を通過することを確認した。

### R4 — scout YAML と既存 3 YAML の `command` / `defaults` ドリフト

**検証済み**。`command:` / `defaults:` セクションは既存 3 YAML からコピーし完全一致。`test_scout_yaml_uses_only_allowed_keys` と `test_scout_yaml_passes` が load_workflow / validate_startup の経路で構造検証済み。4 YAML 間のドリフトは今後 rule §3（scripts.md）の「4 ファイル同一内容維持」運用で防止する。

### R5 — `RESERVED_WORKFLOW_VALUES` の他箇所参照

**検証済み**。`Grep "RESERVED_WORKFLOW_VALUES|claude_loop_scout|\"scout\""` を実装前に実行し、コード参照は `scripts/claude_loop_lib/workflow.py:16` の定義のみであることを確認（他はすべて docs 側のテキスト）。追加後に自動選択ロジックへ混入する経路なし（`_resolve_target_yamls` の auto 分岐は `FULL` / `QUICK` / `ISSUE_PLAN` の 3 つに限定、IMPLEMENT.md 設計通り）。

### R6 — SKILL.md シェル補間のフォールバック

**検証済み（設計レベル）**。SKILL.md では `$(cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app)` でカテゴリを取得し、その値を引数にして `python scripts/issue_status.py <cat>` を呼ぶ形にした。既存 `issue_review/SKILL.md` / `issue_plan/SKILL.md` と同じフォールバックパターンなので実運用でも `CURRENT_CATEGORY` 未設定時は `app` で動作する。SKILL コンテキスト生成エラーは想定外。

### R7 — `issue_worklist.py` への raw/ai 流入

**検証済み**。`scripts/issue_worklist.py` を Read し、`argparse` のデフォルト `--status ready,review`（line 153）で `raw` が除外されることを確認。scout 起票物（`raw / ai`）は `/issue_plan` の JSON 入力（`issue_worklist.py --format json --limit 20`）に混入しないため、`/issue_plan` コンテキストは肥大化しない。

### R8 — 単一ステップ scout YAML のログ体裁差

**検証済み**。`python scripts/claude_loop.py --workflow scout --dry-run` の出力は既存 `claude_loop_issue_plan.yaml`（同じく 1 ステップ）と同じ形式で、`[1/1] issue_scout` / `Model: opus, Effort: high, Session: ...` / `Workflow completed.` が出ている。`continue: true` を入れていないが単一ステップなので session 引き継ぎ不要。通知・サマリの体裁崩れなし。

## 動作確認結果

- `python -m unittest scripts.tests.test_workflow scripts.tests.test_validation scripts.tests.test_claude_loop_integration` → **105 tests OK**
- `python scripts/claude_loop.py --workflow scout --dry-run` → validation + resolve 完走、exit 0
- `npx nuxi typecheck` → 既知の vue-router volar モジュール解決エラー（CLAUDE.md 記載済、本変更と無関係）。Python-only の実装のため typecheck への影響なし

## ドキュメント更新の提案（`/write_current` 対象）

- `docs/util/ver15.0/CURRENT.md`（メジャー版なので新規作成）で以下を CURRENT_scripts / CURRENT_skills にそれぞれ追記する:
  - `SCOUT_YAML_FILENAME` / `claude_loop_scout.yaml` / `.claude/skills/issue_scout/SKILL.md` の追加
  - 「ワークフロー体系」節に scout workflow の説明を追加
  - 「4 ファイル同期義務」への更新（3 → 4）
- `CLAUDE.md` は「やらないこと」「技術スタック」両方の観点で `issue_scout` は util カテゴリ内部の運用詳細なので更新不要と判断。

## 先送りリスクの ISSUE 化

- `ISSUES/util/medium/issue-scout-noise-risk.md` — R1 / R2 の検証先送り分（初回 smoke test 後の観察項目）

## 次バージョンへの引き継ぎ候補

- ver15.1 `/issue_plan` 着手時:
  - 初回 scout run（`/wrap_up` smoke test か手動起動）の起票件数・品質を観察
  - 必要なら件数上限の調整・価値観点の再定義
  - PHASE7.1 §2（`QUESTIONS/` / `question` workflow）着手

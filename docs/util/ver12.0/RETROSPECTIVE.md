# ver12.0 RETROSPECTIVE — PHASE7.0 §2 起動前 validation

## 1. ドキュメント構成整理

### 1-1. `docs/util/MASTER_PLAN.md`

- 1 行サマリ形式維持。PHASE7.0 行を「§1・§2 完了・§3〜§8 未着手」に更新済（wrap_up 対応）。肥大化なし
- **再構成提案: なし**

### 1-2. `MASTER_PLAN/PHASE7.0.md`

- §1 / §2 完了、§3〜§8 未着手。現行 PHASE は未完走で、残り 6 節分の余地がある
- **新 PHASE（PHASE8.0）骨子は不要**。PHASE7.0 残節が明確

### 1-3. `CLAUDE.md` の肥大化チェック

- ルート `CLAUDE.md` 60 行台、`.claude/CLAUDE.md` は ROLE.md 参照のみで健全
- ver12.0 で追加された「起動前 validation」挙動は `scripts/USAGE.md` と `CURRENT.md` に記載済。CLAUDE.md への反映は不要
- **分割提案: なし**

### 1-4. ISSUES ディレクトリ健全性

- util カテゴリ 4 件（medium 3 / low 1）で件数閾値未到達
- **構成変更提案: なし**

## 2. バージョン作成の流れの検討

### 2-1. 各ステップの効果

| ステップ | 評価 | コメント |
|---|---|---|
| `/issue_plan` | ◎ | `workflow: full` / `source: master_plan` を frontmatter に記録。ready/ai 1 件（util 単体消化不能）を除外し、PHASE7.0 §2 を単独スコープにする判断を ROUGH_PLAN に明文化 |
| `/split_plan` | ◎ | IMPLEMENT.md で 5 検証カテゴリ → 5 関数に責務割り当て、`Violation` データ構造・エラー集約戦略（YAML parse 失敗時のスキップ単位）・`--workflow auto` 接続方針を確定。plan_review_agent で review 実施 |
| `/imple_plan` | ◎ | `validation.py`（約 260 行）新規追加、test_validation 37 ケース追加。計画乖離 3 件（テスト数、既存 integration テストへの patch 追加、`_validate_executable_and_cwd` の 2 関数分割）は MEMO §「計画からの乖離」に記載済。IMPLEMENT.md §6 のリスク 7 件全て検証結果を MEMO §「リスク・不確実性の検証結果」に対応付け |
| `/wrap_up` | ◎ | MASTER_PLAN PHASE7.0 §1/§2 状態更新、MASTER_PLAN.md PHASE7.0 行更新、`scripts/USAGE.md` に起動前 validation 段落追記。plan_review_agent の「軽微・再レビュー不要」承認に基づく対応 |
| `/write_current` | ◎ | 4 分割構成維持。`CURRENT_scripts.md` に `validation.py` モジュール追加、`CURRENT_tests.md` に test_validation.py 追加、`CURRENT.md` に起動前 validation 節追加 |
| `/retrospective` | — | 本ステップ |

### 2-2. 流れに対する改善提案

ver12.0 は計画通りの full ワークフローで、大きな構造的問題は観察されなかった。検討した観点（いずれも改修不要）:

- **a. IMPLEMENT.md のリスク列挙 → MEMO 検証マトリクス運用**: IMPLEMENT.md §6 で 7 件のリスクを列挙し、MEMO で 1 件ずつ「検証済」「検証不要（設計判断として確定）」を justification 付きで記録するパターンは ver8.0 から安定継続。SKILL 側の改修不要
- **b. 既存 integration テストへの影響の事前予測失敗**: IMPLEMENT.md §2-4 は「既存テストは修正不要」としたが、`test_claude_loop_integration.py::TestRunMainAuto` が tmp_dir を cwd とするため validation で落ちる問題が実装時に判明し、`validate_startup` を patch で no-op 化する 1 行追加で回避。MEMO §2 で乖離として記録済で事後追跡可能。SKILL で「既存テストの cwd 依存を split_plan で grep せよ」と強制するほどの頻度ではないため、改修不要
- **c. Windows パス表記の OS 依存**: エラーメッセージで `relative_to(cwd)` が OS 依存の出力差を生む可能性をリスク §6-7 で事前抽出し、POSIX リテラル文字列に変更して軽微化。事前リスク列挙の実効性が示された

### 2-3. 即時適用したスキル変更

**なし**。ver12.0 は事前計画通りに進行し、SKILL 改修を要する問題は観察されなかった。

## 3. 次バージョンの種別推奨

### 3-1. 判定材料 3 点の突合

1. **ISSUE 状況**（`issue_worklist.py` 結果 ready/ai 1 件）:
   - `ISSUES/util/medium/issue-review-rewrite-verification.md` — util 単体消化不能（ver6.0 からの持ち越し継続）
   - 加えて raw/ai 3 件: `cli-flag-compatibility-system-prompt.md` / `test-issue-worklist-limit-omitted-returns-all.md` / `system-prompt-replacement-behavior-risk.md`
2. **MASTER_PLAN の次項目**: PHASE7.0 §3「legacy `--auto` 撤去」、§4「FEEDBACKS 1 ループ限定運用」、§5「REQUESTS→ISSUES 統合」、§6「retrospective handoff FEEDBACK」、§7「`.claude/rules` 整備」、§8「workflow prompt/model 評価」が未着手
3. **現行 PHASE 完走状態**: PHASE7.0 §1/§2 完了、§3〜§8 未着手。PHASE 未完走で、新 PHASE 骨子不要

### 3-2. 推奨

**推奨: ver12.1（マイナー、quick）で `test-issue-worklist-limit-omitted-returns-all.md` 消化 → ver13.0（メジャー、full）で PHASE7.0 §3 + §4 + §5 （legacy 撤去 + FEEDBACKS 1 ループ限定 + REQUESTS 廃止）に着手**

推奨根拠:

- **ver12.1（quick, マイナー）**: `test_limit_omitted_returns_all` は ver10.0 / ver11.0 RETROSPECTIVE で連続して持ち越された pre-existing テスト失敗で、`issue_worklist.py` の `limit` パラメータ省略時挙動を決める単体修正。変更範囲は `scripts/claude_loop_lib/issues.py` + `scripts/tests/test_issue_worklist.py` の 2 ファイル程度で quick 適合（3 ファイル以下 / 100 行以下）。3 バージョン連続持ち越しは baseline 健全性の観点でそろそろ解消したい。ver12.0 で新規追加した `validate_startup()` の正常系 regression guard（`TestValidateStartupExistingYamls`）が効いている間に、周辺テストの baseline を揃えておくほうが後続バージョンでの混乱を避けられる
- **ver13.0（full, メジャー）**: PHASE7.0 §3（legacy `--auto` 撤去）は CLI 仕様変更 + YAML `mode` 系設定削除 + docs/tests の一斉更新を伴うアーキテクチャ変更で、メジャー昇格が妥当。§4（FEEDBACKS 1 ループ限定）・§5（REQUESTS→ISSUES 統合）は運用ルール変更で粒度は小さいが、CLAUDE.md / README / SKILL 群の参照先一括更新が必要なため、§3 と同バージョンで扱って「CLI / YAML / 運用ルールの整理」を一括でやり切るほうがレビュー負荷のトータルは小さい。§6〜§8 は「retrospective 強化」と「rules 整備」で主題が異なるため ver13.1 / ver14.0 で段階的に切り分ける
- **raw/ai ISSUES の扱い**:
  - `cli-flag-compatibility-system-prompt.md` → ver12.0 の validation 実装で「override キー → CLI flag 存在チェック」は現状未実装（MEMO §「計画からの乖離」に特段の言及なし）。§3 の `--auto` 撤去と合わせて CLI 整理時に同時処理する候補
  - `system-prompt-replacement-behavior-risk.md` → §3 以降の運用整理で再評価
- **`issue-review-rewrite-verification.md`** → util 単体消化不能のまま持ち越し継続

**代替案 A（採用しない）**: ver12.1 で PHASE7.0 §3 直接着手。欠点は `test_limit_omitted` を更に 1 バージョン先送りにする点。§3 は CLI 仕様変更でメジャー昇格相当のためマイナーには不適合

**代替案 B（採用しない）**: ver12.1 skip して ver13.0 で §3 + §4 + §5 + `test_limit_omitted` を一括。欠点は §3 の CLI 整理コミットと `test_limit_omitted` の単体修正コミットが混在してレビュー面で追いにくい

→ **最終推奨: ver12.1（quick）で test_limit_omitted 消化 → ver13.0（full）で PHASE7.0 §3+§4+§5 一括着手**

## 4. 振り返り結果の記録

### 4-1. ISSUES ファイルの整理

- **削除**: なし（ver12.0 は MASTER_PLAN 新項目着手バージョンで ISSUE 消化を伴わない）
- **持ち越し**（削除しない、理由記載済）:
  - `ISSUES/util/medium/issue-review-rewrite-verification.md` — util 単体消化不能、持ち越し継続
  - `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md` — ver13.0 PHASE7.0 §3 と合わせて処理候補
  - `ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md` — ver12.1 quick で消化予定（§3-2）
  - `ISSUES/util/low/system-prompt-replacement-behavior-risk.md` — ver13.0 以降で再評価
- **frontmatter 無しファイル**: なし

### 4-2. `REQUESTS/AI/` の整理

- `REQUESTS/AI/` 配下に実ファイルなし（ディレクトリ空）。**変更なし**

### 4-3. 即時適用したスキル変更

**なし**（§2-3 のとおり）。

### 4-4. 次バージョン ver12.1 への引き継ぎ

`test-issue-worklist-limit-omitted-returns-all.md` 消化時の注意点:

1. **スコープ**: ISSUE 本文に従い、`limit` パラメータ省略時の挙動を「全件返す」ことを確定する仕様として固める。関数シグネチャ・テスト期待値の片側に合わせる単体作業
2. **変更対象想定**: `scripts/claude_loop_lib/issues.py`（`issue_worklist` 関数の `limit` 既定値ハンドリング）+ `scripts/tests/test_issue_worklist.py`（`test_limit_omitted_returns_all` の期待値）
3. **quick 適合性**: 2 ファイル / 数十行以内で完結する見込み
4. **ver12.0 validation との相互作用**: `validate_startup()` 自体は `issue_worklist` を呼ばないため、validation regression 懸念なし。既存 `TestValidateStartupExistingYamls` は引き続き通過することを確認

### 4-5. ver13.0（PHASE7.0 §3+§4+§5）への事前メモ

ver12.1 完了後に `/issue_plan` が ROUGH_PLAN を作る際の前提として:

- **§3 legacy `--auto` 撤去**: 現状 `scripts/claude_loop.py` 101 行目で `--auto` フラグを受理し `resolve_mode(config, args.auto)` で `auto_mode` を導出している。撤去時は CLI 引数削除 + YAML `mode` 関連フィールド削除 + `commands.py` の `auto_args` 解決削除 + docs（`scripts/README.md` / `scripts/USAGE.md` / CLAUDE.md）一括更新が必要。`--auto` 指定時のエラー文言（移行案内）を §3-1 方針に従い設計
- **§4 FEEDBACKS 1 ループ限定**: 現行 `feedbacks.py` が `FEEDBACKS/` 直下を読み、正常完了時に `FEEDBACKS/done/` へ移動する実装は既に存在。§4 で必要な変更は「`FEEDBACKS/done/` 自動再読込の抑止」「異常終了時の移動有無の仕様確定」の 2 点のみの可能性あり。ROUGH_PLAN で現行実装の挙動を先に精査する
- **§5 REQUESTS→ISSUES 統合**: `REQUESTS/AI/` / `REQUESTS/HUMAN/` は現状空。主作業は docs / SKILL / CLAUDE.md の「REQUESTS に書く」記述を ISSUES 参照に置換 + ディレクトリ削除の可否判断

### 4-6. 今バージョンからの学び（手法面）

- **IMPLEMENT.md §6 リスク列挙 → MEMO 検証マトリクス運用の実効性**: ver12.0 は 7 件のリスクを事前抽出し、MEMO で各々「検証済」「検証不要（設計判断）」を justification 付きで記録。Windows パス表記の OS 依存（§6-7）が実装時に設計変更を誘発するなど、事前抽出が実際の実装判断に効いた。この運用は PHASE7.0 §3 以降の CLI 仕様変更バージョン（破壊的変更を伴うため事前リスク列挙が特に効く）でも継続すべき
- **pre-existing テスト失敗の 3 バージョン連続持ち越し**: `test_limit_omitted_returns_all` は ver10.0 / ver11.0 / ver12.0 と 3 バージョン連続で先送りされた。毎回「baseline 健全性に影響なし」「高優先度 ISSUE が優先」と判定されたが、3 バージョンは許容上限と見なすべき。ver12.1 で確実に消化する方針で固定化
- **MASTER_PLAN 新項目着手バージョンでの ISSUE 消化ゼロ**: ver12.0 はスコープを PHASE7.0 §2 単独に絞り、raw/ai ISSUE を混ぜなかった結果、IMPLEMENT.md 設計の焦点が保たれ plan_review_agent の承認も軽微対応のみで済んだ。「MASTER_PLAN 新項目 × 関連 ISSUE 同時消化」を避け、ISSUE は後続 quick バージョンで拾う運用パターンが ver10.0（§1 単独） / ver12.0（§2 単独）で 2 回成功しており、PHASE7.0 §3 以降でも踏襲推奨

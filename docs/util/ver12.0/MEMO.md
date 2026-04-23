# ver12.0 MEMO — PHASE7.0 §2 起動前 validation

## 実装サマリ

`scripts/claude_loop_lib/validation.py` を新規追加し、`claude_loop.py` の `main()` に `validate_startup()` 呼び出しを挿入した。検査項目・重大度・エラー集約戦略は IMPLEMENT.md §1-1〜§1-7 のとおり実装。

### 変更ファイル

- `scripts/claude_loop_lib/validation.py`（新規, 約 260 行）
- `scripts/claude_loop.py`（import 追加 + `main()` に 1 行挿入）
- `scripts/tests/test_validation.py`（新規, 37 ケース）
- `scripts/tests/test_claude_loop_integration.py`（`validate_startup` のパッチ追加 + `TestStartupValidationIntegration` 1 ケース追加）
- `scripts/README.md`（「起動前 validation」節および `validation.py` モジュール行追記）

## 計画からの乖離

### 1. テストケース数（IMPLEMENT.md §2-4 想定: 約 35 → 実績: 37）

クラス構成はほぼ計画どおり。`TestValidateDefaultsSection` を独立クラスとして切り出した分 2 ケース増。その他は計画どおり。

### 2. 既存 integration テストへの影響

IMPLEMENT.md §2-4 では既存テストは「修正不要」としていたが、`test_claude_loop_integration.py::TestRunMainAuto` は tmp_dir を cwd として使用しており、当該 tmp_dir に `.claude/skills/` が存在しないため validation が error を出して先に進まなくなる。`validate_startup` を patch で no-op 化する 1 行を `_run_main_auto` に追加して既存挙動を維持した（乖離理由: 既存テストは validation の振る舞いを検証する意図ではなく phase1/phase2 分岐を検証する意図のため）。

### 3. validation.py の内部構成

IMPLEMENT.md §2-1-1 のモジュール概形では `_validate_executable_and_cwd()` を 1 つにまとめていたが、executable 検査は YAML ごとに異なる可能性があるため実装では `_validate_cwd()` と `_validate_command_section()`（YAML ごと）に分離した。責務境界が明確になる。

## リスク・不確実性の検証結果

IMPLEMENT.md §6 の各項目について:

### §6-1 `shutil.which` の OS 依存性 — **検証済み**

- 開発環境（Windows MinGW 上の Git Bash）で `which claude` は `/c/Users/xingw/.local/bin/claude` に解決。validation を通過することを `python scripts/claude_loop.py --workflow auto --dry-run --no-log --no-notify` で確認
- `test_validation.py` の大半のケースで `shutil.which` を `unittest.mock.patch` で mock しており、CI など claude CLI 未インストール環境でも通る
- 例外: `TestValidateStartupExistingYamls` は real `shutil.which` を呼ぶ。`claude` が PATH になければ失敗するが、これは `claude_loop.py` 自体を実行できる環境前提のため実害なし

### §6-2 SKILL 解決の `/prompt args` パース — **検証済み**

`TestValidateStepReferences::test_prompt_with_args_resolves_by_first_token` で `"/foo extra arg"` の形式から `foo` を抽出してルックアップできることを確認。

### §6-3 warning / error の境界線 — **検証不要（設計判断として確定）**

IMPLEMENT.md §6-3 で確定したとおり:
- model / effort 未知値: **warning**（CLI 側で新 alias が追加される可能性を残す）
- 未解決 SKILL: **error**（「validation 通過 = 最後まで到達可能」契約を満たすため）
- 型不正・unknown key・YAML parse 失敗: **error**

`TestValidateOverrideWhitelist` / `TestValidateStartupAggregation::test_warnings_only_does_not_raise` で挙動を検証済み。

### §6-4 既存 3 YAML の regression guard — **検証済み**

`TestValidateStartupExistingYamls` (4 ケース) がリポジトリの 3 本の YAML を実ファイルで load し、いずれも violation ゼロで通過することを確認。将来 YAML 編集で schema 違反が発生した場合、このテストが失敗することで検出される。

### §6-5 `OVERRIDE_STRING_KEYS` 等の再 import 依存 — **検証不要**

`validation.py` は `workflow.py` から定数を import するだけで、循環依存は存在しない（`workflow.py` は `validation.py` を import しない）。`scripts/README.md` の「拡張ガイド」節に定数変更時の追随性を明記済み。

### §6-6 エラーメッセージ I18N — **検証不要**

実装で全エラー文言を英語に統一済み。

### §6-7 Windows パス表記 — **検証済み（影響軽微と判断）**

エラーメッセージでは `.claude/skills/<name>/SKILL.md` のようにリテラルの POSIX 相対パス表記で出力するよう実装変更（当初計画の `skill_md.relative_to(cwd)` は OS 依存が残るため）。開発者が読めば意図は伝わる。

## 動作確認サマリ

| 確認項目 | 結果 |
|---|---|
| `python -m unittest scripts.tests.test_validation -v` | 37/37 PASS |
| `python -m unittest discover -s scripts/tests -t .` | 229/230 PASS（唯一の失敗は pre-existing: `test_issue_worklist.test_limit_omitted_returns_all` — ROUGH_PLAN.md §除外事項で明示されている別 ISSUE 扱い） |
| `python scripts/claude_loop.py --workflow auto --dry-run --no-log --no-notify` | validation 通過、phase1 dry-run 完了 |
| `python scripts/claude_loop.py --workflow full --dry-run --no-log --no-notify` | validation 通過、全 step dry-run 完了 |
| `python scripts/claude_loop.py --workflow quick --dry-run --no-log --no-notify` | validation 通過、全 step dry-run 完了 |
| `npx nuxi typecheck` | 既知の vue-router volar 警告（CLAUDE.md で既知エラーと明示）。Python 変更のため影響なし |

## 未修整のリントエラー・テストエラー

なし（pre-existing の `test_limit_omitted_returns_all` は ver12.0 のスコープ外）。

## `/wrap_up` への引き継ぎ事項

- `docs/util/MASTER_PLAN/PHASE7.0.md` の「実装進捗」表で **§1 を「実装済」**、**§2 を「実装済（ver12.0）」** に更新が必要（IMPLEMENT.md §1-6 参照）
- `docs/util/MASTER_PLAN.md` の PHASE7.0 進捗記述を「§1 完了・§2 完了」へ更新（ROUGH_PLAN.md §成果物）
- `scripts/README.md` のテストケース件数記述（もしあれば）を +37 / +1 相当に更新（現状 README には具体件数は書かれていないので対応不要）
- `scripts/USAGE.md` に「step 1 実行前に validation が走る」旨を 1 行追記する余地あり（IMPLEMENT.md §2-6）

## 更新が必要そうなドキュメントと更新内容の案

- `docs/util/MASTER_PLAN/PHASE7.0.md` — 実装進捗表: §1/§2 を「実装済」に
- `scripts/USAGE.md` — 起動時挙動節に「validation が step 1 前に走る（失敗時 exit code 2）」を 1 行追記

## 古くて削除が推奨されるコード・ドキュメントの提案

なし。既存 `workflow.py` の raise-on-first-error 検証はランタイム防衛として意図的に残置（IMPLEMENT.md §2-3）。

## wrap_up 対応結果

plan_review_agent の承認（「修正等があっても軽微で、再度のレビュー不要」）を受けて以下を実施。

| 対応項目 | 結果 |
|---|---|
| `docs/util/MASTER_PLAN/PHASE7.0.md` §1 状態 | ✅ 「部分完了」→「実装済（ver10.0 で条件①②、ver12.0 で条件③）」に更新 |
| `docs/util/MASTER_PLAN/PHASE7.0.md` §2 状態 | ✅ 「未着手」→「実装済（ver12.0）」に更新 |
| `docs/util/MASTER_PLAN.md` PHASE7.0 行 | ✅ 「§1 部分完了・§2〜§8 未着手」→「§1・§2 完了・§3〜§8 未着手」へ更新 |
| `scripts/USAGE.md` 起動前 validation 追記 | ✅ `--workflow auto` 分岐仕様節の後に「起動前 validation」段落を追記 |
| ISSUES 整理 | ⏭️ 対応不要: 既存 4 件（`cli-flag-compatibility-system-prompt`, `test-issue-worklist-limit-omitted-returns-all`, `system-prompt-replacement-behavior-risk`, `issue-review-rewrite-verification`）はいずれも ver12.0 スコープ外で削除・更新は不要 |

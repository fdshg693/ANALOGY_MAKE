# ver11.0 IMPLEMENT — `tests/test_claude_loop.py` 分割と `scripts/tests/` 新設

本ドキュメントは `ROUGH_PLAN.md` が `/split_plan` に委ねた 7 件の判断事項を確定させ、実装手順を定める。対象は `ISSUES/util/high/pythonテスト肥大化.md`。プロダクションコード（`scripts/claude_loop.py` / `scripts/claude_loop_lib/`）には触れない。

## 1. 確定した設計判断

### 1-1. 配置先ディレクトリ: `scripts/tests/`

- ISSUE 本文で「`scripts`フォルダに`tests`フォルダを新設するなどして」と明示されているため、ISSUE 文面を尊重して `scripts/tests/` とする。
- Vitest (`vitest.config.ts`, `environment: 'node'`, alias `~ → .`) は `.test.ts` / `.test.js` のみを対象にし、`scripts/` 配下を探索しても `.py` は拾わないため干渉は発生しない（確認済み: `package.json` の `test` スクリプトは `vitest run`、include pattern 未指定のため Vitest デフォルトの `**/*.{test,spec}.{js,ts,...}` が適用される）。
- `scripts/tests/` は Python テスト専用とし、Nuxt 側 Vitest テスト（`tests/composables/` / `tests/server/` / `tests/utils/` / `tests/fixtures/`）はそのまま `tests/` に据え置く。

### 1-2. `__init__.py` / `sys.path` 設計

- `scripts/tests/__init__.py` を**空ファイル**で新設し、通常パッケージとして扱う。
- `scripts/__init__.py` は**作らない**。現状 `scripts/` は単独スクリプト群であり、既存の `claude_loop.py` から `from claude_loop_lib.xxx import ...` のように parent を参照せず動作している。パッケージ化すると `claude_loop.py` 内の絶対 import が壊れるリスクがあるため触らない。
- `scripts/tests/` 配下のテストは `scripts/` を `sys.path` に追加した上で `import claude_loop` / `from claude_loop_lib.xxx import ...` する既存スタイルを継承する。共通化のため以下の bootstrap モジュールを新設:

```python
# scripts/tests/_bootstrap.py
"""sys.path setup for scripts/tests/ — imported for side effect only."""
from __future__ import annotations
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent  # scripts/
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
```

- 各テストファイルの冒頭で `from . import _bootstrap  # noqa: F401` を実行してから `import claude_loop` / `from claude_loop_lib.xxx import ...` する。現行ファイル先頭 17 行の `sys.path.insert(...)` ハックを各ファイルにコピーすると将来のパス変更時に横展開負荷が高いため、単一化する。
- Windows / Linux 双方で `Path.resolve()` を用いるため可搬。既存 `tests/test_claude_loop.py:17` と同じ構造のため挙動差なし。

### 1-3. ファイル分割粒度

`claude_loop_lib/` の 8 モジュール + `scripts/claude_loop.py` CLI 層 + 統合テスト + `scripts/issue_worklist.py` 個別テストの計 **11 ファイル**に分割する。41 テストクラスの割り付けは以下。行数目安は 22〜347 行、1 ファイル平均 4 クラス弱・平均 162 行・最大 380 行程度（`test_workflow.py` に import + sentinel + `if __name__` ブロックを加えた概算）で、いずれも ROUGH_PLAN §7 の「1 ファイル 200〜400 行」目安に収まる。

| 新ファイル（`scripts/tests/`） | 含める TestClass（現 `tests/test_claude_loop.py` 行範囲） | クラス数 | 現ソース合計行数 |
|---|---|---|---|
| `test_logging_utils.py` | `TestCreateLogPath` (45–89) / `TestFormatDuration` (128–162) | 2 | 78 |
| `test_git_utils.py` | `TestGetHeadCommit` (90–127) / `TestCheckUncommittedChanges` (336–363) / `TestAutoCommitChanges` (364–397) | 3 | 97 |
| `test_notify.py` | `TestNotifyCompletion` (232–254) | 1 | 22 |
| `test_frontmatter.py` | `TestParseFrontmatter` (414–445) | 1 | 31 |
| `test_feedbacks.py` | `TestParseFeedbackFrontmatter` (446–485) / `TestLoadFeedbacks` (486–546) / `TestConsumeFeedbacks` (547–596) | 3 | 148 |
| `test_commands.py` | `TestBuildCommandWithLogFilePath` / `TestBuildCommandWithMode` / `TestBuildCommandWithFeedbacks` / `TestBuildCommandWithModelEffort` / `TestBuildCommandWithSession` / `TestBuildCommandWithSystemPrompt` / `TestBuildCommandWithAppendSystemPrompt` | 7 | 302 |
| `test_workflow.py` | `TestResolveMode` / `TestResolveCommandConfigAutoArgs` / `TestResolveDefaults` / `TestGetStepsModelEffort` / `TestGetStepsContinue` / `TestResolveWorkflowValue` / `TestResolveDefaultsOverrideKeys` / `TestGetStepsOverrideKeys` / `TestYamlSyncOverrideKeys` / `TestOverrideInheritanceMatrix` | 10 | 347 |
| `test_issues.py` | `TestExtractStatusAssigned` (968–1017) | 1 | 49 |
| `test_claude_loop_cli.py` | `TestParseArgsLoggingOptions` / `TestParseArgsAutoOption` / `TestParseArgsNotifyOption` / `TestParseArgsAutoCommitBefore` / `TestParseArgsWorkflow` / `TestValidateAutoArgs` / `TestReadWorkflowKind` / `TestFindLatestRoughPlan` / `TestComputeRemainingBudget` | 9 | 260 |
| `test_claude_loop_integration.py` | `TestYamlIntegration` (751–790) / `TestRunStepsSessionTracking` (864–967) / `TestAutoWorkflowIntegration` (1441–1562) | 3 | 263 |
| `test_issue_worklist.py` | `TestIssueWorklist` (1018–1203) | 1 | 185 |
| **合計** | | **41** | **1782** |

補足:
- `TestOverrideInheritanceMatrix` はモジュールスコープ sentinel `_UNSET = object()` を使うため、`test_workflow.py` の末尾近く（override 関連クラス群の隣）に配置。`_UNSET` はファイル冒頭で定義する。
- `TestGetHeadCommit` は `logging_utils.py` とはテスト対象が別（`git_utils.py`）であるため、現ファイルの配置に関わらず `test_git_utils.py` に移す。
- `TestIssueWorklist` は `scripts/issue_worklist.py` のテストであり `claude_loop_lib` とは独立。ファイル名で対象を明示する。
- 「現ソース合計行数」は各クラスの行数単純合計。実ファイルはこれに import ブロック + 末尾 `if __name__ == "__main__": unittest.main()` が加わり、上限 400 行を超える見込みなのは `test_workflow.py` (347 + 30 行程度 ≈ 380 行)・`test_commands.py` (302 + 30 行 ≈ 330 行)・`test_claude_loop_integration.py` (263 + 30 行 ≈ 290 行) のみ。いずれも 400 行以内に収まる見込み。

### 1-4. 共通ヘルパの切り出し

ver11.0 調査結果により、**現行 `tests/test_claude_loop.py` 内には複数クラスから参照されるヘルパが存在しない**（ヘルパメソッドはすべてクラスの `self._make_step()` / `self._parse()` / `self._write()` 等として各クラスのメソッドとして定義されている）。従って以下の方針を採る:

- クラス内部のヘルパは**移動先ファイルのクラス内部にそのまま残す**（切り出さない）。
- 共通化対象は `sys.path` bootstrap のみであり、これは §1-2 の `_bootstrap.py` で対応。
- `scripts/tests/conftest.py` は**作らない**（`unittest` ベースのため `pytest` 風 conftest は機能しない。将来 pytest 移行時に再検討）。
- モジュールスコープ sentinel `_UNSET` は `TestOverrideInheritanceMatrix` 専用なので、`test_workflow.py` の冒頭（import 直後）に同じ定義を 1 行で置く。

### 1-5. テスト実行コマンドの集約

現行: `python -m unittest tests.test_claude_loop`

新規（§R1 の Phase A 動作確認を前提とする）:

```bash
# 推奨（全件実行）
python -m unittest discover -s scripts/tests -t .

# 単一モジュール指定
python -m unittest scripts.tests.test_commands

# 単一クラス指定
python -m unittest scripts.tests.test_workflow.TestOverrideInheritanceMatrix
```

- `-t .` でプロジェクトルートを top-level directory とし、`scripts.tests.xxx` のドット記法でアクセス可能にする（`scripts/tests/__init__.py` のみでよく、`scripts/__init__.py` は不要。discover は `-t` 配下から `-s` までのパスを辿ってパッケージ解決する）。
- 事前検証: 上記 3 コマンドそれぞれで 192 件（pre-existing fail 1 件含む）が収集され、新旧で pass/fail 件数が一致すること。

更新箇所:
- `scripts/README.md:334-340` の「## テスト」節: 実行コマンドを `python -m unittest discover -s scripts/tests -t .` に置換し、`tests/test_claude_loop.py` への言及を `scripts/tests/` 配下の分割ファイル群に書き換える。具体的な新文面は §2-6 で定義。
- `Justfile`: 既存レシピに Python テスト系は無く（確認済み）、本 ISSUE のスコープで新規追加はしない。将来的な `just pytest` 等のレシピ新設は `scripts構成改善.md` / 別 ISSUE の範疇。
- `.github/workflows/deploy.yml`: `pnpm build` のみで Python テストは走らせていない（確認済み）。変更不要。

### 1-6. `tests/` 配下の既存非-Python テストへの影響

- 以下は Vitest 側で動作しており、`scripts/tests/` への移動対象外:
  - `tests/composables/useChat.test.ts` / `useThreads.test.ts`
  - `tests/server/*.test.ts`（12 ファイル）
  - `tests/utils/sse-parser.test.ts`
  - `tests/fixtures/settings.ts`
- `tests/__pycache__/` は `.gitignore` 37 行目 `__pycache__` でカバー済み（git に含まれていない）。Python テスト削除後に残る `.pyc` は次回 `unittest` 実行時に再生成されない（tests/ に .py が無くなるため）。
- `tests/test_claude_loop.py` 削除後、`tests/` 配下は .ts ファイルのみになる。ディレクトリ自体は維持。

### 1-7. 移行手順（破壊的変更の中間状態保全）

**一括書き換えではなく、段階的移行を採用する**。理由: 1881 行・41 クラスの単一ファイル分割は、途中で import ミス・コピー漏れが発生した場合の巻き戻しコストが大きいため、各段階で `python -m unittest` が通る中間状態を確保できる構造を採る。

**Phase A — 基盤作成（新配置を動く状態で立ち上げる）**
1. `scripts/tests/__init__.py` を空で作成。
2. `scripts/tests/_bootstrap.py` を §1-2 の内容で作成。
3. 1 ファイルだけ先行移動して discover が動くことを確認。候補は `test_notify.py`（22 行・1 クラス、依存少）。
4. `python -m unittest discover -s scripts/tests -t .` で 1 クラスが検出され pass することを確認。
5. **ここではまだ `tests/test_claude_loop.py` を触らない**。旧ファイルには該当クラスが残っているため、discovery は旧側でも走り、同じテストが 2 回実行される過渡期になる（各 assertion は side-effect free なので問題は起きない、ただし Phase B の各ステップで旧側から対応クラスを削除していく）。

**Phase B — 分割移行（モジュールごとに新 → 旧順で移動）**

以下の順で、1 ステップ = 「新ファイル作成 + 旧ファイルから該当クラス削除 + テスト実行」の 3 アクションを 1 まとまりとする。

1. `test_notify.py`（Phase A で作成済み）に対応する旧ファイル側 `TestNotifyCompletion` クラス（232–254 行）を削除。
2. `test_logging_utils.py` 新設 → 旧ファイル側 `TestCreateLogPath` (45–89) / `TestFormatDuration` (128–162) 削除。
3. `test_git_utils.py` 新設 → 旧ファイル側 `TestGetHeadCommit` (90–127) / `TestCheckUncommittedChanges` (336–363) / `TestAutoCommitChanges` (364–397) 削除。
4. `test_frontmatter.py` 新設 → 旧ファイル側 `TestParseFrontmatter` (414–445) 削除。
5. `test_feedbacks.py` 新設 → 旧ファイル側 3 クラス削除。
6. `test_issues.py` 新設 → 旧ファイル側 `TestExtractStatusAssigned` 削除。
7. `test_commands.py` 新設 → 旧ファイル側 `TestBuildCommand*` 7 クラス削除。
8. `test_workflow.py` 新設（`_UNSET` sentinel 含む）→ 旧ファイル側 workflow 関連 10 クラス削除。
9. `test_claude_loop_cli.py` 新設 → 旧ファイル側 parse args / validate 系 9 クラス削除。
10. `test_claude_loop_integration.py` 新設 → 旧ファイル側 `TestYamlIntegration` / `TestRunStepsSessionTracking` / `TestAutoWorkflowIntegration` 削除。
11. `test_issue_worklist.py` 新設 → 旧ファイル側 `TestIssueWorklist` 削除。

**各ステップ完了後に必須で実行する検証:**
- `python -m unittest tests.test_claude_loop` と `python -m unittest discover -s scripts/tests -t .` の**両方**を実行。
- 両者の合計テスト件数が 192 件（pre-existing fail 1 件含む）で一致すること。
- `test_limit_omitted_returns_all` 以外はすべて pass のままであること。

**Phase C — 旧ファイル削除**
12. すべてのクラス移動完了後、`tests/test_claude_loop.py` を `git rm` する（残骸の import 文のみになっているはず）。
13. `python -m unittest discover -s scripts/tests -t .` で 192 件収集・191 pass + 1 fail を確認。
14. `tests/__pycache__/test_claude_loop.cpython-313.pyc` は git 管理外のため git 側は無視。ローカル clean したい場合は `git clean -fX tests/` を任意で実行。

**Phase D — ドキュメント更新**
15. `scripts/README.md` の「## テスト」節（334–340 行）を §1-5 / §2-6 の新文面に置換。

**Phase E — 関連 ISSUE の状態確認（スコープ外だが確認のみ）**
16. `ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md` の本文中の `tests/test_claude_loop.py` / `TestIssueWorklist` 参照は `scripts/tests/test_issue_worklist.py` / `TestIssueWorklist` に改訂が必要。**本 ISSUE のスコープ外**（`/issue_plan` が別バージョンで扱う）のため、本バージョンでは ISSUE 本文を書き換えない。ver11.0 は**メジャーバージョン**のため CHANGES.md は作成されない（CHANGES.md はマイナー専用、CLAUDE.md バージョン管理規則）。`MEMO.md` に「関連 ISSUE (`test-issue-worklist-limit-omitted-returns-all.md`) の参照先は次バージョン以降で更新が必要」と残す。

**コミット粒度の推奨**: Phase B を 1 コミットにまとめると 1881 行の分割を `git bisect` できず、コピー漏れ・import ミスが発生した場合の切り分けコストが高い。また ROUGH_PLAN §7 の「テストが常に通る中間状態を確保する設計が望ましい」方針とも整合しない。**Phase B の各ステップ（1〜11）を別コミット**として積む。PR レビュー時の `git log --follow` の煩雑さはトレードオフとして許容する。コミット例:
- `test(ver11.0): scripts/tests/ 基盤（__init__.py / _bootstrap.py）追加` (Phase A ステップ 1–2)
- `test(ver11.0): test_notify.py を scripts/tests/ に先行移動` (Phase A ステップ 3–4 + Phase B ステップ 1)
- `test(ver11.0): test_logging_utils.py 分割` (Phase B ステップ 2)
- `test(ver11.0): test_git_utils.py 分割` (Phase B ステップ 3)
- ...（Phase B のステップ 4–11 も各 1 コミット）
- `test(ver11.0): tests/test_claude_loop.py を削除` (Phase C)
- `docs(ver11.0): scripts/README.md のテスト実行コマンドを更新` (Phase D)

**旧ファイルの import 文整理タイミング**: Phase B の各ステップで旧ファイルから特定クラスを削除する際、そのクラスだけが使っていた import は**その場で削除しない**。孤立 import が残っていても `python -m unittest tests.test_claude_loop` は ImportError にならない（モジュール全体の import は失敗しても、parse エラーにはならず test 実行時に初めて参照されるため。ただし top-level の `from claude_loop import _run_steps` 等は module 読み込み時に評価される点に注意）。安全策として、**Phase B の全ステップ終了後・Phase C 直前**に旧ファイルの未使用 import をまとめて削除する。Phase C で丸ごと削除するため、未使用 import 整理は不要（削除ファイルに対して lint を通す必要なし）とも判断できるが、中間検証 (`python -m unittest tests.test_claude_loop` で 0 件収集) を通すために、Phase B 最終ステップの前までに `top-level import 評価時に失敗しないこと`は保証する。

## 2. 実装詳細

### 2-1. `scripts/tests/__init__.py`

空ファイル。

### 2-2. `scripts/tests/_bootstrap.py`

§1-2 参照。内容再掲:

```python
"""sys.path setup for scripts/tests/ — imported for side effect only."""
from __future__ import annotations
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent  # scripts/
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
```

### 2-3. 各テストファイル共通の冒頭テンプレート

```python
"""Tests for scripts/claude_loop_lib/<module>.py."""
from __future__ import annotations

# <必要な標準ライブラリ import>

from . import _bootstrap  # noqa: F401  — must precede claude_loop_lib imports

# <必要な claude_loop / claude_loop_lib imports>


class TestXxx(unittest.TestCase):
    ...


if __name__ == "__main__":
    unittest.main()
```

- 旧ファイル冒頭 17 行の `sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))` は `_bootstrap` 側に集約するため、各テストファイルでは書かない。
- 旧ファイルは「Tests for logging features in scripts/claude_loop.py.」という 1 行の docstring を使っているが、分割後は各ファイルの対象モジュールを反映した docstring に書き換える。
- `if __name__ == "__main__": unittest.main()` は旧ファイルでは末尾に無いが、分割後は各ファイルに 1 行加える（`python scripts/tests/test_commands.py` 直接実行を可能にする。discover は `__main__` ブロック有無に関わらず動作）。

### 2-4. 各ファイルの import 設計

ファイル間の import 重複を最小化するため、各ファイルは**そのファイル内で実際に参照する名前のみ**を import する。現 `tests/test_claude_loop.py:19-29` の一括 import は分割時に各ファイルへ「必要分だけ」をコピーする。

確定した対応:

| 新ファイル | claude_loop_lib から | claude_loop から | 標準ライブラリ |
|---|---|---|---|
| `test_logging_utils.py` | `logging_utils`: `create_log_path`, `format_duration` | （なし） | `unittest`, `tempfile`, `pathlib.Path` |
| `test_git_utils.py` | `git_utils`: `get_head_commit`, `check_uncommitted_changes`, `auto_commit_changes` | （なし） | `unittest`, `subprocess`, `unittest.mock.patch` / `MagicMock` |
| `test_notify.py` | `notify`: `notify_completion`, `_notify_toast` | （なし） | `unittest`, `unittest.mock.patch` |
| `test_frontmatter.py` | `frontmatter`: `parse_frontmatter` | （なし） | `unittest`, `tempfile`, `pathlib.Path` |
| `test_feedbacks.py` | `feedbacks`: `parse_feedback_frontmatter`, `load_feedbacks`, `consume_feedbacks` | （なし） | `unittest`, `shutil`, `tempfile`, `pathlib.Path` |
| `test_commands.py` | `commands`: `build_command` | （なし） | `unittest` |
| `test_workflow.py` | `workflow`: `load_workflow`, `get_steps`, `resolve_defaults`, `resolve_command_config`, `resolve_mode`, `resolve_workflow_value`, `FULL_YAML_FILENAME`, `QUICK_YAML_FILENAME`, `ISSUE_PLAN_YAML_FILENAME`, `OVERRIDE_STRING_KEYS`, `ALLOWED_STEP_KEYS`, `ALLOWED_DEFAULTS_KEYS` | （なし） | `unittest`, `pathlib.Path`, `typing.Any` |
| `test_issues.py` | `issues`: `extract_status_assigned` | （なし） | `unittest`, `tempfile`, `pathlib.Path` |
| `test_claude_loop_cli.py` | （なし） | `parse_args`, `validate_auto_args`, `_find_latest_rough_plan`, `_read_workflow_kind`, `_compute_remaining_budget`, `_version_key` | `unittest`, `argparse`, `tempfile`, `pathlib.Path`, `unittest.mock.patch` |
| `test_claude_loop_integration.py` | `workflow`: `load_workflow`, `get_steps`, `resolve_defaults`, `FULL_YAML_FILENAME`, `QUICK_YAML_FILENAME` （`TestYamlIntegration` 用。`TestRunStepsSessionTracking` / `TestAutoWorkflowIntegration` は workflow を直接呼ばない） | `_run_steps`, `claude_loop`（module 全体：`@patch("claude_loop.subprocess.run")` 等のパッチターゲット用） | `unittest`, `json`, `subprocess`, `tempfile`, `pathlib.Path`, `unittest.mock.patch` / `MagicMock` |
| `test_issue_worklist.py` | （なし） | （なし） | `unittest`, `json`, `tempfile`, `pathlib.Path`, `unittest.mock.patch` |

補足:
- `test_issue_worklist.py` は `_bootstrap` で `scripts/` が `sys.path` に追加されるため、トップレベルで `import issue_worklist` が可能。現行 `TestIssueWorklist` はメソッド内で `issue_worklist` を参照するため、ファイル冒頭で `import issue_worklist` した後はそのまま `issue_worklist.collect(...)` 等として呼び出せる（現行コードは `scripts/issue_worklist.py` の関数を `scripts/` をパス追加した上で module 経由で参照している。分割後も同じ参照形式を維持）。`patch.object(issue_worklist, "REPO_ROOT", ...)` 形式のパッチターゲットも現行と同じ module オブジェクト参照のため変更不要。
- `test_claude_loop_integration.py` は `import claude_loop`（module オブジェクト全体）が必要。`claude_loop.subprocess.run` / `claude_loop.uuid.uuid4` を `@patch` ターゲットに使うため。
- 各ファイルでどの `claude_loop_lib.*` モジュールが参照されるかは、実際にコピーしたコードで `grep` し、未使用 import を `F401` 警告が出ないように整理する。

### 2-5. `_UNSET` sentinel の扱い

- 現位置: `tests/test_claude_loop.py:1782` （`TestOverrideInheritanceMatrix` の直前）。
- 移動先: `scripts/tests/test_workflow.py` の import ブロック直後（クラス定義より前）。
- 定義: `_UNSET = object()`
- 参照: `TestOverrideInheritanceMatrix` 内のメソッドのみ。他ファイルからは参照しないため、`test_workflow.py` 内に閉じた private 定数として扱う。

### 2-6. `scripts/README.md` 更新

現在の「## テスト」節（`scripts/README.md:334-340`）を以下の 3 ブロック（見出し 1 行 + bash コードブロック + 説明 1 段落）に置換する。以下は Markdown フェンス入れ子を避けるため、フェンスを `~~~` で表記しているが、実際の README ではバッククォート 3 本のフェンスを使うこと:

見出し: `## テスト`

bash コードブロック（実 README では ` ``` ` フェンス）:

~~~bash
# 全件実行（推奨）
python -m unittest discover -s scripts/tests -t .

# 個別ファイル指定
python -m unittest scripts.tests.test_commands

# 個別クラス指定
python -m unittest scripts.tests.test_workflow.TestOverrideInheritanceMatrix
~~~

説明段落（そのまま README に貼り付け）:

> テストは `scripts/tests/` 配下に対象モジュール別に分割されている（`test_<module>.py` の命名規則）。`claude_loop_lib.*` のパッチターゲットを使って個別モジュールをモックし、`_run_steps` の session 引き継ぎ統合テストは `claude_loop.subprocess.run` / `claude_loop.uuid.uuid4` をパッチして検証する。

※ 件数の記述（現行「現状 192 件」）は、再構成後も 192 件で変化しないが、将来のテスト追加時の docstring メンテ負担を減らすため記述自体を削除し、実件数は `unittest` の出力に委ねる。

### 2-7. pre-existing fail の保全

- `TestIssueWorklist.test_limit_omitted_returns_all` は ver10.0 MEMO で pre-existing fail として記録済み（ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md）。
- 分割後も同一のアサーション・同一のテストロジックで `scripts/tests/test_issue_worklist.py::TestIssueWorklist::test_limit_omitted_returns_all` として失敗する状態を保全する。
- 本 ISSUE のスコープは「ファイル構成変更」のみであり、失敗テストの修正は別 ISSUE。

## 3. リスク・不確実性

新規ライブラリや未使用 API は扱わないが、以下の不確実性がある:

### R1: `python -m unittest discover -s scripts/tests -t .` の動作

- 不確実性: `scripts/__init__.py` を作らない場合、`scripts.tests.test_xxx` のドット記法解決が環境によって失敗する可能性。`discover` は `-t` からの相対パスで namespace package を辿るが、Python 3.13（確認済みの開発環境 `__pycache__/*.cpython-313.pyc`）では implicit namespace package が効くはずではある。
- 軽減策: 実装 Phase A の初手で `scripts/tests/` に 1 ファイル置いた直後に `python -m unittest discover -s scripts/tests -t .` / `python -m unittest scripts.tests.test_notify` の両方で動作確認する。万一 `scripts.tests.test_notify` 形式が失敗した場合は discover 形式 (`python -m unittest discover -s scripts/tests -t .`) のみを README に記載する運用に切り替える（ドット記法はオプションだが、discover 形式だけでも運用可能）。
- 代替案: それでも動かない場合は `scripts/__init__.py` を**空で**新設する。これは本ファイルの §1-2 の方針（作らない）を覆す変更だが、リスクとしては小さい（既存 `scripts/claude_loop.py` 内は `from claude_loop_lib.xxx import ...` のように `scripts.` プリフィクスを書いていないため、`scripts/` 自身を `sys.path` に入れている限り `scripts/__init__.py` の有無は直接 import に影響しない）。ただし本 IMPLEMENT では**まず作らない方針**で進め、Phase A の検証結果で必要と判断された場合のみ追加する。

### R2: `__pycache__/test_claude_loop.cpython-313.pyc` の stale キャッシュ

- 不確実性: 旧 `tests/test_claude_loop.py` を削除した後、開発者環境に `tests/__pycache__/test_claude_loop.cpython-313.pyc` が残っていると `python -m unittest tests.test_claude_loop` がまだ動いてしまい、移行ミスを隠蔽する可能性。
- 軽減策: Phase C (`tests/test_claude_loop.py` 削除) 後、README 書き換え時に「新コマンドは `python -m unittest discover -s scripts/tests -t .`」と明記。また Phase B 終了時点で `tests/test_claude_loop.py` が import 文だけ残った空ファイルになるため、旧コマンドで実行するとテスト 0 件の状態になり視認可能。

### R3: `sys.path` の二重 insert

- 不確実性: 複数のテストファイルが `_bootstrap` を import すると `sys.path.insert(0, ...)` が複数回走らないか。
- 軽減策: `_bootstrap.py` 内で `if str(_SCRIPTS_DIR) not in sys.path:` ガードを入れる（§1-2 のコード参照）。Python モジュールのキャッシュにより 2 回目以降の `from . import _bootstrap` は no-op になるため実質問題ないが、防御的に書く。

### R4: `test_claude_loop_integration.py` の `@patch` ターゲット文字列

- 不確実性: 現行 `TestAutoWorkflowIntegration` / `TestRunStepsSessionTracking` は `@patch("claude_loop.subprocess.run")` / `@patch("claude_loop.uuid.uuid4")` / `@patch("claude_loop._find_latest_rough_plan")` のように `claude_loop` モジュールを dotted path で指定している。`_bootstrap.py` で `scripts/` を `sys.path` に入れてから `import claude_loop` すれば `claude_loop.xxx` のパッチターゲットは同じ名前で動作するはず。
- 軽減策: Phase B ステップ 10（`test_claude_loop_integration.py` 新設）で、1 ケースずつ `@patch` デコレータが効くか確認する。問題があれば `@patch` ターゲットを書き換え（`scripts.claude_loop.xxx` 等）。

### R5: Vitest のテスト探索への干渉

- 不確実性: Vitest は `scripts/tests/*.py` を拾わないはずだが、設定の implicit デフォルトに依存している。
- 軽減策: `vitest.config.ts` の include は明示されておらず、デフォルトパターンは `**/*.{test,spec}.?(c|m)[jt]s?(x)`（Vitest 公式）。`.py` はマッチしないため安全。実装後、`pnpm test` が正常に走ることを確認する（Phase D 相当の確認）。

### R6: 段階移行中の discover 重複検出

- 不確実性: Phase B のステップ移行中、旧ファイルに残っているクラスと新ファイルに移動済みクラスが**両方** discover に引っかかる可能性がある。
- 軽減策: `python -m unittest discover -s scripts/tests -t .` は `scripts/tests/` 配下のみ、`python -m unittest tests.test_claude_loop` は `tests/test_claude_loop.py` のみを見るため、両者は分離される。混乱を避けるため各ステップで両方のコマンドを実行し、件数の合計が 192 件で一致することを確認。

## 4. 変更予定ファイル一覧

### 新規作成

- `scripts/tests/__init__.py`（空）
- `scripts/tests/_bootstrap.py`（§2-2）
- `scripts/tests/test_logging_utils.py`
- `scripts/tests/test_git_utils.py`
- `scripts/tests/test_notify.py`
- `scripts/tests/test_frontmatter.py`
- `scripts/tests/test_feedbacks.py`
- `scripts/tests/test_commands.py`
- `scripts/tests/test_workflow.py`
- `scripts/tests/test_issues.py`
- `scripts/tests/test_claude_loop_cli.py`
- `scripts/tests/test_claude_loop_integration.py`
- `scripts/tests/test_issue_worklist.py`

### 削除

- `tests/test_claude_loop.py`
- `tests/__pycache__/test_claude_loop.cpython-313.pyc`（git 管理外なので git 側は無視、ローカル任意 clean）

### 修正

- `scripts/README.md`（334–340 行の「## テスト」節、§2-6）

### 変更なし（確認済み）

- `.github/workflows/deploy.yml`（Python テストを走らせていない）
- `Justfile`（Python テスト系レシピなし）
- `vitest.config.ts`（`.py` を拾わない）
- `tests/composables/` / `tests/server/` / `tests/utils/` / `tests/fixtures/`（Vitest 側、対象外）
- `scripts/claude_loop.py` / `scripts/claude_loop_lib/*.py` / `scripts/issue_worklist.py` / `scripts/issue_status.py` / `scripts/claude_sync.py`（プロダクションコード、触らない）

## 5. 受け入れ基準

1. `python -m unittest discover -s scripts/tests -t .` が 192 件収集し、191 pass + 1 fail（`test_limit_omitted_returns_all`）となる。
2. `tests/test_claude_loop.py` は存在しない。
3. `python -m unittest tests.test_claude_loop` は `ModuleNotFoundError` 相当になる（旧コマンドは実行できない状態）。`tests/__pycache__/` に stale な `.pyc` が残る環境では事前に `git clean -fX tests/` を実行したうえで確認すること（§R2）。
4. `pnpm test` が Vitest 側で正常に走り、非-Python テストの件数が既存と一致する。
5. `scripts/README.md` のテスト節が新コマンドに更新されている。
6. 新ファイル各々が `python scripts/tests/test_<module>.py` の直接実行でも動く（`__name__ == "__main__"` ブロックあり）。

## 6. 参照ドキュメント

- `ROUGH_PLAN.md`（本バージョン）
- `ISSUES/util/high/pythonテスト肥大化.md`
- `docs/util/ver10.0/CURRENT_tests.md`（既存テスト構成）
- `docs/util/ver10.0/CURRENT_scripts.md`（`scripts/` 配下構成）
- `docs/util/ver10.0/MEMO.md`（pre-existing fail の記録）
- `scripts/README.md`（更新対象）

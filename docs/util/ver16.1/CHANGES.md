# CHANGES: util ver16.1 — PHASE8.0 §2 deferred execution 実装

## 変更ファイル一覧

### 新規追加

| ファイル | 概要 |
|---|---|
| `scripts/claude_loop_lib/deferred_commands.py` | deferred execution コアモジュール（scan / validate / execute / consume / resume prompt 組み立て / orphan 検知） |
| `scripts/tests/test_deferred_commands.py` | `deferred_commands.py` 専用テスト（14 case） |
| `experiments/deferred-execution/NOTES.md` | 「有望な方式 / 避けるべき方式」まとめ（IMPLEMENT.md 完了条件 5） |
| `experiments/deferred-execution/large-stdout/compare_excerpts.py` | 巨大 stdout の excerpt 行数比較実験スクリプト（§0-3 検証） |
| `experiments/deferred-execution/large-stdout/.gitignore` | large-stdout 実験の生成物を除外 |
| `experiments/deferred-execution/orphan-recovery/test_marker.py` | `.started` marker による orphan 検知実験スクリプト（§5-2 検証） |
| `experiments/deferred-execution/resume-twice/README.md` | 二重 resume 未検証の理由と fallback 方針の記録（§5-1） |
| `experiments/deferred-execution/retention-check/check_retention.py` | session retention 確認スクリプト |

### 変更

| ファイル | 変更概要 |
|---|---|
| `scripts/claude_loop.py` | `_execute_single_step()` 抽出・`_process_deferred()` 追加・`_run_steps` への deferred 分岐差し込み・`--no-deferred` CLI フラグ追加 |
| `scripts/claude_loop_research.yaml` | `write_current` step に `effort: high` 追加 |
| `scripts/claude_loop.yaml` | `write_current` step に `effort: high` 追加 |
| `scripts/README.md` | deferred execution 概要・`DEFERRED/` 配置・`deferred_commands.py` のモジュール一覧への追記 |
| `scripts/USAGE.md` | `--no-deferred` フラグ・request schema・result meta.json スキーマ・巨大出力注意の追記 |
| `scripts/tests/test_claude_loop_integration.py` | deferred 経路の統合テスト 2 case 追加（計 280 → 296 PASS） |
| `.claude/SKILLS/retrospective/SKILL.md` | ISSUE 管理手順へ「レトロスペクティブで追記すべきと判断したもの」の項を追記 |

---

## 変更内容の詳細

### `scripts/claude_loop_lib/deferred_commands.py`（新規）

deferred execution の中核。以下の公開関数を提供する:

| 関数 | 役割 |
|---|---|
| `scan_pending(deferred_dir)` | `DEFERRED/*.md` を非再帰 glob（`done/` と `results/` を除外） |
| `validate_request(path)` | frontmatter + body パース、必須フィールド・cwd 存在・fenced code block 1 個を検査 |
| `execute_request(req, deferred_dir)` | subprocess.run で順次実行。meta.json / stdout.log / stderr.log を書き出し |
| `consume_request(req_path, done_dir)` | request を `done/` へ move（失敗時も必ず呼ぶ → orphan 防止） |
| `build_resume_prompt(results)` | resume 用追加 prompt 組み立て（exit_code / stdout_bytes / path を含む） |
| `summarize_result(result)` | step footer 直後に挿入する 2〜4 行の要約（`logging_utils.py` への配置案を変更、詳細は §計画との乖離） |

設計上の特徴:
- 型は `TypedDict`（`DeferredRequest` / `DeferredResult`）を使用。dataclass 禁止（`.claude/rules/scripts.md` §1 準拠）
- frontmatter 読み取りは既存 `frontmatter.py::parse_frontmatter` を再利用
- `HEAD_EXCERPT_LINES = 20`, `TAIL_EXCERPT_LINES = 20`（EXPERIMENT.md §U4 で C 案を採用）
- `.started` marker を実行前に書き出し、SIGKILL 後の次回 scan で orphan を検知

#### Request スキーマ（`DEFERRED/<request_id>.md`）

```
---
request_id: <uuid4>
source_step: <step name>
session_id: <Claude session id>
cwd: <absolute or repo-relative path>
expected_artifacts:
  - <path>
timeout_sec: <int | null>
note: |
  (resume 時に Claude に渡す補足メモ)
---

# Commands

```bash
<command line 1>
<command line 2>
```
```

#### Result meta スキーマ（`DEFERRED/results/<request_id>.meta.json`）

```json
{
  "request_id": "...",
  "source_step": "...",
  "session_id": "...",
  "commands": ["..."],
  "started_at": "...",
  "ended_at": "...",
  "duration_sec": 192,
  "exit_codes": [0, 0, 127],
  "overall_exit_code": 127,
  "stdout_bytes": 4823091,
  "stdout_path": "DEFERRED/results/<request_id>.stdout.log",
  "stderr_bytes": 12890,
  "stderr_path": "DEFERRED/results/<request_id>.stderr.log",
  "head_excerpt": "...",
  "tail_excerpt": "..."
}
```

### `scripts/claude_loop.py`（変更）

1. **`_execute_single_step()` 抽出**（REFACTOR.md）: `_run_steps` の ~30 行を private helper として分離。シグネチャ `(*, command, cwd, tee, prev_commit, step_start) -> tuple[int, str | None]`。`command_str` は未使用のため省略（IMPLEMENT.md 記載シグネチャから変更）
2. **`_process_deferred()` 追加**: scan → validate → execute → consume → build_resume_prompt を 1 関数にまとめたヘルパー。各 request ごとに try/finally で `consume_request` を呼ぶことで orphan を防止
3. **`_run_steps` への差し込み**: フィードバック消費と `previous_session_id` 更新の間に `_process_deferred` 呼び出しを挿入。deferred あり時は `_execute_resume()` で `claude -r <session_id> -p <resume_prompt>` を起動
4. **`--no-deferred` CLI フラグ**: `parse_args` に追加し `_run_steps` へ伝播（問題切り分け用）

### `scripts/claude_loop_research.yaml` / `scripts/claude_loop.yaml`（変更）

`write_current` step に `effort: high` を追加。他 4 YAML（`claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` / `claude_loop_scout.yaml` / `claude_loop_question.yaml`）は対象外。`.claude/rules/scripts.md` §3 の sync 対象は `command` / `defaults` セクションのみで `steps[].effort` は各 YAML 独自構成のため、sync 契約の逸脱ではない。

### `experiments/deferred-execution/`（新規）

| サブディレクトリ | 内容 |
|---|---|
| `large-stdout/` | excerpt 行数 A/B/C 案の比較（§0-3・§5-3 検証）。C 案（head 20 + tail 20）採用根拠 |
| `orphan-recovery/` | `.started` marker による SIGKILL 後の orphan 検知実験（§5-2 検証） |
| `resume-twice/` | 二重 resume の安全性検証（§5-1 未検証、README に先送り理由を記録） |
| `retention-check/` | session retention 確認 |
| `NOTES.md` | 「有望な方式 / 避けるべき方式」まとめ（完了条件 5） |

---

## 技術的判断

### `validate_deferred_request` をインラインに変更

計画では `validation.py` に追加予定だったが `deferred_commands.validate_request` 内でインライン実装に変更した。理由: `validation.py` は startup 時の YAML 一括検証専用で `Violation` dataclass を返すインフラ。deferred request の実行時検査は `ValueError` を投げる方が自然で、呼び出し箇所を 1 箇所に閉じられる。

### `summarize_result` を `deferred_commands.py` に配置

計画では `logging_utils.py` に `format_deferred_result` を追加する予定だったが、`DeferredResult` TypedDict が `deferred_commands.py` で定義されており、`logging_utils.py` に分離すると型の循環参照になる。「`logging_utils.py` は汎用 IO、`deferred_commands.py` は deferred 固有整形」の責務境界で整合する。

### excerpt 行数は C 案（head 20 + tail 20）を採用

EXPERIMENT.md §U4 で実測。10MB stdout でも resume prompt は 2.2KB 前後に収まり、`test_excerpt_stays_bounded_for_large_stdout` で < 4000 bytes を assert している。

### session resume 二重起動リスクは先送り

RESEARCH.md §A3 / §A6 で Anthropic 公式 docs の `-p --resume <id>` が headless 継続の正典 pattern であることを確認。EXPERIMENT.md §U2/§U3 は nested `claude` 起動による観測バイアスのため未検証扱いとし、`ISSUES/util/medium/deferred-resume-twice-verification.md` に追加。本番発生時は IMPLEMENT.md §5-1 fallback（新規 session id + 履歴 prompt 貼り付け）に切り替える。

### orphan 検知方式

`execute_request` 実行前に `<request_id>.started` marker を書き出し、次回 `scan_pending` 時に marker 残存を検出して workflow を停止・人手復旧 ISSUE 自動起票。副作用あるコマンドの自動再実行を防止する最小機構として ver16.1 に実装。本格的な冪等性保証は ver16.2 以降。

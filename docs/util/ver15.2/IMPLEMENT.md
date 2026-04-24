# ver15.2 IMPLEMENT — PHASE7.1 §2: QUESTIONS/ + question workflow

PHASE7.1 §2 の実装計画。新規 `QUESTIONS/` queue・新規 `question` workflow YAML・新規 SKILL・新規 Python スクリプト（status / worklist / 共通ライブラリ）の add-only 追加と、既存 `claude_loop.py` / `workflow.py` / `README.md` / `USAGE.md` / 関連 SKILL への最小分岐追加を組み合わせる。ver15.0 の scout 実装（`docs/util/ver15.0/IMPLEMENT.md`）を参考モデルとし、構造・テスト方針・risk テーブルの様式を継承する。

## ゴール（完了条件の再掲）

- `--workflow question` で `scripts/claude_loop_question.yaml` を起動でき、既存 `auto` / `full` / `quick` / `scout` の挙動は変更されない
- `QUESTIONS/{カテゴリ}/{high,medium,low}/*.md` を起点に `ready / ai` の Question を 1 件拾い、`docs/{カテゴリ}/questions/{slug}.md` に調査報告書を出力できる
- Question のライフサイクル（`raw / ready / need_human_action` × `human / ai`）と `QUESTIONS/{カテゴリ}/done/` への移動規約が `QUESTIONS/README.md` で明示される
- 既存 105 件のテストは全件グリーン。新規テストを Python 側に 8〜10 件追加する
- 付随対応 ISSUE 2 件（`imple-plan-four-file-yaml-sync-check.md` / `readme-workflow-yaml-table-missing-scout.md`）は本バージョン内で消化する（理由は §付随 ISSUE 合流判断）

## 付随 ISSUE 合流判断

ROUGH_PLAN 「付随的に触れる ISSUE」2 件について、以下の理由で本バージョンに合流消化する。

| ISSUE | 合流判断 | 理由 |
|---|---|---|
| `ISSUES/util/medium/imple-plan-four-file-yaml-sync-check.md` | **合流**（ready/ai 昇格→消化→`done/` 移動） | 本バージョンで 5 ファイル目の YAML（`claude_loop_question.yaml`）を追加するため、「YAML 増減時に rule / docs の同期対象リストを更新する」チェックを SKILL 本文に先に仕込んでおくのが予防的に合理的。本 ISSUE を放置して §2 を実装すると、`.claude/rules/scripts.md` §3 の「4 ファイル」記述を再び rot させるリスクが明確に存在する。対応は `.claude/skills/imple_plan/SKILL.md` と `.claude/skills/quick_impl/SKILL.md` に 1〜2 文の注意文追記のみで、100 行枠を大きく下回る |
| `ISSUES/util/low/readme-workflow-yaml-table-missing-scout.md` | **合流**（消化→`done/` 移動） | §2 で `scripts/README.md` を編集するタイミングで、同じテーブル（L17-25）に `claude_loop_question.yaml` 行を追加することになる。scout 行の欠落を同時に埋めれば別バージョンで再度 README を触る必要がなくなる。変更は 1 行追加のみ |

いずれも「§2 と同じファイルに触る」合流条件を満たし、かつ ver15.0 `/retrospective` §4 / scout 起票時点での指摘どおり「rule と docs のずれ」を本バージョンで先回り解消する位置付け。

## 成果物一覧

| # | パス | 操作 | 概要 |
|---|---|---|---|
| 1 | `QUESTIONS/README.md` | 新規 | Question の frontmatter 仕様・ライフサイクル・報告書配置規約・ISSUE との境界を定義 |
| 2 | `QUESTIONS/util/high/.gitkeep` / `medium/.gitkeep` / `low/.gitkeep` / `done/.gitkeep` | 新規 | ディレクトリ骨格（空ディレクトリを git に残すための placeholder） |
| 2a | `docs/util/questions/.gitkeep` | 新規 | 調査報告書の出力先ディレクトリを先行作成（R6 の解決策として初回実行時のディレクトリ欠如エラーを予防） |
| 3 | `scripts/claude_loop_question.yaml` | 新規 | 調査専用 workflow 定義。`question_research` 1 ステップ（opus/high）。`command` / `defaults` は既存 4 ファイルと同一内容 |
| 4 | `scripts/claude_loop_lib/questions.py` | 新規 | Question frontmatter ヘルパー（`VALID_STATUS` / `VALID_ASSIGNED` / `VALID_COMBOS` / `extract_status_assigned`）。`issues.py` の並列コピーで、status から `review` を除外した Question 固有の combos を持つ |
| 5 | `scripts/question_status.py` | 新規 | `QUESTIONS/{カテゴリ}/{priority}/*.md` の status × assigned 分布表示（`issue_status.py` の並列コピー、Question 用 DISPLAY_ORDER を採用） |
| 6 | `scripts/question_worklist.py` | 新規 | `QUESTIONS/` の着手候補抽出（`issue_worklist.py` の並列コピー、既定 `--status ready`） |
| 7 | `scripts/claude_loop_lib/workflow.py` | 変更 | `QUESTION_YAML_FILENAME` 定数追加・`RESERVED_WORKFLOW_VALUES` に `"question"` 追加・`resolve_workflow_value` に分岐追加 |
| 8 | `scripts/claude_loop.py` | 変更なし（予定） | `_run_selected()` 一般経路を通るため本体コード変更は発生しない。`--workflow` help テキストは ver15.0 precedent に従い非変更（リスク R2 参照） |
| 9 | `.claude/skills/question_research/SKILL.md` | 新規 | 調査報告書作成手順。探索・証拠収集・結論・不確実性・次アクション候補の 5 項目出力規約 |
| 10 | `.claude/skills/issue_plan/SKILL.md` | 変更（最小） | 「`QUESTIONS/` 配下は本 SKILL の対象外（`question_research` 専属）」を 1 段落追記 |
| 11 | `.claude/skills/imple_plan/SKILL.md` | 変更 | 付随 ISSUE 10a の消化: YAML 増減時の rule / docs 同期チェックリストを 1 段落追記 |
| 12 | `.claude/skills/quick_impl/SKILL.md` | 変更 | 付随 ISSUE 10a の消化: 同上、quick 経路用の短縮版注意文を追記 |
| 13 | `.claude/rules/scripts.md` | 変更 | §3 の「4 ファイル」→「5 ファイル」に更新し、`claude_loop_question.yaml` を同期対象として追加 |
| 14 | `scripts/README.md` | 変更 | L17-25 ファイル一覧テーブルに `claude_loop_scout.yaml`（付随 ISSUE 10b 消化）と `claude_loop_question.yaml` を追加。L98-112 下に「question（調査専用）」節を追加 |
| 15 | `scripts/USAGE.md` | 変更 | L137 の 4 ファイル同期契約を 5 ファイルに更新。L141-164 のサンプル YAML 一覧に question を追加。`QUESTIONS/` と `ISSUES/` の境界を短く追記 |
| 16 | `scripts/tests/test_workflow.py` | 変更 | `QUESTION_YAML_FILENAME` import 追加・`TestResolveWorkflowValue` に question 解決テスト追加・`TestYamlSyncOverrideKeys` に question YAML テスト追加・`RESERVED_WORKFLOW_VALUES` drift-guard テスト追加 |
| 17 | `scripts/tests/test_questions.py` | 新規 | `extract_status_assigned` の Question 用 combos 検証（`test_issues.py` の並列コピー） |
| 18 | `scripts/tests/test_question_worklist.py` | 新規 | `question_worklist.py` のフィルタ・JSON 出力・limit・priority 不整合警告テスト（`test_issue_worklist.py` の並列コピー） |
| 19 | `scripts/tests/test_validation.py` | 変更 | `TestValidateStartupExistingYamls` に question YAML の存在検査を追加（ver15.0 scout と同型） |
| 20 | `ISSUES/util/medium/imple-plan-four-file-yaml-sync-check.md` | 移動 | `ISSUES/util/done/imple-plan-four-file-yaml-sync-check.md` へ移動（frontmatter の `status` 調整は不要、`done/` 移動のみ） |
| 21 | `ISSUES/util/low/readme-workflow-yaml-table-missing-scout.md` | 移動 | `ISSUES/util/done/readme-workflow-yaml-table-missing-scout.md` へ移動 |
| 22 | `docs/util/MASTER_PLAN/PHASE7.1.md` | 変更なし（予定） | §2 の進捗更新は `/wrap_up` または `/write_current` ステップで実施する（IMPLEMENT の責務外） |
| 23 | `docs/util/ver15.2/MEMO.md` / `CHANGES.md` | 後続で生成 | full workflow 成果物、`/wrap_up` / `/write_current` / `/retrospective` ステップで順次生成 |

新規追加の Python スクリプトは `scripts/issue_*.py` / `claude_loop_lib/issues.py` を「そのまま Question 用に置き換えた並列コピー」として作る（ver15.0 scout 実装で確立した add-only precedent を踏襲）。共通ユーティリティへの抽象化は行わない — 抽象化は将来 3rd queue が現れた段階で検討し、本バージョンでは 2 queue を明示的に並存させる方針を取る（リスク R7 参照）。

## 設計の要点

### 1. workflow 入口の実装方針（`workflow.py` 変更）

`scripts/claude_loop_lib/workflow.py` への最小変更:

```python
# L12-18 付近
FULL_YAML_FILENAME = "claude_loop.yaml"
QUICK_YAML_FILENAME = "claude_loop_quick.yaml"
ISSUE_PLAN_YAML_FILENAME = "claude_loop_issue_plan.yaml"
SCOUT_YAML_FILENAME = "claude_loop_scout.yaml"
QUESTION_YAML_FILENAME = "claude_loop_question.yaml"   # 新規

RESERVED_WORKFLOW_VALUES = ("auto", "full", "quick", "scout", "question")  # "question" 追加
```

```python
# L32-51 resolve_workflow_value 内
    if value == "scout":
        return yaml_dir / SCOUT_YAML_FILENAME
    if value == "question":   # 新規分岐（scout と同型）
        return yaml_dir / QUESTION_YAML_FILENAME
    return Path(value).expanduser()
```

**`claude_loop.py` への変更は不要**。ver15.0 scout と同じ理由で、`resolved = resolve_workflow_value(...)` 以降の `_run_selected()` 一般経路（`if resolved == "auto"` の else）を question も通過するため。validation への影響も `_resolve_target_yamls()` の else 経由で吸収される。

**argparse help テキスト（L60）の扱い**: ver15.0 scout で更新しなかった precedent に従い、本バージョンでも更新しない。help の改善は別 ISSUE（R2 で MEMO に残す候補）として扱う。理由と先送り根拠は R2 参照。

### 2. `scripts/claude_loop_question.yaml` の骨格

```yaml
# NOTE: --workflow question で起動する opt-in 調査専用 workflow。
#       --workflow auto には自動混入しない（validation.py / claude_loop.py の auto 経路で選ばれない）。
#       The `command` / `defaults` sections must stay in sync with claude_loop.yaml,
#       claude_loop_quick.yaml, claude_loop_issue_plan.yaml, and claude_loop_scout.yaml.
#       Allowed `defaults`/`steps[]` override keys (string-typed):
#         model, effort, system_prompt, append_system_prompt

command:
  executable: claude
  prompt_flag: -p
  args:
    - --dangerously-skip-permissions
    - --disallowedTools "AskUserQuestion"

defaults:
  model: sonnet
  effort: medium

steps:
  - name: question_research
    prompt: /question_research
    model: opus
    effort: high
```

- 1 ステップのみ（調査は `question_research` SKILL 内で完結する設計。ISSUE 起票が必要になったら SKILL 内部で既存 `ISSUES/` flow に接続する）
- `defaults` の `model: sonnet` / `effort: medium` は 5 ファイル同期契約のため既存 4 ファイルと完全一致させる
- ステップ側で `model: opus` / `effort: high` にオーバーライド（scout と同様に、1 回の高価値判断を重視）

### 3. `.claude/skills/question_research/SKILL.md` の責務

**パス表記の注意**: `docs/util/ver15.0/IMPLEMENT.md` および `docs/util/MASTER_PLAN/PHASE7.1.md` L124-127 は `.claude/SKILLS/`（大文字）表記だが、実ディスク上は `.claude/skills/`（小文字）。Windows は大文字小文字を区別しないが Linux では区別されるため、`claude_sync.py` 経由で操作する際は必ず **小文字** の `.claude/skills/question_research/SKILL.md` を使うこと。

ver15.0 `issue_scout` SKILL と同型の frontmatter (`name` / `description` / `disable-model-invocation: true` / `user-invocable: true`)。本文は以下 7 節:

1. **コンテキスト** — `cat .claude/CURRENT_CATEGORY` / `bash .claude/scripts/get_latest_version.sh` / `date +%Y-%m-%d` / `python scripts/question_worklist.py --category $(cat .claude/CURRENT_CATEGORY)` で現状 queue を注入
2. **役割** — 調査専用であること（コード・テスト・デプロイ・`docs/{cat}/ver*/` 更新はしない。やらないことを明示列挙）
3. **調査手順（3 段階）** — (a) Question 1 件選定（`ready / ai` の最上位優先度）、(b) 証拠収集（関連ファイル Read・grep・既存 RETROSPECTIVE / MEMO 参照、必要ならサブエージェント並列実行）、(c) 結論・不確実性整理
4. **報告書の出力先と内容** — `docs/{カテゴリ}/questions/{slug}.md` に Markdown で出力。5 項目「問い」「確認した証拠（ファイル名 + 行番号）」「結論」「不確実性」「次アクション候補」を固定セクションとする。ファイル名 `slug` は Question 本体のファイル名と一致させる
5. **後処理ルール** — 完了時は Question を `QUESTIONS/{カテゴリ}/done/` へ移動。調査結果で実装課題が明確化した場合は新規 ISSUE を `ISSUES/{カテゴリ}/{priority}/` に起票し、Question 本文末尾にリンクを追記。人間の追加情報が必要な場合は Question を `need_human_action / human` に戻し、本文末尾に確認事項を追記。**結論不確実ケース**: 調査しても結論が出せなかった場合（情報不足で判断保留 / 追加調査に外部ツール必要 等）は、報告書の「結論」を「未確定」・「不確実性」に理由を詳述したうえで Question を `need_human_action / human` に戻し、本文末尾に「追加調査に必要な情報 / ツール / 権限」を列挙する。`done/` 移動は行わない（結論確定まで queue に残す）
6. **やらないこと** — コード修正 / テスト修正 / デプロイ / `QUESTIONS/` 以外の再配置 / `docs/{cat}/ver*/` バージョンフォルダ作成 / `.claude/` 編集
7. **Git コミット** — 「`docs(ver15.2): question_research による調査 ({slug})` + Question の `done/` 移動」を 1 コミットにまとめる。push はしない

`.claude/` 配下の編集は `scripts/claude_sync.py` export → edit → import の 3 ステップで行う（`.claude/rules/claude_edit.md`）。

### 4. `QUESTIONS/README.md` の規約

`ISSUES/README.md` を簡素化したコピー。次の 4 節:

1. **配置ルール** — `QUESTIONS/{category}/{high,medium,low}/{slug}.md`。完了後は `QUESTIONS/{category}/done/` へ移動
2. **frontmatter 仕様** —

   | キー | 値 | 必須 |
   |---|---|---|
   | `status` | `raw` \| `ready` \| `need_human_action` | ✓ |
   | `assigned` | `human` \| `ai` | ✓ |
   | `priority` | `high` \| `medium` \| `low`（ディレクトリと一致） | ✓ |
   | `reviewed_at` | `"YYYY-MM-DD"`（文字列クオート必須） | 任意（人間レビュー / AI ready 化の最終確認日付。`ISSUES/` と同用途。Question の "調査完了日" ではない — 調査完了日は報告書側に記載する） |

   有効 combos（ISSUES と違い `review` ステータスは持たない）:
   - `(raw, human)` — 人間が起票しただけ
   - `(raw, ai)` — AI が起票したが ready 化未実施
   - `(ready, ai)` — AI が調査可能な状態
   - `(need_human_action, human)` — 人間の確認待ち
3. **ISSUES との境界** — 「実装依頼 → ISSUES」「調査依頼（成果物が報告書）→ QUESTIONS」の判定フロー。既存 `auto` / `full` / `quick` / `scout` は `QUESTIONS/` を読まないことを明記
4. **報告書の配置** — `docs/{カテゴリ}/questions/{slug}.md` にリンクし、書式は `question_research/SKILL.md` §報告書 を一次資料とする旨を記載

### 5. `scripts/claude_loop_lib/questions.py` の骨格

`issues.py` の並列コピーで、`review` ステータスを除外する点のみが差分:

```python
"""Shared helpers for reading Question frontmatter."""

from __future__ import annotations

import sys
from pathlib import Path

from .frontmatter import parse_frontmatter

VALID_STATUS = {"raw", "ready", "need_human_action"}   # ISSUES と違い "review" なし
VALID_ASSIGNED = {"human", "ai"}

VALID_COMBOS = {
    ("raw", "human"),
    ("raw", "ai"),
    ("ready", "ai"),
    ("need_human_action", "human"),
}


def _warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)


def extract_status_assigned(path: Path) -> tuple[str, str, dict | None, str]:
    """Return (status, assigned, frontmatter, body) for a single QUESTION file.

    Fallbacks:
      - read error / no frontmatter / parse error -> ("raw", "human", None, text or "")
    Warnings are emitted to stderr for unknown status/assigned and invalid combos.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        _warn(f"{path}: read failed ({exc})")
        return "raw", "human", None, ""

    fm, body = parse_frontmatter(text)
    if fm is None:
        return "raw", "human", None, body

    status = str(fm.get("status", "raw"))
    assigned = str(fm.get("assigned", "human"))

    if status not in VALID_STATUS:
        _warn(f"{path}: unknown status '{status}'")
    if assigned not in VALID_ASSIGNED:
        _warn(f"{path}: unknown assigned '{assigned}'")
    if (status, assigned) not in VALID_COMBOS:
        _warn(f"{path}: invalid combo status={status}, assigned={assigned}")

    return status, assigned, fm, body
```

### 6. `question_status.py` / `question_worklist.py` の骨格

- **`question_status.py`**: `issue_status.py` をコピーして以下のみ差し替え:
  - `ISSUES_DIR` → `QUESTIONS_DIR = REPO_ROOT / "QUESTIONS"`
  - `from claude_loop_lib.issues import extract_status_assigned` → `from claude_loop_lib.questions import extract_status_assigned`
  - `DISPLAY_ORDER` から `("review", "ai")` を削除し 4 行に縮める
- **`question_worklist.py`**: `issue_worklist.py` をコピーして以下のみ差し替え:
  - `ISSUES_DIR` → `QUESTIONS_DIR` （変数名も整える）
  - import 先を `claude_loop_lib.questions` に変更（`VALID_ASSIGNED` / `VALID_STATUS` / `extract_status_assigned` すべて `claude_loop_lib.questions` から取得する。`_parse_status_list()` 内の `VALID_STATUS` 参照先も Question 用に切り替わることで、`--status review` を CLI から渡しても Question では拒否される）
  - 既定 `--status` を `ready,review` → `ready`（Question は review を持たない）
  - 警告文言の "issues" → "questions" 若干の文言調整
  - `format_text` 内の `"(no matching issues)"` → `"(no matching questions)"`、`"{total} issues"` → `"{total} questions"`

共通関数への抽象化はしない（R7 参照）。両ファイルは「並列に存在し diff で同期を確認できる」状態を維持する。

### 7. `.claude/skills/issue_plan/SKILL.md` への最小追記

`/issue_plan` が `QUESTIONS/` を誤って扱わないことを明示する 1 段落を追記する。挿入位置は SKILL 本文の「やらないこと」あるいは冒頭の「役割」近辺（実装時に SKILL の既存構造を確認してから確定する）:

> `QUESTIONS/` 配下の Question は本 SKILL の対象外（`question_research` 専属 queue）。ISSUE レビュー・候補選定・plan 作成のいずれのステップでも `QUESTIONS/` を走査・変更しないこと。

### 8. `.claude/skills/imple_plan/SKILL.md` と `quick_impl/SKILL.md` への追記（付随 ISSUE 10a 消化）

両 SKILL に以下の趣旨を追記する。挿入位置は各 SKILL の「実装品質ガイドライン」または「実装」節末尾:

> **ワークフロー YAML 同期チェック**: `scripts/claude_loop*.yaml` を新規追加・削除した場合は、以下の全ファイルを同期更新する:
> - `.claude/rules/scripts.md` §3 の「N ファイル間で同一内容を保つ」記述（ファイル数と列挙）
> - `scripts/USAGE.md` L137 付近の 4 ファイル同期契約記述
> - `scripts/README.md` の「ワークフロー実行」ファイル一覧テーブル
> - 既存ワークフロー YAML 先頭 NOTE コメントの相互参照一覧

`quick_impl` 用はさらに短縮したリスト箇条書き版にする（quick は詳細ガイドラインを持たない設計のため）。

### 9. `.claude/rules/scripts.md` §3 の更新

L24 を次のように更新する:

```
- `claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` / `claude_loop_scout.yaml` / `claude_loop_question.yaml` の `command` / `defaults` セクションは 5 ファイル間で同一内容を保つ
```

### 10. `scripts/README.md` / `scripts/USAGE.md` の更新

- **README L17-25** ファイル一覧テーブル: scout 行と question 行を追加（scout 追加は付随 ISSUE 10b の消化）
- **README 末尾付近**: 既存 scout 節（L98-112）の直後に「question（調査専用）」節を 15 行程度で追記。起動例 / 1 ステップのみ実施 / auto 非混入 / `QUESTIONS/` 起点 / 推奨頻度（アドホック）
- **USAGE.md L137**: 「4 ファイル」→「5 ファイル」、列挙に question を追加
- **USAGE.md L141-164**: サンプル YAML 一覧の最後に question を追加。YAML 抜粋は scout と同型で 1 ステップ分のみ
- **USAGE.md 末尾**: 短い「`QUESTIONS/` と `ISSUES/` の違い」段落を追加（実装依頼 vs 調査依頼の判定フロー。1 段落 5 行程度）

### 11. 実装順序と作業ステップ（順序固定）

0. **事前確認**（grep / Read）:
   - `RESERVED_WORKFLOW_VALUES` の参照箇所を grep（`workflow.py` 以外で参照していないか確認）
   - `claude_loop.py` L338 付近で `resolved = resolve_workflow_value(...)` の戻り値を検索し、ver15.0 からの構造変化がないか確認
   - **`claude_loop.py` の `_run_auto()` 内部に YAML ファイル一覧のハードコード走査がないか grep 確認**（`FULL_YAML_FILENAME` / `QUICK_YAML_FILENAME` / `ISSUE_PLAN_YAML_FILENAME` の使用箇所を特定し、question YAML が auto 経路に混入する余地がないことを明示的に保証する）
   - `.claude/skills/` が小文字ディレクトリであることを再確認（`ls .claude/skills/`）
   - `pytest scripts/tests/ -q` または `python -m unittest discover scripts/tests` で現状グリーン確認
1. `scripts/claude_loop_lib/workflow.py` に `QUESTION_YAML_FILENAME` / `RESERVED_WORKFLOW_VALUES` 追加 / `resolve_workflow_value` 分岐追加
2. `scripts/claude_loop_question.yaml` を新規作成（5 ファイル同期契約を守る）
3. `scripts/claude_loop_lib/questions.py` を新規作成（`issues.py` 並列コピー）
4. `scripts/question_status.py` / `scripts/question_worklist.py` を新規作成
5. `QUESTIONS/README.md` / `QUESTIONS/util/{high,medium,low,done}/.gitkeep` を新規作成
6. `.claude/skills/question_research/SKILL.md` を新規作成（claude_sync.py 経由: export → write → import）
7. `.claude/skills/issue_plan/SKILL.md` / `imple_plan/SKILL.md` / `quick_impl/SKILL.md` を変更（同 claude_sync.py 経由）
8. `.claude/rules/scripts.md` §3 を 5 ファイル表記に更新（同 claude_sync.py 経由）
9. `scripts/README.md` / `scripts/USAGE.md` を変更（scout 行の追加 + question 行の追加）
10. `scripts/tests/test_workflow.py` / `test_validation.py` を変更し、新規 `test_questions.py` / `test_question_worklist.py` を追加
11. `pytest scripts/tests/ -q` で全件グリーン確認
12. `python scripts/claude_loop.py --workflow question --dry-run` 相当で起動パスを smoke 確認（既に `--dry-run` がある場合のみ。なければ 13 へ）
13. 付随 ISSUE 2 件を `ISSUES/util/done/` に移動（`git mv`）
14. `--workflow question` の実行 smoke は `/wrap_up` ステップに委譲（本 IMPLEMENT では計画のみ、実走は後続）

## リスク・不確実性

| # | リスク | 影響 | 抑制策 | MEMO.md で確認する項目 |
|---|---|---|---|---|
| R1 | `RESERVED_WORKFLOW_VALUES` タプルと `resolve_workflow_value` の if-chain がドリフトする（tuple は documentational だが将来の追加時に片方更新漏れ） | 将来の新 workflow 追加時に挙動不整合が静かに発生 | drift-guard テストを `test_workflow.py` に追加: `RESERVED_WORKFLOW_VALUES` の各要素について `resolve_workflow_value(v, d)` が文字列 `"auto"` または `Path` を返すことを assert | drift-guard テストが追加されたか |
| R2 | `claude_loop.py` の argparse `--workflow` help テキストが `scout` / `question` を列挙しない（L60） | ユーザーが `--help` から新 workflow に気付かない | ver15.0 precedent に従い本バージョンでは更新しない。代わりに MEMO.md で「help テキスト改善は別 ISSUE 候補」と残す | help 更新を先送りした理由を記載 |
| R3 | `scripts/tests/test_workflow.py` L278 の docstring が「3 shipped workflow YAMLs」のまま古い | 将来の読み手が誤解する | 本バージョンで "all shipped workflow YAMLs" に更新する（1 行修正） | docstring 更新が適用されたか |
| R4 | Question frontmatter の `review` ステータス不在が将来の運用で不便になる可能性（AI が raw → ready に昇格させる中間状態が欲しくなる等） | Question 運用が歪む | 本バージョンでは PHASE7.1 §2-1 の仕様（`raw / ready / need_human_action`）を厳守し、将来の拡張は別 ISSUE で検討 | 運用後に `review` 不在で困った事例がないか |
| R5 | `QUESTIONS/` 空ディレクトリを git に残すための `.gitkeep` 4 件の placement が散らかる | リポジトリ整理上の負債 | カテゴリ単位で `util/` だけ作成し、`app/` / `infra/` / `cicd/` は未作成で開始する（ディレクトリは必要時に追加） | 他カテゴリ利用時の運用感 |
| R6 | `question_research` SKILL の調査報告書が未定義の `docs/{category}/questions/` ディレクトリに書き込もうとする | 初回実行時にディレクトリ欠如でエラー | SKILL 本文で「初回実行時はディレクトリ作成を含める」ことを明示する。または本 IMPLEMENT 実装時に `docs/util/questions/.gitkeep` を先行作成する（後者採用） | 初回実行時のエラー有無 |
| R7 | `questions.py` / `question_status.py` / `question_worklist.py` が `issues.py` / `issue_status.py` / `issue_worklist.py` と 90%以上同一のコピーになり、将来 3rd queue 登場時の抽象化リファクタ負債が発生する | 将来的な DRY 負担 | 本バージョンでは add-only を優先（ver15.0 scout precedent）。抽象化の検討時期は「3rd queue が登場したとき」を明示して MEMO に残す | 抽象化判断のトリガー条件 |
| R8 | `--workflow question` の smoke 実行時、`ready / ai` の Question がゼロで何もできず終了する（初期状態） | 初回実行が実質ノーオペで検収不明 | 本 IMPLEMENT では smoke を `/wrap_up` に委譲し、最低 1 件のサンプル Question（運用検証用）を本バージョン内で投入するか否かを `/wrap_up` で判断する | サンプル Question 投入の要否と判断根拠 |
| R9 | `.claude/` 配下の複数 SKILL / rules 同時編集を `claude_sync.py` export → edit → import で行う際、export から import までの間に他プロセスが `.claude/` を触るとコンフリクトが起きる | コミット時に予期しない差分 | ステップ 6〜8 を 1 回の export → 全編集 → 1 回の import にまとめる | import 後の `git diff` を目視確認したか |
| R10 | 付随 ISSUE 2 件の `done/` 移動時、`git mv` が Windows の大文字小文字混在で失敗する可能性 | ISSUE 移動が不完全になる | `git mv` で実施し、失敗した場合は `git rm` + `git add` の 2 段で fallback | mv が成功したか |

## テスト方針

### ユニットテスト追加

- **`scripts/tests/test_workflow.py`**（変更、3 メソッド + 1 import 追加）:
  - import 追加: `QUESTION_YAML_FILENAME`（L10-18 のブロック）
  - `TestResolveWorkflowValue` に `test_resolve_question_returns_question_yaml_path` を追加（scout テストと同型、fake Path で十分）
  - `TestYamlSyncOverrideKeys` に `test_question_yaml_uses_only_allowed_keys` を追加（実 YAML ロードして `get_steps` + `resolve_defaults` 成功を assert）
  - **drift-guard** `test_reserved_values_match_resolve_workflow_if_chain` を追加: `RESERVED_WORKFLOW_VALUES` の各要素について `resolve_workflow_value(v, Path("/x"))` が `"auto"` または `Path` を返すことを assert（単一 TypeError / unreachable で将来の追加漏れを検知）
  - `TestYamlSyncOverrideKeys` の docstring「3 shipped workflow YAMLs」→「all shipped workflow YAMLs」に更新（R3）
- **`scripts/tests/test_validation.py`**（変更、1 メソッド追加）:
  - `TestValidateStartupExistingYamls` に question YAML の存在検査を追加（scout と同型）
- **`scripts/tests/test_questions.py`**（新規、4〜5 メソッド）:
  - `test_extract_status_assigned_valid_ready_ai`
  - `test_extract_status_assigned_review_warned` — `review` 値を含む frontmatter で警告が stderr に出ることを assert（Question は review を許可しないため、既存 ISSUES/ と明確に差別化）
  - `test_extract_status_assigned_missing_frontmatter_fallback`
  - `test_extract_status_assigned_invalid_combo_warned`
  - `test_extract_status_assigned_read_error_fallback`
- **`scripts/tests/test_question_worklist.py`**（新規、5〜6 メソッド）:
  - tempdir + `patch.object(question_worklist, "REPO_ROOT", ...)` / `patch.object(question_worklist, "QUESTIONS_DIR", ...)` でモジュールレベル定数を差し替え（`test_issue_worklist.py` と同型手順。`importlib.reload` は使わない）
  - `test_default_status_is_ready_only`（`issue_worklist` と違い `review` を含まない）
  - `test_filter_by_category`
  - `test_priority_frontmatter_mismatch_warns`
  - `test_limit_truncates_and_reports_total`
  - `test_json_output_schema`

### 手動確認

- ステップ 12 で `python scripts/claude_loop.py --workflow question` を実行し、YAML ロード → ステップ開始直前までの dispatch が成功することを確認（実走はしない）
- `python scripts/question_status.py util` 実行し、空 queue で空ブロックが表示されること
- `python scripts/question_worklist.py --category util` 実行し、`(no matching questions)` が返ること

### 回帰確認

- `pytest scripts/tests/ -q`（または `python -m unittest discover scripts/tests -v`）で全件グリーン
- `--workflow auto` 経路のテストが引き続き 4 YAML（既存 auto 経路の scope）のみを参照すること（question YAML が auto に自動混入していないことの技術的保証）
- `npx nuxi typecheck` は Python 変更のため影響なし（実行は念のため）
- `ISSUES/util/medium/imple-plan-four-file-yaml-sync-check.md` / `ISSUES/util/low/readme-workflow-yaml-table-missing-scout.md` が `done/` に移動していることを `ls ISSUES/util/done/` で確認

## スコープ外（念のため明示）

- PHASE7.1 §3（`ROUGH_PLAN.md` / `PLAN_HANDOFF.md` 分離）— ver15.3 以降で扱う
- PHASE7.1 §4（run 単位通知）— ver15.4 以降で扱う
- `QUESTIONS/app/` / `QUESTIONS/infra/` / `QUESTIONS/cicd/` 配下のカテゴリ別骨格作成（utility のみ初期整備）
- `docs/{category}/questions/` の配下骨格作成（`docs/util/questions/.gitkeep` のみ先行作成、他カテゴリは初回実行時）
- `question_research` による実際の調査実行（実走は `/wrap_up` または後続運用で発生）
- 外部通知連携（Slack / Discord）
- `auto` / `full` / `quick` / `scout` workflow への `question` 自動混入
- `issue-review-rewrite-verification.md` の消化（`app` / `infra` 起動待ち、継続持ち越し）
- ver14.0 持越し 2 件（`rules-paths-frontmatter-autoload-verification.md` / `scripts-readme-usage-boundary-clarification.md`）の消化
- `docs/util/MASTER_PLAN/PHASE7.1.md` §2 進捗表更新（`/wrap_up` または `/write_current` ステップの責務）
- `questions.py` と `issues.py` の共通化リファクタ（R7 参照、3rd queue 登場時点で再検討）

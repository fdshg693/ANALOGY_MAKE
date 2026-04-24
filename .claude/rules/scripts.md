---
paths:
  - "scripts/**/*"
---

`scripts/` 配下（`claude_loop.py` / `claude_loop_lib/` / `issue_*.py` / `claude_sync.py` など）を編集・追加する際に毎回守るべき stable な規約を集約する。詳細仕様・運用上の背景・変更履歴は `scripts/README.md` / `scripts/USAGE.md` を一次資料とする（本 rule に重複して書かない）。

## 1. Python 前提

- Python 3.10+ を前提にする。型ヒントは PEP 604 形式（`str | None`）を使い、`Optional[...]` / `Union[...]` を新規コードに持ち込まない
- 依存は標準ライブラリと PyYAML のみ。dataclass・pydantic・requests 等の 3rd-party 依存や dataclasses モジュールの新規使用を増やさない
- 例外・通知・ログなど周辺ユーティリティは `claude_loop_lib/` 配下の既存モジュールを再利用する

## 2. パス操作

- `pathlib.Path` を使う。文字列連結・`os.path.join` は新規コードで使わない
- 相対パスは `Path(__file__).resolve().parent` を起点に組み立てる（CWD 依存のパスを避ける）
- プロジェクトルート配下の固定パスは `claude_loop_lib/` 内の既存定数・ヘルパを優先して参照する

## 3. CLI 引数処理

- 引数パースは `argparse` を使う。新規オプションを追加する場合は `claude_loop.py` の `parse_args()` と、その値を渡す先（多くは `claude_loop_lib/commands.py` の `build_command`）の両方を更新する
- 廃止オプションを黙って無視しない。argparse レベルで落とすか、`claude_loop_lib/validation.py` で明示的に拒否する
- `claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` / `claude_loop_scout.yaml` / `claude_loop_question.yaml` の `command` / `defaults` セクションは 5 ファイル間で同一内容を保つ

## 4. frontmatter / YAML 更新時の作法

- frontmatter の読み書きは `claude_loop_lib/frontmatter.py` の `parse_frontmatter` を共通基盤として使う（独自に再定義しない）
- ISSUE の frontmatter（`status` / `assigned`）を扱うときは `claude_loop_lib/issues.py` の共通定数（`VALID_STATUS` / `VALID_ASSIGNED`）を参照する
- Question の frontmatter を扱うときは `claude_loop_lib/questions.py` の共通定数（`VALID_STATUS` / `VALID_ASSIGNED` / `VALID_COMBOS`）を参照する。`issues.py` と異なり `review` ステータスは持たない点に注意
- ワークフロー YAML の新しい override キーを追加する場合は、必ず `claude_loop_lib/workflow.py` の定数（`ALLOWED_STEP_KEYS` / `ALLOWED_DEFAULTS_KEYS` / `OVERRIDE_STRING_KEYS`）を起点に拡張し、`claude_loop_lib/validation.py` の検査経路を通す

## 5. ログ出力

- `print()` を直接使わず、`claude_loop_lib/logging_utils.py` の `TeeWriter` / `print_step_header` / `format_duration` を使う
- ログファイル名は `{YYYYMMDD_HHMMSS}_{workflow_stem}.log` 規約（`create_log_path` が生成）を維持する。新規ログ出力先を増やす場合も同規約に従う

---

**参照先**: 上記各項目の「なぜそうするか」「どこまで詳細か」は `scripts/README.md`（全体構成・validation 仕様）および `scripts/USAGE.md`（CLI オプション・ワークフロー継承ルール・拡張手順）を一次資料とする。rule 本文と食い違いがあった場合は docs 側が優先。

# ver4.1 IMPLEMENT

ROUGH_PLAN.md の 3 つのスコープ（README 新規作成 / `claude_loop.py` 分割 / 既存テスト追従）を実装する計画。機能変更はゼロ、純粋なコード整理とドキュメント追加のみ。

## 1. 分割後のファイル構成

```
scripts/
├── README.md                         # 新規（人間向けの使用方法・YAML仕様）
├── claude_loop.py                    # 分割後：CLI エントリ（parse_args / main / _run_steps）
├── claude_loop_lib/                  # 新規パッケージ
│   ├── __init__.py                   # 空でよい（明示的な再エクスポートは行わない）
│   ├── workflow.py                   # YAML ロード・バリデーション・ステップ/設定抽出
│   ├── feedbacks.py                  # frontmatter 解析・ロード・消費
│   ├── commands.py                   # build_command, iter_steps_*
│   ├── logging_utils.py              # TeeWriter, create_log_path, print_step_header, format_duration
│   ├── git_utils.py                  # get_head_commit, check_uncommitted_changes, auto_commit_changes
│   └── notify.py                     # notify_completion, _notify_toast, _notify_beep
└── claude_sync.py                    # 無変更
```

パッケージ名は `claude_loop_lib`（スクリプト本体と区別しやすく、Python stdlib の `logging` 等と衝突しない）。`__init__.py` は空にし、利用側は `from claude_loop_lib.workflow import ...` のように明示インポートさせる（再エクスポートを避け、「どの関数がどのモジュールにあるか」をインポート文から読み取れるようにする）。

## 2. 各モジュールへの関数割当

元 `scripts/claude_loop.py` 698 行の関数・クラスを以下のモジュールに移す。

### `claude_loop.py`（エントリ専用、~200 行想定）

- モジュール先頭の `DEFAULT_WORKFLOW_PATH` / `DEFAULT_WORKING_DIRECTORY` 定数
- `positive_int`（argparse バリデータ）
- `parse_args`
- `main`
- `_run_steps`
- `if __name__ == "__main__": raise SystemExit(main())`

`main` / `_run_steps` は現行コードで以下の stdlib を直接使用しているため、`claude_loop.py` のインポートにこれらを残す（**忘れやすいので明示**）:

```python
import argparse
import shlex         # _run_steps の shlex.join(command)
import shutil        # main の shutil.which(executable)
import subprocess    # _run_steps の subprocess.Popen / subprocess.run
import sys           # main / _run_steps のエラー出力（sys.stderr）
import time          # main / _run_steps の time.monotonic
from datetime import datetime  # _run_steps のタイムスタンプ
from pathlib import Path
from typing import Any
```

他モジュールから必要な関数/クラスを明示的にインポートする:

```python
from claude_loop_lib.workflow import (
    load_workflow, get_steps, resolve_defaults,
    resolve_command_config, resolve_mode,
)
from claude_loop_lib.feedbacks import load_feedbacks, consume_feedbacks
from claude_loop_lib.commands import (
    build_command, iter_steps_for_loop_limit, iter_steps_for_step_limit,
)
from claude_loop_lib.logging_utils import (
    TeeWriter, create_log_path, print_step_header, format_duration,
)
from claude_loop_lib.git_utils import (
    get_head_commit, check_uncommitted_changes, auto_commit_changes,
)
from claude_loop_lib.notify import notify_completion
```

### `claude_loop_lib/workflow.py`

`load_workflow` / `normalize_string_list` / `normalize_cli_args` / `get_steps` / `resolve_defaults` / `resolve_command_config` / `resolve_mode`

- 依存: `yaml`, `shlex`, `Path`, `Any`
- `normalize_string_list` は現状 `claude_loop.py` 内で未使用だが、将来利用を見据えて公開 API として残す（削除しない）

### `claude_loop_lib/feedbacks.py`

`parse_feedback_frontmatter` / `load_feedbacks` / `consume_feedbacks`

- 依存: `yaml`, `shutil`, `Path`

### `claude_loop_lib/commands.py`

`build_command` / `iter_steps_for_loop_limit` / `iter_steps_for_step_limit`

- 依存: `Any` のみ（外部ライブラリなし）

### `claude_loop_lib/logging_utils.py`

`TeeWriter` / `create_log_path` / `print_step_header` / `format_duration`

- 依存: `io`, `subprocess`, `datetime`, `Path`
- **重要**: `create_log_path` 内で `datetime.now()` を呼ぶため、テストでのモックは `claude_loop_lib.logging_utils.datetime` をパッチ対象にする

### `claude_loop_lib/git_utils.py`

`get_head_commit` / `check_uncommitted_changes` / `auto_commit_changes`

- 依存: `subprocess`, `Path`

### `claude_loop_lib/notify.py`

`notify_completion` / `_notify_toast` / `_notify_beep`

- 依存: `subprocess`

### 前提条件セクション（README の最初に置く）

README のクイックスタートの直前に、Python バージョンと PyYAML の前提を 3〜4 行で明示する。現行 `claude_loop.py` 17〜22 行目の `try/except ImportError` エラーメッセージ（`python -m pip install pyyaml`）と整合させる。プロジェクト全体の Python バージョン方針が `CLAUDE.md` 等に明示されていないため、README では「PyYAML が入っていれば動く」「標準ライブラリは Python 3.10+ を想定」と書く程度に留める。

## 3. scripts/README.md の構成

対象読者: 本プロジェクトの開発者（自分自身含む）。`scripts/` を開いて何がどう動くかを即座に把握できるレベルを目指す。

```
# scripts/ — Claude ワークフロー自動化

## これは何か
（1段落で目的を記述）

## ファイル一覧
（表形式: 各ファイルの役割を1行）

## クイックスタート
 - フルワークフロー実行
 - quick ワークフロー実行
 - ログ無効 / dry-run / auto モード
 - 各 CLI オプションの対応付け

## CLI オプション一覧
（表形式: name, short, type, default, 説明）

## YAML ワークフロー仕様
 - 4 セクション（mode / command / defaults / steps）の意味
 - ステップ単位の上書きルール（キー存在ベース、None は未指定扱い）
 - defaults の有無と後方互換
 - フル/quick の実物 YAML へのリンク

## フル/quick の使い分け
（ROUGH_PLAN と CURRENT.md のガイドラインを集約、4〜6 行の表）

## フィードバック注入機能
 - FEEDBACKS/ ディレクトリの役割
 - frontmatter の step フィールドの書き方（string/list/省略）
 - 消費後の done/ 移動

## ログフォーマット
 - workflow header / step header / footer の構造
 - ログパスの命名規則（timestamp + workflow stem）

## claude_sync.py
 - `.claude/` を -p モードで編集するためのワークアラウンド
 - export / import の使い方

## 拡張ガイド
 - 新しい SKILL を追加する場合 → YAML の steps に追記
 - Python コードを拡張する場合 → claude_loop_lib/ 配下のどのモジュールに手を入れるか
 - 新規オプション追加 → parse_args と build_command の両方を触る

## 関連ドキュメント
 - docs/util/MASTER_PLAN.md
 - docs/util/ver{最新}/CURRENT.md（インデックス）
 - docs/util/ver{最新}/CURRENT_scripts.md（詳細）
```

現状 `CURRENT_scripts.md` に書いてある内容のうち、**ユーザー視点で必要な情報**を README に移し、**内部状態の詳細**（各関数の行番号や実装のステップごとの流れ）は CURRENT 側に残す。write_current ステップで ver4.1 の CURRENT を書き直す際、この重複判定を前提にコピペではなく整理した形で反映する（今回の IMPLEMENT では write_current の作業は対象外）。

## 4. 既存テストの更新方針

### インポート更新

`tests/test_claude_loop.py` 冒頭の `from claude_loop import (...)` を、分割後の各モジュールからのインポートに置き換える:

```python
from claude_loop import parse_args
from claude_loop_lib.workflow import (
    load_workflow, get_steps, resolve_defaults,
    resolve_command_config, resolve_mode,
)
from claude_loop_lib.feedbacks import (
    parse_feedback_frontmatter, load_feedbacks, consume_feedbacks,
)
from claude_loop_lib.commands import build_command
from claude_loop_lib.logging_utils import (
    create_log_path, format_duration,
)
from claude_loop_lib.git_utils import (
    get_head_commit, check_uncommitted_changes, auto_commit_changes,
)
from claude_loop_lib.notify import notify_completion, _notify_toast
```

### パッチターゲット更新

`@patch("claude_loop.X")` 形式のパッチを、実際にその関数/モジュールが import されている場所に付け替える。置換のルール:

| 現行パッチ | 新パッチ | 備考 |
|---|---|---|
| `@patch("claude_loop.datetime")` | `@patch("claude_loop_lib.logging_utils.datetime")` | `create_log_path` 内の `datetime.now()` |
| `@patch("claude_loop.subprocess.run")` ※git系 | `@patch("claude_loop_lib.git_utils.subprocess")` | `get_head_commit` / `check_uncommitted_changes` / `auto_commit_changes` 内 |
| `@patch("claude_loop.subprocess.run")` ※notify系 | `@patch("claude_loop_lib.notify.subprocess")` | `_notify_toast` 内（TestNotifyCompletion の toast escape テスト等） |
| `@patch("claude_loop._notify_toast")` | `@patch("claude_loop_lib.notify._notify_toast")` | `notify_completion` 内の呼び出し |
| `@patch("claude_loop._notify_beep")` | `@patch("claude_loop_lib.notify._notify_beep")` | 同上のフォールバック確認 |
| `@patch("claude_loop.notify_completion")` | `@patch("claude_loop_lib.notify.notify_completion")` | main() レベルでの呼び出し検証 |
| `@patch("claude_loop.get_head_commit")` | `@patch("claude_loop_lib.git_utils.get_head_commit")` | `auto_commit_changes` が `get_head_commit` を関数として呼んでいる箇所（`@patch` は呼び出し元の名前空間に向ける必要があるが、今回は `git_utils` 内部での相互呼び出しのため `git_utils.get_head_commit` でよい） |
| `@patch("claude_loop.shutil")` | `@patch("claude_loop_lib.feedbacks.shutil")` | `consume_feedbacks` 内の `shutil.move` |

**実装時のチェックリスト**: 書き換え後に `python -m unittest tests.test_claude_loop -v` を実行し、`subprocess` 系と `get_head_commit` 系は特に確認。上記の `subprocess.run` は現行コードで **git 系と notify 系の 2 つのモジュールに分散する** 点、および `auto_commit_changes → get_head_commit` の相互呼び出しはパッチ先を `git_utils.get_head_commit` に向ける点が漏れやすい。

**注意**: `@patch` の対象は「関数が使われている場所（モジュール名前空間）」であり、「関数が定義されている場所」ではない。一方、以下の2種類に分けて判断する:

- `module.function` 形式で呼び出されるもの（例: `subprocess.run`）→ テスト対象関数があるモジュールの名前空間をパッチ（例: `claude_loop_lib.git_utils.subprocess`）
- `from module import function` で取り込んでいるもの → import された先をパッチ

現行テストは `datetime` / `shutil` / `subprocess` を `import datetime` / `import shutil` / `import subprocess` 形式で取り込んでいるため、**パッチターゲットは「呼び出し元モジュール名.モジュール名」形式**になる。

### `parse_args` テスト

`parse_args` は `claude_loop.py` に残るため `from claude_loop import parse_args` のままでよい。ただし `sys.path.insert` で `scripts/` を先頭に入れている構造は維持する必要がある（`claude_loop` / `claude_loop_lib` の両方がそこから見える）。

### テストクラス再編

パッチ対象のモジュールが複数に分散するため、テストクラスの順序を「モジュール単位でグルーピング」した方が読みやすい。ただし実質的なテストコード書き換えではなく並べ替えなので、今回はオプショナル（やらなくても合格）。

### テスト件数

**89 件を減らさない**。パッチターゲットの書き換えのみで済むはずなので、すべて現行と同じアサーションを維持する。

## 5. 作業順序

1. **パッケージ骨組み作成**: `scripts/claude_loop_lib/__init__.py` を作成（空）
2. **関数移動（機能単位で 1 モジュールずつ）**: 依存の少ない順に移す。順序の一例:
   1. `git_utils.py`（他モジュールに依存しない）
   2. `notify.py`（同上）
   3. `logging_utils.py`（同上）
   4. `feedbacks.py`（同上）
   5. `commands.py`（同上）
   6. `workflow.py`（同上）
3. **`claude_loop.py` の縮小**: 残すのは `parse_args` / `main` / `_run_steps` / 定数 / `positive_int` のみ。他は削除し、明示 import に置き換える
4. **テスト修正**: インポートとパッチターゲットを新構成に追従
5. **動作確認**:
   - `python -m unittest tests.test_claude_loop` → 89 件グリーン
   - `python scripts/claude_loop.py --dry-run --no-log` → ver4.0 と同じコマンド出力
   - `python scripts/claude_loop.py -w scripts/claude_loop_quick.yaml --dry-run --no-log` → 同上
6. **README 作成**: 上記構成案に従って `scripts/README.md` を書く。ver4.0 `CURRENT_scripts.md` と `CURRENT.md` から必要箇所を抽出・再構成（そのままコピペはしない）

各ステップごとに `python -m unittest tests.test_claude_loop` を通すチェックポイントを設けると差分追跡が容易。

## 6. 機能不変の検証

**必須検証項目**:

- `python -m unittest tests.test_claude_loop`: 89 tests passed
- `python scripts/claude_loop.py --dry-run --no-log` の標準出力: ver4.0 の出力と 1 行単位で一致（ステップヘッダ・コマンド文字列・`Model: ..., Effort: ...` 行・ワークフロー完了メッセージ）
- `python scripts/claude_loop.py -w scripts/claude_loop_quick.yaml --dry-run --no-log`: 同上
- `npx nuxi typecheck`: 既知警告のみ（Python/YAML 変更は TS に影響しない想定）

**差分比較手順**:

```bash
# ver4.0 時点の出力を保存（現在のコードで一度実行）
python scripts/claude_loop.py --dry-run --no-log > /tmp/before_full.txt
python scripts/claude_loop.py -w scripts/claude_loop_quick.yaml --dry-run --no-log > /tmp/before_quick.txt

# 分割後に実行して diff
python scripts/claude_loop.py --dry-run --no-log > /tmp/after_full.txt
diff /tmp/before_full.txt /tmp/after_full.txt  # 空であるべき
python scripts/claude_loop.py -w scripts/claude_loop_quick.yaml --dry-run --no-log > /tmp/after_quick.txt
diff /tmp/before_quick.txt /tmp/after_quick.txt  # 空であるべき
```

本実装の冒頭で `before_*.txt` を生成しておけば、各段階の移動作業中もすぐに diff で確認できる。

## 7. リスク・不確実性

### 7-1. パッチターゲットの付け替え漏れ

`@patch("claude_loop.X")` 形式のパッチが 89 件のうち多数に散らばっている。自動置換では誤爆しやすいため、**1 件ずつターゲット関数のありかを確認しながら書き換える**。対応付け表（上述の「パッチターゲット更新」節）を実装時にチェックリスト化する。

**検証**: 書き換え後に `python -m unittest tests.test_claude_loop -v` を実行し、失敗したテストのモック挙動を個別に見ればパッチ漏れは即判明する。

### 7-2. 相対パス / パッケージ初期化の挙動

`python scripts/claude_loop.py ...` 実行時は `sys.path[0]` が `scripts/` になるため、`from claude_loop_lib.workflow import ...` が解決できる。テスト側も `sys.path.insert(0, "scripts")` を維持しているため同様に解決できる。**ただし手動実行と pytest 実行で挙動が揃っているか念のため `--dry-run` で確認**する。

**検証**: 作業順序 5 の動作確認で異常があれば判明。

### 7-3. `claude_loop_lib/__init__.py` を空にした場合の副作用

空の `__init__.py` は、Python 3.3+ の namespace package と通常 package の差異で問題になることがある（今回は明示的に `__init__.py` を置くので通常 package として扱われ問題なし）。**スペース的にファイルを空にするのが最もシンプル**。

### 7-4. README と CURRENT の二重管理

README に書いた内容が、write_current ステップで書かれる `docs/util/ver4.1/CURRENT_scripts.md` と重複する恐れがある。**対策**: 今回の IMPLEMENT.md 範囲では README のみを作成。`write_current` ステップで CURRENT を書く際に、「README にある内容は CURRENT から削る（重複させない）」のルールに従って調整する。方針は ROUGH_PLAN に既に書いてあるため write_current 側の SKILL が自然に処理できる。

### 7-5. wrap_up / write_current / retrospective 側への影響

本 IMPLEMENT で完了するのは「コード分割 + テスト追従 + README 作成」まで。ドキュメント更新（CURRENT の全面書き換え、MASTER_PLAN の PHASE 状態更新）は後続ステップに委ねる。本 IMPLEMENT でドキュメントに勝手に手を入れすぎない。

## 8. 完了条件（IMPLEMENT 範囲）

- [ ] `scripts/claude_loop_lib/` が作成され、6 モジュール + `__init__.py` が配置されている
- [ ] `scripts/claude_loop.py` が ~200 行程度に縮小されている（エントリ専用）
- [ ] `scripts/README.md` が作成され、「3. scripts/README.md の構成」の全セクションを含む
- [ ] `tests/test_claude_loop.py` のインポート・パッチターゲットが新構成に追従し、89 件グリーン
- [ ] `--dry-run --no-log` による出力が ver4.0 と完全一致
- [ ] `claude_sync.py` / YAML 2 ファイルには変更なし（意図しない改変がないことを diff で確認）

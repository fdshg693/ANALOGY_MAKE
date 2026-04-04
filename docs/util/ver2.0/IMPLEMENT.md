# IMPLEMENT: util ver2.0

事前リファクタリング不要。既存の関数構造を維持したまま、ログ機能を追加する。

## 変更対象ファイル

| ファイル | 操作 | 内容 |
|---|---|---|
| `scripts/claude_loop.py` | 変更 | ログ出力・コミット記録・ログパス共有の実装 |
| `scripts/claude_loop.yaml` | 変更なし | 今回は YAML 構造の変更なし |
| `.gitignore` | 変更なし | `logs` は追加済み |

## 1. CLI オプションの追加

`parse_args()` に以下のオプションを追加する:

```python
parser.add_argument(
    "--log-dir",
    type=Path,
    default=Path("logs/workflow"),
    help="Directory for workflow log files (default: logs/workflow/)",
)
parser.add_argument(
    "--no-log",
    action="store_true",
    help="Disable log file output",
)
```

## 2. ログファイルの初期化

### ログファイルパスの生成

`main()` 内で、ワークフロー実行開始時にログファイルを初期化する。

```python
def create_log_path(log_dir: Path, workflow_path: Path) -> Path:
    """Generate timestamped log file path."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workflow_name = workflow_path.stem  # e.g. "claude_loop"
    log_dir = log_dir.resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{timestamp}_{workflow_name}.log"
```

### ログ書き込みユーティリティ

ファイルと端末の両方に書き出すヘルパー:

```python
import io

class TeeWriter:
    """Write to both a file and stdout simultaneously."""

    def __init__(self, log_file: io.TextIOWrapper):
        self.log_file = log_file

    def write_line(self, line: str) -> None:
        """Write a line to both stdout and log file."""
        print(line)
        self.log_file.write(line + "\n")
        self.log_file.flush()

    def write_process_output(self, process: subprocess.Popen) -> int:
        """Stream process stdout/stderr to both stdout and log file.
        Returns the process exit code."""
        # stdout と stderr を統合して読み取る
        # Popen で stdout=PIPE, stderr=STDOUT を指定し、
        # stdout から1行ずつ読みながら端末とファイルに書き出す
        for raw_line in process.stdout:
            line = raw_line.decode("utf-8", errors="replace").rstrip("\n\r")
            print(line)
            self.log_file.write(line + "\n")
            self.log_file.flush()
        process.wait()
        return process.returncode
```

## 3. コミット記録

git コマンドで HEAD のコミットハッシュを取得する関数:

```python
def get_head_commit(cwd: Path) -> str | None:
    """Get current HEAD commit hash, or None if not a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd, capture_output=True, text=True, check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except FileNotFoundError:
        return None
```

ワークフロー開始時・各ステップ完了後にログへ記録する。

## 4. ログのフォーマット

PHASE2.0 の仕様に準拠したプレーンテキスト形式:

```
=====================================
Workflow: claude_loop
Started: 2026-04-04 14:30:00
Commit (start): abc1234
=====================================

[1/5] split_plan
Started: 2026-04-04 14:30:05
$ claude -p /split_plan ...
--- stdout/stderr ---
（Claude CLI の出力）
--- end (exit: 0, duration: 3m 42s) ---
Commit: abc1234 -> def5678

[2/5] imple_plan
...

=====================================
Finished: 2026-04-04 15:45:00
Commit (end): def5678
Duration: 1h 15m 00s
Result: SUCCESS (5/5 steps completed)
=====================================
```

## 5. エージェントへのログパス共有

`build_command()` を拡張し、ログファイルパスを `--append-system-prompt` 経由で注入する:

```python
def build_command(
    executable: str,
    prompt_flag: str,
    common_args: list[str],
    step: dict[str, Any],
    log_file_path: str | None = None,
) -> list[str]:
    cmd = [executable, prompt_flag, step["prompt"], *common_args, *step["args"]]
    if log_file_path:
        cmd.extend([
            "--append-system-prompt",
            f"Current workflow log: {log_file_path}",
        ])
    return cmd
```

## 6. main() の変更

`main()` の実行ループを以下のように変更する:

1. `--no-log` でなければログファイルを作成・オープン
2. ワークフローヘッダー（名前・開始時刻・開始コミット）をログに記録
3. 各ステップの実行を `subprocess.run()` → `subprocess.Popen()` に変更し、`TeeWriter.write_process_output()` で出力をストリーミング
4. 各ステップの前後でコミットハッシュを取得し、変化があればログに記録
5. ワークフロー完了時にフッター（終了時刻・最終コミット・所要時間・結果）をログに記録

### dry-run 時の挙動

`--dry-run` 時はログファイルを作成しない（従来通りコマンドの表示のみ）。

### ログ無効時（--no-log）の挙動

`TeeWriter` を使わず、現在の `subprocess.run()` をそのまま使用する。ログ有効/無効で分岐するが、ステップ実行ロジックの重複を避けるため、ログ無効時は `TeeWriter` の代わりに端末のみに出力するパスを通す。

## 7. テスト方針

既存のテストファイルの有無を確認し、以下のテストを追加する:

- `create_log_path()`: タイムスタンプ付きパスの生成
- `get_head_commit()`: git コマンドの呼び出しとエラーハンドリング
- `build_command()` の `log_file_path` 引数: ログパスが `--append-system-prompt` に正しく変換されるか
- `--no-log` / `--log-dir` オプションのパース

## リスク・不確実性

- **Windows 環境での `Popen` + `stdout=PIPE, stderr=STDOUT`**: Windows でのパイプ処理は Unix と挙動が異なる場合がある。特に長時間実行で出力バッファが詰まる可能性。`flush()` を適切に呼ぶことで対処する
- **Claude CLI の出力エンコーディング**: UTF-8 以外の文字が混入する可能性。`errors="replace"` で対処する

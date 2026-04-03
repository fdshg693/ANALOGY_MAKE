# IMPLEMENT: util ver2.1

## 変更対象ファイル

| ファイル | 操作 | 内容 |
|---|---|---|
| `scripts/claude_loop.py` | 変更 | 完了通知機能・モード設定対応の追加 |
| `scripts/claude_loop.yaml` | 変更 | `mode` セクション・`auto_args` の分離 |
| `tests/test_claude_loop.py` | 変更 | 新機能のテスト追加 |

## 1. ワークフロー完了通知

### 1.1 `notify_completion()` 関数の追加（`claude_loop.py`）

ワークフロー完了時にデスクトップ通知を送る関数を追加する。

```python
def notify_completion(title: str, message: str) -> None:
    """Send desktop notification. Falls back to beep on failure."""
    try:
        _notify_toast(title, message)
    except Exception:
        _notify_beep(title, message)


def _notify_toast(title: str, message: str) -> None:
    """Windows toast notification via PowerShell."""
    # シングルクォートをエスケープ（PowerShell文字列内）
    safe_title = title.replace("'", "''")
    safe_message = message.replace("'", "''")
    script = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
        "$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
        "$text = $template.GetElementsByTagName('text'); "
        f"$text[0].AppendChild($template.CreateTextNode('{safe_title}')) | Out-Null; "
        f"$text[1].AppendChild($template.CreateTextNode('{safe_message}')) | Out-Null; "
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Claude Workflow').Show($toast)"
    )
    result = subprocess.run(
        ["powershell", "-Command", script],
        capture_output=True, check=False, timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError("Toast notification failed")


def _notify_beep(title: str, message: str) -> None:
    """Fallback: beep + console output."""
    print("\a")  # BEL
    print(f"\n{'=' * 40}")
    print(f"  {title}")
    print(f"  {message}")
    print(f"{'=' * 40}\n")
```

**配置**: `format_duration()` の後、`main()` の前に配置する。

### 1.2 CLI オプション `--no-notify` の追加

`parse_args()` に追加:

```python
parser.add_argument(
    "--no-notify",
    action="store_true",
    help="Disable desktop notification on workflow completion",
)
```

**デフォルト動作**: 通知有効（`--notify` フラグは不要。PHASE2.0 設計通り、デフォルト有効・`--no-notify` で無効化）。

### 1.3 `main()` での呼び出し

`_run_steps()` の戻り値を受けた後、通知を送信する:

```python
exit_code = _run_steps(...)

if not args.no_notify and not args.dry_run:
    if exit_code == 0:
        notify_completion("Workflow Complete", f"All steps succeeded ({format_duration(total_duration)})")
    else:
        notify_completion("Workflow Failed", f"Exit code: {exit_code}")
```

**注意**: `_run_steps()` 内ではなく `main()` で呼び出す理由 — `_run_steps()` はログ出力に専念し、通知は外側の制御フローで行う（関心の分離）。

ただし、所要時間の情報が `_run_steps()` 内で計算されているため、`_run_steps()` の戻り値を `(exit_code, duration)` のタプルに変更するか、`main()` 側でも `time.monotonic()` で計測する。後者の方がシンプル（`_run_steps()` のシグネチャ変更不要）。

```python
# main() 内
workflow_start = time.monotonic()
exit_code = _run_steps(...)
total_duration = time.monotonic() - workflow_start

if not args.no_notify and not args.dry_run:
    duration_str = format_duration(total_duration)
    if exit_code == 0:
        notify_completion("Workflow Complete", f"All steps succeeded ({duration_str})")
    else:
        notify_completion("Workflow Failed", f"Exit code: {exit_code} ({duration_str})")
```

## 2. 自動実行モードの設定ファイル化

### 2.1 YAML 構造の変更（`claude_loop.yaml`）

現在の構造:

```yaml
command:
  args:
    - >-
      --dangerously-skip-permissions
      --disallowedTools "AskUserQuestion"
      --append-system-prompt "you cannot ask questions..."
```

変更後:

```yaml
mode:
  auto: false

command:
  executable: claude
  prompt_flag: -p
  args:
    - --dangerously-skip-permissions
  auto_args:
    - --disallowedTools "AskUserQuestion"
    - >-
      --append-system-prompt "you cannot ask questions to the user. so,
      whenever you think you should get human feedback, just write a file under
      `REQUESTS/AI` folder. Human will see this after you finish this step.
      (**So you cannot directly ask nor get human feedback in this session.**)

      ## Editing files under .claude/

      Files under `.claude/` cannot be directly edited in CLI `-p` mode (security restriction).
      To edit files in `.claude/`, use `scripts/claude_sync.py` with the following steps:

      1. `python scripts/claude_sync.py export` — Copy `.claude/` to `.claude_sync/`
      2. Edit the corresponding files in `.claude_sync/` (this directory is writable)
      3. `python scripts/claude_sync.py import` — Write back `.claude_sync/` contents to `.claude/`

      **Note**: Run export/import via the Bash tool with `python scripts/claude_sync.py <command>`."

steps:
  # ... (変更なし)
```

**ポイント**:
- `--dangerously-skip-permissions` は両モード共通のため `command.args` に残す
- `--disallowedTools` と `--append-system-prompt`（質問禁止指示）は自動モード専用のため `command.auto_args` に移動
- `mode.auto: false` をデフォルトにする（手動実行時はこのまま使える）

### 2.2 `resolve_command_config()` の拡張

現在の戻り値 `(executable, prompt_flag, common_args)` に `auto_args` を追加:

```python
def resolve_command_config(config: dict[str, Any]) -> tuple[str, str, list[str], list[str]]:
    command_config = config.get("command") or {}
    # ... (既存の executable, prompt_flag, common_args 処理)
    auto_args = normalize_cli_args(command_config.get("auto_args"), "command.auto_args")
    return executable, prompt_flag, common_args, auto_args
```

### 2.3 `resolve_mode()` 関数の追加

```python
def resolve_mode(config: dict[str, Any], cli_auto: bool, cli_interactive: bool) -> bool:
    """Determine execution mode. Returns True for auto mode."""
    if cli_auto:
        return True
    if cli_interactive:
        return False
    mode_config = config.get("mode") or {}
    return bool(mode_config.get("auto", False))
```

**優先順位**: CLI `--auto`/`--interactive` > YAML `mode.auto`

### 2.4 CLI オプション `--auto` / `--interactive` の追加

`parse_args()` に排他グループとして追加:

```python
mode_group = parser.add_mutually_exclusive_group()
mode_group.add_argument(
    "--auto",
    action="store_true",
    help="Force auto (unattended) execution mode",
)
mode_group.add_argument(
    "--interactive",
    action="store_true",
    help="Force interactive execution mode",
)
```

### 2.5 `main()` でのモード適用

```python
executable, prompt_flag, common_args, auto_args = resolve_command_config(config)
auto_mode = resolve_mode(config, args.auto, args.interactive)

if auto_mode:
    common_args = common_args + auto_args
```

### 2.6 モード情報のエージェント伝達

`build_command()` に `auto_mode` パラメータを追加し、モード情報を `--append-system-prompt` で注入:

```python
def build_command(
    executable: str,
    prompt_flag: str,
    common_args: list[str],
    step: dict[str, Any],
    log_file_path: str | None = None,
    auto_mode: bool = False,
) -> list[str]:
    cmd = [executable, prompt_flag, step["prompt"], *common_args, *step["args"]]
    system_prompts: list[str] = []
    if log_file_path:
        system_prompts.append(f"Current workflow log: {log_file_path}")
    if auto_mode:
        system_prompts.append(
            "Workflow execution mode: AUTO (unattended). "
            "Do not use AskUserQuestion. Write requests to REQUESTS/AI/ instead."
        )
    else:
        system_prompts.append(
            "Workflow execution mode: INTERACTIVE. "
            "You may ask the user questions when needed."
        )
    if system_prompts:
        cmd.extend(["--append-system-prompt", "\n\n".join(system_prompts)])
    return cmd
```

**変更点**: 現在は `log_file_path` 用に単独で `--append-system-prompt` を追加しているが、モード情報も同じ `--append-system-prompt` で送る必要がある。複数の `--append-system-prompt` を渡すのではなく、1 つの `--append-system-prompt` にまとめて渡す（Claude CLI の仕様上、最後の `--append-system-prompt` のみ有効になる可能性があるため）。

### 2.7 `_run_steps()` のシグネチャ変更

`_run_steps()` に `auto_mode: bool` パラメータを追加し、内部の `build_command()` 呼び出しに渡す:

```python
def _run_steps(
    step_iter,
    steps: list[dict[str, Any]],
    executable: str,
    prompt_flag: str,
    common_args: list[str],
    cwd: Path,
    dry_run: bool,
    tee: TeeWriter | None,
    log_path: Path | None,
    auto_mode: bool = False,  # 追加
) -> int:
    # ...
    command = build_command(executable, prompt_flag, common_args, step, log_file_path, auto_mode)
```

`main()` の 2 箇所の `_run_steps()` 呼び出し（ログあり・なし）に `auto_mode` を渡す。

## 3. テスト追加（`tests/test_claude_loop.py`）

### 3.1 通知関連テスト

```python
class TestNotifyCompletion(unittest.TestCase):
    """Tests for notify_completion()."""

    @patch("claude_loop._notify_toast")
    def test_calls_toast_on_success(self, mock_toast):
        notify_completion("title", "msg")
        mock_toast.assert_called_once_with("title", "msg")

    @patch("claude_loop._notify_beep")
    @patch("claude_loop._notify_toast", side_effect=Exception("fail"))
    def test_falls_back_to_beep_on_toast_failure(self, mock_toast, mock_beep):
        notify_completion("title", "msg")
        mock_beep.assert_called_once_with("title", "msg")

    @patch("claude_loop.subprocess.run")
    def test_toast_escapes_single_quotes(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        _notify_toast("it's done", "user's workflow")
        call_args = mock_run.call_args[0][0]
        # PowerShell の args 内に二重シングルクォートが含まれる
        cmd_str = " ".join(call_args)
        assert "it''s done" in cmd_str
```

### 3.2 モード関連テスト

```python
class TestResolveMode(unittest.TestCase):
    """Tests for resolve_mode()."""

    def test_default_is_interactive(self):
        assert resolve_mode({}, cli_auto=False, cli_interactive=False) is False

    def test_yaml_auto_true(self):
        assert resolve_mode({"mode": {"auto": True}}, False, False) is True

    def test_cli_auto_overrides_yaml(self):
        assert resolve_mode({"mode": {"auto": False}}, cli_auto=True, cli_interactive=False) is True

    def test_cli_interactive_overrides_yaml(self):
        assert resolve_mode({"mode": {"auto": True}}, cli_auto=False, cli_interactive=True) is False
```

### 3.3 `build_command()` のモード伝達テスト

```python
class TestBuildCommandWithMode(unittest.TestCase):
    """Tests for build_command() with auto_mode parameter."""

    def _make_step(self):
        return {"name": "test", "prompt": "/test", "args": []}

    def test_auto_mode_includes_auto_prompt(self):
        cmd = build_command("claude", "-p", [], self._make_step(), auto_mode=True)
        assert "--append-system-prompt" in cmd
        idx = cmd.index("--append-system-prompt")
        assert "AUTO" in cmd[idx + 1]

    def test_interactive_mode_includes_interactive_prompt(self):
        cmd = build_command("claude", "-p", [], self._make_step(), auto_mode=False)
        assert "--append-system-prompt" in cmd
        idx = cmd.index("--append-system-prompt")
        assert "INTERACTIVE" in cmd[idx + 1]

    def test_log_and_mode_combined_in_single_prompt(self):
        cmd = build_command("claude", "-p", [], self._make_step(),
                           log_file_path="/log.log", auto_mode=True)
        # --append-system-prompt は 1 回だけ
        assert cmd.count("--append-system-prompt") == 1
```

### 3.4 CLI オプションテスト

```python
class TestParseArgsModeOptions(unittest.TestCase):
    """Tests for --auto / --interactive CLI options."""

    def _parse(self, args):
        with patch("sys.argv", ["claude_loop.py", *args]):
            return parse_args()

    def test_auto_default_is_false(self):
        result = self._parse([])
        assert result.auto is False

    def test_interactive_default_is_false(self):
        result = self._parse([])
        assert result.interactive is False

    def test_auto_flag(self):
        result = self._parse(["--auto"])
        assert result.auto is True

    def test_interactive_flag(self):
        result = self._parse(["--interactive"])
        assert result.interactive is True

    def test_auto_and_interactive_are_mutually_exclusive(self):
        with self.assertRaises(SystemExit):
            self._parse(["--auto", "--interactive"])


class TestParseArgsNotifyOption(unittest.TestCase):
    """Tests for --no-notify CLI option."""

    def _parse(self, args):
        with patch("sys.argv", ["claude_loop.py", *args]):
            return parse_args()

    def test_no_notify_default_is_false(self):
        result = self._parse([])
        assert result.no_notify is False

    def test_no_notify_flag(self):
        result = self._parse(["--no-notify"])
        assert result.no_notify is True
```

### 3.5 `resolve_command_config()` の拡張テスト

```python
class TestResolveCommandConfigAutoArgs(unittest.TestCase):
    """Tests for auto_args in resolve_command_config()."""

    def test_returns_auto_args(self):
        config = {"command": {"auto_args": ["--disallowedTools AskUserQuestion"]}}
        _, _, _, auto_args = resolve_command_config(config)
        assert "--disallowedTools" in auto_args

    def test_empty_auto_args_default(self):
        config = {"command": {}}
        _, _, _, auto_args = resolve_command_config(config)
        assert auto_args == []
```

## 4. 既存テストへの影響

`TestBuildCommandWithLogFilePath` の既存テストは `build_command()` のシグネチャ変更（`auto_mode` パラメータ追加）の影響を受ける。`auto_mode` のデフォルトは `False` にするため、既存テストは **モード情報の system prompt が追加される** 点で出力が変わる。

対応: 既存テストの期待値を更新する。`auto_mode=False` でも `INTERACTIVE` のモード情報が `--append-system-prompt` に含まれるようになるため、`--append-system-prompt` の有無や内容の検証を修正する。

具体的な影響箇所と更新後のアサーション:

- `test_without_log_file_path`: `--append-system-prompt` が含まれるようになる
  ```python
  assert "--append-system-prompt" in cmd
  idx = cmd.index("--append-system-prompt")
  assert "INTERACTIVE" in cmd[idx + 1]
  ```
- `test_empty_string_log_file_path_does_not_add_args`: log_file_path="" でもモード情報は付与される
  ```python
  assert "--append-system-prompt" in cmd
  idx = cmd.index("--append-system-prompt")
  assert "Current workflow log:" not in cmd[idx + 1]  # ログパスは含まれない
  assert "INTERACTIVE" in cmd[idx + 1]  # モード情報は含まれる
  ```
- `test_with_log_file_path_adds_system_prompt_arg`: system prompt の内容にモード情報が追加される
  ```python
  idx = cmd.index("--append-system-prompt")
  prompt_value = cmd[idx + 1]
  assert f"Current workflow log: {log_path}" in prompt_value
  assert "INTERACTIVE" in prompt_value
  ```
- `test_log_file_path_appended_after_step_args`: コマンド配列の末尾 2 要素が `--append-system-prompt` + 結合文字列

### import 文の更新

テストファイル冒頭の import 行に新関数を追加:

```python
from claude_loop import (
    create_log_path, get_head_commit, format_duration, build_command, parse_args,
    notify_completion, _notify_toast, resolve_mode, resolve_command_config,
)
```

## 5. 実装順序

1. `claude_loop.yaml` の構造変更（`mode` セクション・`auto_args` 分離）
2. `claude_loop.py` に `resolve_mode()` 追加
3. `resolve_command_config()` を拡張（`auto_args` 返却）
4. `parse_args()` に `--auto`/`--interactive`/`--no-notify` 追加
5. `build_command()` を拡張（`auto_mode` パラメータ、system prompt 統合）
6. `_run_steps()` に `auto_mode` パラメータを追加し、`build_command()` に引き渡す
7. `main()` にモード解決・引数結合ロジック追加（`_run_steps()` への `auto_mode` 渡し含む）
8. `notify_completion()` / `_notify_toast()` / `_notify_beep()` 追加
9. `main()` に通知呼び出し追加
10. 既存テスト更新 + 新規テスト追加（import 文の更新含む）
11. テスト実行・動作確認

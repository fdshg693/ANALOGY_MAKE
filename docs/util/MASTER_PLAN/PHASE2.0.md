# PHASE2.0: ワークフロー実行基盤の強化（ログ・通知・モード設定）

## 概要

`claude_loop.py` によるワークフロー実行の可観測性と柔軟性を強化する。
具体的には、(1) 実行ログの永続化と前後コミットの記録、(2) ワークフロー完了時の通知、(3) 自動実行モードの設定ファイル化を行う。

## 動機

- 現状はコンソール出力が流れるだけで、後から実行内容を確認する手段がない
- 長時間のワークフロー実行後に完了に気付けない（特にバックグラウンド実行時）
- 自動実行モードの設定が `--append-system-prompt` による後付け上書きで、SKILL 側から実行モードを動的に参照できない

## 前提条件

- Python 3.10+（`claude_loop.py` の実行環境）
- Claude CLI インストール済み
- Windows 11 環境（通知方法の選定に影響）

## やること

### 1. ワークフローログの永続化

`claude_loop.py` の `subprocess.run()` 出力をファイルに記録する。

#### ログファイルの配置

```
logs/
└── workflow/
    └── {YYYYMMDD}_{HHmmss}_{workflow_name}.log
```

- `logs/` は `.gitignore` 済みとする（ログ自体は git 管理しない）
- ワークフロー名は YAML のファイル名（拡張子なし）から取得

#### ログの内容

```
=====================================
Workflow: claude_loop
Started: 2026-04-03 14:30:00
Commit (start): abc1234
=====================================

[1/5] split_plan
$ claude -p /split_plan ...
--- stdout/stderr ---
（Claude CLI の出力）
--- end (exit: 0, duration: 3m 42s) ---

[2/5] imple_plan
...

=====================================
Finished: 2026-04-03 15:45:00
Commit (end): def5678
Duration: 1h 15m 00s
Result: SUCCESS (5/5 steps completed)
=====================================
```

#### 実装方針

- `subprocess.run()` を `subprocess.Popen()` に変更し、stdout/stderr をリアルタイムで端末 **かつ** ログファイルに書き出す（tee 方式）
- 各ステップの開始時刻・終了時刻・所要時間・終了コードをログに記録
- ワークフロー全体の所要時間・成功/失敗ステータスをログ末尾に記録

#### コミット記録

ワークフロー開始前と各ステップ完了後に、現在の HEAD コミットハッシュを記録する:

1. **開始前**: `git rev-parse HEAD` で開始コミットを取得しログに記録
2. **各ステップ後**: ステップがコミットを作成した場合、新しい HEAD をログに記録
3. **終了時**: 最終コミットハッシュをログ末尾に記録

ワークフロー開始前に未コミットの変更がある場合:
- `git status --porcelain` で検出
- 自動コミットは行わず、警告をログに出力してユーザーに判断を委ねる
- `--auto-commit-before` フラグで明示的に許可された場合のみ、開始前に自動コミット

### 2. ログファイルパスのエージェント共有

各ステップの Claude CLI 実行時に、現在のログファイルパスを `--append-system-prompt` 経由でエージェントに伝える。

```python
# 既存の共通 args に加えて、ステップごとにログパスを注入
step_args = [
    "--append-system-prompt",
    f"Current workflow log: {log_file_path}"
]
```

これにより各エージェントが:
- 前のステップの出力を `Read` ツールでログから確認できる
- エラー発生時に前ステップのログを参照して原因調査できる

### 3. ワークフロー完了通知

ワークフロー完了（成功・失敗とも）時に、デスクトップ通知を送る。

#### Windows 環境での通知方法

**案 A: PowerShell 経由の Windows トースト通知（推奨）**

```python
import subprocess

def notify(title: str, message: str):
    script = f"""
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
    $text = $template.GetElementsByTagName('text')
    $text[0].AppendChild($template.CreateTextNode('{title}')) | Out-Null
    $text[1].AppendChild($template.CreateTextNode('{message}')) | Out-Null
    $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Claude Workflow').Show($toast)
    """
    subprocess.run(["powershell", "-Command", script], check=False)
```

**案 B: ビープ音 + コンソール出力（フォールバック）**

```python
def notify_simple(title: str, message: str):
    # システムビープ音
    print("\a")  # BEL character
    print(f"\n{'='*40}")
    print(f"  {title}")
    print(f"  {message}")
    print(f"{'='*40}\n")
```

**方針**:
- 案 A を試行し、失敗時は案 B にフォールバック
- `--notify` / `--no-notify` フラグで制御（デフォルト: 有効）
- 通知内容: ワークフロー名、成功/失敗、所要時間、完了ステップ数

### 4. 自動実行モードの設定ファイル化

#### 設定ファイル

`scripts/claude_loop.yaml` 内に `mode` セクションを追加:

```yaml
mode:
  auto: false  # true: 自動実行モード（デフォルト: false）

command:
  executable: claude
  prompt_flag: -p
  args:
    - --dangerously-skip-permissions
  auto_args:
    - --disallowedTools "AskUserQuestion"
    - >-
      --append-system-prompt "you cannot ask questions to the user. ..."

steps:
  # ...
```

**動作**:
- `mode.auto: true` の場合: `command.args` + `command.auto_args` を結合
- `mode.auto: false` の場合: `command.args` のみ使用
- CLI オプション `--auto` で YAML 設定を上書き可能

#### SKILL 側からのモード参照

ワークフローの実行モードを `--append-system-prompt` 経由で各エージェントに伝達する:

```python
if auto_mode:
    mode_prompt = (
        "Workflow execution mode: AUTO (unattended). "
        "Do not use AskUserQuestion. Write requests to REQUESTS/AI/ instead."
    )
```

各 SKILL は `--append-system-prompt` で渡されたモード情報に基づいて動的に振る舞いを変えられる:
- **AUTO モード時**: ユーザー質問禁止、`REQUESTS/AI/` への書き出し、plan_review_agent のみで判断

### 5. CLI オプションの整理

```bash
# ログ制御
python scripts/claude_loop.py --log-dir ./logs/workflow  # ログ出力先（デフォルト: logs/workflow/）
python scripts/claude_loop.py --no-log                   # ログ無効化

# 通知制御
python scripts/claude_loop.py --no-notify                # 通知無効化

# モード制御
python scripts/claude_loop.py --auto                     # 自動実行モード強制

# コミット制御
python scripts/claude_loop.py --auto-commit-before       # 開始前に未コミット変更を自動コミット
```

## ファイル変更一覧

| ファイル | 操作 | 内容 |
|---|---|---|
| `scripts/claude_loop.py` | 変更 | ログ出力・通知・モード設定の実装 |
| `scripts/claude_loop.yaml` | 変更 | `mode` セクション・`auto_args` の追加 |
| `.gitignore` | 変更 | `logs/` を追加 |

## やらないこと

- ログのローテーション・自動削除（手動で管理する）
- ログの構造化フォーマット（JSON 等）（人が読めるプレーンテキストで十分）
- 外部通知サービスとの連携（Slack, Discord 等）
- ステップ単位の通知（ワークフロー全体の完了時のみ）

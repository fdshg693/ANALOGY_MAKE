# ver2.1 CHANGES

PHASE2.0 の残タスク（完了通知・自動実行モード設定ファイル化）を実装。

## 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---|---|---|
| `scripts/claude_loop.py` | 変更 | 完了通知機能・自動実行モード解決・モード伝搬の追加（448→542行, +94行） |
| `scripts/claude_loop.yaml` | 変更 | `mode` セクション・`auto_args` の追加（38→43行） |
| `tests/test_claude_loop.py` | 変更 | 通知・モード関連の新テストクラス6個追加（203→335行, +132行） |
| `.claude/SKILLS/retrospective/SKILL.md` | 変更 | 即時適用/ユーザー確認の判断基準を緩和 |
| `.gitignore` | 変更 | `__pycache__`・`*.pyc` を追加 |

## 変更内容の詳細

### 1. ワークフロー完了通知（`scripts/claude_loop.py`）

ワークフロー完了時にデスクトップ通知を送信する機能を追加。

- **`notify_completion(title, message)`**: メイン関数。toast を試行し、失敗時は beep にフォールバック
- **`_notify_toast(title, message)`**: Windows PowerShell 経由のトースト通知
  - `Windows.UI.Notifications` API を使用
  - シングルクォートを `''` にエスケープして PowerShell インジェクションを防止
  - タイムアウト 10 秒
  - 非ゼロ終了コード時に `RuntimeError` を送出してフォールバックをトリガー
- **`_notify_beep(title, message)`**: フォールバック（BEL 文字 + コンソール出力）
- **`--no-notify` CLI オプション**: 通知を無効化（デフォルト: 有効）
- **呼び出し位置**: `main()` 内で `_run_steps()` 完了後に呼び出し（関心の分離）
- **所要時間計測**: `main()` 内で `time.monotonic()` を使用（`_run_steps()` 内のログ用計測とは独立）

### 2. 自動実行モード設定ファイル化（`scripts/claude_loop.py` + `scripts/claude_loop.yaml`）

YAML 設定ファイルでの自動実行モード定義と CLI オーバーライドを実装。

#### YAML 構造の変更

```yaml
# 追加されたセクション
mode:
  auto: false

command:
  # 既存
  executable: claude
  prompt_flag: -p
  args: [--dangerously-skip-permissions]
  # 追加
  auto_args:
    - --disallowedTools "AskUserQuestion"
    - >-
      --append-system-prompt "you cannot ask questions to the user. ..."
```

#### 新規関数

- **`resolve_mode(config, cli_auto, cli_interactive)`**: 実行モード判定
  - 優先順位: CLI フラグ > YAML 設定 > デフォルト（`False` = interactive）
- **`resolve_command_config()`**: 戻り値を 3 要素から 4 要素に拡張（`auto_args` 追加）

#### CLI オプション

- `--auto` / `--interactive`: 相互排他グループとして追加
- `main()` 内で `auto_mode=True` 時に `common_args + auto_args` を結合

### 3. モード伝搬（`scripts/claude_loop.py`）

各ステップ実行時に実行モード情報をエージェントに伝達。

- **`build_command()`**: `auto_mode` パラメータを追加
  - AUTO モード: `"Workflow execution mode: AUTO (unattended). Do not use AskUserQuestion..."`
  - INTERACTIVE モード: `"Workflow execution mode: INTERACTIVE. You may ask the user questions..."`
- ログパスとモード情報を **単一の `--append-system-prompt`** に結合（改行区切り）
- `_run_steps()` に `auto_mode` パラメータを追加して伝搬

### 4. テスト追加（`tests/test_claude_loop.py`）

6 つの新テストクラスを追加:

| テストクラス | テスト数 | 対象 |
|---|---|---|
| `TestNotifyCompletion` | 3 | toast 成功・beep フォールバック・クォートエスケープ |
| `TestResolveMode` | 4 | デフォルト・YAML 設定・CLI オーバーライド優先順位 |
| `TestBuildCommandWithMode` | 3 | AUTO/INTERACTIVE プロンプト注入・単一 `--append-system-prompt` 結合 |
| `TestParseArgsModeOptions` | 5 | `--auto`/`--interactive` フラグ・相互排他 |
| `TestParseArgsNotifyOption` | 2 | `--no-notify` フラグ |
| `TestResolveCommandConfigAutoArgs` | 2 | `auto_args` 抽出・デフォルト空リスト |

既存テスト（`TestBuildCommandWithLogFilePath`）も更新: `build_command()` がモード情報を常に注入するようになったため、`--append-system-prompt` の存在と `INTERACTIVE` テキストの検証に変更。

### 5. retrospective SKILL の判断基準変更（`.claude/SKILLS/retrospective/SKILL.md`）

- **即時適用してよい変更**: SKILL 新規作成・ワークフローステップ追加/削除・エージェント定義変更を即時適用可能な範囲に含めるよう拡大
- **ユーザー確認が必要な変更**: リスクのあるスクリプトのワークフロー組み込み・大量変更（目安: 計500行以上）に限定

### 6. .gitignore 追加（`.gitignore`）

Python キャッシュファイル（`__pycache__/`・`*.pyc`）を除外対象に追加。

## 技術的判断

- **通知のフォールバック戦略**: Windows トースト通知を最優先とし、PowerShell 実行失敗時にビープ音+コンソール出力にフォールバック。外部ライブラリ不要で追加依存なし。
- **`_run_steps()` と `main()` の duration 重複計測**: ログ用（`_run_steps()` 内）と通知用（`main()` 内）で `time.monotonic()` を別々に計測。機能的に正しく、将来的な統合は低優先度。
- **モード情報の単一プロンプト結合**: ログパスとモード情報を改行区切りで1つの `--append-system-prompt` にまとめることで、コマンドライン引数の重複を回避。

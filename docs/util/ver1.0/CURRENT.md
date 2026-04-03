# CURRENT: util ver1.0

util カテゴリのコード現況。Claude Code ワークフロー自動化基盤の全体像を記述する。

## ファイル一覧

### SKILL ファイル（`.claude/SKILLS/`）

| ファイル | 行数 | 役割 |
|---|---|---|
| `split_plan/SKILL.md` | 81 | ステップ 1: 計画策定。MASTER_PLAN・ISSUES・前回 RETROSPECTIVE から今回バージョンの計画ドキュメント（ROUGH_PLAN / REFACTOR / IMPLEMENT）を作成 |
| `imple_plan/SKILL.md` | 75 | ステップ 2: 実装。CURRENT.md + 計画ドキュメントに基づきコード実装。サブエージェントで編集・テスト実行。MEMO.md を出力 |
| `wrap_up/SKILL.md` | 44 | ステップ 3: 残課題対応。MEMO.md の項目を ✅完了 / ⏭️不要 / 📋先送り に分類し、ISSUES 整理 |
| `write_current/SKILL.md` | 70 | ステップ 4: ドキュメント更新。メジャー版は CURRENT.md、マイナー版は CHANGES.md を作成。CLAUDE.md・MASTER_PLAN も更新 |
| `retrospective/SKILL.md` | 51 | ステップ 5: 振り返り。git diff ベースでバージョン作業を振り返り、SKILL 自体の改善を即時適用 |
| `meta_judge/SKILL.md` | 18 | メタ評価。ワークフロー全体の有効性を評価する手動実行専用 SKILL（`disable-model-invocation: true`） |
| `meta_judge/WORKFLOW.md` | 12 | meta_judge 参照用のワークフロー概要ドキュメント |

### サブエージェント

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/agents/plan_review_agent.md` | 17 | 計画レビュー専用エージェント。Sonnet モデル、Read/Glob/Grep のみ使用。split_plan と wrap_up で利用 |

### ユーティリティスクリプト

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/scripts/get_latest_version.sh` | 43 | バージョン番号の算出。`latest` / `major` / `next-minor` / `next-major` の 4 モードに対応。旧形式（`ver12`）と新形式（`ver13.0`）の両方をパース |
| `scripts/claude_loop.py` | 252 | Python 自動化スクリプト。YAML ワークフロー定義に従い Claude CLI を順次実行 |
| `scripts/claude_loop.yaml` | 27 | フルワークフロー定義。5 ステップ（split_plan → imple_plan → wrap_up → write_current → retrospective）を定義 |

### Hooks 関連（ver1.0 で追加、未インストール）

| ファイル | 行数 | 役割 |
|---|---|---|
| `_staged_hooks/permission_handler.py` | 37 | PermissionRequest フックハンドラ。AskUserQuestion 以外のツールを自動許可する Python スクリプト |
| `_staged_hooks/install.sh` | 31 | フックファイルを `.claude/hooks/` と `.claude/settings.local.json` にコピーするインストールスクリプト |
| `_staged_hooks/settings.local.json` | 40 | 更新版の設定ファイル。フックの外部スクリプト化 + `permissions.allow` に `.claude/**` の Edit/Write 許可を追加 |

### 非同期コミュニケーション

| ディレクトリ | 役割 |
|---|---|
| `REQUESTS/AI/` | AI → ユーザーへの確認事項を書き出す場所。自動実行モードで質問が必要な場合の代替手段 |
| `REQUESTS/HUMAN/` | ユーザー → AI への要望を記載する場所 |

## scripts/claude_loop.py の実装詳細

### アーキテクチャ

単一ファイルの CLI ツール。依存は PyYAML のみ。

### 主要関数

| 関数 | 概要 |
|---|---|
| `parse_args()` | argparse による CLI 引数パース。`-w`（ワークフロー指定）、`-s`（開始ステップ）、`--cwd`、`--dry-run`、`--max-loops` / `--max-step-runs`（排他） |
| `load_workflow(path)` | YAML 読み込み・バリデーション |
| `normalize_cli_args(value, field_name)` | YAML の args を `shlex.split` でトークン化 |
| `get_steps(config)` | steps セクションのパース。各ステップは `name` / `prompt` / `args` |
| `resolve_command_config(config)` | command セクションから executable / prompt_flag / common_args を取得 |
| `build_command(...)` | `[executable, prompt_flag, prompt, *common_args, *step_args]` のコマンド配列を構築 |
| `iter_steps_for_loop_limit(...)` | `--max-loops` 指定時のステップイテレータ。初回ループは start_index から、2 回目以降は先頭から |
| `iter_steps_for_step_limit(...)` | `--max-step-runs` 指定時のステップイテレータ。ステップ数上限でループ |
| `main()` | エントリポイント。設定読み込み → バリデーション → ステップ順次実行（`subprocess.run`） |

### 実行例

```bash
python scripts/claude_loop.py                   # フル 1 ループ（デフォルト）
python scripts/claude_loop.py --start 3         # ステップ 3 (wrap_up) から開始
python scripts/claude_loop.py --max-loops 2     # 2 ループ実行
python scripts/claude_loop.py --max-step-runs 7 # 最大 7 ステップ実行
python scripts/claude_loop.py --dry-run         # コマンド確認のみ
python scripts/claude_loop.py -w path/to.yaml   # 別ワークフロー指定
```

### 自動化時の制約

`claude_loop.yaml` の `command.args` で以下を設定:
- `--dangerously-skip-permissions`: 権限確認スキップ
- `--disallowedTools "AskUserQuestion"`: ユーザー質問禁止
- `--append-system-prompt`: 質問が必要な場合は `REQUESTS/AI/` にファイルを書き出すよう指示

## Hooks システムの現状（ver1.0）

### 背景

`.claude/settings.local.json` の PermissionRequest フックが全ツールを無条件に自動許可しており、以下の問題が発生:
1. 手動モードで AskUserQuestion が自動許可され、ユーザーが回答できない
2. 自動化モード（`-p`）で `.claude` 配下のファイル書き込みが失敗する
3. フックコマンドがインライン echo で管理しにくい

### ver1.0 で実施した対応

Claude Code の `.claude` ディレクトリ保護制限により、AI から直接フックファイルを書き込めなかったため、ステージングディレクトリ方式を採用:

1. **`_staged_hooks/permission_handler.py`**: AskUserQuestion を除外する Python フックハンドラを作成
2. **`_staged_hooks/settings.local.json`**: フックの外部スクリプト化 + `Edit(/.claude/**)` / `Write(/.claude/**)` を `permissions.allow` に追加
3. **`_staged_hooks/install.sh`**: 上記ファイルを `.claude/` にコピーするインストールスクリプト

### インストール状態

**未インストール**。ユーザーによる `bash _staged_hooks/install.sh` の実行待ち。

### 現在の settings.local.json（インストール前）

フックは旧来のインライン echo 方式のまま:
```json
"hooks": {
  "PermissionRequest": [{
    "matcher": "",
    "hooks": [{
      "type": "command",
      "command": "echo '{\"hookSpecificOutput\": ...}'"
    }]
  }]
}
```

`permissions.allow` には `.claude` 関連のエントリなし。

### インストール後の settings.local.json（予定）

- フック: `python "$CLAUDE_PROJECT_DIR/.claude/hooks/permission_handler.py"` を呼び出す方式に変更
- `permissions.allow`: `Edit(/.claude/**)` / `Write(/.claude/**)` を追加

### permission_handler.py のロジック

1. stdin から JSON を読み取り `tool_name` を取得
2. `AskUserQuestion` の場合: 何も出力せず exit 0 → 通常のパーミッションダイアログを表示
3. それ以外: `{"behavior": "allow"}` を JSON で出力 → 自動許可

## 未解決の課題

### ISSUES/util/medium/hooks_env_var_verification.md

`$CLAUDE_PROJECT_DIR` 環境変数が Windows 環境で展開されるか未確認。展開されない場合は絶対パスへの変更が必要。
また `permissions.allow` の `Edit(/.claude/**)` / `Write(/.claude/**)` が `bypassPermissions` モードの保護を上書きできるか未確認。上書きできない場合は `PreToolUse` フックでの対応を検討。

### ISSUES/util/medium/hooks_post_install_tasks.md

インストール後の残タスク:
- 手動モード・自動化モードでの動作確認
- `_staged_hooks/` ディレクトリの削除
- `REQUESTS/AI/hooks_install_request.md` のクローズ

### ISSUES/util/high/HOOKS設定.md

親課題。実装完了・インストール待ちのステータス。インストールと検証が完了次第クローズ。

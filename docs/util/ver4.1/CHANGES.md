# ver4.1 CHANGES

ver4.0 からの変更差分。機能変更ゼロ、純粋なコード整理とドキュメント追加のみ。

## 変更ファイル一覧

| ファイル | 変更種別 | 概要 |
|---|---|---|
| `scripts/claude_loop.py` | 変更 | エントリ専用に縮小（698行 → 349行）。機能関数を `claude_loop_lib/` に移動 |
| `scripts/claude_loop_lib/__init__.py` | 追加 | パッケージ初期化（空ファイル） |
| `scripts/claude_loop_lib/workflow.py` | 追加 | YAML ロード・バリデーション・ステップ/設定抽出（`load_workflow`, `get_steps`, `resolve_defaults`, `resolve_command_config`, `resolve_mode`, `normalize_string_list`, `normalize_cli_args`） |
| `scripts/claude_loop_lib/feedbacks.py` | 追加 | frontmatter 解析・ロード・消費（`parse_feedback_frontmatter`, `load_feedbacks`, `consume_feedbacks`） |
| `scripts/claude_loop_lib/commands.py` | 追加 | コマンド構築・ステップ反復（`build_command`, `iter_steps_for_loop_limit`, `iter_steps_for_step_limit`） |
| `scripts/claude_loop_lib/logging_utils.py` | 追加 | TeeWriter・ログパス生成・ヘッダ出力・時間フォーマット（`TeeWriter`, `create_log_path`, `print_step_header`, `format_duration`） |
| `scripts/claude_loop_lib/git_utils.py` | 追加 | Git 操作（`get_head_commit`, `check_uncommitted_changes`, `auto_commit_changes`） |
| `scripts/claude_loop_lib/notify.py` | 追加 | 完了通知（`notify_completion`, `_notify_toast`, `_notify_beep`） |
| `scripts/README.md` | 追加 | scripts/ の使用方法・CLI オプション・YAML 仕様・フィードバック注入・ログフォーマット・拡張ガイドを記載した人間向けドキュメント |
| `tests/test_claude_loop.py` | 変更 | インポート元・`@patch` ターゲットを新モジュール構成に追従（89件グリーン維持） |

## 変更内容の詳細

### `scripts/claude_loop.py` の縮小

- 698行から349行に削減。残したのはエントリ専用の関数のみ: `positive_int`（argparse バリデータ）・`parse_args`・`main`・`_run_steps`・定数2件
- 機能関数はすべて `claude_loop_lib/` 配下の専用モジュールへ移動。`claude_loop.py` は明示インポートで参照する形に変更
- `_run_steps` は `main` と密結合（ワークフロー出力フォーマット・tee 分岐含む ~150行）のため、~200行目標に対して349行になったが、完了条件の趣旨（機能関数の外部化）は達成

### `claude_loop_lib/` パッケージ新設

- 依存の少ない順（`git_utils` → `notify` → `logging_utils` → `feedbacks` → `commands` → `workflow`）に移動
- `__init__.py` は空。利用側は `from claude_loop_lib.workflow import ...` のように明示インポートする設計（再エクスポートなし）
- `sys.path[0] = scripts/` で実行されるため `claude_loop_lib` パッケージが解決できる。テスト側も既存の `sys.path.insert(0, "scripts")` を維持し同一解決ルートを確保

### `tests/test_claude_loop.py` のパッチターゲット更新

関数が各モジュールに移動したため、`@patch("claude_loop.X")` を実際の定義モジュールに付け替え:

| 旧パッチ | 新パッチ |
|---|---|
| `@patch("claude_loop.datetime")` | `@patch("claude_loop_lib.logging_utils.datetime")` |
| `@patch("claude_loop.subprocess.run")` (git系) | `@patch("claude_loop_lib.git_utils.subprocess")` |
| `@patch("claude_loop.subprocess.run")` (notify系) | `@patch("claude_loop_lib.notify.subprocess")` |
| `@patch("claude_loop._notify_toast")` | `@patch("claude_loop_lib.notify._notify_toast")` |
| `@patch("claude_loop._notify_beep")` | `@patch("claude_loop_lib.notify._notify_beep")` |
| `@patch("claude_loop.notify_completion")` | `@patch("claude_loop_lib.notify.notify_completion")` |
| `@patch("claude_loop.get_head_commit")` | `@patch("claude_loop_lib.git_utils.get_head_commit")` |
| `@patch("claude_loop.shutil")` | `@patch("claude_loop_lib.feedbacks.shutil")` |

### `scripts/README.md` 新設

- 対象読者: 本プロジェクトの開発者
- 包含セクション: これは何か / ファイル一覧 / クイックスタート / CLI オプション一覧 / YAML ワークフロー仕様 / フル/quick の使い分け / フィードバック注入機能 / ログフォーマット / claude_sync.py / 拡張ガイド / 関連ドキュメント
- `CURRENT_scripts.md` の「ユーザー視点で必要な情報」を README に集約。内部実装の詳細（関数一覧・行番号等）は CURRENT 側に残す方針（write_current ステップで整理）

## 技術的判断

### `claude_loop.py` の行数が目標を超えた理由

IMPLEMENT.md では ~200行を目標としていたが、実測349行。`_run_steps` がワークフロー出力フォーマット（ヘッダ・フッタ・ステップヘッダ・失敗時フッタ）と tee の分岐を含むため ~150行を占有する。さらに `workflow_runner.py` 等に切り出すことも可能だが、`main` との密結合が強く責務も「ワークフロー実行本体」で一貫しているため今回はエントリに残した。

### README と CURRENT の重複排除方針

`scripts/README.md` には使用方法を記載し、`docs/util/ver4.1/CURRENT_scripts.md`（write_current ステップで作成）には内部実装の詳細を記載する。write_current 時に ver4.0 の `CURRENT_scripts.md` の関数行番号テーブルを「モジュール + 関数名」の対応表に差し替える。

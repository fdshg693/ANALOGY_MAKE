# CURRENT_scripts: util ver7.0 — Python スクリプトと YAML ワークフロー定義

`scripts/` 配下のユーティリティスクリプトと YAML ワークフロー定義。ver6.1 で `claude_loop_lib/frontmatter.py` を追加、ver7.0 で `claude_loop_lib/issues.py` と `issue_worklist.py` を追加した状態。

## ファイル一覧

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/scripts/get_latest_version.sh` | 43 | バージョン番号算出。`latest` / `major` / `next-minor` / `next-major` の 4 モード |
| `scripts/claude_loop.py` | 395 | エントリポイント。`claude_loop_lib/` を組み合わせてワークフローを実行 |
| `scripts/claude_loop_lib/__init__.py` | 0 | パッケージ初期化（空） |
| `scripts/claude_loop_lib/workflow.py` | 135 | YAML 読み込み・バリデーション・各設定値のリゾルバ |
| `scripts/claude_loop_lib/commands.py` | 69 | コマンド構築・ステップイテレータ |
| `scripts/claude_loop_lib/feedbacks.py` | 50 | フィードバックファイルのロード・消費（ver6.1 で `parse_frontmatter` 共通化により短縮） |
| `scripts/claude_loop_lib/frontmatter.py` | 42 | **ver6.1 で新規追加**。共通 `parse_frontmatter(text) -> (dict\|None, str)` 実装 |
| `scripts/claude_loop_lib/issues.py` | 53 | **ver7.0 で新規追加**。ISSUE frontmatter の共通ヘルパ（`VALID_STATUS` / `VALID_ASSIGNED` / `VALID_COMBOS` / `extract_status_assigned`） |
| `scripts/claude_loop_lib/logging_utils.py` | 57 | TeeWriter・ログパス生成・ステップヘッダ表示・duration フォーマット |
| `scripts/claude_loop_lib/git_utils.py` | 40 | git HEAD 取得・未コミット検出・自動コミット |
| `scripts/claude_loop_lib/notify.py` | 43 | Windows toast 通知・beep フォールバック |
| `scripts/claude_loop.yaml` | 52 | フルワークフロー定義（5 ステップ） |
| `scripts/claude_loop_quick.yaml` | 44 | 軽量ワークフロー定義（3 ステップ） |
| `scripts/claude_sync.py` | 58 | `.claude/` ⇔ `.claude_sync/` 同期。CLI `-p` モードの `.claude/` 編集制限を回避 |
| `scripts/issue_status.py` | 93 | `ISSUES/{category}/{high,medium,low}/*.md` の `status × assigned` 分布を表示する読み取り専用スクリプト（ver7.0 で `claude_loop_lib.issues` を利用する形にリファクタ） |
| `scripts/issue_worklist.py` | 163 | **ver7.0 で新規追加**。`assigned` / `status` で ISSUE を絞り込み、`text` / `json` で出力する読み取り専用スクリプト |
| `scripts/README.md` | 277 | スクリプト全体のドキュメント（ver7.0 で `issue_worklist.py` 説明を追加） |

## scripts/claude_loop_lib/frontmatter.py（ver6.1 新規）

シグネチャ: `parse_frontmatter(text: str) -> tuple[dict | None, str]`

- 先頭 `---` 〜 `---` の YAML ブロックを抽出し `(frontmatter_dict, body)` を返す
- `feedbacks.py` と `issue_status.py` の両方から利用
- フォールバック: 先頭 `---` なし / 閉じ `---` なし / YAML パースエラー / dict 以外 → `(None, text 相当)`

## scripts/claude_loop_lib/issues.py（ver7.0 新規）

ISSUE frontmatter 読み取りの共通ヘルパ。`issue_status.py` と `issue_worklist.py` が共有することで、`status` / `assigned` の妥当性判定ロジックの drift を防ぐ。

### 定数

| 定数 | 値 |
|---|---|
| `VALID_STATUS` | `{"raw", "review", "ready", "need_human_action"}` |
| `VALID_ASSIGNED` | `{"human", "ai"}` |
| `VALID_COMBOS` | `{(raw, human), (raw, ai), (review, ai), (ready, ai), (need_human_action, human)}` |

### `extract_status_assigned(path: Path) -> tuple[str, str, dict | None, str]`

戻り値: `(status, assigned, frontmatter_dict, body)`

- 読み取りエラー → `("raw", "human", None, "")`
- frontmatter なし → `("raw", "human", None, body)`
- 不明な status / assigned / 無効な combo → stderr に警告を出したうえで値をそのまま返す

ver6.0 の `issue_status.py` ローカル関数 `_extract_status_assigned` と比べ、戻り値を 4-tuple に拡張（`fm` / `body` を追加）した点が差分。

## scripts/issue_worklist.py（ver7.0 新規）

ISSUE を `assigned` / `status` で絞り込んで一覧表示する読み取り専用スクリプト。`/retrospective` SKILL が次バージョン推奨の材料収集に利用する。

### CLI

```bash
python scripts/issue_worklist.py [--category util|app|infra|cicd] [--assigned ai|human] [--status ready,review|...] [--format text|json]
```

| オプション | 既定値 | 備考 |
|---|---|---|
| `--category` | `.claude/CURRENT_CATEGORY` の値。未設定時 `app` | |
| `--assigned` | `ai` | |
| `--status` | `ready,review` | カンマ区切りで複数指定可 |
| `--format` | `text` | `json` で JSON 配列出力 |

### 出力フォーマット（text）

```text
[util]
- medium | ready  | ai | ISSUES/util/medium/foo.md | タイトル
```

0 件時: `[util]` の次行に `  (no matching issues)`

### 出力フォーマット（json）

```json
{
  "category": "util",
  "filter": {"assigned": "ai", "status": ["ready", "review"]},
  "items": [{ "path": "...", "title": "...", "priority": "...", "status": "...", "assigned": "...", "reviewed_at": "...", "summary": "..." }]
}
```

`items` は priority 順（high → medium → low）→ path アルファベット順。

### 実装上の注意

- Windows 既定の `cp932` で em-dash 含むタイトルが `UnicodeEncodeError` になるため、`sys.stdout.reconfigure(encoding="utf-8", errors="replace")` を冒頭で設定
- `done/` サブディレクトリ・直下ファイル・`README.md` は走査対象外

## scripts/issue_status.py（ver6.0 新規、ver7.0 でリファクタ）

ver7.0 でローカルの `VALID_STATUS` / `VALID_ASSIGNED` / `VALID_COMBOS` 定義と `_extract_status_assigned` を削除し、`from claude_loop_lib.issues import extract_status_assigned` に置き換えた。外部挙動は変わらず（全カテゴリ / カテゴリ指定 / 存在しないカテゴリの各出力が同一）。

現在の主な関数:

| 関数 | 概要 |
|---|---|
| `collect_priority(category_dir, priority)` | 優先度サブディレクトリの `Counter[tuple[str, str]]` を返す |
| `format_priority_line(priority, counter)` | 5 区分の固定表示 + 未知区分のソート済み追記 |
| `print_category(category)` | カテゴリブロック（3 優先度分）を標準出力に表示 |
| `main(argv)` | CLI エントリポイント。終了コード 0 を返す |

## YAML ワークフロー定義

### `scripts/claude_loop.yaml`（フル）のステップ別設定

| ステップ | model | effort | continue |
|---|---|---|---|
| split_plan | opus | high | false |
| imple_plan | opus | high | false |
| wrap_up | sonnet（defaults） | medium（defaults） | true |
| write_current | sonnet（defaults） | low | false |
| retrospective | opus | medium（defaults） | false |

### `scripts/claude_loop_quick.yaml`（quick）のステップ別設定

| ステップ | model | effort | continue |
|---|---|---|---|
| quick_plan | sonnet（defaults） | medium（defaults） | false |
| quick_impl | sonnet（defaults） | high | true |
| quick_doc | sonnet（defaults） | low | true |

## 自動化時の制約

YAML の `command.args` で `--dangerously-skip-permissions` を設定。`command.auto_args`（auto モード時のみ付与）では `--disallowedTools "AskUserQuestion"` と、質問を `REQUESTS/AI/` に書き出す指示 + `.claude/` 編集時の `claude_sync.py` 利用手順を `--append-system-prompt` で注入。

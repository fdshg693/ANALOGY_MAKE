# CURRENT_scripts: util ver6.0 — Python スクリプトと YAML ワークフロー定義

`scripts/` 配下のユーティリティスクリプトと YAML ワークフロー定義。ver6.0 で `issue_status.py` を追加し、`claude_loop.yaml` の `imple_plan` ステップから `continue: true` を削除した。

## ファイル一覧

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/scripts/get_latest_version.sh` | 43 | バージョン番号の算出。`latest` / `major` / `next-minor` / `next-major` の 4 モードに対応 |
| `scripts/claude_loop.py` | 395 | エントリポイント。`claude_loop_lib/` の各モジュールを組み合わせてワークフローを実行 |
| `scripts/claude_loop_lib/__init__.py` | 0 | パッケージ初期化（空） |
| `scripts/claude_loop_lib/workflow.py` | 135 | YAML 読み込み・バリデーション・各設定値のリゾルバ |
| `scripts/claude_loop_lib/commands.py` | 69 | コマンド構築・ステップイテレータ |
| `scripts/claude_loop_lib/feedbacks.py` | 66 | フィードバックファイルのロード・消費 |
| `scripts/claude_loop_lib/logging_utils.py` | 57 | TeeWriter・ログパス生成・ステップヘッダ表示・duration フォーマット |
| `scripts/claude_loop_lib/git_utils.py` | 40 | git HEAD 取得・未コミット検出・自動コミット |
| `scripts/claude_loop_lib/notify.py` | 43 | Windows toast 通知・beep フォールバック |
| `scripts/claude_loop.yaml` | 52 | フルワークフロー定義（5 ステップ）。ver6.0 で `imple_plan` の `continue: true` を削除 |
| `scripts/claude_loop_quick.yaml` | 44 | 軽量ワークフロー定義（3 ステップ） |
| `scripts/claude_sync.py` | 58 | `.claude/` ⇔ `.claude_sync/` 同期。CLI `-p` モードの `.claude/` 編集制限を回避 |
| `scripts/issue_status.py` | 145 | **ver6.0 で新規追加**。`ISSUES/{category}/{high,medium,low}/*.md` の `status × assigned` 分布を表示する読み取り専用スクリプト |
| `scripts/README.md` | 247 | スクリプト全体のドキュメント（ver4.1 で新規作成） |

## scripts/issue_status.py（ver6.0 新規）

### 概要

ISSUE ファイルの `status × assigned` をカテゴリ別・優先度別に集計して表示する読み取り専用スクリプト。書き換えは行わない。

### 仕様

- **入力**: コマンドライン引数 `[category]`（省略時は全カテゴリ）
- **走査対象**: `ISSUES/{category}/{high,medium,low}/*.md`
- **パース**: 先頭 `---` 〜 `---` の YAML を `yaml.safe_load`
- **出力**: カテゴリ → 優先度 → `status/assigned=件数` の表
- **終了コード**: 常に 0（警告は stderr のみ）

### フォールバック

| ケース | 扱い |
|---|---|
| frontmatter 無し | `raw / human` として集計 |
| YAML パース失敗 | `raw / human` として集計（stderr に警告） |
| 既定値外の status / assigned | そのまま集計しつつ stderr に警告 |
| 不正な status × assigned の組み合わせ | 集計するが stderr に警告 |

### 出力フォーマット

```
util:
  high:    ready/ai=0, review/ai=0, need_human_action/human=0, raw/human=0, raw/ai=0
  medium:  ready/ai=1, review/ai=0, need_human_action/human=0, raw/human=0, raw/ai=0
  low:     ready/ai=0, review/ai=0, need_human_action/human=0, raw/human=0, raw/ai=1
app:
  high:    ...
```

0 件時も 5 区分すべてを `=0` で表示する。カテゴリが存在しない場合のみブロックをスキップ。

### 主な関数

| 関数 | 概要 |
|---|---|
| `parse_frontmatter(path)` | 1ファイルを読み `(status, assigned)` を返す。フォールバック処理込み |
| `collect_priority(category_dir, priority)` | 優先度サブディレクトリの `Counter[tuple[str, str]]` を返す |
| `format_priority_line(priority, counter)` | 5 区分の固定表示 + 未知区分のソート済み追記 |
| `print_category(category)` | カテゴリブロック（3 優先度分）を標準出力に表示 |
| `main(argv)` | CLI エントリポイント。終了コード 0 を返す |

`reviewed_at: 2026-04-23`（クオート無し）は `datetime.date` に変換されるが、`parse_frontmatter()` 内で `str()` 強制文字列化して吸収済み。

## scripts/claude_loop.py

`claude_loop_lib/` に委譲する構造は ver5.0 から変わらず。ver6.0 での変更なし（詳細は ver5.0 の CURRENT_scripts.md を参照）。

## YAML ワークフロー定義の構造（変更点のみ）

### `scripts/claude_loop.yaml`（フル）のステップ別設定

| ステップ | model | effort | continue | 備考 |
|---|---|---|---|---|
| split_plan | opus | high | false | 計画策定は重い。前提セッションなし |
| imple_plan | opus | high | **false**（ver6.0 で変更） | ver5.0 では `true`。セッション継続を外した（独立セッションに戻す） |
| wrap_up | sonnet（defaults） | medium（defaults） | true | imple_plan の実装文脈を引き継ぐ |
| write_current | sonnet（defaults） | low | false | ドキュメント整形中心。独立セッション |
| retrospective | opus | medium（defaults） | false | 振り返り。独立セッション |

### `scripts/claude_loop_quick.yaml`（quick）のステップ別設定

| ステップ | model | effort | continue | 理由 |
|---|---|---|---|---|
| quick_plan | sonnet（defaults） | medium（defaults） | false | 軽量計画。独立セッション |
| quick_impl | sonnet（defaults） | high | true | quick_plan の計画文脈を引き継ぐ |
| quick_doc | sonnet（defaults） | low | true | quick_impl の実装文脈を引き継ぐ |

## 自動化時の制約

YAML の `command.args` で `--dangerously-skip-permissions` を設定。`command.auto_args`（auto モード時のみ付与）では `--disallowedTools "AskUserQuestion"` と、質問を `REQUESTS/AI/` に書き出す指示 + `.claude/` 編集時の `claude_sync.py` 利用手順を `--append-system-prompt` で注入。

ログ有効時は `build_command()` が各ステップのコマンドにログファイルパスを `--append-system-prompt` で追加注入する。auto モード時はログパス・モード情報・フィードバックが単一の `--append-system-prompt` に改行区切りで結合される。

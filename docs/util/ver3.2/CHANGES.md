# ver3.2 CHANGES

ISSUES対応: `ISSUES/util/medium/ユーザーFB.md`
ユーザーフィードバックファイルをワークフローステップ実行時にプロンプトへ自動注入する機能を追加。

## 変更ファイル一覧

| ファイル | 種別 | 概要 |
|---|---|---|
| `scripts/claude_loop.py` | 変更 | フィードバック読み込み・注入・消費の3関数追加、`build_command()` と `_run_steps()` の拡張 |
| `tests/test_claude_loop.py` | 変更 | フィードバック関連の5テストクラス・20テストケースを追加 |
| `ISSUES/util/medium/ユーザーFB.md` | 変更 | 制約セクションを追記（Python スクリプトでのプロンプト注入方式を明記） |

## 変更内容の詳細

### `scripts/claude_loop.py`

#### 新規関数（3つ）

1. **`parse_feedback_frontmatter(content) -> (step_names, body)`**
   - フィードバックファイルの YAML frontmatter を解析
   - `step` フィールドが文字列の場合はリストに変換、リストの場合はそのまま返却
   - frontmatter なし・`step` フィールドなしの場合は `step_names=None`（キャッチオール）
   - YAML パースエラー時は元のコンテンツ全体を body として返却

2. **`load_feedbacks(feedbacks_dir, step_name) -> list[(Path, str)]`**
   - `FEEDBACKS/` ディレクトリ内の `*.md` ファイルをアルファベット順に走査
   - `step_names` がマッチするか、キャッチオール（`step_names=None`）のファイルを返却
   - `done/` サブディレクトリ内のファイルは `glob("*.md")` の対象外（直下のみ走査）
   - ディレクトリが存在しない場合は空リストを返却

3. **`consume_feedbacks(files, done_dir) -> None`**
   - 消費済みフィードバックファイルを `done/` ディレクトリへ `shutil.move` で移動
   - `done/` ディレクトリは必要時に自動作成（`mkdir(parents=True, exist_ok=True)`）
   - 空リストの場合はディレクトリ作成もスキップ

#### 既存関数の変更

- **`build_command()`**: `feedbacks` パラメータ（`list[str] | None`）を追加。フィードバックがある場合、`## User Feedback` セクションとして `--append-system-prompt` に注入。複数フィードバックは `---` 区切りで結合
- **`_run_steps()`**: 各ステップ実行前に `load_feedbacks()` でマッチするフィードバックを取得し、`build_command()` に渡す。ステップ正常完了後に `consume_feedbacks()` で消費済みファイルを移動

### `tests/test_claude_loop.py`

5つのテストクラスを追加（計20テストケース）:

| テストクラス | テスト数 | テスト対象 |
|---|---|---|
| `TestParseFeedbackFrontmatter` | 6 | frontmatter 解析（文字列/リスト/なし/無効YAML/空body） |
| `TestLoadFeedbacks` | 7 | ファイル読み込み（マッチ/不一致/キャッチオール/ソート順/done除外） |
| `TestConsumeFeedbacks` | 4 | ファイル移動（正常/ディレクトリ自動作成/空リスト/上書き） |
| `TestBuildCommandWithFeedbacks` | 3 | コマンド構築（注入/複数FB/なし） |

新規インポート: `shutil`, `tempfile`, および `parse_feedback_frontmatter`, `load_feedbacks`, `consume_feedbacks`

## 技術的判断

- **フィードバック注入方式**: SKILL ファイルへの直接埋め込みではなく、Python スクリプト側で `--append-system-prompt` を通じて注入する方式を採用。理由: メンテナンス性・カスタマイズ性が高く、SKILL ファイルの肥大化を防ぐ
- **キャッチオール動作**: `step` フィールドが未指定のフィードバックファイルは全ステップにマッチする仕様。ステップを横断する汎用フィードバックを簡便に記述可能
- **消費タイミング**: ステップ正常完了後に消費（失敗時は消費しない）。失敗時に再度フィードバックが適用されるようにするため
- **同名ファイルの上書き**: `done/` ディレクトリに同名ファイルが存在する場合は上書き。IMPLEMENT.md でリスクとして認識済みだが、シンプルさを優先

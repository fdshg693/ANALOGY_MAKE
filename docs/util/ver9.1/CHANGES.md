# CHANGES: util ver9.1

前バージョン (ver9.0) からの変更差分。

## 変更ファイル一覧

| ファイル | 変更種別 | 概要 |
|---|---|---|
| `scripts/claude_loop.py` | 修正 | `_find_latest_rough_plan` に mtime 閾値対応を追加、関連ヘルパー 2 関数を新設、`_run_auto` にフェーズ 1 前スナップショット記録を追加 |
| `tests/test_claude_loop.py` | 修正 | 閾値ロジック向けテスト 4 件追加、統合テストで `_find_latest_rough_plan` をパッチ |
| `ISSUES/util/medium/issue-plan-split-plan-handoff-verification.md` | 移動 → `done/` | 人間コメントによる実ログ検証で Close 判定済み、status を `done` に更新 |
| `docs/util/ver9.1/MEMO.md` | 追加 | 実装メモ・ROUGH_PLAN との乖離・残課題 |

## 変更内容の詳細

### `scripts/claude_loop.py`

#### 追加: `_rough_plan_candidates(cwd) -> tuple[Path, list[Path]]`

`docs/{category}/ver*/ROUGH_PLAN.md` の候補列挙ロジックを独立関数に切り出した。`_find_latest_rough_plan` と `_run_auto` の両方から呼ばれるため DRY 化のために分離。

#### 追加: `_version_key(path) -> tuple[int, int]`

`ver{X}.{Y}` 形式のディレクトリ名から `(major, minor)` タプルを生成する。`ver10.0 > ver9.1` のような 2 桁以上のバージョンを正しく自然順ソートするために導入（文字列ソートでは `ver9.1 > ver10.0` になる問題を回避）。旧整数形式 `ver9` は `(9, -1)` として扱い、ソート順の一貫性を保持。

#### 修正: `_find_latest_rough_plan(cwd, mtime_threshold=None) -> Path`

`mtime_threshold: float | None = None` 引数を追加。

- `mtime_threshold=None` の場合: 従来通り `max(mtime)` を返す（後方互換）
- `mtime_threshold` が指定された場合:
  - `mtime > threshold` を満たすファイルのみを候補とする（フェーズ 1 開始前に存在したファイルを除外）
  - 候補が複数あれば `_version_key` で最大バージョンを選ぶ
  - 候補 0 件なら `SystemExit` で失敗（「/issue_plan が ROUGH_PLAN.md を書かなかった」ことをユーザーに通知するメッセージ付き）

#### 修正: `_run_auto(...)`

フェーズ 1 実行直前に `_rough_plan_candidates` で既存ファイルを列挙し、`mtime_threshold = max(mtime, default=0.0)` を記録する。フェーズ 2 の `_find_latest_rough_plan` 呼び出し時にこの閾値を渡すことで、フェーズ 1 が書いたファイルのみが候補になる。

### `tests/test_claude_loop.py`

#### 追加: `TestFindLatestRoughPlan` — 閾値テスト 4 件

| テスト名 | 検証内容 |
|---|---|
| `test_threshold_excludes_pre_existing_files` | mtime = threshold のファイルは除外され、mtime > threshold のみ返る |
| `test_threshold_no_new_files_raises` | 全ファイルが mtime ≤ threshold のとき `SystemExit` が発生し適切なメッセージが含まれる |
| `test_threshold_multiple_new_files_highest_version_wins` | 複数の新規ファイルがある場合に最大バージョン（ver10.0）が選ばれる |
| `test_version_key_natural_sort` | `(9,1) < (10,0)` が成立することを確認 |

#### 修正: `TestAutoWorkflowIntegration._run_main_auto`

`claude_loop._find_latest_rough_plan` をパッチして、pre-created stub ファイルを直接返すよう変更した。フェーズ 1 はサブプロセスモックのため実ファイルを作成しないが、従来テストは mtime 依存のため閾値導入後に全件 `SystemExit` となる問題を解消。閾値ロジック自体は `TestFindLatestRoughPlan` で独立テストされるため、統合テストのスコープ（フェーズ 2 ディスパッチ検証）と役割分離が明確になった。

## API 変更

### `_find_latest_rough_plan` のシグネチャ変更

```python
# ver9.0
def _find_latest_rough_plan(cwd: Path) -> Path: ...

# ver9.1
def _find_latest_rough_plan(cwd: Path, mtime_threshold: float | None = None) -> Path: ...
```

デフォルト引数のため後方互換を保持。既存の直接呼び出しは変更不要。

### 新規公開関数

- `_rough_plan_candidates(cwd: Path) -> tuple[Path, list[Path]]`
- `_version_key(path: Path) -> tuple[int, int]`

いずれもモジュール内プライベート（`_` プレフィックス）だが、テストから `from claude_loop import _version_key` でインポート済み。

## 技術的判断

### mtime 厳密比較（`>`）の採用

`mtime > threshold` の厳密比較を採用した。`>=` にするとフェーズ 1 が既存ファイルと同一 mtime で書いた場合に既存ファイルも候補に入り、`touch` 耐性が低下する。厳密比較では FAT32 などの粗い解像度環境で新規ファイルが threshold と同一 mtime になると候補 0 件 → `SystemExit` になり得るが、このケースは実際の FAT32 FS でのみ発生し、現運用環境（NTFS/ext4）では問題ない。

### 統合テストでの `_find_latest_rough_plan` パッチ

統合テストでフェーズ 1 をモックする設計の都合上、実ファイル作成が行われない。閾値ロジックのテストは `TestFindLatestRoughPlan` に集中させ、統合テストは「フェーズ 2 が正しい YAML を起動するか」の検証に限定した。これは単一責任の観点からも適切。

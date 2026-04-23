# CHANGES: util ver9.2

前バージョン (ver9.1) からの変更差分。

## 変更ファイル一覧

| ファイル | 種別 | 概要 |
|---|---|---|
| `scripts/issue_worklist.py` | 変更 | `--limit N` オプション追加、出力関数にトランケーション情報を付加 |
| `tests/test_claude_loop.py` | 変更 | `TestIssueWorklist` クラスに `--limit` 関連テスト 5 件追記 |
| `.claude/skills/issue_plan/SKILL.md` | 変更 | コンテキスト行の `issue_worklist.py` 呼び出しに `--limit 20` を追加 |

## 変更内容の詳細

### `scripts/issue_worklist.py` — `--limit N` オプション追加

**なぜ**: `/issue_plan` SKILL のプロンプトに `issue_worklist.py --format json` の出力が毎回埋め込まれるため、ISSUE 件数増加時にコンテキストが肥大化する問題（`ISSUES/util/low/issue-worklist-json-context-bloat.md`）への防御的対応。

**何を変えたか**:

- `parse_args()`: `--limit` 引数（`type=int, default=None`）を追加。省略時は全件返す（後方互換）
- `main()`: `collect()` 後に `items[:limit]` でスライス。`total = len(全件)` と `limit` を各 format 関数に渡す
- `format_text()`: シグネチャに `total: int | None` / `limit: int | None` を追加。切り捨て発生時（`total > limit`）は末尾に `(showing first N of M issues)` 行を付加
- `format_json()`: シグネチャに `total` / `limit` を追加。`--limit` 指定時のみ `total` / `truncated` / `limit` フィールドをペイロードのトップレベルに追加（`--limit` 未指定時はフィールド自体を省略し後方互換を維持）

**どう変えたか（設計判断）**:

- `collect()` は変更なし。スライスを `main()` に集約することで、`collect()` の責務（収集・フィルタ）と件数上限の責務を分離
- CLI デフォルトを `None`（全件）にし、SKILL 側で `--limit 20` を明示指定する 2 段階方式を採用。これにより `retrospective` SKILL など `--limit` 未指定の既存呼び出しに影響を与えない

### `tests/test_claude_loop.py` — `--limit` テスト追加

`TestIssueWorklist` クラスに以下 5 ケースを追記:

1. `test_limit_returns_top_n_in_priority_order` — `--limit 3` で先頭 3 件が priority 順で返り、JSON に `total=6 / truncated=true / limit=3` が含まれること
2. `test_limit_omitted_returns_all` — `--limit` 省略時は全件返り、JSON に `total` フィールドが含まれないこと（後方互換確認）
3. `test_limit_exceeds_count_no_truncation` — `--limit 100` で件数超過時は切り捨てが発生せず `truncated=false` であること
4. `test_limit_text_format_appends_truncation_note` — `text` 形式で切り捨て発生時に補助行が出ること
5. `test_limit_text_format_no_note_when_not_truncated` — `text` 形式で切り捨てなし時に補助行が出ないこと

### `.claude/skills/issue_plan/SKILL.md` — コンテキスト行の更新

```diff
- AI 向け ready/review ISSUE: !`python scripts/issue_worklist.py --format json`
+ AI 向け ready/review ISSUE: !`python scripts/issue_worklist.py --format json --limit 20`
```

これにより `/issue_plan` SKILL 起動時に埋め込まれる ISSUE リストが常に 20 件以内に収まる。

## API変更

### `format_text(category, items, total=None, limit=None)`

引数 `total: int | None` と `limit: int | None` を追加（省略可能、デフォルト `None`）。既存呼び出しは無変更で動作する。

### `format_json(category, assigned, status_list, items, total=None, limit=None)`

引数 `total: int | None` と `limit: int | None` を追加（省略可能、デフォルト `None`）。`total` が指定された場合、出力 JSON のトップレベルに `total` / `truncated` / `limit` フィールドを追加する。

## 技術的判断

### CLI デフォルトを `None`（全件）にする理由

ISSUE 本文は「デフォルト 20 件程度」を提案していたが、CLI のデフォルトを `None` にすることで:

- `retrospective` SKILL など `--limit` を指定しない既存の呼び出し元が全件を引き続き受け取れる（後方互換）
- `--limit` を必要とする呼び出し元（`/issue_plan` SKILL）が明示的に件数を指定するため、意図が明確になる
- 将来的に呼び出し元ごとに異なる上限を設定しやすい

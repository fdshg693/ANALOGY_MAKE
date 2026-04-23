# ver12.1 CHANGES

前バージョン: ver12.0（`b5fc206`）→ 本バージョン: ver12.1（HEAD）

## 変更ファイル一覧

| ファイル | 種別 | 概要 |
|---|---|---|
| `scripts/issue_worklist.py` | 修正 | `main()` — `--limit` 省略時の JSON ペイロードから `total`/`truncated`/`limit` を除外 |
| `ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md` | 移動 | → `ISSUES/util/done/`（消化済み） |

## 変更内容の詳細

### `scripts/issue_worklist.py` — `main()` の `total` 計算タイミング修正

**なぜ**: `--limit` 省略時（`args.limit is None`）でも `total = len(items)` が常に評価されていたため、`format_json()` の `if total is not None:` ガードが機能せず、JSON ペイロードに `total`/`truncated`/`limit` フィールドが混入していた。ver9.2 設計意図（`--limit` 未指定時はこれらのフィールドを省略）に反し、`test_limit_omitted_returns_all` が ver10.0 以来失敗し続けていた（pre-existing 失敗、3バージョン連続持ち越し）。

**何を**: `total = len(items)` の代入を `if limit is not None:` ブロック内に移動し、`total` の初期値を `None` にした。

**どう変えたか**:

```python
# 変更前
items = collect(args.category, args.assigned, status_list)
total = len(items)
limit: int | None = args.limit
if limit is not None:
    items = items[:limit]

# 変更後
items = collect(args.category, args.assigned, status_list)
limit: int | None = args.limit
total: int | None = None
if limit is not None:
    total = len(items)
    items = items[:limit]
```

**影響範囲**: `--limit` 指定時の挙動は変化なし（`total`/`truncated`/`limit` を従来通り出力）。`--limit` 省略時のみ JSON ペイロードが `category`/`filter`/`items` の 3 キーのみになる。

## API変更

### `scripts/issue_worklist.py` — JSON 出力形式（`--format json` 時）

| 状況 | 変更前 | 変更後 |
|---|---|---|
| `--limit` 省略時 | `total`, `truncated`, `limit` が誤って出力されていた（バグ） | これら 3 フィールドを含まない（仕様通り） |
| `--limit` 指定時 | `total`, `truncated`, `limit` を出力 | 変更なし |

`format_json()` / `format_text()` 関数自体のシグネチャは変更なし（`total=None, limit=None` のデフォルト引数は ver9.2 から存在）。

## 技術的判断

- **実装側の修正を選択**: テストの期待値（`"total" not in payload`）を変更せず、実装を ver9.2 の設計意図に揃えた。テスト名 `test_limit_omitted_returns_all` が仕様ドキュメントとして機能しており、テスト側が正しいと判断
- **`claude_loop_lib/issues.py` は変更なし**: FEEDBACKS/NEXT.md では変更対象候補として挙がっていたが、実際の `limit` 制御ロジックは `scripts/issue_worklist.py` 側にあり、変更は不要だった（ROUGH_PLAN の「状況次第」注記通り）

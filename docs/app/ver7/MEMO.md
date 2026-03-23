# ver7 実装メモ

## h3 イベントモック戦略（実装時に決定）

サーバーAPIテストで h3 イベントをモックする方法は2つの候補がある:

### 候補A: `createEvent` で実際の h3 イベントを構築
- `IncomingMessage` に body を注入して `createEvent` に渡す
- 実際の h3 の挙動に近いが、`Readable` ストリームの手組みが必要でやや煩雑

### 候補B（推奨）: `vi.mock('h3')` で h3 関数自体をモック
- `readBody` をモックして固定値を返す
- `createEventStream` をモックして `{ push: vi.fn(), close: vi.fn(), send: vi.fn(), onClosed: vi.fn() }` を返す
- `createError` と `defineEventHandler` は実際の h3 のものを使うか、シンプルなモックにする
- ハンドラ関数を直接呼び出せてシンプル

実装時に詰まった場合は候補Bを優先して試す。

**結果**: 候補B を採用。h3 関数をすべて `vi.mock('h3')` でモックし、ハンドラ関数を直接呼び出す方式で実装した。

## 計画との乖離

### `vi.mock` のパス解決

IMPLEMENT.md では `vi.mock('../utils/analogy-agent')` と記載していたが、vitest の `vi.mock()` はテストファイルからの相対パスで解決するため、`tests/server/chat.test.ts` からは `../../server/utils/analogy-agent` が正しいパスだった。実装時に修正済み。

## 更新が必要そうなドキュメント

- `ISSUES/high/auto-test.md` — ver7 で対応済みのため、状態を更新する（`CURRENT.md` 更新フローで対応）
- `ISSUES/low/sse-parser-extraction.md` — SSEパーサー切り出しは ver7 で実施済み。状態更新が必要
- `docs/ver6/CURRENT.md` の ISSUES 管理表 — auto-test の状態を「ver7 で対応済み」に更新

## 削除が推奨されるもの

なし

---

## wrap_up 対応結果

| # | 項目 | 対応 | 詳細 |
|---|---|---|---|
| 1 | h3 イベントモック戦略 | ⏭️ 対応不要 | 実装時に候補B採用で解決済み。記録として残すのみ |
| 2 | 計画との乖離（vi.mock パス） | ⏭️ 対応不要 | 実装時に修正済み |
| 3a | `ISSUES/high/auto-test.md` 状態更新 | ✅ 対応完了 | ユーザーからの指示でISSUEは削除|
| 3b | `ISSUES/low/sse-parser-extraction.md` 状態更新 | ✅ 対応完了 | ユーザーからの指示でISSUEは削除|
| 3c | `docs/ver6/CURRENT.md` ISSUES管理表更新 | ⏭️ 対応不要 | ver6 CURRENT.md は ver6 完了時点の歴史的スナップショット。過去バージョンのスナップショットを遡及更新するのではなく、ver7 CURRENT.md に現在の状態を記録するのが適切（plan_review_agent 承認済み） |
| 4 | 削除推奨 | ⏭️ 対応不要 | 該当なし |

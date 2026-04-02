# ver11 実装メモ

## 計画との乖離

### better-sqlite3 の直接依存追加

`thread-store.ts` が `better-sqlite3` を直接インポートするため、`pnpm add better-sqlite3` および `pnpm add -D @types/better-sqlite3` で直接依存に追加した。元々はトランジティブ依存（`@langchain/langgraph-checkpoint-sqlite` 経由）として存在していたが、pnpm の厳密な依存解決により直接インポートが不可能だった。

⏭️ 対応不要 — 実装は完了しており、計画との乖離の記録として十分。

### generateTitle での apiKey 取得

IMPLEMENT.md では `generateTitle` 関数で `ChatOpenAI` のコンストラクタに `apiKey` を渡していなかったが、`useRuntimeConfig()` 経由で API キーを取得するように実装した。既存の `analogy-agent.ts` と同じパターン。

⏭️ 対応不要 — 実装は完了しており、計画との乖離の記録として十分。

## テスト関連の注意点

### thread-store.test.ts の CJS モジュールモック

`better-sqlite3` は CJS モジュールのため、vitest の `vi.importActual` でのインポートが不安定。`createRequire(import.meta.url)` を使って vitest のモック解決を回避し、実際の `better-sqlite3` コンストラクタを取得するアプローチを採用した。

⏭️ 対応不要 — テスト実装上の注意点の記録として十分。

## 更新が必要そうなドキュメント

- `CURRENT.md` — ver11 完了時のコード現況を新規作成する必要あり
- `CLAUDE.md` — `better-sqlite3` の直接依存追加を反映

✅ 対応完了:
- `docs/app/ver11/CURRENT.md` を新規作成（ver11 完了時のコード現況）
- `CLAUDE.md` の「開発上の注意」セクションに `better-sqlite3` 直接依存の記述を追加

## 追加の動作確認

- dev サーバー起動 + ブラウザでのスレッド切り替え動作は未確認（ユーザー確認待ち）

⏭️ 対応不要 — ユーザー手動確認の範囲であり、wrap_up のスコープ外。

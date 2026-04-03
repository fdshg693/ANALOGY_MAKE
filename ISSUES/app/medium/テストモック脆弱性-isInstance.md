# テストモックの脆弱性: isInstance 依存

## 概要

ver14.3 で追加したテスト（`tests/server/chat-history.test.ts`）の「isInstance ベースの型チェックでデシリアライズ後メッセージを正しく処理」は、`HumanMessage.isInstance` / `AIMessage.isInstance` の内部実装に依存したモックを使用している。

## 詳細

モックは以下の構造に依存:
- `Symbol.for('langchain.message')` プロパティの存在
- `type` プロパティ（`"human"` / `"ai"`）

`@langchain/core` のバージョンアップで `isInstance` の判定ロジックが変更された場合、モック構造の見直しが必要。

## 対応タイミング

`@langchain/core` のメジャーバージョンアップ時にモックが壊れていないか確認する。

## 関連事例

- ver14.4: `logger.ts` に `appendFileSync` を追加した際、`tests/server/thread-store.test.ts` の `node:fs` モック全体に `appendFileSync: vi.fn()` の追加が必要になった。モジュール全体をモックする際に新しいエクスポートが追加されると壊れるパターンであり、`isInstance` の件と同根の問題。

## 発生バージョン

ver14.3

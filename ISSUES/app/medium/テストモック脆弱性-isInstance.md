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

## 発生バージョン

ver14.3

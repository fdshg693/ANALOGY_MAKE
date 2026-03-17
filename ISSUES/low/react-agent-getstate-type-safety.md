# ReactAgent.getState() の型安全性

## 概要

`server/api/chat/history.get.ts` で `ReactAgent.getState()` を呼び出す際に `(agent as any).getState()` という型キャストを使用している。`ReactAgent` の `getState()` は `@internal` として `never` 型で公開されているため、型安全にアクセスできない。

## リスク

- LangChain/LangGraph のバージョンアップで `getState()` の内部実装が変更された場合、ランタイムエラーになる可能性がある
- `as any` により TypeScript の型チェックが無効化されており、引数・戻り値の不整合を検出できない

## 対応候補

- LangGraph の正式な公開APIで `getState()` 相当の機能が提供されるか定期的に確認する
- `@langchain/langgraph` のバージョンアップ時に、型定義の変更を確認し、`as any` を除去できるか検討する
- 代替手段として、SQLite データベースを直接クエリして会話履歴を取得する方式も検討可能

## 発生バージョン

ver10（会話履歴永続化の導入時）

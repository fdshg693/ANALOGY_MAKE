# ver2 実装メモ

## 確認済み事項

- **API接続の動作確認**: 2026-03-16 実施済み。`pnpm exp:basic` / `exp:memory` / `exp:analogy` すべて正常動作
  - 3形式（文字列 / HumanMessageクラス / {role, content}オブジェクト）すべてで応答取得を確認
  - `usage_metadata` によるトークン使用量の取得も確認
- **`createAgent` API の動作**: `langchain` v1.2.32 の `createAgent` は `{ model, tools, prompt, checkpointer }` の引数で正常動作。ドキュメントと実装の乖離なし
- **会話メモリ管理方式の決定**: **アプローチB（MemorySaver / LangGraph チェックポイント）を採用**。ver3 で `server/api/chat.post.ts` に統合する際に MemorySaver + thread_id 管理を導入する

## リファクタリングの検討事項（ver3 向け）

- **`02-memory-management.ts` の整理**: アプローチB採用が決定。ver3 でアプローチA のコードを削除し、MemorySaver 方式を `server/api/chat.post.ts` に統合する
- **アナロジープロンプトの改善**: `03-analogy-prompt.ts` の実験で、類似事例にカワセミが自動で挙がらなかった。プロンプトに「生物の形態模倣（バイオミミクリー）」を例示カテゴリとして追加することを検討

## 対応不要と判断した事項

- **LangChain メッセージ型の使い分けドキュメント**: ユーザー判断により不要。コード内コメントで十分

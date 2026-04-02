# ver14.0 実装メモ

## IMPLEMENT.md との乖離

### TavilySearch.invoke() の入力形式

IMPLEMENT.md では `tavily.invoke(query)` と文字列を直接渡す設計だったが、`@langchain/tavily` の型定義では `StructuredToolCallInput` を要求するため、`tavily.invoke({ query })` に変更した。

> ⏭️ **対応不要**: 実装時に対応済み。ドキュメント上の記録のみ。

### chat.post.ts のメッセージ入力形式

既存コードでは `{ role: "user", content: body.message }` というプレーンオブジェクトを `stream()` に渡していたが、`StateGraph` の `messages` フィールドは `BaseMessage[]` 型を要求するため、`new HumanMessage(body.message)` に変更した。

> ⏭️ **対応不要**: 実装時に対応済み。ドキュメント上の記録のみ。

## リスク・検証が必要な項目

### streamMode: "messages" のメタデータ構造

IMPLEMENT.md に記載の通り、`streamMode: "messages"` でメタデータに `langgraph_node` が含まれることは型定義から推測されるが、実際のランタイム動作は未検証。dev起動での手動テストで確認が必要。

> ⏭️ **対応不要**: `chat.post.ts` で `metadata?.langgraph_node` をオプショナルチェーンで参照し、`STREAMED_NODES.has()` でフィルタリング。メタデータが存在しない場合も安全に `false` を返す防御的な実装。手動テストでの動作確認は引き続き推奨。

### abstractionNode の LLM 出力ストリーミング混入

`streamMode: "messages"` は全ノードの LLM 呼び出しをインターセプトする。abstractionNode の出力をメタデータの `langgraph_node` でフィルタリングする設計だが、メタデータが期待通りにノード名を含まない場合、不要なトークンがクライアントに送信される可能性がある。

> ⏭️ **対応不要**: `STREAMED_NODES = new Set(["caseSearch", "solution", "followUp"])` でホワイトリスト方式のフィルタリングを実装済み。`abstraction` は明示的に除外されており、メタデータなしの場合もストリーミングされない安全な設計。

### LangGraph チェックポイントの互換性

既存の SQLite チェックポイントデータは `createReactAgent` のステート構造で保存されている。`StateGraph` への移行によりステート構造が変わったため、既存チェックポイントは読み込めない可能性がある。`data/` ディレクトリの削除が必要。

> ⏭️ **対応不要**: 開発専用プロジェクト（本番デプロイなし）であり、`data/` は `.gitignore` 済み。問題発生時は手動削除で対応可能。

## 削除を推奨するもの

### ISSUES/app/low/streaming-tool-call-compatibility.md

Tavily Search がツールとしてではなくノード内で直接呼び出されるようになったため、ツール呼び出し時のストリーミング互換性の検証は不要になった。

> ⏭️ **対応不要**: ファイルは既に存在しない（削除済み）。

## wrap_up 時の追加対応

### ISSUES/app/low/react-agent-getstate-type-safety.md を削除

v14.0 で `createReactAgent` → `StateGraph` に移行した結果、`history.get.ts` の `agent.getState()` が `(agent as any)` キャストなしで型安全に呼び出せるようになったため、当該 ISSUE は解決済みとして削除した。

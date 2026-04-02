# ver14.0 実装メモ

## IMPLEMENT.md との乖離

### TavilySearch.invoke() の入力形式

IMPLEMENT.md では `tavily.invoke(query)` と文字列を直接渡す設計だったが、`@langchain/tavily` の型定義では `StructuredToolCallInput` を要求するため、`tavily.invoke({ query })` に変更した。

### chat.post.ts のメッセージ入力形式

既存コードでは `{ role: "user", content: body.message }` というプレーンオブジェクトを `stream()` に渡していたが、`StateGraph` の `messages` フィールドは `BaseMessage[]` 型を要求するため、`new HumanMessage(body.message)` に変更した。

## リスク・検証が必要な項目

### streamMode: "messages" のメタデータ構造

IMPLEMENT.md に記載の通り、`streamMode: "messages"` でメタデータに `langgraph_node` が含まれることは型定義から推測されるが、実際のランタイム動作は未検証。dev起動での手動テストで確認が必要。

### abstractionNode の LLM 出力ストリーミング混入

`streamMode: "messages"` は全ノードの LLM 呼び出しをインターセプトする。abstractionNode の出力をメタデータの `langgraph_node` でフィルタリングする設計だが、メタデータが期待通りにノード名を含まない場合、不要なトークンがクライアントに送信される可能性がある。

### LangGraph チェックポイントの互換性

既存の SQLite チェックポイントデータは `createReactAgent` のステート構造で保存されている。`StateGraph` への移行によりステート構造が変わったため、既存チェックポイントは読み込めない可能性がある。`data/` ディレクトリの削除が必要。

## 削除を推奨するもの

### ISSUES/app/low/streaming-tool-call-compatibility.md

Tavily Search がツールとしてではなくノード内で直接呼び出されるようになったため、ツール呼び出し時のストリーミング互換性の検証は不要になった。

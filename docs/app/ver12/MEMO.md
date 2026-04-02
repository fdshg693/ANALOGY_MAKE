# ver12 実装メモ

## 計画との乖離

### TavilySearch コンストラクタのパラメータ名

IMPLEMENT.md では `apiKey` と記載されていたが、実際の `@langchain/tavily@1.2.0` の型定義では `tavilyApiKey` が正しいパラメータ名だった。`tavilyApiKey` を使用して実装した。

## ストリーミングとツール呼び出しの互換性（未検証）

IMPLEMENT.md のリスク2で指摘されている、ツール呼び出し時の `ToolMessage` や `AIMessageChunk` の `tool_calls` プロパティの混在について、実際の Tavily API キーを使った動作確認は未実施。`chat.post.ts` の `chunk instanceof AIMessageChunk && typeof chunk.content === 'string' && chunk.content` フィルタで問題ないかは、実環境での確認が必要。

問題が発生した場合、`ToolMessage` のフィルタリングを `chat.post.ts` に追加する必要がある。

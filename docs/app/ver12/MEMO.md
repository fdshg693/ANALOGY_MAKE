# ver12 実装メモ

## 計画との乖離

### TavilySearch コンストラクタのパラメータ名

IMPLEMENT.md では `apiKey` と記載されていたが、実際の `@langchain/tavily@1.2.0` の型定義では `tavilyApiKey` が正しいパラメータ名だった。`tavilyApiKey` を使用して実装した。

## ストリーミングとツール呼び出しの互換性（未検証）

IMPLEMENT.md のリスク2で指摘されている、ツール呼び出し時の `ToolMessage` や `AIMessageChunk` の `tool_calls` プロパティの混在について、実際の Tavily API キーを使った動作確認は未実施。`chat.post.ts` の `chunk instanceof AIMessageChunk && typeof chunk.content === 'string' && chunk.content` フィルタで問題ないかは、実環境での確認が必要。

問題が発生した場合、`ToolMessage` のフィルタリングを `chat.post.ts` に追加する必要がある。

---

## wrap_up 対応結果

### 1. TavilySearch コンストラクタのパラメータ名
- **⏭️ 対応不要**: 計画との乖離の記録として完結しており、コードは正しい `tavilyApiKey` で実装済み。修正不要。

### 2. ストリーミングとツール呼び出しの互換性（未検証）
- **📋 次バージョンへ先送り**: 実 Tavily API キー環境での動作確認が必要であり、wrap_up スコープ外。現行フィルタは `instanceof AIMessageChunk` で `ToolMessage` を除外し、`typeof chunk.content === 'string'` で配列型コンテンツも除外する防御的実装。`ISSUES/app/low/streaming-tool-call-compatibility.md` として Issue 登録済み。

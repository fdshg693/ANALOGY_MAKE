# ストリーミングとツール呼び出しの互換性検証

## 概要

Tavily検索ツール統合時のストリーミング処理で、実Tavily APIキー環境での動作確認が未実施。

## 詳細

`server/api/chat.post.ts` のストリーミングフィルタ:

```ts
chunk instanceof AIMessageChunk && typeof chunk.content === 'string' && chunk.content
```

このフィルタは理論上、以下を正しく処理する:
- `ToolMessage` → `instanceof AIMessageChunk` で除外
- `AIMessageChunk.content` が配列型（`tool_use` ブロック含む）→ `typeof chunk.content === 'string'` で除外

ただし、実際のTavily API呼び出しを含むストリーミングで、`AIMessageChunk.content` が配列型で返るケースの実環境検証が必要。

## 対応方針

実Tavily APIキーを用いた環境で、検索ツールが呼ばれるような質問を送信し、ストリーミングが正常に動作することを確認する。

## 発生元

ver12 MEMO.md（IMPLEMENT.md リスク2）

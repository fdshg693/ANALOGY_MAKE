# ver5 リファクタリング計画

## 結論: 大規模なリファクタリングは不要

ver5の変更はSSEパーサーのイベントハンドリング追加とエラー表示UIの追加であり、既存コードの構造変更を必要としない。以下の軽微な変更のみ。

## 1. Message インターフェースの拡張

**対象**: `app/pages/index.vue` 2行目

```typescript
// 現状
interface Message {
  role: 'user' | 'assistant'
  content: string
}

// 変更後
interface Message {
  role: 'user' | 'assistant'
  content: string
  isError?: boolean
}
```

**理由**: エラーメッセージを通常のassistantメッセージと視覚的に区別するため。ChatMessage コンポーネントにフラグを渡し、エラー時に異なるスタイルを適用する。

## 2. catch ブロックの整理

**対象**: `app/pages/index.vue` 70-75行目

現在の `catch` ブロックはコンテンツが空のassistantメッセージを `pop()` するが、ver5では空メッセージを削除する代わりにエラーメッセージを表示する方針に統一する。これにより、SSE `error` イベント経由のエラーと `catch` 経由のエラーで同一の表示方式になる。

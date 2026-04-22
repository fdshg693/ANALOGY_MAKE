# フロントエンド現況（ver16.0）

## ページ

### `app/app.vue`（7行）

変更なし。`<NuxtRouteAnnouncer />` と `<NuxtPage />` を配置するルートレイアウト。

### `app/pages/index.vue`（169行）

- 2カラムレイアウト: `ThreadSidebar` + チャットエリア（`display: flex`, `height: 100dvh`）
- `useChat()`, `useThreads()`, `useSettings()` を統合利用
- **ver16.0 変更**: メッセージループで assistant メッセージかつ `msg.searchResults?.length` がある場合に `SearchResultsList` コンポーネントを `ChatMessage` の直後に挿入

```vue
<template v-for="(msg, i) in messages" :key="i">
  <ChatMessage ... />
  <SearchResultsList
    v-if="msg.role === 'assistant' && msg.searchResults?.length"
    :results="msg.searchResults"
  />
</template>
```

## コンポーネント

### `app/components/SearchResultsList.vue`（74行）— ver16.0 新規

Tavily 検索結果を折りたたみ表示するコンポーネント。

- **Props**: `results: SearchResult[]`（`useChat.ts` から import）
- **UI 構成**: HTML ネイティブ `<details>`/`<summary>` で折りたたみ。デフォルトで閉じた状態
- `getDomain(url)`: `new URL(url).hostname` でドメイン名を抽出（`www.` 除去）
- 各検索結果: タイトル（外部リンク、`target="_blank" rel="noopener noreferrer"`）・ドメイン・スニペット
- `max-width: 80%`, `align-self: flex-start` で assistant メッセージと同じ幅感に合わせる
- Vue テンプレート補間で XSS を自動エスケープ

### `app/components/SettingsPanel.vue`（156行）

ver16.0 で変更なし。粒度プリセット・カスタム指示・検索設定（ON/OFF・深度・件数）の UI を提供。

### `app/components/ChatMessage.vue`（181行）

ver16.0 で変更なし。Markdown レンダリング（`marked` + `DOMPurify`）、80ms スロットリング。

### `app/components/ChatInput.vue`（86行）

ver16.0 で変更なし。送信・停止ボタン。

### `app/components/ThreadSidebar.vue`（131行）

ver16.0 で変更なし。スレッド一覧・新規作成。

## Composables

### `app/composables/useChat.ts`（138行）

- **ver16.0 追加**: `SearchResult` インターフェース（`{ title, url, content }`）をエクスポート
- **ver16.0 変更**: `Message` インターフェースに `searchResults?: SearchResult[]` を追加
- **ver16.0 変更**: `sendMessage()` で `onSearchResults` コールバックを `parseSSEStream` に渡す。型ガードで `unknown[]` → `SearchResult[]` に変換し、`assistantMessage.searchResults` に設定
- **ver16.0 変更**: `loadHistory()` は `data.messages` をそのまま代入（`searchResults` フィールドが含まれる場合も JSON.parse の `any` 相当で通る）

```typescript
export interface SearchResult {
  title: string
  url: string
  content: string
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
  isError?: boolean
  searchResults?: SearchResult[]  // ver16.0 追加
}
```

### `app/composables/useThreads.ts`（86行）

ver16.0 で変更なし。

### `app/composables/useSettings.ts`（44行）

ver16.0 で変更なし。

## ユーティリティ

### `app/utils/sse-parser.ts`（59行）

- **ver16.0 変更**: `SSECallbacks` に `onSearchResults?: (results: unknown[]) => void` を追加（オプショナル）
- **ver16.0 変更**: `search_results` イベントの dispatch を `done` 処理の前に配置

```typescript
export interface SSECallbacks {
  onToken: (content: string) => void
  onDone: () => void
  onError: (message: string) => void
  onSearchResults?: (results: unknown[]) => void  // ver16.0 追加
}
```

dispatch ロジック（`done` の `return` より前）:

```typescript
if (eventType === 'search_results' && data) {
  const parsed = JSON.parse(data)
  callbacks.onSearchResults?.(Array.isArray(parsed.results) ? parsed.results : [])
}

if (eventType === 'done') {
  callbacks.onDone()
  return
}
```

`onSearchResults` をオプショナルにすることで既存テストへの影響を最小化。

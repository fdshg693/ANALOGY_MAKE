# フロントエンド現況（ver17.0）

## ページ

### `app/app.vue`（7行）

変更なし。`<NuxtRouteAnnouncer />` と `<NuxtPage />` を配置するルートレイアウト。

### `app/pages/index.vue`（243行）

- 2カラムレイアウト: `ThreadSidebar` + チャットエリア（`display: flex`, `height: 100dvh`）
- `useChat()`, `useThreads()`, `useSettings()`, `useBranches()` を統合利用（ver17.0 で `useBranches` 追加）

**ver17.0 追加の配線:**

- `onMounted` / `switchThread` で `useBranches.loadBranches(threadId)` を実行してアクティブ分岐を復元
- `ChatMessage` の `start-edit` イベントでフォームを編集モードに切替（`editMode` state 更新）
- `ChatInput` の `submit-edit` で `useBranches.fork(...)` → 成功後 `useChat.sendMessage(newMessage)`
- `BranchNavigator` の `switch-branch` で `useBranches.setActiveBranch(...)` → `useChat.switchThread(threadId, newBranchId)`

**ver16.0 のメッセージ表示ループ:**

```vue
<template v-for="(msg, i) in messages" :key="i">
  <ChatMessage ... @start-edit="onStartEdit(i)" />
  <BranchNavigator
    v-if="msg.role === 'user' && hasBranchAtIndex(i)"
    :branches="branches"
    :active-branch-id="activeBranchId"
    :fork-message-index="i"
    @switch-branch="onSwitchBranch"
  />
  <SearchResultsList
    v-if="msg.role === 'assistant' && msg.searchResults?.length"
    :results="msg.searchResults"
  />
</template>
```

## コンポーネント

### `app/components/BranchNavigator.vue`（94行）— ver17.0 新規

同一 `forkMessageIndex` を持つ分岐グループを `◀ N/M ▶` ナビで表示。

- **Props**: `branches: Branch[]`, `activeBranchId: string`, `forkMessageIndex: number`
- **表示条件**: 同じ `forkMessageIndex` を持つ分岐（main を含め）が 2 つ以上あるとき
- 現在アクティブな分岐の位置（N/M）を計算して表示
- **emit**: `switch-branch(branchId: string)` — 分岐切替を親に通知

### `app/components/ChatMessage.vue`（224行）

- **ver17.0 追加**: ユーザーメッセージのホバー時に「編集」ボタンを表示（`.chat-message.user:hover .edit-btn`、`opacity: 0 → 1`）
- 「編集」クリック時: emit `start-edit(messageIndex: number)`
- AI メッセージは変更なし（Markdown レンダリング、検索結果は `SearchResultsList` で別表示）
- Markdown レンダリング（`marked` + `DOMPurify`）、80ms スロットリング（ver16.x から継続）

### `app/components/ChatInput.vue`（131行）

- **ver17.0 追加**: `editMode: { messageIndex: number, originalText: string } | null` prop を受け取る
- 編集モード時:
  - テキストエリアに `originalText` を初期表示
  - 送信ボタンのラベルを「分岐として送信」に変更
  - キャンセルボタン表示 → emit `cancel-edit`
  - 送信時は emit `submit-edit`（通常送信 `submit` とは別イベント）

### `app/components/SearchResultsList.vue`（74行）

ver17.0 で変更なし。Tavily 検索結果を HTML `<details>`/`<summary>` で折りたたみ表示。

### `app/components/SettingsPanel.vue`（156行）

ver17.0 で変更なし。粒度プリセット・カスタム指示・検索設定・応答モード切替・システムプロンプト上書き（dev のみ）を提供。

### `app/components/ThreadSidebar.vue`（131行）

ver17.0 で変更なし。スレッド一覧・新規作成。

## Composables

### `app/composables/useBranches.ts`（71行）— ver17.0 新規

```typescript
export const MAIN_BRANCH_ID = 'main'   // サーバー側と重複定義（shared/ 統合は将来対応）

export interface Branch {
  branchId: string
  parentBranchId: string | null
  forkMessageIndex: number | null
  createdAt: string | null
}

export function useBranches() {
  const branches = ref<Branch[]>([])
  const activeBranchId = ref<string>('main')

  async function loadBranches(threadId: string): Promise<void>
  async function setActiveBranch(threadId: string, branchId: string): Promise<void>
  async function fork(params: {
    threadId: string
    fromBranchId: string
    forkMessageIndex: number
  }): Promise<string>
  // fork: POST /api/chat/fork → branchId 返却 → activeBranchId.value 更新 → loadBranches 再取得

  return { branches, activeBranchId, loadBranches, setActiveBranch, fork }
}
```

- `setActiveBranch`: `PUT /api/threads/:id/settings` で `{ activeBranchId }` のみ渡す
- `fork`: fork API のみ。AI 応答生成は呼び出し側（`index.vue`）が `useChat.sendMessage()` を続けて呼ぶ

### `app/composables/useChat.ts`（141行）

- **ver17.0 追加**: `currentBranchId: Ref<string>` を保持（`useBranches` の `activeBranchId` と `index.vue` で同期）
- **ver17.0 変更**: `switchThread(threadId, branchId = 'main')` にシグネチャ拡張。`branchId` を `GET /api/chat/history` クエリに含める
- **ver17.0 変更**: `sendMessage()` で fetch body に `branchId` を含める
- **ver17.0 追加**: `startEdit(messageIndex)` — 編集対象インデックスをセット
- **ver16.0 変更**: `Message` インターフェースに `searchResults?: SearchResult[]` を追加（継続）

```typescript
export interface Message {
  role: 'user' | 'assistant'
  content: string
  isError?: boolean
  searchResults?: SearchResult[]
}
```

### `app/composables/useThreads.ts`（86行）

ver17.0 で変更なし。スレッド一覧・アクティブスレッド（localStorage 永続化）。

### `app/composables/useSettings.ts`（66行）

- **ver17.0 追加**: `ThreadSettings` に `activeBranchId: string`（デフォルト `'main'`）を追加
- **ver16.1 追加**: `responseMode: ResponseMode`, `systemPromptOverride: string` を追加（継続）
- サーバー側 `ThreadSettings` と型定義を重複保持（`shared/` 統合は将来対応）

```typescript
export interface ThreadSettings {
  granularity: 'concise' | 'standard' | 'detailed'
  customInstruction: string
  search: SearchSettings
  responseMode: ResponseMode
  systemPromptOverride: string
  activeBranchId: string   // ver17.0 追加
}
```

## ユーティリティ

### `app/utils/sse-parser.ts`（59行）

ver17.0 で変更なし。

```typescript
export interface SSECallbacks {
  onToken: (content: string) => void
  onDone: () => void
  onError: (message: string) => void
  onSearchResults?: (results: unknown[]) => void  // ver16.0 追加
}
```

`search_results` イベントを `done` より前に dispatch するロジックを含む。

## 既知の制限（スコープ外）

- AI メッセージ編集不可（ユーザーメッセージのみ）
- 分岐ツリー階層の可視化なし（同一 `forkMessageIndex` グループのみ）
- 分岐削除・マージ・命名なし
- エコーモードでの分岐ナビゲーション専用 UX なし

# フロントエンド現況

## ページ

### `app/app.vue`（7行）

- `<NuxtRouteAnnouncer />` と `<NuxtPage />` を配置するルートレイアウト

### `app/pages/index.vue`（169行）

- 2カラムレイアウト: `ThreadSidebar` + チャットエリア（`display: flex`, `height: 100dvh`）
- `useChat()`, `useThreads()`, `useSettings()` を統合利用
- **ver15.0 追加**: ヘッダーに設定ボタン（歯車アイコン `&#9881;`）、`showSettings` ref で `SettingsPanel` の開閉制御
- 初期化フロー（`onMounted`）:
  1. `initActiveThread()` — localStorage からアクティブスレッドID復元
  2. `loadThreads()` — サーバーからスレッド一覧取得
  3. `activeThreadId` があれば `switchThread()` + `loadSettings()` で会話履歴・設定ロード、なければ `handleNewThread()` で新規作成
- スレッド切り替え: `handleSelectThread()` で `switchThread()` + `loadSettings()` を呼び出し
- 新規スレッド作成: `handleNewThread()` で `createNewThread()` + `switchThread()` + `loadSettings()`（前スレッドの設定残留を防止）
- 自動スクロール: `watch` で `messages.length` と最終メッセージの `content.length` を結合監視

## コンポーネント

### `app/components/SettingsPanel.vue`（156行）— ver15.0 新規

スレッドごとのAI回答設定を管理するパネルコンポーネント。

- **Props**: `settings: ThreadSettings`, `isSaving: boolean`
- **Emits**: `update:settings`, `save`
- **UI 構成**:
  - 回答粒度プリセット: 3つの `<button>` で選択（簡潔 / 標準 / 詳細）。アクティブ: 青背景
  - カスタム指示: `<textarea>`（placeholder: 「例: 英語で回答して」）
  - 保存ボタン: `isSaving` 時は「保存中...」表示
- **Emit タイミング**:
  - `update:settings`: プリセットボタンクリック時・カスタム指示入力時に即時 emit
  - `save`: 保存ボタンクリック時に emit（サーバーへの永続化トリガー）
- Scoped CSS でスタイリング

### `app/components/ChatMessage.vue`（181行）

- Props: `role`, `content`, `isError?`, `isStreaming?`
- assistant メッセージのみ `marked.parse()` → `DOMPurify.sanitize()` でリッチ HTML 生成
- **ver14.2 追加**: Markdown レンダリングのスロットリング（80ms 間隔、`RENDER_THROTTLE_MS` 定数）
  - ストリーミング中: `content` 変更時に最大 80ms に1回だけレンダリング
  - ストリーミング完了時: `isStreaming` が `false` になった瞬間に即座に最終レンダリング
  - `onBeforeUnmount` でタイマーをクリーンアップ

### `app/components/ChatInput.vue`（86行）

- Props: `{ disabled, isStreaming }`
- Emits: `send(content)`, `abort()`
- ストリーミング中は赤色「停止」ボタン、通常時は青色「送信」ボタン

### `app/components/ThreadSidebar.vue`（131行）

- Props: `threads: Thread[]`, `activeThreadId: string`, `isLoading: boolean`
- Emits: `selectThread(threadId)`, `newThread()`
- サイドバー（幅 240px 固定）、ヘッダー（「スレッド」+ 「+ 新規」ボタン）、スレッド一覧（ボタンリスト）
- アクティブスレッド: 青背景（`#dbeafe`）で視覚的に区別

## Composables

### `app/composables/useChat.ts`（117行）

- `Message` インターフェース（`{ role: 'user' | 'assistant', content: string, isError?: boolean }`）をエクスポート
- `useChat()` composable をエクスポート。戻り値: `{ messages, isLoading, isStreaming, threadId, sendMessage, abort, switchThread, loadHistory }`
- リアクティブ状態:
  - `messages: Ref<Message[]>` — チャット履歴
  - `isLoading: Ref<boolean>` — 送信〜応答完了 or 履歴ロード中の全体ローディング
  - `isStreaming: Ref<boolean>` — 初回トークン受信〜ストリーム完了のストリーミング状態
  - `threadId: Ref<string>` — 初期値は空文字列。外部から `switchThread()` で設定
- `threadId` の初期化と永続化は `useThreads` composable が担当。`useChat` は `threadId` を受動的に受け取るのみ
- `threadId` 未設定時（空文字列）は `sendMessage()` が早期リターンするガード
- `switchThread(newThreadId)` — ストリーミング中なら `abort()` で自動中断、`messages` リセット、`threadId` 設定、`loadHistory()` 呼び出し

### `app/composables/useThreads.ts`（86行）

- `Thread` インターフェース（`{ threadId, title, createdAt, updatedAt }`）をエクスポート
- `useThreads()` composable をエクスポート。戻り値: `{ threads, activeThreadId, isLoadingThreads, loadThreads, createNewThread, setActiveThread, initActiveThread, updateLocalTitle }`
- モジュールスコープのシングルトン状態
- `ACTIVE_THREAD_KEY = 'analogy-threadId'` を localStorage キーとして使用
- `createNewThread()`: `crypto.randomUUID()` でID生成、楽観的に `threads` 先頭に追加、localStorage に保存
- `import.meta.client` ガードで SSR 安全性を確保

### `app/composables/useSettings.ts`（44行）— ver15.0 新規

- `ThreadSettings` インターフェース（`{ granularity: 'concise' | 'standard' | 'detailed', customInstruction: string }`）をエクスポート
- `useSettings()` composable をエクスポート。戻り値: `{ settings, isSaving, loadSettings, saveSettings }`
- `loadSettings(threadId)` — `$fetch` で `GET /api/threads/:id/settings` を呼び出し。エラー時はデフォルト値にフォールバック
- `saveSettings()` — `$fetch` で `PUT /api/threads/:id/settings` を呼び出し
- スレッド切り替え時に呼ぶことで、前スレッドの設定が残留することを防止

## ユーティリティ

### `app/utils/sse-parser.ts`（54行）

- `SSECallbacks` インターフェース: `onToken(content)`, `onDone()`, `onError(message)`
- `parseSSEStream(stream, callbacks): Promise<void>` — `ReadableStream` を消費しSSEイベントをコールバックで通知

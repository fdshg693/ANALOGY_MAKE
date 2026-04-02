# ver11 実装計画: 複数スレッド管理

## 概要

サイドバーによるスレッド一覧表示・切り替え・新規作成・タイトル自動生成を実装する。

## アーキテクチャ方針

### スレッドメタデータの管理

LangGraph の SqliteSaver は会話状態（checkpoints テーブル）を管理するが、「スレッド一覧」や「タイトル」を返すAPIを持たない。そのため、スレッドのメタデータ（threadId・タイトル・作成日時・更新日時）を管理する **独自のSQLiteテーブル** を同じDBファイル（`./data/langgraph-checkpoints.db`）に追加する。

`better-sqlite3` を直接使用してメタデータテーブルを操作する（LangGraph の SqliteSaver とは独立した接続）。

### Composable の分割戦略

- `useThreads.ts`（新規）— スレッド一覧・アクティブスレッドの管理
- `useChat.ts`（修正）— `switchThread()` メソッド追加、threadId 外部指定対応
- `index.vue` が両 composable を統合し、スレッド切り替えイベントを仲介

### localStorage 戦略

現在の単一 `threadId` 保存を **アクティブスレッドID** の保存に転用する。スレッドメタデータはサーバー側で管理するため、クライアントは「最後にアクティブだったスレッドID」のみ保持。

### ストリーミング中のスレッド切り替え

ストリーミング中にスレッド切り替えが発生した場合は `abort()` を暗黙的に呼び出してからスレッドを切り替える。

---

## 新規ファイル

### 1. `server/utils/thread-store.ts`

スレッドメタデータのCRUDを担当するサーバーユーティリティ。

```typescript
import Database from 'better-sqlite3'
import { mkdirSync } from 'node:fs'

const DB_PATH = './data/langgraph-checkpoints.db'

interface ThreadRecord {
  thread_id: string
  title: string
  created_at: string  // ISO 8601
  updated_at: string  // ISO 8601
}

let _db: Database.Database | null = null

function getDb(): Database.Database {
  if (!_db) {
    mkdirSync('./data', { recursive: true })
    _db = new Database(DB_PATH)
    _db.pragma('journal_mode = WAL')  // LangGraphとの並行アクセスに備える
    _db.exec(`
      CREATE TABLE IF NOT EXISTS threads (
        thread_id TEXT PRIMARY KEY,
        title TEXT NOT NULL DEFAULT '新しいチャット',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
      )
    `)
  }
  return _db
}

/** スレッド一覧を更新日時降順で取得 */
export function getThreads(): ThreadRecord[] {
  const db = getDb()
  return db.prepare('SELECT * FROM threads ORDER BY updated_at DESC').all() as ThreadRecord[]
}

/** スレッドを新規登録（既存なら updated_at のみ更新） */
export function upsertThread(threadId: string, title?: string): void {
  const db = getDb()
  db.prepare(`
    INSERT INTO threads (thread_id, title)
    VALUES (?, ?)
    ON CONFLICT(thread_id) DO UPDATE SET updated_at = datetime('now')
  `).run(threadId, title ?? '新しいチャット')
}

/** スレッドタイトルを更新 */
export function updateThreadTitle(threadId: string, title: string): void {
  const db = getDb()
  db.prepare('UPDATE threads SET title = ?, updated_at = datetime(\'now\') WHERE thread_id = ?').run(title, threadId)
}

/** スレッドの現在のタイトルを取得（存在しなければ null） */
export function getThreadTitle(threadId: string): string | null {
  const db = getDb()
  const row = db.prepare('SELECT title FROM threads WHERE thread_id = ?').get(threadId) as { title: string } | undefined
  return row?.title ?? null
}
```

**設計ポイント:**
- LangGraph と同じ DB ファイルを使用。`WAL` モードで並行読み取りを安全に
- `better-sqlite3` は同期APIのため、サーバーユーティリティとして素直に使える
- `upsertThread` で INSERT OR UPDATE パターンを使い、冪等な操作にする

### 2. `server/api/threads.get.ts`

スレッド一覧を返す API エンドポイント。

```typescript
import { defineEventHandler } from 'h3'
import { getThreads } from '../utils/thread-store'

export default defineEventHandler(() => {
  const threads = getThreads()
  return {
    threads: threads.map(t => ({
      threadId: t.thread_id,
      title: t.title,
      createdAt: t.created_at,
      updatedAt: t.updated_at,
    }))
  }
})
```

**API仕様:**
- `GET /api/threads`
- レスポンス: `{ threads: [{ threadId, title, createdAt, updatedAt }] }`
- 更新日時降順でソート済み

### 3. `app/composables/useThreads.ts`

スレッド一覧のクライアント側管理。

```typescript
import { ref } from 'vue'
import type { Ref } from 'vue'

export interface Thread {
  threadId: string
  title: string
  createdAt: string
  updatedAt: string
}

const ACTIVE_THREAD_KEY = 'analogy-threadId'  // 既存のキーを流用

// モジュールスコープでシングルトン的に状態管理
const threads: Ref<Thread[]> = ref([])
const activeThreadId: Ref<string> = ref('')
const isLoadingThreads: Ref<boolean> = ref(false)

export function useThreads() {
  /** サーバーからスレッド一覧を取得 */
  async function loadThreads(): Promise<void> {
    isLoadingThreads.value = true
    try {
      const res = await fetch('/api/threads')
      const data = await res.json()
      threads.value = data.threads
    } catch {
      // サイレントに無視（空リストのまま）
    } finally {
      isLoadingThreads.value = false
    }
  }

  /** 新しいスレッドを作成し、アクティブにする。新しいthreadIdを返す */
  function createNewThread(): string {
    const newId = crypto.randomUUID()
    threads.value.unshift({
      threadId: newId,
      title: '新しいチャット',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    })
    activeThreadId.value = newId
    if (import.meta.client) {
      localStorage.setItem(ACTIVE_THREAD_KEY, newId)
    }
    return newId
  }

  /** アクティブスレッドを切り替える */
  function setActiveThread(threadId: string): void {
    activeThreadId.value = threadId
    if (import.meta.client) {
      localStorage.setItem(ACTIVE_THREAD_KEY, threadId)
    }
  }

  /** 初期化: localStorageからアクティブスレッドを復元 */
  function initActiveThread(): void {
    if (import.meta.client) {
      const stored = localStorage.getItem(ACTIVE_THREAD_KEY)
      if (stored) {
        activeThreadId.value = stored
      }
    }
  }

  /** スレッドタイトルをローカルに更新（サーバーからの通知を反映） */
  function updateLocalTitle(threadId: string, title: string): void {
    const thread = threads.value.find(t => t.threadId === threadId)
    if (thread) {
      thread.title = title
    }
  }

  return {
    threads,
    activeThreadId,
    isLoadingThreads,
    loadThreads,
    createNewThread,
    setActiveThread,
    initActiveThread,
    updateLocalTitle,
  }
}
```

**設計ポイント:**
- モジュールスコープのシングルトン状態（複数コンポーネントから共有可能）
- `createNewThread` はクライアント側で楽観的にリスト追加（サーバーへの登録は `POST /api/chat` 時に行われる）
- 既存の localStorage キー `'analogy-threadId'` をそのまま流用
- **楽観的追加の挙動**: 新規作成後に何も送信せずに `loadThreads()` が走ると、サーバー未登録のためリストから消える。これは **許容する**（未使用の空スレッドが残り続けるよりもクリーンな挙動）

### 4. `app/components/ThreadSidebar.vue`

スレッド一覧サイドバーコンポーネント。

```vue
<script setup lang="ts">
import type { Thread } from '../composables/useThreads'

defineProps<{
  threads: Thread[]
  activeThreadId: string
  isLoading: boolean
}>()

const emit = defineEmits<{
  selectThread: [threadId: string]
  newThread: []
}>()
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h2>スレッド</h2>
      <button class="new-thread-btn" @click="emit('newThread')">
        + 新規
      </button>
    </div>
    <div class="thread-list">
      <div v-if="isLoading" class="loading">読み込み中...</div>
      <button
        v-for="thread in threads"
        :key="thread.threadId"
        class="thread-item"
        :class="{ active: thread.threadId === activeThreadId }"
        @click="emit('selectThread', thread.threadId)"
      >
        <span class="thread-title">{{ thread.title }}</span>
      </button>
      <div v-if="!isLoading && threads.length === 0" class="empty">
        スレッドがありません
      </div>
    </div>
  </aside>
</template>

<style scoped>
/* サイドバーのスタイル: 幅240px固定、左寄せ、スクロール可能 */
/* アクティブスレッドはbackground-colorで強調 */
/* 新規ボタンは目立つ配色 */
</style>
```

**設計ポイント:**
- Props + Emits のみで状態に依存しない純粋なプレゼンテーショナルコンポーネント
- スレッド選択・新規作成のイベントを親に通知

---

## 既存ファイルの修正

### 5. `app/composables/useChat.ts` の修正

**変更内容:**
- `switchThread(threadId: string)` メソッドを追加
- threadId の初期化ロジックを外部から設定可能に変更
- `loadHistory()` を公開（現在は内部関数）

```typescript
// 追加するメソッド
function switchThread(newThreadId: string): void {
  // ストリーミング中なら中断
  if (isStreaming.value) {
    abort()
  }
  // 状態リセット
  messages.value = []
  threadId.value = newThreadId
  // 履歴ロード
  loadHistory()
}
```

**修正箇所の詳細:**
1. `getOrCreateThreadId()` の呼び出しを削除し、外部（`useThreads`）から `threadId` を設定可能にする
   - 初期値は空文字列、`switchThread()` 経由で設定
   - `THREAD_ID_KEY` 定数と `getOrCreateThreadId()` 関数を削除（threadId 管理は `useThreads` に移行）
   - 初期化時の自動 `loadHistory()` 呼び出し（46〜48行目）を削除（`switchThread` 経由で呼ばれるため）
2. `loadHistory()` を composable の戻り値に追加
3. `switchThread()` を composable の戻り値に追加
4. `sendMessage()` に threadId 未設定ガードを追加: `if (!threadId.value) return`（`switchThread` 呼び出し前の誤送信を防止）
5. 戻り値: `{ messages, isLoading, isStreaming, threadId, sendMessage, abort, switchThread }`

**既存テストへの影響:**
- `初期状態` テスト → `threadId.value` の期待値を `'mock-uuid'` から `''`（空文字列）に**修正**
- `threadId の永続化` セクション（SSR時 / クライアント新規生成 / クライアント復元の3ケース）→ `getOrCreateThreadId()` 削除に伴い**全件削除**。threadId 管理は `useThreads.test.ts` に移行
- `履歴復元` セクション（正常取得 / 取得失敗の2ケース）→ 自動ロード削除に伴い**全件削除**。`switchThread()` 経由のロードテストに置き換え
- 計: 既存1件修正 + 5件削除 + `switchThread` テスト3件 + ガードテスト1件で置き換え

### 6. `app/pages/index.vue` の修正

**変更内容:**
- レイアウトをサイドバー + メインエリアの2カラム構成に変更
- `useThreads()` を統合
- スレッド選択・新規作成のイベントハンドリング追加
- 初期化フロー: `initActiveThread()` → `loadThreads()` → `switchThread(activeThreadId)`

```vue
<script setup lang="ts">
import { useChat } from '../composables/useChat'
import { useThreads } from '../composables/useThreads'

const { messages, isLoading, isStreaming, sendMessage, abort, switchThread } = useChat()
const {
  threads, activeThreadId, isLoadingThreads,
  loadThreads, createNewThread, setActiveThread, initActiveThread
} = useThreads()

// 初期化
onMounted(async () => {
  initActiveThread()
  await loadThreads()
  // アクティブスレッドがあれば履歴ロード、なければ新規作成
  if (activeThreadId.value) {
    switchThread(activeThreadId.value)
  } else {
    handleNewThread()
  }
})

function handleSelectThread(threadId: string) {
  setActiveThread(threadId)
  switchThread(threadId)
}

function handleNewThread() {
  const newId = createNewThread()
  switchThread(newId)
}

// sendMessage をラップし、完了後にスレッド一覧を再取得
async function handleSend(content: string) {
  await sendMessage(content)
  // タイトル生成完了を反映するため、一覧を再取得
  await loadThreads()
}
</script>
```

**`handleSend` の設計意図:** `sendMessage` 完了後に `loadThreads()` を呼ぶことで、バックエンド側で非同期生成されたタイトルを取得する。タイトル生成が `sendMessage` 完了時点でまだ終わっていない場合は、次回の `handleSend` またはスレッド切り替え時に反映される。

**テンプレートの構造:**
```html
<div class="app-layout">
  <ThreadSidebar
    :threads="threads"
    :active-thread-id="activeThreadId"
    :is-loading="isLoadingThreads"
    @select-thread="handleSelectThread"
    @new-thread="handleNewThread"
  />
  <main class="chat-area">
    <!-- 既存のチャットUI（ヘッダー、メッセージ一覧、入力エリア） -->
  </main>
</div>
```

**レイアウト CSS:**
```css
.app-layout {
  display: flex;
  height: 100vh;
}
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}
```

### 7. `server/api/chat.post.ts` の修正

**変更内容:**
- スレッドメタデータの upsert を追加（メッセージ送信ごとに `updated_at` を更新）
- 初回応答完了後のタイトル自動生成を追加

```typescript
import { upsertThread, getThreadTitle, updateThreadTitle } from '../utils/thread-store'

// ストリーム処理の前に:
upsertThread(threadId)

// ストリーム完了後（done イベント送信後）:
const currentTitle = getThreadTitle(threadId)
if (currentTitle === '新しいチャット' || currentTitle === null) {
  // タイトル生成（非同期・ノンブロッキング）
  void generateTitle(threadId, message, fullResponse)
}
```

**タイトル生成関数（同ファイル内 or ユーティリティとして切り出し）:**

```typescript
async function generateTitle(threadId: string, userMessage: string, aiResponse: string): Promise<void> {
  try {
    const { ChatOpenAI } = await import('@langchain/openai')
    const model = new ChatOpenAI({
      modelName: 'gpt-4.1-mini',
      temperature: 0,
      maxTokens: 30,
    })
    const result = await model.invoke([
      { role: 'system', content: '以下の会話の内容を10文字以内の日本語タイトルにしてください。タイトルのみ出力してください。' },
      { role: 'user', content: `ユーザー: ${userMessage}\nAI: ${aiResponse.slice(0, 200)}` },
    ])
    const title = (result.content as string).trim().slice(0, 30)
    if (title) {
      updateThreadTitle(threadId, title)
    }
  } catch {
    // タイトル生成失敗はサイレントに無視
  }
}
```

**設計ポイント:**
- タイトル生成は `void` で非同期実行（SSEレスポンスをブロックしない）
- タイトル生成は「新しいチャット」のままのスレッドに対してのみ実行
- 生成はストリーム完了後なので、`fullResponse`（AIの全文）を使える
- `temperature: 0` で安定したタイトルを生成
- クライアントは次回の `loadThreads()` 呼び出し時（またはスレッド切り替え時）にタイトルを取得

### 8. テストファイル

#### `tests/server/threads.test.ts`（新規）

- `GET /api/threads` のテスト
- `thread-store.ts` のモック
- ケース: 正常取得（複数スレッド）、空リスト

#### `tests/server/thread-store.test.ts`（新規）

- `thread-store.ts` のユニットテスト
- `better-sqlite3` をインメモリDBでテスト
- ケース: `getThreads`（空・複数）、`upsertThread`（新規・既存更新）、`updateThreadTitle`、`getThreadTitle`

#### `tests/server/chat.test.ts`（修正）

- `thread-store` モジュールのモックを追加（`vi.mock('../../server/utils/thread-store')`）
  - `upsertThread`、`getThreadTitle`、`updateThreadTitle` のスタブ
- 既存5テストケースは `thread-store` モック追加のみで通過する見込み
- タイトル生成のテストは `thread-store.test.ts` でカバーするため、ここでは追加不要

#### `tests/composables/useChat.test.ts`（修正）

- **削除**: `threadId の永続化` セクション（3件）— threadId 管理は `useThreads` に移行したため
- **削除**: `履歴復元` セクション（2件）— 自動ロードは削除され、`switchThread` 経由に変更したため
- **追加**: `switchThread()` のテストケース:
  - スレッド切り替え時に messages がクリアされること
  - ストリーミング中の切り替えで abort が呼ばれること
  - 切り替え後に loadHistory が呼ばれること
- **追加**: `sendMessage()` の threadId 未設定ガードのテスト（空文字列で呼び出し → 何もしない）

#### `tests/composables/useThreads.test.ts`（新規）

- `useThreads` composable のテスト
- `fetch` のモック
- ケース: `loadThreads`（正常・失敗）、`createNewThread`、`setActiveThread`、`initActiveThread`

---

## 実装順序

1. **`server/utils/thread-store.ts`** — バックエンドの基盤。テスト作成
2. **`server/api/threads.get.ts`** — スレッド一覧API。テスト作成
3. **`server/api/chat.post.ts` 修正** — upsert + タイトル自動生成
4. **`app/composables/useThreads.ts`** — クライアント側スレッド管理。テスト作成
5. **`app/composables/useChat.ts` 修正** — switchThread 追加。テスト修正
6. **`app/components/ThreadSidebar.vue`** — UIコンポーネント
7. **`app/pages/index.vue` 修正** — レイアウト変更、統合

## ファイル一覧

| ファイル | 操作 | 概要 |
|---|---|---|
| `server/utils/thread-store.ts` | 新規 | スレッドメタデータ管理 |
| `server/api/threads.get.ts` | 新規 | スレッド一覧API |
| `app/composables/useThreads.ts` | 新規 | スレッド状態管理composable |
| `app/components/ThreadSidebar.vue` | 新規 | サイドバーUIコンポーネント |
| `server/api/chat.post.ts` | 修正 | upsert + タイトル生成追加 |
| `app/composables/useChat.ts` | 修正 | switchThread追加 |
| `app/pages/index.vue` | 修正 | レイアウト変更、統合 |
| `tests/server/thread-store.test.ts` | 新規 | thread-storeテスト |
| `tests/server/threads.test.ts` | 新規 | スレッド一覧APIテスト |
| `tests/composables/useThreads.test.ts` | 新規 | useThreadsテスト |
| `tests/composables/useChat.test.ts` | 修正 | switchThreadテスト追加 |

## リスク・不確実性

### better-sqlite3 の並行アクセス

- LangGraph の SqliteSaver と独自の `thread-store` が同じDBファイルにアクセスする
- `WAL` モードを使用することで並行読み取りは安全だが、書き込みの競合が起きる可能性がある
- **対策**: thread-store の書き込みは軽量（メタデータのみ）であり、LangGraph の checkpointer 書き込みとの競合は実用上問題にならない見込み。問題が発生した場合はDBファイルを分離する

### タイトル生成の信頼性

- `gpt-4.1-mini` で短いタイトルを生成するが、LLMの出力は非決定的
- タイトルが長すぎる・不適切な場合の対策として `slice(0, 30)` で切り詰め
- 生成失敗時はサイレントに無視し「新しいチャット」のまま残す

### タイトルのクライアント反映タイミング

- タイトル生成は非同期で行われるため、生成完了時にクライアントのスレッド一覧に即座に反映されない
- クライアントは次回の `loadThreads()` 呼び出し時に最新タイトルを取得する
- **対策**: sendMessage 完了後に `loadThreads()` を再取得することで、タイトル生成完了後の反映を実現する。ただしタイミングによっては1回の送信では反映されない可能性がある（次回メッセージ送信 or スレッド切り替え時に反映）

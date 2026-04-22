# コード現況（ver17.0 追加要素）

ver16.0 からの差分のみを記載。ver16.0 時点の全体現況は `docs/app/ver16.0/CURRENT_backend.md` / `CURRENT_frontend.md` / `CURRENT_tests.md` を参照。

---

## バックエンド追加要素

### `server/utils/langgraph-thread.ts`（6行）

- `MAIN_BRANCH_ID = 'main'` 定数
- `toLangGraphThreadId(threadId, branchId)`: `branchId === 'main'` の場合は raw `threadId` を返す（ver16.x 以前と完全互換）。それ以外は `${threadId}::${branchId}` を返す

### `server/utils/branch-store.ts`（69行）

- `thread_branches` テーブルの初期化（`getDb()` 内で `CREATE TABLE IF NOT EXISTS`）
  - `branch_id TEXT PRIMARY KEY`, `thread_id TEXT NOT NULL`, `parent_branch_id TEXT`, `fork_message_index INTEGER NOT NULL`, `created_at TEXT`
  - `FOREIGN KEY (thread_id) REFERENCES threads(thread_id) ON DELETE CASCADE`
  - インデックス: `idx_thread_branches_thread_id`
  - WAL モード + `foreign_keys = ON`（thread-store と独立した better-sqlite3 接続）
- `getBranches(threadId)`: 非 main 分岐一覧を `created_at` 昇順で取得
- `branchBelongsToThread(threadId, branchId)`: 所属チェック
- `createBranch({ threadId, parentBranchId, forkMessageIndex })`: UUID で `branch_id` を採番して挿入、`BranchRecord` を返す

### `server/api/chat/fork.post.ts`（76行）

- `POST /api/chat/fork` — 会話分岐作成エンドポイント
- リクエスト: `{ threadId, fromBranchId, forkMessageIndex }`
- 処理フロー:
  1. `fromBranchId` の所属チェック（`MAIN_BRANCH_ID` or `branchBelongsToThread`）
  2. `agent.getState({ configurable: { thread_id: toLangGraphThreadId(threadId, fromBranchId) } })` で親スナップショット取得
  3. `parentMessages.slice(0, forkMessageIndex)` で切り出し
  4. `createBranch()` で `thread_branches` にレコード挿入
  5. `agent.updateState()` で新 thread_id に切り出したメッセージ + `currentStep` + `abstractedProblem` を永続化
  6. `thread-store` の `activeBranchId` を新分岐に更新
- レスポンス: `{ branchId, activeBranchId }`

### `server/api/chat/branches.get.ts`（37行）

- `GET /api/chat/branches?threadId=xxx` — 分岐一覧取得エンドポイント
- `main` 分岐（`forkMessageIndex: null, createdAt: null`）を先頭に追加し、`getBranches()` の結果をマージして返す
- `getThreadSettings()` から `activeBranchId` を取得して付与
- レスポンス: `{ branches: BranchView[], activeBranchId: string }`

### `server/api/chat.post.ts`（変更）

- `branchId` パラメータ受け取り追加（`body.branchId ?? MAIN_BRANCH_ID`）
- `toLangGraphThreadId(threadId, branchId)` で LangGraph thread_id を合成
- `branchId === MAIN_BRANCH_ID` ガードを追加してタイトル自動生成を main 分岐のみに限定

### `server/api/chat/history.get.ts`（変更）

- `branchId` クエリパラメータ追加（未指定時は `MAIN_BRANCH_ID`）
- `toLangGraphThreadId(threadId, branchId)` で LangGraph thread_id を合成して `agent.getState()` に渡す

### `server/utils/analogy-agent.ts`（変更）

- `deriveCurrentStep(messages)` を export 追加:
  - `messages` が空 or 末尾が HumanMessage → `'initial'`
  - 末尾が AIMessage かつ `additional_kwargs.searchResults` あり → `'awaiting_selection'`
  - 末尾が AIMessage かつ `additional_kwargs.searchResults` なし → `'completed'`

---

## フロントエンド追加要素

### `app/composables/useBranches.ts`（71行）

- `MAIN_BRANCH_ID = 'main'` 定数（サーバー側と重複定義）
- `Branch` インターフェース: `{ branchId, parentBranchId, forkMessageIndex, createdAt }`
- `useBranches()` composable:
  - `branches: Ref<Branch[]>`, `activeBranchId: Ref<string>`
  - `loadBranches(threadId)`: `GET /api/chat/branches` を呼び出して状態更新
  - `setActiveBranch(threadId, branchId)`: `PUT /api/threads/:id/settings` で `activeBranchId` を永続化
  - `fork({ threadId, fromBranchId, forkMessageIndex })`: `POST /api/chat/fork` を呼び出し、`loadBranches` で再取得

### `app/components/BranchNavigator.vue`（94行）

- 同一 `forkMessageIndex` を持つ分岐グループを `◀ N/M ▶` で表示
- props: `branches: Branch[]`, `activeBranchId: string`, `forkMessageIndex: number`
- 表示条件: 同じ `forkMessageIndex` を持つ分岐が複数（main + 非 main で 2 つ以上）あるとき
- emit: `switch-branch(branchId: string)`

### `app/components/ChatMessage.vue`（変更）

- ユーザーメッセージのホバー時に「編集」ボタンを表示（`.chat-message.user:hover .edit-btn` / `opacity: 0 → 1`）
- 編集クリック時: `useChat.startEdit(messageIndex)` → `ChatInput` に編集モード通知
- `BranchNavigator` を各ユーザーメッセージの直下に埋め込み。`forkMessageIndex` が一致するメッセージ位置のみ表示

### `app/composables/useChat.ts`（変更）

- `currentBranchId: Ref<string>` を追加（`useBranches` の `activeBranchId` と同期）
- `switchThread(threadId, branchId)`: `branchId` を切り替えて `GET /api/chat/history?branchId=xxx` で履歴再取得
- `startEdit(messageIndex)`: 編集対象インデックスをセットして `ChatInput` に渡す
- `submitEdit(messageIndex, newContent)`: `fork()` → 新分岐で送信

---

## DB スキーマ追加

```sql
CREATE TABLE IF NOT EXISTS thread_branches (
  branch_id TEXT PRIMARY KEY,
  thread_id TEXT NOT NULL,
  parent_branch_id TEXT,
  fork_message_index INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (thread_id) REFERENCES threads(thread_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_thread_branches_thread_id ON thread_branches(thread_id);
```

---

## テスト追加

| ファイル | ケース数 | 内容 |
|---|---|---|
| `tests/server/fork.test.ts` | 新規 | `POST /api/chat/fork` の正常系・異常系 |
| `tests/server/branches.test.ts` | 新規 | `GET /api/chat/branches` の正常系・異常系 |
| `tests/server/branch-store.test.ts` | 新規 | `getBranches` / `branchBelongsToThread` / `createBranch` |
| `tests/server/langgraph-thread.test.ts` | 新規 | `toLangGraphThreadId` / `MAIN_BRANCH_ID` |
| `tests/server/analogy-agent.test.ts` | 追加 | `deriveCurrentStep` の 5 ケース |

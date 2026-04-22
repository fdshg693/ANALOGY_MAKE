# バックエンド現況（ver17.0）

## API エンドポイント

### `server/api/chat.post.ts`（198行）

- `POST /api/chat` SSE ストリーミングエンドポイント
- ストリーミングフィルタ: `STREAMED_NODES = new Set(["caseSearch", "solution", "followUp"])`
- リクエストボディに `branchId`（省略時 `MAIN_BRANCH_ID`）を追加（ver17.0）
- `toLangGraphThreadId(threadId, branchId)` で LangGraph thread_id を合成（ver17.0）
- `branchId === MAIN_BRANCH_ID` ガード: タイトル自動生成・タイトル取得を main 分岐のみに限定（ver17.0）
- `settings.responseMode === 'echo'` のとき LangGraph をバイパスして `handleEchoResponse()` に処理移譲（ver16.1）

**リクエスト:**
```json
{ "message": "string", "threadId": "string", "branchId": "string (省略可、デフォルト 'main')" }
```

**レスポンス:** SSE ストリーム（`Content-Type: text/event-stream`）

| event | data | 説明 |
|---|---|---|
| `token` | `{"content": "..."}` | トークン1つ分のテキスト |
| `search_results` | `{"results": [{title, url, content}...]}` | Tavily 検索結果（検索結果ありの場合のみ、`done` 直前に 1 回） |
| `done` | `{}` | ストリーミング正常完了 |
| `error` | `{"message": "..."}` | エラー発生 |

**エコーモード時の特殊挙動:**
- LangGraph をバイパス。入力を 8 文字単位・30ms 間隔で `token` SSE 配信
- `agent.updateState()` で `[HumanMessage, AIMessage]` を SQLite に永続化
- タイトル生成は入力先頭 10 文字を流用（LLM 呼び出しなし）
- `search_results` イベントは送信しない

### `server/api/chat/history.get.ts`（100行）

- `GET /api/chat/history?threadId=xxx&branchId=yyy` 会話履歴取得エンドポイント
- `branchId` クエリパラメータを追加（省略時 `MAIN_BRANCH_ID`）（ver17.0）
- `toLangGraphThreadId(threadId, branchId)` で合成キーを生成して `agent.getState()` に渡す
- `extractSearchResults()` で `additional_kwargs.searchResults` を型ガード付きで展開
- 旧スレッド（ver15.x 以前）の AI メッセージは `searchResults` なしで返る

**レスポンス:**
```json
{
  "messages": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "...", "searchResults": [{...}] }
  ]
}
```

### `server/api/chat/fork.post.ts`（76行）— ver17.0 新規

- `POST /api/chat/fork` — 会話分岐作成エンドポイント（**非ストリーミング**）
- 分岐作成のみ。新分岐への AI 応答生成は `POST /api/chat` を別途呼び出す

**リクエスト:**
```json
{
  "threadId": "string",
  "fromBranchId": "string",
  "forkMessageIndex": 0
}
```

**処理フロー:**
1. `fromBranchId` の所属チェック（`MAIN_BRANCH_ID` または `branchBelongsToThread`）
2. `agent.getState()` で親ブランチのスナップショット取得
3. `parentMessages.slice(0, forkMessageIndex)` で切り出し
4. `createBranch()` で `thread_branches` テーブルにレコード挿入
5. `agent.updateState()` で新 thread_id にメッセージ + `currentStep` + `abstractedProblem` を永続化
6. `getThreadSettings()` / `updateThreadSettings()` で `activeBranchId` を新分岐に更新

**レスポンス:**
```json
{ "branchId": "<newBranchId>", "activeBranchId": "<newBranchId>" }
```

### `server/api/chat/branches.get.ts`（37行）— ver17.0 新規

- `GET /api/chat/branches?threadId=xxx` — 分岐一覧取得エンドポイント
- `main` 分岐（`forkMessageIndex: null, createdAt: null`）を先頭に付与
- `getBranches()` の結果（`created_at` 昇順）をマージ
- `getThreadSettings()` から `activeBranchId` を取得して付与

**レスポンス:**
```json
{
  "branches": [
    { "branchId": "main", "parentBranchId": null, "forkMessageIndex": null, "createdAt": null },
    { "branchId": "<uuid>", "parentBranchId": "main", "forkMessageIndex": 3, "createdAt": "..." }
  ],
  "activeBranchId": "<current>"
}
```

### `server/api/threads.get.ts`（15行）

変更なし。`GET /api/threads` スレッド一覧取得（更新日時降順）。

### `server/api/threads/[id]/settings.get.ts`（8行）

変更なし。`GET /api/threads/:id/settings` スレッド設定取得。

### `server/api/threads/[id]/settings.put.ts`（48行）

`PUT /api/threads/:id/settings` スレッド設定更新（ver17.0 変更）。

- `activeBranchId` バリデーション追加: `MAIN_BRANCH_ID` または `branchBelongsToThread` に合致しない場合は `MAIN_BRANCH_ID` にフォールバック（ver17.0）
- `responseMode` バリデーション（`'ai' | 'echo'`）（ver16.1）
- `systemPromptOverride` は `isDev` のみ受け付け、本番では強制クリア（ver16.1）
- `customInstruction` 500文字上限、`granularity`（`'concise' | 'standard' | 'detailed'`）

## エージェント・プロンプト

### `server/utils/analogy-agent.ts`（250行）

LangGraph `StateGraph` によるマルチノード構成のアナロジー思考ワークフロー。

#### エクスポート追加（ver17.0）

```typescript
export function deriveCurrentStep(
  messages: BaseMessage[]
): 'initial' | 'awaiting_selection' | 'completed'
```

判定ロジック:
- `messages` が空 または 末尾が `HumanMessage` → `'initial'`
- 末尾が `AIMessage` かつ `additional_kwargs.searchResults` が 1 件以上 → `'awaiting_selection'`
- 末尾が `AIMessage` かつ `searchResults` がない or 空配列 → `'completed'`

※ `followUp` 実行後も `'completed'` と同判定になるが、`routeByStep` の分岐では `completed → followUp` として同じ挙動になるため実害なし。

#### `SearchResult` 型

```typescript
export interface SearchResult {
  title: string
  url: string
  content: string
}
```

#### ステート定義（`AnalogyState`）

```typescript
const AnalogyState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({ reducer: messagesStateReducer, default: () => [] }),
  currentStep: Annotation<string>({ reducer: (_prev, next) => next, default: () => "initial" }),
  abstractedProblem: Annotation<string>({ reducer: (_prev, next) => next, default: () => "" }),
})
```

#### ステップ遷移

| currentStep | 意味 | 次に実行されるノード |
|---|---|---|
| `initial` | 新規スレッド、課題未入力 | abstraction → caseSearch |
| `awaiting_selection` | 事例提示済み、ユーザー選択待ち | solution |
| `completed` | 解決策提示済み（followUp 後も同値） | followUp |

#### グラフ構造

```
START ──→ [routeByStep: conditional edge]
              ├── "initial"            → abstraction → caseSearch → END
              ├── "awaiting_selection" → solution → END
              └── "completed"          → followUp → END
```

#### シングルトン管理

`_compiledGraph` をモジュールレベルで保持。`getAnalogyAgent()` は async 関数で、初回のみ `SqliteSaver.fromConnString(DB_PATH)` で checkpointer を初期化してコンパイル。

### `server/utils/analogy-prompt.ts`（82行）

変更なし。`buildSystemPrompt(basePrompt, settings?)` ヘルパー（`systemPromptOverride` の先頭追記を含む）と 4 プロンプト定数を提供。

## ストレージ

### `server/utils/langgraph-thread.ts`（6行）— ver17.0 新規

```typescript
export const MAIN_BRANCH_ID = 'main'

export function toLangGraphThreadId(threadId: string, branchId: string = MAIN_BRANCH_ID): string {
  if (branchId === MAIN_BRANCH_ID) return threadId
  return `${threadId}::${branchId}`
}
```

- `branchId === 'main'` 時は raw `threadId` を返す（ver16.x 以前の既存スレッドと完全互換）
- それ以外は `${threadId}::${branchId}` を返す（`::` は UUID v4 の `-` と衝突しない）

### `server/utils/branch-store.ts`（69行）— ver17.0 新規

`thread_branches` テーブルの初期化・操作。thread-store とは**独立した** better-sqlite3 接続を持つ（WAL モード + `foreign_keys = ON`）。

```typescript
export interface BranchRecord {
  branch_id: string
  thread_id: string
  parent_branch_id: string | null
  fork_message_index: number
  created_at: string
}

export function getBranches(threadId: string): BranchRecord[]
export function branchBelongsToThread(threadId: string, branchId: string): boolean
export function createBranch(params: {
  threadId: string
  parentBranchId: string
  forkMessageIndex: number
}): BranchRecord
```

- `getBranches`: main を除く非 main 分岐一覧を `created_at` 昇順で取得
- `createBranch`: `crypto.randomUUID()` で `branch_id` を採番して挿入

### `server/utils/thread-store.ts`（123行）

ver17.0 で `ThreadSettings` に `activeBranchId: string`（デフォルト `MAIN_BRANCH_ID`）を追加。

```typescript
export interface ThreadSettings {
  granularity: 'concise' | 'standard' | 'detailed'
  customInstruction: string
  search: SearchSettings
  responseMode: ResponseMode        // ver16.1 追加
  systemPromptOverride: string      // ver16.1 追加
  activeBranchId: string            // ver17.0 追加
}

export const DEFAULT_SETTINGS: ThreadSettings = {
  granularity: 'standard',
  customInstruction: '',
  search: { enabled: true, depth: 'basic', maxResults: 3 },
  responseMode: 'ai',
  systemPromptOverride: '',
  activeBranchId: 'main',
}
```

`getThreadSettings()` はスプレッドマージで既存スレッドの JSON に新フィールドがなくても補完。`MAIN_BRANCH_ID` を `langgraph-thread.ts` から import（循環依存なし）。

### `server/utils/db-config.ts`（11行）

変更なし。DB パス一元管理（開発: `./data/`、本番: `/home/data/`）。

### `server/utils/logger.ts`（50行）

変更なし。

## データベーススキーマ

### threads テーブル

変更なし。`settings TEXT NOT NULL DEFAULT '{}'` カラムを含む。

### thread_branches テーブル（ver17.0 新規）

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

- `main` 分岐はこのテーブルに登録しない。レコードが存在しないことが「main のみ」を示す
- `foreign_keys = ON` は `branch-store.ts` の `getDb()` で有効化済み（スレッド削除時に CASCADE が機能）
- スレッド削除 UI は現状存在しないため CASCADE は将来の保険

### LangGraph チェックポイントステート

| フィールド | 型 | 用途 |
|---|---|---|
| `messages` | `BaseMessage[]` | 会話メッセージ履歴（AIMessage の `additional_kwargs.searchResults` に検索結果を添付） |
| `currentStep` | `string` | 対話フローの現在ステップ |
| `abstractedProblem` | `string` | 抽象化された課題テキスト |

**分岐時の thread_id 合成**: `main` 分岐は raw `threadId`、非 main 分岐は `${threadId}::${branchId}` で LangGraph checkpointer に保存。

## 技術的な決定事項（ver17.0 追加）

- **方針 B（main は raw threadId）**: ver16.x 以前の既存スレッドをマイグレーション不要で `main` 分岐と同一視できる
- **`deriveCurrentStep` のヒューリスティクス**: LangGraph 状態履歴 API に依存しない静的ロジック。`followUp` 後も `'completed'` と同判定だが実害なし
- **fork API は非ストリーミング**: チェックポイントコピーのみ行い、AI 応答生成は既存の `POST /api/chat` を再利用
- **タイトル生成の非 main ガード**: `branchId !== MAIN_BRANCH_ID` の場合はタイトル生成をスキップ。分岐作成時にスレッドタイトルが上書きされるのを防ぐ

## 未解決の課題（ISSUES）

- **`fork-checkpoint-verification.md`（medium）**: `updateState` による複数メッセージ配列の永続化・`::` 含む `thread_id` の LangGraph checkpointer 挙動が実機未検証
- **`getState-timing.md`（medium）**: ストリーム完了直後のスナップショットに最新 AIMessage が含まれるか未検証
- **`additional-kwargs-sqlite.md`（medium）**: `AIMessage.additional_kwargs` の任意オブジェクトが SQLite に正しく保存・復元されるか未検証
- **`db-connection-refactor.md`（low）**: `thread-store.ts` と `branch-store.ts` の `getDb()` 重複（独立した better-sqlite3 接続）、`MAIN_BRANCH_ID` のサーバー/フロント重複定義

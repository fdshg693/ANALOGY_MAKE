# ver17.0 IMPLEMENT — 会話分岐の実装計画

REFACTOR.md で確定した方針をもとに、具体的な実装手順を示す。

## 全体構成

```
ユーザー操作: メッセージ編集ボタン → テキスト書き換え → 送信
    ↓
[フロント useBranches.fork(threadId, originalBranchId, forkMessageIndex, newMessage)]
    ↓
[POST /api/chat/fork]
    ├─ thread_branches テーブルに新ブランチレコード挿入
    ├─ LangGraph 合成 thread_id = ${threadId}::${newBranchId} で新規に会話を再生成
    │   ├─ 親ブランチの fork_message_index までのメッセージを親から読み出し（getState）
    │   ├─ updateState で新ブランチにコピー
    │   └─ 編集済みメッセージを HumanMessage として graph.stream で実行
    └─ SSE で新ブランチ用の応答をストリーミング
    ↓
フロント: activeBranchId = newBranchId → UI がその分岐を表示
    ↓
ユーザー: ◀ 1/2 ▶ ナビで元の分岐に戻せる（activeBranchId 切替 → history 再取得）
```

## 実装順序

事前リファクタ（REFACTOR.md §7.1 / §7.2）→ データモデル → API → フロント composable → UI → テスト の順で積み上げる。各段階でテストがグリーンになる状態を保つ。

### Phase R（REFACTOR）

1. `server/utils/langgraph-thread.ts` 新規作成（1 関数）
2. `chat.post.ts` / `chat/history.get.ts` の 3 箇所を差し替え
3. `tests/fixtures/settings.ts` 新規作成
4. `thread-settings.test.ts` / `settings-api.test.ts` / `chat.test.ts` の DEFAULT_SETTINGS ハードコード/スプレッドを `makeThreadSettings()` に置換
5. `pnpm test` 全グリーン確認

### Phase I（IMPLEMENT 本体）

5. **I.0 検証スクリプト**: `experiments/fork-checkpoint.ts` を実装して、リスク R1（`updateState` による複数メッセージ初期化）・R2（`::` 含む `thread_id`）・R4（`deriveCurrentStep` の妥当性）を実機確認する。想定通り動かなかった場合は I.3 設計と §R4 の `deriveCurrentStep` 方針を再検討してから次に進む
6. `thread_branches` テーブル作成 + `branch-store.ts`
7. `ThreadSettings` に `activeBranchId` を追加（サーバー・フロント両方）
8. `POST /api/chat/fork` と `GET /api/chat/branches` API 追加
9. `GET /api/chat/history` に `branchId` パラメータ対応
10. `POST /api/chat` に `branchId` パラメータ対応
11. `useBranches` composable 新規 + `useChat` 修正
12. `ChatMessage.vue` 編集 UI + `BranchNavigator.vue` 新規
13. `ChatInput.vue` 編集モード対応 + `index.vue` 配線

## Phase R: 事前リファクタの詳細

### R.1 `server/utils/langgraph-thread.ts`（新規）

```typescript
export const MAIN_BRANCH_ID = 'main'

export function toLangGraphThreadId(threadId: string, branchId: string = MAIN_BRANCH_ID): string {
  if (branchId === MAIN_BRANCH_ID) return threadId
  return `${threadId}::${branchId}`
}
```

### R.2 既存コード差し替え

以下 3〜4 箇所を `toLangGraphThreadId(body.threadId)` 経由に差し替える（行番号はコード実態に合わせて最終確認。Explore 報告では `chat.post.ts` L85 / L115 / L38、`chat/history.get.ts` L53 付近）:

- `chat.post.ts`: `agent.stream(...)` 呼び出し時の `configurable.thread_id`
- `chat.post.ts`: `agent.getState(...)` 呼び出し時の `configurable.thread_id`
- `chat.post.ts`: エコーモード `agent.updateState(...)` の `configurable.thread_id`
- `chat/history.get.ts`: `agent.getState(...)` の `configurable.thread_id`

※ 既存挙動と完全同値（`branchId` 省略時は raw threadId を返す）。既存テストはパスする。

### R.3 `tests/fixtures/settings.ts`（新規）

REFACTOR.md §5 のコードをそのまま配置。

### R.4 テスト置換

手順:

1. `thread-settings.test.ts` L30, L35, L42 の `expect(settings).toEqual(DEFAULT_SETTINGS)` → `expect(settings).toEqual(makeThreadSettings())`
2. 既存の `{ ...DEFAULT_SEARCH_SETTINGS }` スプレッドは、`makeThreadSettings({ search: {...} })` の形で書き換え
3. `settings-api.test.ts` のテスト内 `const DEFAULT_SEARCH_SETTINGS = {...}` ローカル定義を削除し、`makeThreadSettings().search` 参照に差し替え
4. `chat.test.ts` の `mockGraph` フィクスチャ設定部分を `makeThreadSettings()` 経由に統一

**テスト差分の量**: 約 18 箇所を差し替え、DEFAULT 値参照が 1 箇所（`makeThreadSettings` 内）に集約される。

## Phase I: 機能追加の詳細

### I.1 `thread_branches` テーブルと `branch-store.ts`

**ファイル**: `server/utils/branch-store.ts`（新規）

**スキーマ作成**: `thread-store.ts` と同パターンで DB 初期化時に `CREATE TABLE IF NOT EXISTS`。`thread-store.ts` の `initDB()` 相当部分に並置するか、新規の `initBranchesTable()` を export して `thread-store.ts` から呼び出す。具体的な配置は既存 `thread-store.ts` の DB 初期化関数を確認して合わせる。

**エクスポート関数**:

```typescript
export interface BranchRecord {
  branch_id: string
  thread_id: string
  parent_branch_id: string | null
  fork_message_index: number
  created_at: string
}

// main は返さない（呼び出し側で main を先頭に足す）
export function getBranches(threadId: string): BranchRecord[]

// branch_id は crypto.randomUUID() で採番
export function createBranch(params: {
  threadId: string
  parentBranchId: string
  forkMessageIndex: number
}): BranchRecord
```

### I.2 `ThreadSettings` に `activeBranchId` 追加

**`server/utils/thread-store.ts`**:

```typescript
export interface ThreadSettings {
  granularity: 'concise' | 'standard' | 'detailed'
  customInstruction: string
  search: SearchSettings
  responseMode: ResponseMode
  systemPromptOverride: string
  activeBranchId: string   // 追加（デフォルト 'main'）
}

export const DEFAULT_SETTINGS: ThreadSettings = {
  // ... 既存
  activeBranchId: MAIN_BRANCH_ID,
}
```

**`app/composables/useSettings.ts`**: 同じフィールドを追加。

**`server/api/threads/[id]/settings.put.ts`**:

- `activeBranchId` バリデーション: 文字列かつ `MAIN_BRANCH_ID` または `thread_branches` 内に該当レコードが存在することを確認（`thread_id` も一致）。不正値は `'main'` にフォールバック

### I.3 `POST /api/chat/fork` API

**ファイル**: `server/api/chat/fork.post.ts`（新規）

**リクエストボディ**:

```typescript
{
  threadId: string
  fromBranchId: string          // 分岐元（通常は activeBranchId）
  forkMessageIndex: number      // 分岐元の HumanMessage のインデックス（0-origin）
  newMessage: string            // 編集後のユーザー入力
}
```

**処理フロー（非ストリーミング）**:

1. 入力バリデーション
2. `createBranch()` で `thread_branches` に新レコード追加 → `newBranchId` 取得
3. 親ブランチの LangGraph 状態を取得:

   ```typescript
   const parentThreadId = toLangGraphThreadId(threadId, fromBranchId)
   const parentSnapshot = await agent.getState({ configurable: { thread_id: parentThreadId } })
   const parentMessages = parentSnapshot.values.messages as BaseMessage[]
   ```

4. `forkMessageIndex` までの要素のみをコピー（編集したメッセージ以降は含めない）:

   ```typescript
   const newMessages = parentMessages.slice(0, forkMessageIndex)
   ```

5. 新ブランチ thread_id で updateState してコピーを永続化:

   ```typescript
   const newThreadId = toLangGraphThreadId(threadId, newBranchId)
   const newCurrentStep = deriveCurrentStep(newMessages)
   await agent.updateState(
     { configurable: { thread_id: newThreadId } },
     { messages: newMessages, currentStep: newCurrentStep, abstractedProblem: parentSnapshot.values.abstractedProblem },
   )
   ```

   `deriveCurrentStep` の実装方針（§R4 参照）は**案 B（末尾メッセージ種別のヒューリスティクス）をデフォルト採用**し、`experiments/fork-checkpoint.ts`（§I.0）の検証結果で他案に切り替える可能性を残す。

6. `activeBranchId` を新ブランチに切替:

   ```typescript
   const settings = getThreadSettings(threadId)
   updateThreadSettings(threadId, { ...settings, activeBranchId: newBranchId })
   ```

7. レスポンス:

   ```json
   { "branchId": "<newBranchId>", "activeBranchId": "<newBranchId>" }
   ```

**注意**: この API はチェックポイントコピーと DB 更新のみで**新メッセージの AI 応答生成は行わない**。AI 応答は `POST /api/chat` で `newMessage` を送信して実行する（既存の SSE 経路を再利用）。こうすることでフロント側の処理は `fork → 成功 → activeBranchId 切替 → 既存の sendMessage(newMessage)` と素直に書ける。

### I.4 `GET /api/chat/branches` API

**ファイル**: `server/api/chat/branches.get.ts`（新規）

**クエリ**: `?threadId=xxx`

**レスポンス**:

```json
{
  "branches": [
    { "branchId": "main", "parentBranchId": null, "forkMessageIndex": null, "createdAt": null },
    { "branchId": "<uuid>", "parentBranchId": "main", "forkMessageIndex": 3, "createdAt": "..." }
  ],
  "activeBranchId": "<current>"
}
```

- main は常に先頭に入れる（DB には登録されていないが、API レスポンスでは仮想的に含める）
- 並び: main → `created_at` 昇順

### I.5 `GET /api/chat/history` に `branchId` 対応

**ファイル**: `server/api/chat/history.get.ts`（変更）

- クエリに `branchId`（省略時 `'main'`）を追加
- `toLangGraphThreadId(threadId, branchId)` で合成キーを生成
- 既存の `getState` を置き換える

### I.6 `POST /api/chat` に `branchId` 対応

**ファイル**: `server/api/chat.post.ts`（変更）

- リクエストボディに `branchId`（省略時 `'main'`）を追加
- `stream`, `getState`, エコーモードの `updateState` 3 箇所で `toLangGraphThreadId(body.threadId, body.branchId ?? 'main')` を使用
- `upsertThread` / `getThreadTitle` / `updateThreadTitle` は**スレッド単位**の操作なので、branchId 非依存（従来通り threadId のみで呼ぶ）
- タイトル自動生成: 初回メッセージで生成するロジックは main 分岐の先頭メッセージに紐づくため、**非メイン分岐では発火しない**ようにガード（`branchId !== 'main'` なら title 生成をスキップ）

### I.7 `useBranches` composable（新規）

**ファイル**: `app/composables/useBranches.ts`

```typescript
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
  async function setActiveBranch(threadId: string, branchId: string): Promise<void>   // settings PUT 経由
  async function fork(params: { threadId, fromBranchId, forkMessageIndex, newMessage }): Promise<string>
  //   fork 内部: POST /api/chat/fork → branchId 返却 → activeBranchId.value 更新 → branches.value 再読込

  return { branches, activeBranchId, loadBranches, setActiveBranch, fork }
}
```

- `setActiveBranch` は `PUT /api/threads/:id/settings` で `{ activeBranchId }` のみ渡す。サーバー側は既存の差分更新ロジックで吸収
- `fork` は fork API のみ。AI 応答生成は `useChat.sendMessage(newMessage)` を呼び出し側が続けて呼ぶ

### I.8 `useChat` 修正

**ファイル**: `app/composables/useChat.ts`（変更）

- `branchId` を ref で保持（`useBranches` からではなく独自に持つ。`index.vue` で同期）
- `loadHistory` / `sendMessage` で `branchId` を引数/fetch body に含める
- `switchThread(threadId, branchId = 'main')` とシグネチャ拡張

### I.9 `useSettings` 修正

- `activeBranchId` フィールドのみ追加（型定義と DEFAULT_SETTINGS）
- 他の変更は不要

### I.10 `BranchNavigator.vue`（新規）

**ファイル**: `app/components/BranchNavigator.vue`

**Props**: `{ branches: Branch[], activeBranchId: string, forkMessageIndex: number }`

**責務**: 特定メッセージ（`forkMessageIndex` が一致する分岐が存在するメッセージ）の下に `◀ N/M ▶` を表示。クリックで emit `change-branch`。

- 同一 `forkMessageIndex` を持つ分岐のみをグループ化して表示（ただし main 分岐は常に 1/N の 1 番目として含める実装で十分）
- **簡略化**: 初期版では「各メッセージ位置で発生している分岐のうち、現在アクティブなパスを含むグループ」のみを表示する。複数階層の分岐ツリー表示は対象外（ROUGH_PLAN のスコープ外）

### I.11 `ChatMessage.vue` 変更

- ユーザーメッセージ（`role === 'user'`）にホバー時の「編集」ボタンを追加
- 編集クリックで emit `start-edit` (messageIndex)
- `BranchNavigator` を配置する slot（編集済み位置のメッセージのみ）
- AI メッセージは変更なし（既存の検索結果表示はそのまま）
- **非アクティブ分岐のメッセージ表示方針**: 分岐切替時は `useChat.switchThread(threadId, newBranchId)` で history 全体を再ロードし、メッセージリストを**完全に差し替える**。グレーアウトや薄表示などの中間表現は用意しない（シンプルさ優先、非アクティブ分岐の内容は DB に残っているため `◀ ▶` で戻せばすぐ閲覧できる）

### I.12 `ChatInput.vue` 変更

- `editMode: { messageIndex: number, originalText: string } | null` prop を受け取る
- 編集モード時:
  - テキストエリアに `originalText` を初期表示
  - 送信ボタンのラベルを「送信」→「分岐として送信」に変更
  - キャンセルボタン追加 → emit `cancel-edit`
  - 送信時は emit `submit-edit`（通常送信とは別イベント）

### I.13 `app/pages/index.vue` 変更

- `useBranches` 追加、`onMounted` / `switchThread` で `loadBranches(threadId)` を実行
- `ChatMessage` の `start-edit` イベントでフォームを編集モードに切替
- `ChatInput` の `submit-edit` で `useBranches.fork(...)` → 成功後 `useChat.sendMessage(newMessage)`
- `BranchNavigator` の `change-branch` で `useBranches.setActiveBranch(...)` → `useChat.switchThread(threadId, newBranchId)`

## テスト計画

### 新規テストファイル

- `tests/server/branch-store.test.ts` — `getBranches` / `createBranch` の DB 操作
- `tests/server/chat-fork.test.ts` — `POST /api/chat/fork` のフロー（mock agent で updateState / getState 確認）
- `tests/server/chat-branches.test.ts` — `GET /api/chat/branches` のレスポンス形（main 先頭 + DB レコード）
- `tests/server/langgraph-thread.test.ts` — `toLangGraphThreadId` の単純ユニット
- `tests/composables/useBranches.test.ts` — `loadBranches` / `fork` / `setActiveBranch`

### 既存テスト更新

- `tests/server/chat.test.ts` — `branchId` を受け取るケースを追加、`toLangGraphThreadId` 経由の合成キー確認
- `tests/server/chat-history.test.ts` — `branchId` クエリパラメータ追加ケース
- `tests/server/thread-settings.test.ts` — `activeBranchId` フィールド追加（makeThreadSettings 経由でほぼ自動的に追従）
- `tests/server/settings-api.test.ts` — `activeBranchId` バリデーション（不正値のフォールバック）
- `tests/composables/useChat.test.ts` — `branchId` パラメータ引き回し

### テスト件数目安

- 現状 107 ケース
- 追加: 新規 5 ファイル × 平均 4〜6 ケース = 約 25 ケース + 既存更新 5 件 = **+30 ケース前後**
- 目標: **137 ケース前後**

## リスク・不確実性

### R1. LangGraph `agent.updateState()` による任意メッセージ配列の永続化が正しく動くか

- ver16.1 エコーモードで 1 メッセージペアを `updateState` する使い方は実装済みだが、**fork では「親の途中までをコピー」として複数メッセージを `messages` チャネルに書く必要がある**
- LangGraph の `messagesStateReducer` は AIMessage/HumanMessage の追加・差し替えを扱うが、「N 件に切り詰めた履歴で新 thread_id を初期化する」挙動は公式ドキュメントに明示がない可能性
- **対応**: 実装時にまず小さな検証スクリプト（`experiments/fork-checkpoint.ts` 新規）で以下を確認する:
  1. 空の `thread_id` に `updateState({ messages: [h1, a1, h2] })` を呼んで state が 3 件になるか
  2. 以降 `stream` で実行 → `[h1, a1, h2, a2]` になるか
- **フォールバック**: 上記が動かない場合、`messages` の reducer をカスタマイズして「初回のみ完全上書き」を可能にする、または各メッセージを 1 件ずつ順に updateState で流し込む方式に切替

### R2. LangGraph checkpointer の `thread_id` キーが `::` を含む文字列で問題なく動くか

- SqliteSaver の内部 SQL で `thread_id` をそのまま `WHERE thread_id = ?` で使っていればエスケープ不要
- **対応**: `langgraph-thread.test.ts` で `::` を含む thread_id で round-trip（updateState → getState）が通ることを確認
- **フォールバック**: もし何らかの理由で動かない場合、セパレータを `:::` や他の記号に変更、あるいは分岐専用のハッシュ化

### R3. `caseSearch` ノードでの検索結果再現性

- 分岐作成時に親の途中までをコピーすると、AIMessage の `additional_kwargs.searchResults` もそのまま保持される
- ただし新分岐で `caseSearch` を**再実行**すると、Tavily の検索結果が変わる可能性がある（時系列や外部要因）
- **判断**: 「分岐の本質は再生成」なので、検索結果が変わることはユーザーにとって許容される仕様と扱う
- **対応不要**。特記なし

### R4. `currentStep` の復元ロジック

- 既存 `analogy-agent.ts` の `routeByStep` は `state.currentStep` の値のみを見る。`currentStep` は各ノード（`caseSearchNode` → `awaiting_selection`、`solutionNode` → `completed`、`followUpNode` → 維持）が実行後に更新する
- 分岐では「fork 位置までのメッセージ配列から `currentStep` を推測」する必要があり、これは既存コードにないロジック
- **採用方針: 案 B（ヒューリスティクス）**

  `deriveCurrentStep(messages: BaseMessage[]): 'initial' | 'awaiting_selection' | 'completed'`:

  ```
  - messages 長 === 0 または末尾が HumanMessage → 'initial'
    （次は abstraction → caseSearch が走る）
  - 末尾が AIMessage かつ additional_kwargs.searchResults がある
      → 'awaiting_selection'
    （次は solution が走る — 事例提示済みの状態）
  - 末尾が AIMessage かつ searchResults がない
      → 'completed'
    （次は followUp が走る — 解決策提示後の追加質問ループ）
  ```

  この判定は既存の 4 ノード構造と `STREAMED_NODES` の組み合わせから導出できる。**ただし `followUp` ノード実行後も AIMessage は `searchResults` を持たないため `completed` と区別できない**。これは現行の設計上、どちらも next = `followUp` で同じ挙動になるので実害はない（`routeByStep` の条件分岐に `'completed'` → followUp、`'awaiting_selection'` → solution の 2 値で足りる）

- **代替案（A / C）と採用しない理由**:
  - 案 A（スナップショット履歴から中間チェックポイント復元）: `getStateHistory` を使う実装は LangGraph 依存度が高く、`experiments/fork-checkpoint.ts` で API 挙動を確認してからでないと成立性が不明
  - 案 C（常に `'initial'` で再開）: 分岐後に abstraction から再実行され、ユーザーが過去に提示した事例が失われる。分岐の目的（「選択を変えて別の解決策を見る」）を達成できない

- **実装位置**: `server/utils/analogy-agent.ts` に `export function deriveCurrentStep(messages: BaseMessage[])` として追加。`fork.post.ts` から import
- **テスト**: `tests/server/langgraph-thread.test.ts`（または `analogy-agent.test.ts` 新規）で 4 パターン（空 / 末尾 Human / 末尾 AI+searchResults / 末尾 AI-searchResults）のユニットを追加

### R5. `thread_branches` テーブルの `FOREIGN KEY` + `ON DELETE CASCADE`

- `better-sqlite3` はデフォルトで `PRAGMA foreign_keys = ON` が無効（`better-sqlite3` のデフォルト挙動を確認）。有効化されていないと CASCADE が効かない
- **対応**: `thread-store.ts` の DB 初期化で `db.pragma('foreign_keys = ON')` を確認（既にある場合は不要、ない場合は追加）
- **代替案**: スレッド削除機能は現状 UI に存在しないため、CASCADE は将来の保険。ドキュメントに「CASCADE 挙動は foreign_keys ON 前提」と明記すれば当面問題なし

### R6. ver16.1 未解消の ISSUES（`additional-kwargs-sqlite`・`getState-timing`）との干渉

- 分岐機能は `getState` と `updateState` を多用するため、これら ISSUES が表面化する可能性がある
- **対応**: 分岐機能のユニットテストは mock checkpointer で通すため、ユニットテストでは影響を受けない。実機検証はユーザー側のデプロイ後手動確認に委ねる（RETROSPECTIVE の方針に準拠）

## コード変更規模の見積もり

### 新規ファイル（10 ファイル）

| ファイル | 見積行数 |
|---|---|
| `server/utils/langgraph-thread.ts` | 10 |
| `server/utils/branch-store.ts` | 70 |
| `server/api/chat/fork.post.ts` | 100 |
| `server/api/chat/branches.get.ts` | 30 |
| `app/composables/useBranches.ts` | 80 |
| `app/components/BranchNavigator.vue` | 60 |
| `tests/fixtures/settings.ts` | 20 |
| `tests/server/langgraph-thread.test.ts` | 30 |
| `tests/server/branch-store.test.ts` | 80 |
| `tests/server/chat-fork.test.ts` | 120 |
| `tests/server/chat-branches.test.ts` | 60 |
| `tests/composables/useBranches.test.ts` | 100 |

### 変更ファイル（10 ファイル）

| ファイル | 変更規模 |
|---|---|
| `server/api/chat.post.ts` | +20 |
| `server/api/chat/history.get.ts` | +10 |
| `server/api/threads/[id]/settings.put.ts` | +15 |
| `server/utils/thread-store.ts` | +5（`activeBranchId` 追加） |
| `server/utils/analogy-agent.ts` | +20（`deriveCurrentStep` 切り出し） |
| `app/composables/useChat.ts` | +15 |
| `app/composables/useSettings.ts` | +5 |
| `app/components/ChatMessage.vue` | +40 |
| `app/components/ChatInput.vue` | +30 |
| `app/pages/index.vue` | +30 |
| 既存テスト更新（Phase R 含む） | +50 |

**合計**: 新規 760 行 + 変更 240 行 ≒ **1000 行規模**（メジャーバージョンとして想定範囲）

## 完了基準

1. `pnpm test` 全グリーン（107 → 137 ケース前後）
2. `npx nuxi typecheck` のエラー 0（既知の volar 警告を除く）
3. dev サーバー起動で以下が動作:
   - 新規スレッド → メッセージ送信 → AI 応答（既存挙動が壊れていない）
   - 自分のメッセージ編集 → 分岐作成 → 新しい AI 応答
   - `◀ 1/2 ▶` で元の分岐に戻れる
   - リロード後も activeBranchId が復元される
4. 既存の ver16.x スレッドを開いて、編集せずに会話を続けた場合に従来通り動作する（`branchId = 'main'` = raw threadId の後方互換確認）

## やらないこと

- 分岐ツリーのビジュアライゼーション（`forkMessageIndex` が複数段に分かれる複雑な UI）
- 分岐の削除・マージ機能
- 分岐ごとのタイトル命名 UI
- AI メッセージの編集
- エコーモードでの分岐ナビゲーション最適化（動作する範囲で十分）

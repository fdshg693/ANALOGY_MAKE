# テスト現況（ver17.0）

## テストファイル一覧

| ファイル | 行数 | テストケース数 | 備考 |
|---|---|---|---|
| `tests/utils/sse-parser.test.ts` | 167 | 8 | SSE パーサー（ver17.0 で変更なし） |
| `tests/composables/useChat.test.ts` | 264 | 11 | `branchId` パラメータ引き回しを追加（ver17.0） |
| `tests/composables/useThreads.test.ts` | 165 | 13 | `importFresh` パターン（ver17.0 で変更なし） |
| `tests/server/thread-store.test.ts` | 85 | 8 | `createRequire` で CJS モック回避（ver17.0 で変更なし） |
| `tests/server/threads.test.ts` | 45 | 2 | threads API（ver17.0 で変更なし） |
| `tests/server/chat.test.ts` | 421 | 14 | `branchId` 引き回し・エコーモード（ver17.0/16.1 追加） |
| `tests/server/chat-history.test.ts` | 272 | 11 | `branchId` クエリパラメータ追加ケース（ver17.0） |
| `tests/server/prompt-builder.test.ts` | 130 | 8 | `buildSystemPrompt()` のテスト（ver17.0 で変更なし） |
| `tests/server/settings-api.test.ts` | 296 | 16 | `activeBranchId` バリデーション追加（ver17.0） |
| `tests/server/thread-settings.test.ts` | 174 | 12 | `activeBranchId` フィールド追加（ver17.0） |
| `tests/server/analogy-agent.test.ts` | 45 | 5 | `deriveCurrentStep` ユニット（ver17.0 新規） |
| `tests/server/branch-store.test.ts` | 106 | 8 | `getBranches` / `branchBelongsToThread` / `createBranch`（ver17.0 新規） |
| `tests/server/langgraph-thread.test.ts` | 28 | 4 | `toLangGraphThreadId` / `MAIN_BRANCH_ID`（ver17.0 新規） |
| `tests/server/chat-fork.test.ts` | 196 | 9 | `POST /api/chat/fork` 正常系・異常系（ver17.0 新規） |
| `tests/server/chat-branches.test.ts` | 125 | 16 | `GET /api/chat/branches` 正常系・異常系（ver17.0 新規） |

## 合計

- **15 ファイル**、**145 テストケース**（ver16.1: 15ファイル・107ケースから増加）

## テスト補助ファイル

### `tests/fixtures/settings.ts`（10行）— ver17.0 新規

`ThreadSettings` テストフィクスチャファクトリ。`DEFAULT_SETTINGS` のスプレッドを一元管理し、フィールド追加時の更新コストを削減。

```typescript
export function makeThreadSettings(override: Partial<ThreadSettings> = {}): ThreadSettings {
  return {
    ...DEFAULT_SETTINGS,
    ...override,
    search: { ...DEFAULT_SETTINGS.search, ...(override.search ?? {}) },
  }
}
```

- `thread-settings.test.ts` / `settings-api.test.ts` / `chat.test.ts` 等の DEFAULT 値比較箇所で使用

## ver17.0 追加テスト

### `tests/server/analogy-agent.test.ts`（5ケース）

`deriveCurrentStep` の判定パターンを検証:
- 空配列 → `'initial'`
- 末尾が `HumanMessage` → `'initial'`
- 末尾が `AIMessage` かつ `searchResults` あり → `'awaiting_selection'`
- 末尾が `AIMessage` かつ `searchResults` なし → `'completed'`
- 末尾が `AIMessage` かつ `searchResults` が空配列 → `'completed'`

### `tests/server/branch-store.test.ts`（8ケース）

`getBranches` / `branchBelongsToThread` / `createBranch` の DB 操作を in-memory SQLite で検証。

### `tests/server/langgraph-thread.test.ts`（4ケース）

- `MAIN_BRANCH_ID` が `'main'` であること
- `toLangGraphThreadId(threadId, 'main')` が raw `threadId` を返すこと
- `toLangGraphThreadId(threadId, uuid)` が `${threadId}::${uuid}` を返すこと
- `branchId` 省略時も `'main'` のデフォルトが機能すること

### `tests/server/chat-fork.test.ts`（9ケース）

`POST /api/chat/fork` のフロー（mock agent で `getState` / `updateState` の呼び出し確認）:
- 正常系: 分岐作成・`activeBranchId` 更新・レスポンス形式
- 異常系: `fromBranchId` 不正・`forkMessageIndex` 範囲外・必須パラメータ欠落

### `tests/server/chat-branches.test.ts`（16ケース）

`GET /api/chat/branches` のレスポンス形式を検証:
- `main` 分岐が先頭に付与されること
- DB のレコードが `created_at` 昇順で続くこと
- `activeBranchId` が settings から正しく取得されること
- `threadId` 欠落時の 400 エラー

## テスト戦略の特記事項（ver17.0）

- **`experiments/fork-checkpoint.ts` の作成をスキップ**: R1（`updateState` 複数メッセージ）・R2（`::` 含む `thread_id`）の実機検証は本番デプロイ後の手動確認に委譲（`fork-checkpoint-verification.md` に追記）
- **mock agent 方式の継続**: `chat-fork.test.ts` では `vi.mock('@langchain/langgraph')` ではなく `vi.mock('../../server/utils/analogy-agent')` で `getAnalogyAgent` を差し替え。LangGraph 実機を呼ばずに API レイヤーのロジックをテスト
- その他の戦略（`environment: 'node'`、`importFresh`、`createRequire`、`node:fs` モック）は ver15.x から継続

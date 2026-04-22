# ver17.0 REFACTOR — 会話分岐導入前の事前整理

会話分岐（`(threadId, branchId)` 二本立て）を入れる前に、方針確定と小規模な整理を行う。本ファイルは「IMPLEMENT.md で採用する方針の事前合意」と「不可避の軽量リファクタ」に限定する。

## 1. LangGraph `thread_id` キーの合成方針

### 現状

`server/api/chat.post.ts` / `chat/history.get.ts` は `body.threadId` / `query.threadId` を**そのまま** LangGraph の `config.configurable.thread_id` に渡している。SqliteSaver は `thread_id` を 1 次元キーとして扱うため、1 スレッド = 1 会話履歴になっている。

### 方針（確定）

**方針 B: メイン分岐は raw `threadId`、非メイン分岐のみ `${threadId}::${branchId}` を合成**

| branchId | LangGraph の `thread_id` 値 | 用途 |
|---|---|---|
| `"main"`（デフォルト） | `threadId`（raw） | ver16.x 以前に作成された既存スレッドと完全互換 |
| その他（UUID） | `${threadId}::${branchId}` | 分岐作成時に新規払い出し |

**選定理由**:

- **既存スレッドを無変更で引き継げる**: ver16.x 以前に作成されたスレッドは LangGraph checkpointer に `thread_id = raw threadId` で保存されている。これを「main 分岐」と同一視でき、DB マイグレーション不要
- **分岐作成時のみ新規キー**: 新規分岐のチェックポイントは別の合成 `thread_id` で保存されるので、メインと分岐が独立して進行する
- **`::` セパレータ**: UUID v4 は `-` を含むため誤パースのリスクあり、`:` の連続は UUID には現れず衝突しない

**代替案と不採用理由**:

- **方針 A（全てを `${threadId}::${branchId}` に統一）**: 既存スレッドの LangGraph チェックポイントを一括リネームするマイグレーションが必要。SqliteSaver は内部テーブルにアクセスするための public API を提供していない可能性があり、リスクが高い。本バージョンでは採用しない
- **方針 C（カスタム Checkpointer）**: 保守負荷が大きく、今回のスコープ外

### 実装箇所（IMPLEMENT.md で詳細化）

- `server/utils/langgraph-thread.ts`（新規）に 1 関数だけ追加: `toLangGraphThreadId(threadId, branchId)`
- `chat.post.ts` / `chat/history.get.ts` の `thread_id:` を渡す 3 箇所をこのヘルパー経由に差し替える

## 2. `branchId` のデフォルト値と型

### 方針（確定）

- サーバー境界（API リクエスト・レスポンス）で `branchId` は**オプショナル**（省略時は `"main"`）
- サーバー内部・`useBranches` 内部では**必須**の `string` として扱う
- 型名は `BranchId = string` のまま（brand 型は導入しない — オーバーエンジニアリング）
- `"main"` は予約文字列定数として `const MAIN_BRANCH_ID = 'main'` を export（マジックストリング回避）

### 実装箇所

- `server/utils/thread-store.ts` 末尾 or 新規 `server/utils/branch-store.ts` で定数を export
- フロント側は `app/composables/useBranches.ts` から同じ定数を独自定義（既存の `ThreadSettings` 型重複と同じ流儀、`shared/` 統合は将来対応）

## 3. `useBranches.ts` 分離設計

### 設計方針（確定）

- `useChat.ts` は既存のメッセージストリーム・送受信責務のみ保持（branchId は read-only で参照するのみ）
- `useBranches.ts`（新規）が分岐の一覧・アクティブ分岐・分岐作成・分岐切替を管理
- `useThreads.ts` は既存通りスレッド一覧のみ（分岐情報は持たない）
- `app/pages/index.vue` で 3 つの composable を束ね、`switchThread` 時に `useBranches.loadBranches(threadId)` → アクティブ分岐の history load を実行

### 各 composable の責務再定義

| composable | 責務 | 他 composable への依存 |
|---|---|---|
| `useThreads` | スレッド一覧・アクティブスレッド（localStorage 永続化） | なし |
| `useBranches`（新規） | 分岐一覧・アクティブ分岐・分岐作成/切替 API 呼び出し | なし（threadId は引数経由） |
| `useChat` | メッセージストリーム（SSE）・送信・履歴復元 | なし（threadId・branchId は引数経由） |
| `useSettings` | スレッド単位の設定 GET/PUT | なし |

`index.vue` の `onMounted` / `switchThread` で順序を明示的に制御する（3 composables 間に暗黙的な副作用を作らない）。

## 4. `threads` テーブル vs `thread_branches` テーブル

### 方針（確定）

- `threads` テーブル（既存）は**変更しない**。`settings` カラム拡張で済ませる案も検討したが、JSON 内配列の UPDATE は同時編集に弱く、分岐メタデータを正規化できない
- 新規テーブル `thread_branches` を追加（MASTER_PLAN PHASE3.md §3.3 の案をそのまま採用）
- アクティブ分岐 ID の保持は `threads.settings`（JSON の `ThreadSettings`）に `activeBranchId` として追加する（設定系で既存パスが整っているため）

### `thread_branches` スキーマ

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

**MASTER_PLAN 案との差分**:

- `checkpoint_id TEXT NOT NULL` は**削除**。LangGraph の合成 `thread_id` で特定チェックポイントを引き当てる方式（方針 B）に切り替えたため不要
- `ON DELETE CASCADE` を追加（スレッド削除時の孤児レコード防止）

**main 分岐の扱い**: `thread_branches` には**登録しない**（存在しないことが「main のみ」を示す）。暗黙扱いにすることで、既存スレッドとの互換性が保たれる。分岐作成時に初めて非メインブランチ 1 件が登録される（= `branches` 一覧には main + 非メインが含まれる）。

## 5. `ThreadSettings` テストフィクスチャのテストヘルパ導入

### 背景

ver15.1（`search` 追加）・ver16.1（`responseMode` + `systemPromptOverride` 追加）・ver17.0（`activeBranchId` 追加）と `ThreadSettings` が拡張される度に、`thread-settings.test.ts` / `settings-api.test.ts` / `chat.test.ts` の合計約 18 箇所で完全一致アサーションや DEFAULT 値のハードコードを更新している。

### 方針（確定）

**本バージョンで導入する。** ver17.0 で `activeBranchId` 追加による更新コストが同時に発生するため、先にヘルパを整備してから新フィールドを入れる流れが最も安価。

**導入内容**:

```ts
// tests/fixtures/settings.ts（新規）
import { DEFAULT_SETTINGS } from '../../server/utils/thread-store'
import type { ThreadSettings } from '../../server/utils/thread-store'

export function makeThreadSettings(override: Partial<ThreadSettings> = {}): ThreadSettings {
  return {
    ...DEFAULT_SETTINGS,
    ...override,
    search: { ...DEFAULT_SETTINGS.search, ...(override.search ?? {}) },
  }
}
```

**置換対象（事前洗い出し）**:

- `tests/server/thread-settings.test.ts` 約 8 箇所（DEFAULT_SETTINGS 完全一致アサーション・スプレッドの半数）
- `tests/server/settings-api.test.ts` 約 7 箇所（テスト内ローカル定義 `const DEFAULT_SEARCH_SETTINGS = {...}` の除去）
- `tests/server/chat.test.ts` 約 3 箇所（`mockGraph` のハードコード設定）

**やらないこと**:

- フロント側 `useSettings.ts` の `DEFAULT_SETTINGS` と server 側の重複定義の統合（別議題、`shared/` 集約と合わせて将来バージョンで対応）
- テスト全体のリファクタ（該当する DEFAULT 値比較の 18 箇所のみを差し替える最小変更）

## 6. メッセージ編集ボタンの表示範囲

### 方針（確定）

- **すべてのユーザーメッセージに編集ボタンを表示**（ホバー時のみ）
- AI メッセージには表示しない（スコープ外）
- 「同一メッセージに対して複数回の分岐」は許容（連番 `1/2/3...` が増える）
- 分岐元より前のメッセージを編集する操作も UI 上は可能（分岐は編集位置から発生、分岐元を複数持てる）

**UX の簡潔さを優先**: 制限ロジック（「最新の AI 回答完了後のみ」等）を入れると、ストリーミング中の中断・エラー回復時の境界条件が複雑になる。最小仕様で出して、実運用で不都合があれば次バージョンで調整する。

## 7. 事前リファクタで実施する変更（小規模）

本バージョンの機能追加の前に、別コミットで以下の最小リファクタを実施する。これらは分岐機能なしでも有効な整理で、機能追加コミットを純粋化するために先出しする。

### 7.1 `toLangGraphThreadId` ヘルパーの骨組み作成

- `server/utils/langgraph-thread.ts`（新規）に `toLangGraphThreadId(threadId, branchId = 'main')` を置き、既存の 3 箇所（`chat.post.ts` で 2 箇所、`chat/history.get.ts` で 1 箇所）を差し替える
- `branchId` は未定義だがデフォルト `'main'` で現状挙動と同値（raw threadId を返す分岐は `branchId === 'main'` 時のみ）。既存テストに影響なし

### 7.2 `tests/fixtures/settings.ts` ヘルパー導入 + 置換

- §5 のヘルパーを作成
- `thread-settings.test.ts` / `settings-api.test.ts` / `chat.test.ts` の該当箇所を差し替える
- この時点では `ThreadSettings` は現状維持（`activeBranchId` はまだ追加しない）
- テストが全てグリーンであることを確認してから機能追加コミットに進む

### 7.3 やらないこと

- `thread_branches` テーブル作成・`ThreadSettings` の `activeBranchId` 追加は IMPLEMENT フェーズで実施
- API 追加は IMPLEMENT フェーズ
- フロント composable 新規作成は IMPLEMENT フェーズ
- 既存コンポーネントの UI 変更は IMPLEMENT フェーズ

## 8. リファクタ不要と判断した項目

| 検討項目 | 判断 | 理由 |
|---|---|---|
| `ThreadSettings` 型のフロント/サーバー統合 | 本 ver では不要 | `shared/` 集約は既知の課題（ver16.0 で明記）だが、会話分岐と独立。別 ver で対応 |
| `SearchResult` 型の `shared/` 移動 | 本 ver では不要 | 同上 |
| `threads` テーブルスキーマの変更 | 不要 | `settings` JSON への `activeBranchId` 追加で済む |
| `useChat` / `useBranches` 以外の composable の再設計 | 不要 | `useThreads` / `useSettings` は現状の責務のまま拡張不要 |
| SqliteSaver のカスタム Checkpointer 化 | 不要 | 方針 B（合成キー）で十分 |

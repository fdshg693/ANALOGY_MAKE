# バックエンド現況

## API エンドポイント

### `server/api/chat.post.ts`（112行）

- `POST /api/chat` SSE ストリーミングエンドポイント
- `upsertThread(body.threadId)` でスレッドメタデータ登録・更新
- **ver15.0 追加**: `getThreadSettings(body.threadId)` で設定を読み込み、`configurable.settings` 経由で LangGraph ノード関数に渡す
- ストリーム完了後にタイトル自動生成（`generateTitle()`、gpt-4.1-mini, temperature: 0, maxTokens: 30、非同期・非ブロッキング）
- ストリーミングフィルタ: `STREAMED_NODES = new Set(["caseSearch", "solution", "followUp"])` でホワイトリスト方式。`abstraction` ノードの出力はフィルタリング
- 入力は `new HumanMessage(body.message)`（`StateGraph` の `messages` フィールドが `BaseMessage[]` を要求）

**リクエスト:**
```json
{ "message": "string", "threadId": "string" }
```

**レスポンス:** SSE ストリーム（`Content-Type: text/event-stream`）

| event | data | 説明 |
|---|---|---|
| `token` | `{"content": "..."}` | トークン1つ分のテキスト |
| `done` | `{}` | ストリーミング正常完了 |
| `error` | `{"message": "..."}` | エラー発生 |

### `server/api/chat/history.get.ts`（67行）

- `GET /api/chat/history?threadId=xxx` 会話履歴取得エンドポイント
- `graph.getState()` で LangGraph チェックポイントからスナップショット取得
- **ver14.5 で全面改修**: `@langchain/core/messages` への依存を完全排除。ローカルに `CheckpointMessage` インターフェースと `isChatMessage()` 型ガード関数を定義
- `isChatMessage()` は `type` プロパティ（`'human'` / `'ai'`）で判定（デシリアライズ後のプレーンオブジェクトにも対応）
- **ver14.4 追加**: デバッグログポイント（`rawMessages` の件数、`isInstance` フィルタリング前後の件数差）

**レスポンス:**
```json
{
  "messages": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

### `server/api/threads.get.ts`（15行）

- `GET /api/threads` スレッド一覧取得（更新日時降順）

### `server/api/threads/[id]/settings.get.ts`（8行）— ver15.0 新規

- `GET /api/threads/:id/settings` スレッド設定取得
- `getThreadSettings(id)` を呼び出して返却

### `server/api/threads/[id]/settings.put.ts`（16行）— ver15.0 新規

- `PUT /api/threads/:id/settings` スレッド設定更新
- バリデーション: `granularity` は `'concise' | 'standard' | 'detailed'` のみ許可
- `customInstruction` は 500 文字上限（過度に長い入力を防止）

## エージェント・プロンプト

### `server/utils/analogy-agent.ts`（188行）

LangGraph `StateGraph` によるマルチノード構成のアナロジー思考ワークフロー。

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
| `completed` | 解決策提示済み | followUp |

#### グラフ構造

```
START ──→ [routeByStep: conditional edge]
              ├── "initial"           → abstraction → caseSearch → END
              ├── "awaiting_selection" → solution → END
              └── "completed"         → followUp → END
```

#### ノード関数

- `abstractionNode(state)` — ユーザーの具体的課題を抽象概念に変換。`abstractedProblem` に格納。粒度設定は適用しない（常に簡潔に抽象化）
- `caseSearchNode(state, config)` — `performSearch()` で Tavily Web検索を実行し、抽象化結果とともに LLM に類似事例の提示を依頼。**ver15.0**: `config.configurable?.settings` から設定を読み取り `buildSystemPrompt()` で動的プロンプト構築
- `solutionNode(state, config)` — ユーザー選択事例に基づく解決策生成。**ver15.0**: 設定に基づく動的プロンプト構築
- `followUpNode(state, config)` — 解決策提示後の追加質問に応答。**ver15.0**: 設定に基づく動的プロンプト構築

#### Tavily Search 呼び出し（`performSearch` 関数）

- ノードロジック内で直接呼び出し（ツールとしてではない）
- `config.tavilyApiKey` が truthy の場合のみ実行、未設定時は空文字列を返す
- `maxResults: 3`、エラー時はサイレントに空文字列を返す

#### シングルトン

- `getAnalogyAgent()`: `CompiledStateGraph` をシングルトンで保持
- `SqliteSaver.fromConnString()` でチェックポインターを初期化（DB パスは `db-config.ts` から取得）

### `server/utils/analogy-prompt.ts`（82行）

ノード別の4プロンプト定数 + 動的プロンプト構築ヘルパー。

| 定数名 | 用途 |
|---|---|
| `ABSTRACTION_PROMPT` | 課題の抽象化（固有名詞・分野を除去、1〜2文で簡潔に） |
| `CASE_SEARCH_PROMPT` | 類似事例の提示（3〜5個、7カテゴリ例示付き、Web検索結果を優先）（ver14.1 で体系的カテゴリ例示に改修） |
| `SOLUTION_PROMPT` | 解決策の提案（原理説明 + 適用方法 + 実現可能性） |
| `FOLLOWUP_PROMPT` | フォローアップ対応 |

**ver15.0 追加**: `buildSystemPrompt(basePrompt, settings?)` ヘルパー関数

- `GRANULARITY_INSTRUCTIONS` マップで粒度別の追加指示を定義（`concise`: 箇条書き、`detailed`: 具体例・背景説明）
- `standard` はエントリなし → ベースプロンプトのまま
- `customInstruction` があれば `## 追加指示` セクションとして末尾に付加

## ストレージ

### `server/utils/thread-store.ts`（96行）

`better-sqlite3` を直接インポートしてスレッドメタデータと設定を CRUD 操作。

- シングルトンパターンで DB 接続を管理（`getDb()`）、WAL モード
- `getThreads()`, `upsertThread()`, `updateThreadTitle()`, `getThreadTitle()`
- **ver15.0 追加**: `getThreadSettings(threadId)`, `updateThreadSettings(threadId, settings)`
- **ver15.0 追加**: `ThreadSettings` インターフェース、`DEFAULT_SETTINGS` 定数をエクスポート
- DB スキーマ: `ALTER TABLE threads ADD COLUMN settings TEXT NOT NULL DEFAULT '{}'`（`getDb()` 内で安全に実行）

#### ThreadSettings 型定義

```typescript
export interface ThreadSettings {
  granularity: 'concise' | 'standard' | 'detailed'
  customInstruction: string
}

export const DEFAULT_SETTINGS: ThreadSettings = {
  granularity: 'standard',
  customInstruction: '',
}
```

### `server/utils/db-config.ts`（11行）

- DB パスを一元管理（開発: `./data/`、本番: `/home/data/`）
- `getDbPath(filename)` 関数をエクスポート

### `server/utils/logger.ts`（50行）

- モジュール別プレフィックス付きロガーユーティリティ
- **ver14.4 追加**: ファイル出力機能（開発環境限定、`logs/app-YYYY-MM-DD.log`、JSON Lines 形式、`appendFileSync`）
- シグネチャ: `(msg: string, ctx?: Record<string, unknown>)`
- 4モジュール: `logger.agent`, `logger.chat`, `logger.thread`, `logger.history`

## データベーススキーマ

### threads テーブル

```sql
CREATE TABLE IF NOT EXISTS threads (
  thread_id TEXT PRIMARY KEY,
  title TEXT NOT NULL DEFAULT '新しいチャット',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
)
-- ver15.0 で追加
ALTER TABLE threads ADD COLUMN settings TEXT NOT NULL DEFAULT '{}'
```

- LangGraph チェックポインター（`langgraph-checkpoints.db`）と同一 DB ファイルに格納
- WAL モードで並行読み取り対応

### LangGraph チェックポイントステート

| フィールド | 型 | 用途 |
|---|---|---|
| `messages` | `BaseMessage[]` | 会話メッセージ履歴 |
| `currentStep` | `string` | 対話フローの現在ステップ |
| `abstractedProblem` | `string` | 抽象化された課題テキスト |

## その他

### `experiments/inspect-db.ts`（ver14.4 追加）

SQLite データベースの内容を直接確認できる CLI ツール。

```bash
npx tsx experiments/inspect-db.ts threads                # スレッド一覧
npx tsx experiments/inspect-db.ts history <threadId>      # メッセージ履歴
npx tsx experiments/inspect-db.ts checkpoints <threadId>  # チェックポイント一覧
```

### `experiments/_shared.ts`, `01-basic-connection.ts`, `02-memory-management.ts`

実験スクリプト（LangChain/OpenAI の基本接続・メモリ管理テスト用）。

## 技術的な決定事項

### 継続中の決定事項

- **ストリーミング方式**: h3 `createEventStream` + LangGraph `graph.stream()` による SSE（`streamMode: "messages"`）
- **SSE パーサーの分離**: `parseSSEStream()` を `app/utils/sse-parser.ts` に切り出し
- **composable 設計**: `useChat()`（メッセージ・通信）と `useThreads()`（スレッド一覧・アクティブ管理）で責務分離
- **AbortController による応答中断**
- **リアクティビティ戦略**: 空の assistant メッセージオブジェクトを先に追加し、同一参照の `.content` を更新
- **会話メモリの永続化**: LangGraph チェックポイント機構により SQLite に自動保存
- **Markdown レンダリング**: `marked` + `DOMPurify`、`import.meta.client` ガード
- **h3 明示的インポート**: auto-import 非依存（Vitest モック設定を簡潔に）
- **テスト環境**: Vitest `environment: 'node'`
- **ネイティブモジュール除外**: `nitro.externals.external: ['better-sqlite3']`
- **楽観的 UI 更新**: `createNewThread()` でサーバー通信なしに即座にスレッドをリストに追加
- **タイトル自動生成**: `generateTitle()` で gpt-4.1-mini を使い10文字以内の日本語タイトルを非同期生成
- **better-sqlite3 の直接依存**: pnpm の厳密な依存解決による
- **thread-store のシングルトン DB**: LangGraph チェックポインターと同一 DB ファイルを共有
- **CJS モジュールテスト**: `createRequire(import.meta.url)` で vitest のモック解決を回避
- **composable テストの importFresh**: モジュールスコープ状態をテスト間で分離
- **Router パターン**: 各 API 呼び出しが `graph.stream(input, config)` で統一
- **ノード別プロンプト分割**: 単一プロンプトを4つの専用プロンプトに分割
- **Tavily Search のノード内直接呼び出し**: ツールとしてではなくノードロジック内で呼び出し
- **ストリーミングフィルタのホワイトリスト方式**: `metadata?.langgraph_node` に基づくフィルタリング
- **`useRuntimeConfig()` のキャッシュ**: ノード関数がリクエストコンテキスト外で実行される可能性への対処
- **DB パスの一元管理**: `db-config.ts` で開発/本番パスを切り替え（ver14.3 infra 対応で追加）
- **履歴の type プロパティベース判定**: `@langchain/core/messages` への依存を排除（ver14.5）
- **永続ログのファイル出力**: 開発環境限定、`appendFileSync` による同期書き込み（ver14.4）

### ver15.0 で追加

- **動的設定システム**: スレッドごとに `ThreadSettings`（粒度プリセット + カスタム指示）を DB に保存し、`configurable.settings` 経由で LangGraph ノード関数に渡す
- **`buildSystemPrompt()` ヘルパー**: ベースプロンプトに粒度指示・カスタム指示を付加する関数。`abstraction` ノードには適用しない（常に簡潔に抽象化）
- **`ALTER TABLE ADD COLUMN` によるスキーマ拡張**: SQLite は `ADD COLUMN IF NOT EXISTS` をサポートしないため、`try/catch` でカラム既存時のエラーを無視
- **設定 API の分離**: `GET/PUT /api/threads/:id/settings` として独立エンドポイントを設置（スレッド CRUD とは別）
- **`useSettings` composable**: フロントエンドでのスレッド設定状態管理。スレッド切り替え時に `loadSettings()` で設定をリセット

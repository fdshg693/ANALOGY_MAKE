# バックエンド現況（ver16.0）

## API エンドポイント

### `server/api/chat.post.ts`（134行）

- `POST /api/chat` SSE ストリーミングエンドポイント
- ストリーミングフィルタ: `STREAMED_NODES = new Set(["caseSearch", "solution", "followUp"])`
- **ver16.0 追加**: token ストリームループ完了後に `agent.getState()` でスナップショット取得し、最終 AIMessage の `additional_kwargs.searchResults` を読み出す。取得できた場合は `search_results` SSE イベントを 1 回配信してから `done` を送信。スナップショット取得失敗時は `warn` ログのみでスキップ（`done` は必ず送信）

**リクエスト:**
```json
{ "message": "string", "threadId": "string" }
```

**レスポンス:** SSE ストリーム（`Content-Type: text/event-stream`）

| event | data | 説明 |
|---|---|---|
| `token` | `{"content": "..."}` | トークン1つ分のテキスト |
| `search_results` | `{"results": [{title, url, content}...]}` | Tavily 検索結果（検索結果ありの場合のみ、`done` 直前に 1 回） |
| `done` | `{}` | ストリーミング正常完了 |
| `error` | `{"message": "..."}` | エラー発生（`search_results` は送られない） |

### `server/api/chat/history.get.ts`（97行）

- `GET /api/chat/history?threadId=xxx` 会話履歴取得エンドポイント
- **ver16.0 変更**: `CheckpointMessage` インターフェースに `additional_kwargs?: Record<string, unknown>` を追加。AI メッセージの map で `extractSearchResults()` ヘルパーを呼び出し、有効な searchResults が存在すれば `{ ...base, searchResults }` を返す
- `extractSearchResults()`: `additional_kwargs.searchResults` の配列要素を型ガード（title/url/content の string 検証）でフィルタリング。後方互換として不正形式は無視
- 旧スレッド（ver15.x 以前）の AI メッセージには `additional_kwargs.searchResults` がないため、`searchResults` フィールドなしで返る

**レスポンス:**
```json
{
  "messages": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "...", "searchResults": [{...}] }
  ]
}
```
※ `searchResults` は検索結果がある AI メッセージのみ付与

### `server/api/threads.get.ts`（15行）

- `GET /api/threads` スレッド一覧取得（更新日時降順）

### `server/api/threads/[id]/settings.get.ts`（8行）

- `GET /api/threads/:id/settings` スレッド設定取得

### `server/api/threads/[id]/settings.put.ts`（16行）

- `PUT /api/threads/:id/settings` スレッド設定更新
- バリデーション: `granularity`（`'concise' | 'standard' | 'detailed'`）、`customInstruction`（500文字上限）
- search 設定: `enabled`（boolean）、`depth`（`'basic' | 'advanced'`）、`maxResults`（1〜10整数）

## エージェント・プロンプト

### `server/utils/analogy-agent.ts`（227行）

LangGraph `StateGraph` によるマルチノード構成のアナロジー思考ワークフロー。

#### `SearchResult` 型（ver16.0 新規エクスポート）

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
| `completed` | 解決策提示済み | followUp |

#### グラフ構造

```
START ──→ [routeByStep: conditional edge]
              ├── "initial"            → abstraction → caseSearch → END
              ├── "awaiting_selection" → solution → END
              └── "completed"          → followUp → END
```

#### `performSearch` 関数（ver16.0 変更）

```typescript
// ver15.1: Promise<string>
// ver16.0: Promise<SearchResult[]>
async function performSearch(query: string, search: SearchSettings): Promise<SearchResult[]>
```

- `search.enabled === false` / APIキー未設定 / エラー時は空配列 `[]` を返す
- 成功時: `tavily.invoke({ query })` の戻り値から `results.results` を `{ title, url, content }` にマップ
- `"error" in results` で失敗を弁別、失敗時は空配列。`try/catch` で例外も空配列にフォールバック

#### `caseSearchNode`（ver16.0 変更）

- `performSearch()` から `SearchResult[]` を受け取り、LLM への入力は番号付きリスト形式に整形（既存の JSON.stringify から変更）
- 検索結果が 1 件以上の場合、`result.additional_kwargs.searchResults = searchResults` を設定
- 検索結果なし（空配列）の場合は `additional_kwargs` に付加しない

### `server/utils/analogy-prompt.ts`（82行）

ver16.0 で変更なし。`buildSystemPrompt(basePrompt, settings?)` ヘルパー、4プロンプト定数を提供。

## ストレージ

### `server/utils/thread-store.ts`（96行）

ver16.0 で変更なし。`ThreadSettings`（`granularity`, `customInstruction`, `search`）と `SearchSettings` の型定義を提供。

### `server/utils/db-config.ts`（11行）

変更なし。DB パスを一元管理（開発: `./data/`、本番: `/home/data/`）。

### `server/utils/logger.ts`（50行）

変更なし。

## データベーススキーマ

### threads テーブル

ver16.0 で変更なし。`settings TEXT NOT NULL DEFAULT '{}'` カラムを含む。

### LangGraph チェックポイントステート

| フィールド | 型 | 用途 |
|---|---|---|
| `messages` | `BaseMessage[]` | 会話メッセージ履歴（AIMessage の `additional_kwargs.searchResults` に検索結果を添付） |
| `currentStep` | `string` | 対話フローの現在ステップ |
| `abstractedProblem` | `string` | 抽象化された課題テキスト |

## 技術的な決定事項（ver16.0 追加）

- **`performSearch` 戻り値の構造化**: 従来の文字列返却から `SearchResult[]` に変更。LLM への入力は番号付きリスト文字列に整形して既存挙動を維持しつつ、フロントエンドへの配信用に構造を保持
- **`additional_kwargs` への検索結果添付**: LangGraph の SQLite チェックポインターが `additional_kwargs` を JSON シリアライズで保持するため、別フィールドを用意せず既存の拡張ポイントを活用。空配列のときは添付しない（「検索なし」と「検索したが結果なし」の区別は現状不要）
- **`search_results` SSE イベントのタイミング**: token ストリーム完了後・`done` 直前に 1 回配信。UI は「本文 → 参考検索結果」の自然な順序で受け取る
- **スナップショット読み取りの例外分離**: `agent.getState()` の失敗はチャット本体に影響しないよう `try/catch` で囲む
- **型重複定義の継続**: `SearchResult` 型はサーバー側（`analogy-agent.ts`）とフロント側（`useChat.ts`、`history.get.ts`）で独立定義。ver15.1 の `ThreadSettings` と同じ流儀（`shared/` への統一は将来バージョンで対応）

## 未解決の課題（ISSUES）

- **`getState-timing.md`（medium）**: ストリーム完了直後のスナップショットに最新 AIMessage が含まれるか、LangGraph 実機で未検証。問題発生時は `streamMode: ["messages", "updates"]` の dual モードでフォールバック
- **`additional-kwargs-sqlite.md`（medium）**: `AIMessage.additional_kwargs` の任意オブジェクトが SQLite に正しく保存・復元されるか未検証。問題発生時は `AnalogyState` に `searchResults` フィールドを追加して state 経由で永続化

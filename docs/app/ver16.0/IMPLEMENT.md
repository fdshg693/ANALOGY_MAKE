# ver16.0 IMPLEMENT

## 実装方針サマリー

Tavily 検索結果（構造化済み）を、`caseSearchNode` 実行中に取得してその AI メッセージの `additional_kwargs.searchResults` に添付する。LangGraph のチェックポイント機構が `additional_kwargs` をそのまま永続化するため、履歴復元も自動的に機能する。SSE ストリーミングでは、token ストリーム完了後に最終スナップショットから検索結果を読み出し、新設する `search_results` イベントで 1 回だけ配信する。フロントエンドは `Message.searchResults` を保持し、専用の折りたたみコンポーネントでレンダリングする。

```
[caseSearchNode]
  performSearch() → SearchResult[] 構造化
     ↓
  LLM invoke（stringify して system prompt に埋め込み、既存挙動維持）
     ↓
  result.additional_kwargs.searchResults = results
  return { messages: [result], ... }
     ↓
[SQLite チェックポイント] ← 永続化（additional_kwargs ごと）
     ↓
[chat.post.ts]
  token ストリーム → 既存どおり逐次配信
  ループ完了後: 最新メッセージの additional_kwargs.searchResults を snapshot から取得
  → SSE event: 'search_results' 1 回配信
  → event: 'done'
     ↓
[フロントエンド useChat]
  onSearchResults → assistantMessage.searchResults = results
     ↓
[UI]
  ChatMessage の下に SearchResultsList（<details> 折りたたみ）
```

## データ型の定義

### 共通型（`server/utils/search-result.ts` を新規作成）

フロントとバックの両方で import できる位置に配置。Nuxt 4 の server ディレクトリ配下は `.vue` からは import できないため、共有型は別の場所に置く必要がある。

**選択肢 A**: `shared/types/search.ts` に配置して双方から import（Nuxt 4 の `shared/` ディレクトリは実際に使用可能で、型の唯一定義という観点では保守性が高い）
**選択肢 B**: サーバ側とフロント側で独立して `SearchResult` 型を定義（ver15.1 の `ThreadSettings` と同じ流儀）

→ **採用: 選択肢 B**。`shared/` も実際には使用可能だが、ver15.0〜15.1 で `ThreadSettings` を重複定義している既存流儀と統一するため今回も重複で進める。型の一元化（選択肢 A への統合）は将来の別バージョンでまとめて対応する（現時点で本バージョンだけ先行して流儀を変えると、統一性が崩れる）。サーバ側は `server/utils/analogy-agent.ts` 内で定義し export、フロント側は `app/composables/useChat.ts` 内で定義する。

```typescript
export interface SearchResult {
  title: string
  url: string
  content: string   // Tavily の snippet 相当
}
```

`score` や `raw_content` は初期スコープでは UI に出さないため保存しない（容量削減・将来必要なら拡張）。

## バックエンド変更

### `server/utils/analogy-agent.ts`

**変更1: `SearchResult` 型を export**

既存の `SearchSettings` import の隣に追加。

**変更2: `performSearch` のシグネチャ変更**

```typescript
// 現状
async function performSearch(query: string, search: SearchSettings): Promise<string>

// 変更後
async function performSearch(
  query: string,
  search: SearchSettings
): Promise<SearchResult[]>
```

- `search.enabled === false` / API キー未設定 / エラー時は空配列 `[]` を返す
- 成功時: `tavily.invoke({ query })` の戻り値の型は `TavilySearchResponse | { error: string }`（ユニオン）。`"error" in results` で失敗を弁別し、失敗時は空配列。成功時は `results.results` を `.map(r => ({ title: r.title, url: r.url, content: r.content }))` に整形

**変更3: `caseSearchNode` の書き換え**

```typescript
async function caseSearchNode(state, config) {
  const settings = config?.configurable?.settings as ThreadSettings | undefined
  const search = settings?.search ?? DEFAULT_SEARCH_SETTINGS
  const searchResults = await performSearch(state.abstractedProblem, search)

  // LLM への入力は既存挙動を維持するため、ここで string 化
  const searchResultsText = searchResults.length
    ? searchResults
        .map((r, i) => `[${i + 1}] ${r.title}\n${r.url}\n${r.content}`)
        .join("\n\n")
    : "(検索結果なし)"

  const contextMessage = [
    `[内部コンテキスト]`,
    `抽象化された課題: ${state.abstractedProblem}`,
    ``,
    `Web検索結果:`,
    searchResultsText,
  ].join("\n")

  const fullSystemPrompt = buildSystemPrompt(
    `${CASE_SEARCH_PROMPT}\n\n${contextMessage}`,
    settings
  )

  const result = await model.invoke([
    { role: "system", content: fullSystemPrompt },
    ...state.messages,
  ])

  // additional_kwargs に添付（空配列でも明示的に付けておくことで「検索は走ったが結果なし」と「そもそも検索していない」を区別する必要がある場合に備える）
  // → ただし空配列のときはフロントで UI を出さないだけで良いので、空配列でも添付して問題なし
  if (searchResults.length > 0) {
    result.additional_kwargs = {
      ...result.additional_kwargs,
      searchResults,
    }
  }

  return {
    messages: [result],
    currentStep: "awaiting_selection",
  }
}
```

**プロンプト文脈の整合性**: 従来は `tavily.invoke` の戻り値を丸ごと `JSON.stringify` していた。今回は構造化して人間が読みやすい形式にフォーマット（番号付きリスト）。LLM が参照するコンテキストの質的変化はあるが、同等以上の情報量であり、事例生成の品質低下リスクは低い。既存の `case-search-prompt` テストがあれば回帰確認、なければ実装時にサンプル実行で確認する。

### `server/api/chat.post.ts`

**変更: ストリームループ完了後に `search_results` SSE を配信**

```typescript
// 既存の for await ループ終了後、'done' を push する前に追加
const finalSnapshot = await agent.getState({
  configurable: { thread_id: body.threadId },
})
const finalMessages = finalSnapshot?.values?.messages
const lastMessage = Array.isArray(finalMessages)
  ? finalMessages[finalMessages.length - 1]
  : undefined
const searchResults = (lastMessage as any)?.additional_kwargs?.searchResults
if (Array.isArray(searchResults) && searchResults.length > 0) {
  await eventStream.push({
    event: 'search_results',
    data: JSON.stringify({ results: searchResults }),
  })
}
// その後 'done' を push（既存）
```

**配置理由**: token ストリームが完了してから配信することで、UI は「AI メッセージ本文 → 参考検索結果」という論理的に自然な順序で受け取る。検索結果は text のように逐次送る必要がなく、一括送信が妥当。

**エラー時挙動**: ストリームエラーパス（catch 節）では `search_results` を送らず `error` のみ送る。スナップショット取得自体は失敗してもロジック本体に影響を与えないよう、snapshot 取得を try/catch で囲み、失敗時は無視してログのみ残す。

### `server/api/chat/history.get.ts`

**変更: AI メッセージの `additional_kwargs.searchResults` を戻り値に含める**

```typescript
// 既存: CheckpointMessage の拡張
interface CheckpointMessage {
  type: string
  content: unknown
  additional_kwargs?: Record<string, unknown>  // 追加
}

// map 部分を拡張
const messages = rawMessages
  .filter(isChatMessage)
  .map((msg) => {
    const base = {
      role: msg.type === 'human' ? 'user' as const : 'assistant' as const,
      content: typeof msg.content === 'string' ? msg.content : '',
    }
    if (msg.type === 'ai') {
      const raw = (msg.additional_kwargs as any)?.searchResults
      if (Array.isArray(raw) && raw.length > 0) {
        // 型確認の上で拾う（後方互換: 形が違う場合は無視）
        const results = raw
          .filter(
            (r: any): r is { title: string; url: string; content: string } =>
              typeof r?.title === 'string' &&
              typeof r?.url === 'string' &&
              typeof r?.content === 'string'
          )
          .map((r) => ({ title: r.title, url: r.url, content: r.content }))
        if (results.length > 0) {
          return { ...base, searchResults: results }
        }
      }
    }
    return base
  })
```

**後方互換**: ver15.x 以前に作成された AI メッセージには `additional_kwargs.searchResults` がないため、単に省略される（ROUGH_PLAN の「含まないもの: 古いスレッドへの遡及的な補完」と整合）。

## フロントエンド変更

### `app/utils/sse-parser.ts`

**変更: `SSECallbacks` に `onSearchResults` を追加、event dispatch 追加**

```typescript
export interface SSECallbacks {
  onToken: (content: string) => void
  onDone: () => void
  onError: (message: string) => void
  onSearchResults?: (results: SearchResult[]) => void  // 追加・オプショナル
}
```

`onSearchResults` はオプショナルにする（既存のテストコードが落ちない・必要最小限の変更）。

dispatch 部分:

```typescript
if (eventType === 'search_results' && data) {
  const parsed = JSON.parse(data)
  if (callbacks.onSearchResults && Array.isArray(parsed.results)) {
    callbacks.onSearchResults(parsed.results)
  }
}
```

**`SearchResult` 型の置き場所**: ここでは依存を避けるため、parser は `unknown[]` で受け、呼び出し側（useChat）で型付けする。→ 以下のように単純化:

```typescript
if (eventType === 'search_results' && data) {
  const parsed = JSON.parse(data)
  callbacks.onSearchResults?.(parsed.results ?? [])
}
```

`SSECallbacks.onSearchResults` のシグネチャは `(results: unknown[]) => void` にする。型検証は上位で行う。

**重要な配置ルール**: 現行の `parseSSEStream` は `done` イベントを受けた時点で即座に `return` してループを抜ける（既存 40〜44 行目）。したがって `search_results` の dispatch ブロックは必ず `done` 処理の **前** に配置すること（もしくは `done` の `return` より前で分岐させること）。順序を誤るとイベントがサイレントに欠落する。サーバ側は `search_results` を `done` より前に push する前提だが、パーサ側でも防御的に順序を守る。

### `app/composables/useChat.ts`

**変更1: `SearchResult` 型と `Message.searchResults` を追加**

```typescript
export interface SearchResult {
  title: string
  url: string
  content: string
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
  isError?: boolean
  searchResults?: SearchResult[]  // 追加
}
```

**変更2: `sendMessage` で `onSearchResults` コールバックを渡す**

```typescript
await parseSSEStream(response.body, {
  onToken(content) { /* 既存 */ },
  onDone() {},
  onError(message) { /* 既存 */ },
  onSearchResults(results) {
    // unknown[] → SearchResult[] の型ガード
    const validated = results
      .filter((r: any): r is SearchResult =>
        r &&
        typeof r.title === 'string' &&
        typeof r.url === 'string' &&
        typeof r.content === 'string'
      )
    if (validated.length > 0) {
      assistantMessage.searchResults = validated
    }
  },
})
```

**変更3: `loadHistory` の型乗り**

`fetch('/api/chat/history')` の戻り値に `searchResults` が含まれるようになる。`messages.value = data.messages` の代入は、JSON.parse の戻り値が `any` 相当であるため実行時は通るが、TypeScript の strict モードで厳密な型推論が入った場合に `unknown` 経由のエラーが出る可能性がある。

**実装時の確認手順**:
1. まず既存通り `messages.value = data.messages` のままで `npx nuxi typecheck` を実行
2. 型エラーが出た場合は `messages.value = data.messages as Message[]` にキャスト
3. 余力があれば `parseHistoryResponse(data)` 風の型ガード関数で安全化（必須ではない。API 側で既に型ガード済みなので実質リスクはない）

API レスポンスの形式自体（role/content/searchResults の3フィールド）は Message 型と完全に互換。

### `app/components/SearchResultsList.vue`（新規）

```vue
<script setup lang="ts">
import type { SearchResult } from '~/composables/useChat'

defineProps<{ results: SearchResult[] }>()

function getDomain(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}
</script>

<template>
  <details class="search-results">
    <summary>参考にした Web 検索結果 ({{ results.length }} 件)</summary>
    <ul>
      <li v-for="(r, i) in results" :key="i">
        <a :href="r.url" target="_blank" rel="noopener noreferrer">{{ r.title }}</a>
        <span class="domain">{{ getDomain(r.url) }}</span>
        <p class="snippet">{{ r.content }}</p>
      </li>
    </ul>
  </details>
</template>

<style scoped>
.search-results {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 0.875rem;
}
.search-results summary {
  cursor: pointer;
  font-weight: 500;
  color: #4b5563;
}
.search-results ul {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0 0 0;
}
.search-results li {
  padding: 0.5rem 0;
  border-bottom: 1px solid #e5e7eb;
}
.search-results li:last-child { border-bottom: none; }
.search-results a {
  color: #2563eb;
  text-decoration: none;
  font-weight: 500;
}
.search-results a:hover { text-decoration: underline; }
.search-results .domain {
  color: #6b7280;
  font-size: 0.75rem;
  margin-left: 0.5rem;
}
.search-results .snippet {
  color: #4b5563;
  margin: 0.25rem 0 0 0;
  line-height: 1.4;
}
</style>
```

デフォルトで閉じた `<details>`。エスケープは Vue が自動で行う（テンプレート補間）。`rel="noopener noreferrer"` で外部リンクのセキュリティを担保。

### `app/pages/index.vue`

**変更: メッセージループで SearchResultsList を出す**

既存の `ChatMessage` レンダリング箇所（未読取だが ver15.0 現況から推定）に、assistant メッセージかつ `searchResults` がある場合に追加表示。実装時に `pages/index.vue` の現状のループを確認してから挿入位置を決める。

```vue
<template v-for="(msg, i) in messages" :key="i">
  <ChatMessage ... />
  <SearchResultsList
    v-if="msg.role === 'assistant' && msg.searchResults?.length"
    :results="msg.searchResults"
  />
</template>
```

### 「検索中…」フィードバック

ROUGH_PLAN レビューで指摘された通り、これは実装者判断。**初期リリースでは含めない**（ストリーム開始までの待ち時間は既存の isLoading スピナーでカバー済み、追加 UI は過剰）。必要性は実機確認で判断。

## テスト計画

### 新規: `tests/server/search-results.test.ts`

1. `performSearch` が `search.enabled === false` で空配列を返す
2. `performSearch` が API キー未設定で空配列を返す
3. `caseSearchNode` が結果を AI メッセージの `additional_kwargs.searchResults` に添付する（モック Tavily で）
4. `caseSearchNode` が空配列のとき `additional_kwargs.searchResults` を設定しない

**モック戦略**: `@langchain/tavily` の `TavilySearch` クラスを `vi.mock` でモックし、`invoke()` の戻り値をテストごとに差し替える。既存の `chat.test.ts` が ChatOpenAI をモックする流儀を踏襲。

※ ver15.1 MEMO で「perform-search.test.ts はモック設計 ROI が低い」と判断し省略した経緯あり。ver16.0 ではノードの戻り値構造自体の検証が必要になるため、最低限のテストは入れる（Tavily のモックは限定的でも、additional_kwargs への添付・空配列時の分岐は確認価値が高い）。

### 拡張: `tests/server/chat.test.ts`

- `POST /api/chat` のレスポンスに `search_results` SSE イベントが含まれるケース（検索結果ありのとき）
- `search_results` イベントが含まれないケース（検索結果が空のとき）
- エラーパスで `search_results` が送られないこと

既存の chat.test.ts が SSE をどうモックしているかは実装時に確認。最悪、新規の `search-results.test.ts` に統合してもよい。

### 拡張: `tests/server/history-api.test.ts` （存在すれば）

- AI メッセージに `additional_kwargs.searchResults` があるとき、レスポンスの `messages[i].searchResults` に展開される
- 形式が不正な searchResults はフィルタアウトされる（後方互換）
- 古い形式（additional_kwargs 自体がない）は `searchResults` フィールドなしで返る

既存テストの有無は実装時に確認。なければ本バージョンで新設。

### 既存テストの型追従

- `tests/server/chat.test.ts` などで `Message` 型や `BaseMessage` のモック戻り値を使う箇所があれば、`additional_kwargs` の存在を前提にしたアサーション更新

## リスク・不確実性

### 1. `agent.getState()` の挙動（中）

ストリーム完了直後に `getState()` を呼んで、直近のチェックポイント（message 追加直後）が取れるかは要確認。LangGraph の `SqliteSaver` は各ステップ後に同期的に書き込まれる想定だが、`graph.stream()` の消費完了とチェックポイント書き込みの同期性は実装時に実機で検証する。

**検証方法**: 実装後に手動でリクエストを飛ばし、`getState()` の `values.messages` の最後のメッセージが、今ストリームで返した AIMessage であり、`additional_kwargs.searchResults` を持つことを確認する。

**フォールバック**: もし getState でタイミング的に取れない場合、caseSearchNode 内でグローバル一時変数・イベントエミッタで chat.post.ts に直接渡す方法は避け、`streamMode: ["messages", "updates"]` の dual モードで updates ストリームから拾う方法に切り替える（これは公式サポートされている）。

### 2. LangChain `AIMessage` の `additional_kwargs` シリアライズ（中）

LangGraph の SQLite チェックポインターが `AIMessage.additional_kwargs` の任意オブジェクトを保持・復元できるかは、`@langchain/langgraph-checkpoint-sqlite` の内部実装に依存。標準的な JSON シリアライズが行われていれば問題ないが、instanceof ベースのデシリアライズを噛ませている場合、カスタム項目が落ちる可能性がある。

**検証方法**: 実装後、スレッドをまたいで history を読んだとき `searchResults` が残っているかを手動検証。または `experiments/inspect-db.ts checkpoints <threadId>` で直接 DB を覗く。

**フォールバック**: もし `additional_kwargs` が落ちるなら、`AnalogyState` に `searchResults: Annotation<SearchResult[]>` を追加して state 経由で永続化。履歴復元時は snapshot.values.searchResults を読み、`caseSearch` が一度しか走らない前提で、最初の assistant メッセージに紐付ける（現在のフローではこれで十分）。

### 3. Tavily `invoke()` 戻り値の型判別（低）

型定義上は `TavilySearchResponse | { error: string }` のユニオン。実行時に `"error" in results` で弁別できるが、Tavily の実際の失敗時挙動（例外スローかエラーオブジェクト返却か）がドキュメント不足。

**検証方法**: `invalid` API キーで意図的に呼び出し、戻り値 vs 例外を観察。実装時に `try/catch` を外側に付けているので（既存コードそのまま）、少なくとも例外パスはカバーされる。

### 4. SSE `search_results` イベントの UI 描画タイミング（低）

streaming 完了 → `done` 直前に `search_results` を送るため、ユーザー視点では「本文が表示された直後に折りたたみセクションが現れる」という視覚変化になる。スムーズに見えない場合（唐突感）は、折りたたみの登場を少しフェードさせるなど UI 微調整。ただしこれは初期リリースで必須ではなく、実機確認後に判断。

### 5. `search_results` イベントのバッファリング（低）

h3 の `createEventStream.push()` が同期的にフラッシュするか、バッファリングされるかは未確認。token と search_results が時間的に近接していても、順序は保証されるはず（同一コネクション・シリアライズ）。順序逆転リスクは理論上ないが実機確認の対象。

## 実装順序（推奨）

1. `performSearch` の戻り値を構造化（型変更 + 整形）、`caseSearchNode` で `additional_kwargs` 添付。単体で動作確認
2. `chat.post.ts` に `search_results` SSE 配信追加。`curl` で SSE 応答を眺めて確認
3. `history.get.ts` で `searchResults` 展開。`/api/chat/history?threadId=...` を直接叩いて確認
4. `sse-parser.ts` に `onSearchResults` 追加
5. `useChat.ts` に `Message.searchResults` + 型ガード
6. `SearchResultsList.vue` 新規作成
7. `pages/index.vue` でレンダリング挿入
8. テスト追加
9. 実機確認（推奨）

1〜3 の各ステップでバックエンド単体の動作確認ができる構造にすることで、フロント着手前にリスク 1・2（getState タイミング、シリアライズ）を検証できる。リスクが顕在化した場合は「フォールバック」パスに切り替える。

## 既存 CLAUDE.md への影響

新規に記載すべき開発者向け注意点は特になし（既存アーキテクチャの自然な拡張）。`SearchResult` 型の重複定義（サーバ/フロント）が気になるなら「やらないこと」の近くに注記する選択肢もあるが、ver15.1 で `ThreadSettings` の型重複を容認した前例があるため、今回も追記不要。

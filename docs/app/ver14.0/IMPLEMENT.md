# ver14.0 実装計画: LangGraphステートマシンによるフロー制御

## 概要

現在の `createReactAgent`（単一エージェント + 単一プロンプト）を、`StateGraph` によるマルチノード構成に置き換える。

### ROUGH_PLAN からの設計変更: Router パターンの採用

ROUGH_PLAN では `interrupt` 機構による中断・再開を想定したが、実装計画の詳細検討により **Router パターン**を採用する。

**理由**:
- `interrupt()` はノード内で呼ばれると、再開時にノード関数を最初から再実行する。つまり `interrupt()` 前の LLM 呼び出しが2回実行されてしまう（コスト・結果の不一致リスク）
- `interruptAfter` はグラフレベルの中断だが、再開には `updateState` + `stream(null)` という異なるAPIフローが必要で、`chat.post.ts` の分岐が増える
- Router パターンでは各 API 呼び出しが `graph.stream(input, config)` で統一され、実装がシンプル

**Router パターンの動作**:
1. 各 `POST /api/chat` 呼び出しで `graph.stream()` を実行
2. グラフは `START` から始まり、永続化された `currentStep` に基づいて条件分岐
3. 該当するノードを実行して `END` に到達
4. `currentStep` を更新して次回の呼び出しに備える

ユーザー体験は ROUGH_PLAN と同じ（5ステップの対話フロー維持、UIに変更なし）。

---

## 1. ステート定義

### ファイル: `server/utils/analogy-agent.ts`

```typescript
import { Annotation, messagesStateReducer } from "@langchain/langgraph"
import { BaseMessage } from "@langchain/core/messages"

const AnalogyState = Annotation.Root({
  // 会話メッセージ履歴（LangGraph 組み込みの reducer で自動追記）
  messages: Annotation<BaseMessage[]>({
    reducer: messagesStateReducer,
    default: () => [],
  }),
  // 対話フローの現在ステップ
  currentStep: Annotation<string>({
    reducer: (_prev, next) => next,
    default: () => "initial",
  }),
  // 抽象化された課題（abstractionNode → caseSearchNode へのデータ受け渡し）
  abstractedProblem: Annotation<string>({
    reducer: (_prev, next) => next,
    default: () => "",
  }),
})
```

### ステップ遷移

| currentStep | 意味 | 次に実行されるノード |
|---|---|---|
| `initial` | 新規スレッド、課題未入力 | abstraction → caseSearch |
| `awaiting_selection` | 事例提示済み、ユーザー選択待ち | solution |
| `completed` | 解決策提示済み | followUp |

---

## 2. グラフ構造

### ファイル: `server/utils/analogy-agent.ts`

```
START ──→ [routeByStep: conditional edge]
              │
              ├── currentStep === "initial"
              │       ↓
              │   abstraction ──→ caseSearch ──→ END
              │
              ├── currentStep === "awaiting_selection"
              │       ↓
              │   solution ──→ END
              │
              └── currentStep === "completed"
                      ↓
                  followUp ──→ END
```

### グラフ構築コード

```typescript
import { StateGraph, START, END } from "@langchain/langgraph"

function buildAnalogyGraph() {
  const graph = new StateGraph(AnalogyState)
    .addNode("abstraction", abstractionNode)
    .addNode("caseSearch", caseSearchNode)
    .addNode("solution", solutionNode)
    .addNode("followUp", followUpNode)
    .addConditionalEdges(START, routeByStep, {
      abstraction: "abstraction",
      solution: "solution",
      followUp: "followUp",
    })
    .addEdge("abstraction", "caseSearch")
    .addEdge("caseSearch", END)
    .addEdge("solution", END)
    .addEdge("followUp", END)

  return graph
}
```

### ルーティング関数

```typescript
function routeByStep(state: typeof AnalogyState.State): string {
  switch (state.currentStep) {
    case "awaiting_selection":
      return "solution"
    case "completed":
      return "followUp"
    default:
      return "abstraction"
  }
}
```

---

## 3. ノード実装

### 3.1 共通: LLM モデル・設定の取得

ノード関数はグラフ実行時に呼ばれるが、`useRuntimeConfig()` が Nuxt リクエストコンテキスト外で正常に動作するかは検証が必要。現行 `analogy-agent.ts` では `getAnalogyAgent()` 内（リクエストハンドラから呼ばれる）で1回だけ呼んでいる。

**対策**: `getAnalogyAgent()` 初期化時に `useRuntimeConfig()` の結果をモジュールスコープ変数にキャッシュし、ノード関数はキャッシュから参照する。

```typescript
let _runtimeConfig: ReturnType<typeof useRuntimeConfig> | null = null

function getRuntimeConfig() {
  if (!_runtimeConfig) {
    _runtimeConfig = useRuntimeConfig()
  }
  return _runtimeConfig
}

function getModel() {
  const config = getRuntimeConfig()
  return new ChatOpenAI({
    model: "gpt-5.4",
    temperature: 0.7,
    apiKey: config.openaiApiKey,
  })
}
```

### 3.2 abstractionNode — 課題の抽象化

**役割**: ユーザーの具体的な課題を抽象的な概念に変換し、`abstractedProblem` に格納する。メッセージ履歴にはAIメッセージを追加しない（caseSearchNode が統合した応答を生成するため）。

```typescript
async function abstractionNode(state: typeof AnalogyState.State) {
  const model = getModel()
  const result = await model.invoke([
    { role: "system", content: ABSTRACTION_PROMPT },
    ...state.messages,
  ])
  return {
    abstractedProblem: typeof result.content === "string" ? result.content : "",
  }
}
```

**ストリーミング注意**: このノードの LLM 出力はユーザーに表示しない。`chat.post.ts` のストリーミングハンドラでメタデータの `langgraph_node` を確認し、`"abstraction"` ノードの出力をフィルタリングする。

### 3.3 caseSearchNode — 事例検索・提示

**役割**: Tavily Search で Web 検索を実行し、抽象化結果とともに LLM に類似事例の提示を依頼する。

```typescript
async function caseSearchNode(state: typeof AnalogyState.State) {
  const searchResults = await performSearch(state.abstractedProblem)
  const model = getModel()

  const contextMessage = [
    `[内部コンテキスト]`,
    `抽象化された課題: ${state.abstractedProblem}`,
    ``,
    `Web検索結果:`,
    searchResults || "(検索結果なし)",
  ].join("\n")

  // コンテキスト情報はシステムプロンプトの末尾に統合する（会話履歴の後に system メッセージを
  // 挿入すると OpenAI API の動作が不安定になる可能性があるため）
  const fullSystemPrompt = `${CASE_SEARCH_PROMPT}\n\n${contextMessage}`

  const result = await model.invoke([
    { role: "system", content: fullSystemPrompt },
    ...state.messages,
  ])

  return {
    messages: [result],
    currentStep: "awaiting_selection",
  }
}
```

**Tavily Search 呼び出し**:

```typescript
async function performSearch(query: string): Promise<string> {
  const config = useRuntimeConfig()
  if (!config.tavilyApiKey) {
    logger.agent.info("Tavily Search skipped (API key not set)")
    return ""
  }
  try {
    const tavily = new TavilySearch({
      maxResults: 3,
      tavilyApiKey: config.tavilyApiKey,
    })
    const results = await tavily.invoke(query)
    logger.agent.info("Tavily Search completed", { query: query.slice(0, 50) })
    return typeof results === "string" ? results : JSON.stringify(results)
  } catch (e) {
    logger.agent.warn("Tavily Search failed", { error: e instanceof Error ? e.message : "Unknown" })
    return ""
  }
}
```

**設計判断**: TavilySearch をツールとしてではなくノードロジック内で直接呼び出す。これにより Web 検索の実行が確実になる（プロンプト依存から脱却）。

### 3.4 solutionNode — 解決策生成

**役割**: ユーザーが選択した事例に基づき、具体的な解決策を提案する。

```typescript
async function solutionNode(state: typeof AnalogyState.State) {
  const model = getModel()
  const result = await model.invoke([
    { role: "system", content: SOLUTION_PROMPT },
    ...state.messages,
  ])
  return {
    messages: [result],
    currentStep: "completed",
  }
}
```

### 3.5 followUpNode — フォローアップ対応

**役割**: 解決策提示後の追加質問に応答する。

```typescript
async function followUpNode(state: typeof AnalogyState.State) {
  const model = getModel()
  const result = await model.invoke([
    { role: "system", content: FOLLOWUP_PROMPT },
    ...state.messages,
  ])
  return {
    messages: [result],
    // currentStep は意図的に更新しない。"completed" を維持することで、
    // 後続のフォローアップも常に followUpNode にルーティングされる。
  }
}
```

---

## 4. プロンプト設計

### ファイル: `server/utils/analogy-prompt.ts`

既存の `ANALOGY_SYSTEM_PROMPT` を削除し、ノード別の4プロンプトに分割する。

### 4.1 ABSTRACTION_PROMPT

```typescript
export const ABSTRACTION_PROMPT = `あなたはアナロジー思考の専門家です。
ユーザーの課題を受け取り、その本質を抽象的な概念として言語化してください。

## ルール
- 具体的な固有名詞や分野を取り除き、構造的な問題として再定義する
- 「〜が〜する際に〜が発生する」のような汎用的な表現にする
- 抽象化の結果のみを出力してください（説明や前置きは不要）
- 1〜2文で簡潔に表現する
- 日本語で出力する`
```

### 4.2 CASE_SEARCH_PROMPT

```typescript
export const CASE_SEARCH_PROMPT = `あなたはアナロジー思考の専門家AIアシスタントです。
ユーザーの課題に対し、抽象化された課題概念とWeb検索結果を活用して、類似する他分野の事例を提示してください。

## 出力フォーマット
1. まず、課題の受け取りと抽象化の説明を簡潔に行う
   - ユーザーの課題を正確に理解したことを示す
   - 「この課題を抽象化すると「{抽象化結果}」と捉えられます」のように抽象化を紹介する
2. 次に、3〜5個の他分野事例を番号付きリストで提示する

## 事例選定の基準
- 元の課題とは異なる分野から選ぶこと（例: 生物の形態模倣、建築、経済、自然現象、スポーツなど）
- Web検索結果から得られた実在の事例を優先的に取り上げる
- 各事例について、なぜ類似しているかを一文で説明する

## 末尾の指示
- 最後に「気になる事例を選んでください」と促す

## ルール
- 応答は日本語で行う
- [内部コンテキスト] の情報はそのまま出力せず、自然な文章に組み込む`
```

### 4.3 SOLUTION_PROMPT

```typescript
export const SOLUTION_PROMPT = `あなたはアナロジー思考の専門家AIアシスタントです。
ユーザーが会話の中で選択した事例に基づき、元の課題への具体的な解決策を提案してください。

## 出力内容
- 選択された事例の原理やメカニズムの説明
- その原理を元の課題にどう適用できるかの具体的な提案
- 実現可能性についての軽い言及

## ルール
- 応答は日本語で行う
- ユーザーの追加質問ややり直しの要求にも柔軟に対応する`
```

### 4.4 FOLLOWUP_PROMPT

```typescript
export const FOLLOWUP_PROMPT = `あなたはアナロジー思考の専門家AIアシスタントです。
これまでの会話の流れを踏まえ、ユーザーの追加質問やリクエストに応答してください。

## 対応できる内容
- 提案した解決策の詳細説明や掘り下げ
- 別の事例での再検討
- 追加の質問への回答

## ルール
- 応答は日本語で行う
- 会話履歴の文脈を踏まえた一貫性のある回答をする`
```

---

## 5. エージェント初期化の変更

### ファイル: `server/utils/analogy-agent.ts` — 全面書き換え

#### 変更前の構成
- `createAgent()` で単一 ReAct エージェントを生成
- `ANALOGY_SYSTEM_PROMPT` を `systemPrompt` パラメータで渡す
- Tavily Search をツールとして渡す

#### 変更後の構成
- `StateGraph` でグラフを構築、`compile()` でコンパイル
- ノード別プロンプトを各ノード関数内で使用
- Tavily Search はノード内で直接呼び出し（ツールではない）
- シングルトンパターンは維持

```typescript
import { StateGraph, Annotation, START, END, messagesStateReducer } from "@langchain/langgraph"
import { SqliteSaver } from "@langchain/langgraph-checkpoint-sqlite"
import { ChatOpenAI } from "@langchain/openai"
import { TavilySearch } from "@langchain/tavily"
import { BaseMessage } from "@langchain/core/messages"
import { mkdirSync } from "node:fs"
import {
  ABSTRACTION_PROMPT,
  CASE_SEARCH_PROMPT,
  SOLUTION_PROMPT,
  FOLLOWUP_PROMPT,
} from "./analogy-prompt"
import { logger } from "./logger"

const DB_PATH = "./data/langgraph-checkpoints.db"

// ステート定義
const AnalogyState = Annotation.Root({ ... })

// ノード関数（上記セクション3の実装）
// routeByStep, abstractionNode, caseSearchNode, solutionNode, followUpNode, performSearch, getModel

// グラフ構築
function buildAnalogyGraph() { ... }

// シングルトン
let _compiledGraph: ReturnType<ReturnType<typeof buildAnalogyGraph>["compile"]> | null = null

export async function getAnalogyAgent() {
  if (!_compiledGraph) {
    logger.agent.info("Initializing analogy graph...")
    mkdirSync("./data", { recursive: true })
    const checkpointer = SqliteSaver.fromConnString(DB_PATH)
    const graph = buildAnalogyGraph()
    _compiledGraph = graph.compile({ checkpointer })
    logger.agent.info("Analogy graph initialized", { dbPath: DB_PATH })
  }
  return _compiledGraph
}
```

**互換性**: `getAnalogyAgent()` の戻り値は `createAgent` の戻り値から `CompiledStateGraph` に変わる。`stream()` と `getState()` は両方ともサポートされるため、呼び出し元（`chat.post.ts`、`history.get.ts`）の基本的なインターフェースは維持される。

---

## 6. chat.post.ts の変更

### ファイル: `server/api/chat.post.ts`

#### 変更点

1. **ストリーミングフィルタの更新**: `metadata.langgraph_node` を使って `abstraction` ノードの出力を除外する
2. **入力形式**: 変更なし（`{ messages: [{ role: "user", content: body.message }] }`）
3. **streamMode**: `"messages"` を維持
4. **generateTitle**: 変更なし（`fullResponse` の蓄積方法は同じ）

#### ストリーミングハンドラの変更箇所

```typescript
// 変更前
for await (const [chunk, _metadata] of stream) {
  if (chunk instanceof AIMessageChunk && typeof chunk.content === 'string' && chunk.content) {
    fullResponse += chunk.content
    await eventStream.push({ event: 'token', data: JSON.stringify({ content: chunk.content }) })
  } else if (!(chunk instanceof AIMessageChunk)) {
    logger.chat.info('Tool activity detected', { ... })
  }
}

// 変更後
const STREAMED_NODES = new Set(["caseSearch", "solution", "followUp"])

for await (const [chunk, metadata] of stream) {
  if (
    chunk instanceof AIMessageChunk &&
    typeof chunk.content === "string" &&
    chunk.content &&
    STREAMED_NODES.has(metadata?.langgraph_node)
  ) {
    fullResponse += chunk.content
    await eventStream.push({ event: 'token', data: JSON.stringify({ content: chunk.content }) })
  }
}
```

**ツール検出ログの削除**: Tavily Search はツールとしてではなくノード内で直接呼び出されるため、`ToolMessage` は発生しない。ツール検出のログ分岐を削除する。

---

## 7. history.get.ts の変更

### ファイル: `server/api/chat/history.get.ts`

#### 変更点

1. **`as any` キャストの除去**: `CompiledStateGraph` は `getState()` を公開しているため、型キャストが不要になる可能性がある。実際の型を確認して対応する
2. **ステートアクセス**: `snapshot.values.messages` のアクセスパスは変更なし（`AnalogyState` の `messages` フィールドに対応）

```typescript
// 変更前
const snapshot = await (agent as any).getState({ configurable: { thread_id: threadId } })

// 変更後
const graph = await getAnalogyAgent()
const snapshot = await graph.getState({ configurable: { thread_id: threadId } })
```

`snapshot.values` には `messages`, `currentStep`, `abstractedProblem` が含まれるが、`history.get.ts` は `messages` のみを使用するため、他のフィールドは無視される。既存のフィルタリングロジック（`HumanMessage`, `AIMessage` のみ抽出）は変更不要。

---

## 8. テスト改修

### 8.1 `tests/server/chat.test.ts`

**モック構造の変更**:

```typescript
// 変更前
const mockAgent = { stream: vi.fn() }
vi.mock('../../server/utils/analogy-agent', () => ({
  getAnalogyAgent: () => Promise.resolve(mockAgent),
}))

// 変更後
const mockGraph = { stream: vi.fn(), getState: vi.fn() }
vi.mock('../../server/utils/analogy-agent', () => ({
  getAnalogyAgent: () => Promise.resolve(mockGraph),
}))
```

**ストリームモックの更新**:
- メタデータに `langgraph_node` を含める

```typescript
const chunks = [
  [new AIMessageChunk({ content: "Hello" }), { langgraph_node: "caseSearch" }],
  [new AIMessageChunk({ content: " World" }), { langgraph_node: "caseSearch" }],
]
```

**既存テストの修正**:
- 正常系テスト「モックエージェントからのストリーム → SSE イベント形式」のチャンクモックにメタデータ `{ langgraph_node: "caseSearch" }` を追加（メタデータなしだと `STREAMED_NODES.has(undefined)` で `false` になりテストが通らなくなるため）

**新規テストケース**:
- `abstraction` ノードの出力がフィルタリングされることの検証

```typescript
it("abstraction ノードの出力はストリーミングされない", async () => {
  const chunks = [
    [new AIMessageChunk({ content: "abstracted" }), { langgraph_node: "abstraction" }],
    [new AIMessageChunk({ content: "cases" }), { langgraph_node: "caseSearch" }],
  ]
  // ... abstraction の content がクライアントに送信されないことを確認
})
```

### 8.2 `tests/server/chat-history.test.ts`

**モック構造の変更**: `mockAgent` → `mockGraph`（`getState` のモック方法は同一）

```typescript
// 変更前
const mockAgent = { getState: vi.fn() }

// 変更後
const mockGraph = { getState: vi.fn() }
```

テストケース自体は変更不要（`snapshot.values.messages` のアクセスパスが同じため）。

---

## 9. ログ更新

### `server/utils/logger.ts` — 変更なし

既存のログモジュール（`agent`, `chat`, `thread`, `history`）はそのまま使用する。各ノード内のログは `logger.agent` を使用する。

---

## 10. 実装順序

1. `server/utils/analogy-prompt.ts` — ノード別プロンプト4つに分割
2. `server/utils/analogy-agent.ts` — ステート定義、ノード関数、グラフ構築、シングルトンを全面書き換え
3. `server/api/chat.post.ts` — ストリーミングフィルタ更新（メタデータによるノードフィルタリング）
4. `server/api/chat/history.get.ts` — `as any` キャストの確認・除去
5. `tests/server/chat.test.ts` — モック更新 + 新規テスト追加
6. `tests/server/chat-history.test.ts` — モック更新
7. 動作確認（手動テスト）

---

## 11. リスク・不確実性

### `streamMode: "messages"` のメタデータ構造

`streamMode: "messages"` で返されるメタデータに `langgraph_node` が含まれることは型定義（`Record<string, any>`）から確認済みだが、実際のキー名と値は実行時の検証が必要。

**対策**: 実装初期に `console.log(metadata)` でメタデータ構造を確認し、フィルタリングキーを確定する。想定と異なる場合は `streamMode: ["messages", "updates"]` の併用や `streamMode: "custom"` への切り替えを検討する。

### abstractionNode の LLM 出力がストリーミングに混入する可能性

`streamMode: "messages"` は全ノードの LLM 呼び出しをインターセプトしてストリーミングする。abstractionNode の出力をメタデータでフィルタリングする設計だが、メタデータが期待通りにノード名を含まない場合、不要なトークンがクライアントに送信される。

**対策**: フォールバックとして、abstractionNode で `ChatOpenAI` を直接 `invoke()` するのではなく、ストリーミング非対応の方法で呼び出す手段を調査する。最悪の場合、abstractionNode と caseSearchNode を統合し、単一ノード内で抽象化 → 検索 → 提示を行う方式にフォールバックする。

### LangGraph チェックポイントの互換性

既存の SQLite チェックポイントデータは `createReactAgent` のステート構造で保存されている。`StateGraph` に移行すると、ステート構造が変わるため、既存チェックポイントが読み込めない可能性がある。

**対策**: 開発時は `data/` ディレクトリを削除してクリーンな状態から開始する。本番データの移行は「やらないこと」（CLAUDE.md: 本番デプロイなし）に該当するため考慮不要。

### `useRuntimeConfig()` のコンテキスト問題

ノード関数はグラフ実行時に呼ばれるが、Nuxt の `useRuntimeConfig()` はリクエストコンテキスト内でのみ動作する。現行実装では `getAnalogyAgent()` 内で1回だけ呼んでいるが、新設計では各ノードの `getModel()` や `performSearch()` からも呼ぶ必要がある。

**対策**: セクション3.1で記載の通り、`getAnalogyAgent()` 初期化時に `useRuntimeConfig()` の結果をモジュールスコープ変数にキャッシュし、ノード関数はキャッシュから参照する。

### TavilySearch の直接呼び出し API

現在は `TavilySearch` をツールとして `createAgent` に渡しているが、ノード内で `tavily.invoke(query)` として直接呼び出す。`invoke()` の引数が文字列なのかオブジェクトなのか、返り値の型（文字列 or オブジェクト）を実行時に検証する必要がある。

**対策**: 実装時に `experiments/` に検証スクリプトを作成し、`TavilySearch.invoke()` の入出力を確認する。

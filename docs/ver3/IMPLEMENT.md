# ver3 実装計画

## 全体構成

```
server/
├── utils/
│   ├── analogy-prompt.ts       # アナロジー思考システムプロンプト定数
│   └── analogy-agent.ts        # エージェント初期化（ChatOpenAI + MemorySaver + createAgent）
└── api/
    └── chat.post.ts            # POST /api/chat（モック → LangChain エージェント呼び出しに置換）
app/
└── pages/
    └── index.vue               # threadId の生成・管理、API リクエスト形式の変更
```

---

## 1. `server/utils/analogy-prompt.ts` — システムプロンプト定数

実験 03 で検証済みのプロンプトをそのまま移動する。

```typescript
export const ANALOGY_SYSTEM_PROMPT = `あなたはアナロジー思考の専門家AIアシスタントです。
ユーザーが提示する課題に対し、以下の5ステップで対話を進めてください。

## 対話フロー

### ステップ1: 課題の受け取り
ユーザーが具体的な課題を入力します。課題を正確に理解したことを簡潔に確認してください。

### ステップ2: 抽象化
課題の本質を抽象的な概念として言語化してください。
- 具体的な固有名詞や分野を取り除き、構造的な問題として再定義する
- 「〜が〜する際に〜が発生する」のような汎用的な表現にする

### ステップ3: 類似事例の提示
抽象化した概念に類似する**他分野の事例**を3〜5個提示してください。
- 元の課題とは異なる分野から選ぶこと
- 各事例について、なぜ類似しているかを一文で説明する
- 番号付きリストで提示する

### ステップ4: 事例の選択
ユーザーが気になる事例を選択、または自由に指示します。選択を受け付けてください。

### ステップ5: 解決策の提案
選択された事例の原理やメカニズムを元の課題に適用し、具体的な解決策を提案してください。
- 事例のどの側面が応用できるかを説明する
- 実現可能性についても軽く触れる

## 重要なルール
- ステップ2と3は1つの応答にまとめて出力してください（ユーザーの待ち時間を減らすため）
- ユーザーが追加質問ややり直しを求めた場合は柔軟に対応してください
- 応答は日本語で行ってください`
```

---

## 2. `server/utils/analogy-agent.ts` — エージェント初期化

サーバープロセスで1回だけ初期化されるシングルトンのエージェントを提供する。

```typescript
import { ChatOpenAI } from "@langchain/openai"
import { createAgent } from "langchain"
import { MemorySaver } from "@langchain/langgraph"
import { ANALOGY_SYSTEM_PROMPT } from "./analogy-prompt"

let _agent: ReturnType<typeof createAgent> | null = null

export function getAnalogyAgent() {
  if (!_agent) {
    const config = useRuntimeConfig()

    const model = new ChatOpenAI({
      model: "gpt-4.1-mini",
      temperature: 0.7,
      apiKey: config.openaiApiKey,
    })

    const checkpointer = new MemorySaver()

    _agent = createAgent({
      model,
      tools: [],
      prompt: ANALOGY_SYSTEM_PROMPT,
      checkpointer,
    })
  }
  return _agent
}
```

### 設計判断

- **シングルトンパターン**: `MemorySaver` はインメモリなので、同一プロセス内で共有する必要がある。モジュールスコープ変数で保持する
- **`useRuntimeConfig()`**: Nuxt の `server/utils/` では auto-import されるため、import 不要。`NUXT_OPENAI_API_KEY` 環境変数から API キーを取得する
- **`createAgent`**: 実験 02 で検証済みの API。`tools: []` でツールなしエージェントとして動作する

---

## 3. `server/api/chat.post.ts` — API エンドポイント改修

モック応答を廃止し、LangChain エージェントを呼び出す。

```typescript
export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  // バリデーション
  if (!body.message || typeof body.message !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'message is required' })
  }
  if (!body.threadId || typeof body.threadId !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'threadId is required' })
  }

  const agent = getAnalogyAgent()

  const result = await agent.invoke(
    { messages: [{ role: "user", content: body.message }] },
    { configurable: { thread_id: body.threadId } },
  )

  const lastMessage = result.messages[result.messages.length - 1]

  return {
    message: {
      role: 'assistant' as const,
      content: lastMessage.content as string,
    },
  }
})
```

### API 契約の変更

| | ver2（モック） | ver3 |
|---|---|---|
| リクエスト | `{ messages: Array<{ role, content }> }` | `{ message: string, threadId: string }` |
| レスポンス | `{ message: { role, content } }` | `{ message: { role, content } }`（変更なし） |

- **`messages` 配列 → 単一 `message`**: MemorySaver がサーバー側で会話履歴を管理するため、クライアントは最新のユーザーメッセージのみ送信する
- **`threadId` の追加**: MemorySaver が会話を識別するためのキー。クライアントが生成する UUID

---

## 4. `app/pages/index.vue` — フロントエンド改修

### 変更内容

1. **`threadId` の生成**: ページロード時に `crypto.randomUUID()` で UUID を生成し、セッション中保持する
2. **`sendMessage()` の変更**: `messages` 配列全体ではなく、`{ message, threadId }` を送信する
3. **`messages` 配列**: 表示用として引き続きクライアント側で維持する（サーバーから返された `message` を push するのは同じ）

```typescript
const threadId = ref(crypto.randomUUID())

async function sendMessage(input: string) {
  if (!input) return

  messages.value.push({ role: 'user', content: input })
  isLoading.value = true

  try {
    const data = await $fetch('/api/chat', {
      method: 'POST',
      body: { message: input, threadId: threadId.value },
    })
    messages.value.push(data.message)
  } catch (error) {
    console.error('Chat error:', error)
  } finally {
    isLoading.value = false
  }
}
```

変更は `sendMessage` 内の `body` のみ。テンプレートやスタイルへの変更はなし。

---

## 5. `nuxt.config.ts` — runtimeConfig 追加

```typescript
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  runtimeConfig: {
    openaiApiKey: '',
  },
})
```

---

## 6. `.env.example` — 更新

```
OPENAI_API_KEY=sk-your-key-here
NUXT_OPENAI_API_KEY=sk-your-key-here
```

---

## 7. 実験コード 02 の整理

`experiments/02-memory-management.ts` からアプローチ A のコードを削除し、アプローチ B のみ残す。
`main()` ラッパーも不要になるため、`approachB()` の中身を直接 `main()` にする。

---

## 実装順序

1. `nuxt.config.ts` に `runtimeConfig` 追加
2. `.env.example` 更新
3. `server/utils/analogy-prompt.ts` 作成（プロンプト定数の移動）
4. `server/utils/analogy-agent.ts` 作成（エージェント初期化）
5. `server/api/chat.post.ts` 改修（モック → エージェント呼び出し）
6. `app/pages/index.vue` 改修（threadId 追加、リクエスト形式変更）
7. `experiments/02-memory-management.ts` 整理
8. 動作確認（`pnpm dev` でチャットが AI 応答を返すことを確認）

# ver2 実装計画

## 全体構成

```
experiments/
├── _shared.ts                    # 共通設定（モデル初期化、env読み込み）
├── 01-basic-connection.ts        # 基本接続確認
├── 02-memory-management.ts       # 会話メモリ管理の検証
└── 03-analogy-prompt.ts          # アナロジー思考プロンプトの検証
.env.example                      # 環境変数テンプレート
```

---

## 0. セットアップ

### `.env.example`

```
OPENAI_API_KEY=sk-your-key-here
```

### `experiments/_shared.ts`

共通のモデル初期化と環境変数読み込みを集約する。

```typescript
import "dotenv/config"
import { ChatOpenAI } from "@langchain/openai"

export const model = new ChatOpenAI({
  model: "gpt-4.1-mini",
  temperature: 0.7,
})
```

- `dotenv/config` のインポートだけで `.env` が自動読み込みされる
- モデルは `gpt-4.1-mini` を使用（実験用途のためコスト抑制）
- `OPENAI_API_KEY` は `ChatOpenAI` が自動で環境変数から取得

---

## 1. `01-basic-connection.ts` — 基本接続確認

### 目的

LangChainからOpenAI APIを呼び出し、応答が返ることを確認する。

### 実装内容

```typescript
import { model } from "./_shared"
import { HumanMessage, SystemMessage } from "@langchain/core/messages"

async function main() {
  // 1. 最もシンプルな呼び出し（文字列）
  console.log("=== 文字列で呼び出し ===")
  const res1 = await model.invoke("こんにちは")
  console.log("応答:", res1.content)
  console.log("トークン使用量:", res1.usage_metadata)

  // 2. メッセージ配列で呼び出し
  console.log("\n=== メッセージ配列で呼び出し ===")
  const res2 = await model.invoke([
    new SystemMessage("あなたは親切なアシスタントです。"),
    new HumanMessage("TypeScriptとは何ですか？一言で。"),
  ])
  console.log("応答:", res2.content)

  // 3. オブジェクト形式（role/content）で呼び出し
  console.log("\n=== オブジェクト形式で呼び出し ===")
  const res3 = await model.invoke([
    { role: "system", content: "一言で答えてください。" },
    { role: "user", content: "日本の首都は？" },
  ])
  console.log("応答:", res3.content)
}

main().catch(console.error)
```

### 確認ポイント

- API接続が成功するか
- レスポンスの `content` フィールドに応答テキストが入るか
- `usage_metadata` でトークン使用量が取得できるか
- メッセージの指定方法（文字列 / クラス / オブジェクト）の違い

---

## 2. `02-memory-management.ts` — 会話メモリ管理の検証

### 目的

会話履歴の保持・受け渡し方法を2つのアプローチで検証し、本アプリに適した方法を確定する。

### 実装内容

2つのアプローチを順に実行して比較する。

#### アプローチA: 手動メッセージ管理 + LCEL チェーン

フロントエンドから会話履歴全体を受け取り、プロンプトテンプレートに埋め込む方式。
現在のNuxtアプリの構造（クライアントが `messages` 配列を送信）と整合する。

```typescript
import { model } from "./_shared"
import { ChatPromptTemplate } from "@langchain/core/prompts"
import { StringOutputParser } from "@langchain/core/output_parsers"
import {
  HumanMessage,
  AIMessage,
  type BaseMessage,
} from "@langchain/core/messages"

async function approachA() {
  console.log("=== アプローチA: 手動メッセージ管理 ===\n")

  const prompt = ChatPromptTemplate.fromMessages([
    ["system", "あなたは親切なアシスタントです。"],
    ["placeholder", "{chat_history}"],
    ["human", "{input}"],
  ])

  const chain = prompt.pipe(model).pipe(new StringOutputParser())

  const history: BaseMessage[] = []

  // ターン1
  const input1 = "私の名前は太郎です。"
  console.log(`User: ${input1}`)
  const res1 = await chain.invoke({ chat_history: history, input: input1 })
  console.log(`AI: ${res1}\n`)

  // 履歴に追加
  history.push(new HumanMessage(input1))
  history.push(new AIMessage(res1))

  // ターン2（前のターンを覚えているか確認）
  const input2 = "私の名前を覚えていますか？"
  console.log(`User: ${input2}`)
  const res2 = await chain.invoke({ chat_history: history, input: input2 })
  console.log(`AI: ${res2}\n`)
}
```

#### アプローチB: MemorySaver（LangGraph チェックポイント）

サーバー側で会話状態を保持する方式。`thread_id` で会話を識別する。

```typescript
import { model } from "./_shared"
import { createAgent } from "langchain"
import { MemorySaver } from "@langchain/langgraph"

async function approachB() {
  console.log("=== アプローチB: MemorySaver ===\n")

  const checkpointer = new MemorySaver()

  const agent = createAgent({
    model: model,
    tools: [],
    prompt: "あなたは親切なアシスタントです。",
    checkpointer,
  })

  const threadConfig = { configurable: { thread_id: "test-thread-1" } }

  // ターン1
  console.log("User: 私の名前は太郎です。")
  const res1 = await agent.invoke(
    { messages: [{ role: "user", content: "私の名前は太郎です。" }] },
    threadConfig,
  )
  const lastMsg1 = res1.messages[res1.messages.length - 1]
  console.log(`AI: ${lastMsg1.content}\n`)

  // ターン2（前のターンを覚えているか確認）
  console.log("User: 私の名前を覚えていますか？")
  const res2 = await agent.invoke(
    { messages: [{ role: "user", content: "私の名前を覚えていますか？" }] },
    threadConfig,
  )
  const lastMsg2 = res2.messages[res2.messages.length - 1]
  console.log(`AI: ${lastMsg2.content}\n`)
}
```

### 確認ポイント

| 観点 | アプローチA（手動） | アプローチB（MemorySaver） |
|---|---|---|
| 履歴の保持 | クライアント側で管理、毎回全量送信 | サーバー側で自動保持 |
| Nuxtとの親和性 | 高い（現在の構造と一致） | thread_id管理が追加で必要 |
| 依存パッケージ | `@langchain/core`, `@langchain/openai` | 上記 + `langchain`, `@langchain/langgraph` |
| スケーラビリティ | 履歴が長くなるとリクエストサイズ増大 | サーバーメモリに依存 |

→ 実験で両方動かし、本アプリにどちらが適切か判断する。

---

## 3. `03-analogy-prompt.ts` — アナロジー思考プロンプトの検証

### 目的

5ステップのアナロジー思考フローを実現するシステムプロンプトを設計し、対話として成立するか検証する。

### 実装内容

```typescript
import { model } from "./_shared"
import { ChatPromptTemplate } from "@langchain/core/prompts"
import { StringOutputParser } from "@langchain/core/output_parsers"
import {
  HumanMessage,
  AIMessage,
  type BaseMessage,
} from "@langchain/core/messages"

const ANALOGY_SYSTEM_PROMPT = `あなたはアナロジー思考の専門家AIアシスタントです。
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

async function main() {
  const prompt = ChatPromptTemplate.fromMessages([
    ["system", ANALOGY_SYSTEM_PROMPT],
    ["placeholder", "{chat_history}"],
    ["human", "{input}"],
  ])

  const chain = prompt.pipe(model).pipe(new StringOutputParser())
  const history: BaseMessage[] = []

  // --- ステップ1〜3: 課題入力 → 抽象化 + 類似事例 ---
  const input1 = "新幹線がトンネルに入る時にドンという大きな音が発生する問題を解決したい"
  console.log(`\n[User] ${input1}\n`)
  const res1 = await chain.invoke({ chat_history: history, input: input1 })
  console.log(`[AI]\n${res1}\n`)

  history.push(new HumanMessage(input1))
  history.push(new AIMessage(res1))

  // --- ステップ4: 事例の選択 ---
  const input2 = "カワセミの事例が面白そうです。それと組み合わせて解決策を考えてください。"
  console.log(`[User] ${input2}\n`)
  const res2 = await chain.invoke({ chat_history: history, input: input2 })
  console.log(`[AI]\n${res2}\n`)

  history.push(new HumanMessage(input2))
  history.push(new AIMessage(res2))

  // --- 追加質問（フロー外の自由な対話） ---
  const input3 = "他にもこの原理を応用できる分野はありますか？"
  console.log(`[User] ${input3}\n`)
  const res3 = await chain.invoke({ chat_history: history, input: input3 })
  console.log(`[AI]\n${res3}\n`)
}

main().catch(console.error)
```

### 確認ポイント

- システムプロンプトで5ステップの対話フローが制御できるか
- ステップ2（抽象化）と3（類似事例）が1回の応答にまとめられるか
- カワセミの事例が類似事例として挙がるか（挙がらない場合はプロンプトの調整が必要）
- ステップ5の解決策が具体的で有用か
- フロー外の自由な追加質問にも柔軟に対応できるか
- プロンプトの改善点があれば記録し、`03-analogy-prompt.ts` を反復的に改良する

---

## 実装順序

1. パッケージのインストール（`pnpm add` / `pnpm add -D`）
2. `.env.example` 作成、ユーザーに `.env` を用意してもらう
3. `experiments/_shared.ts` 作成
4. `experiments/01-basic-connection.ts` 作成 → 実行・確認
5. `experiments/02-memory-management.ts` 作成 → 実行・確認 → メモリ方式の決定
6. `experiments/03-analogy-prompt.ts` 作成 → 実行・確認 → プロンプトの反復改良
7. `package.json` にスクリプト追加

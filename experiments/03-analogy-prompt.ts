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

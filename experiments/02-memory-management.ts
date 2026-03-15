import { model } from "./_shared"
import { ChatPromptTemplate } from "@langchain/core/prompts"
import { StringOutputParser } from "@langchain/core/output_parsers"
import {
  HumanMessage,
  AIMessage,
  type BaseMessage,
} from "@langchain/core/messages"
import { createAgent } from "langchain"
import { MemorySaver } from "@langchain/langgraph"

// --- アプローチA: 手動メッセージ管理 + LCEL チェーン ---
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

// --- アプローチB: MemorySaver（LangGraph チェックポイント） ---
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

async function main() {
  await approachA()
  console.log("\n" + "=".repeat(50) + "\n")
  await approachB()
}

main().catch(console.error)

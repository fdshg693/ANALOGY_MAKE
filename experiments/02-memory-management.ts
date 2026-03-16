import { model } from "./_shared"
import { createAgent } from "langchain"
import { MemorySaver } from "@langchain/langgraph"

async function main() {
  const checkpointer = new MemorySaver()

  const agent = createAgent({
    model: model,
    tools: [],
    systemPrompt: "あなたは親切なアシスタントです。",
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

main().catch(console.error)

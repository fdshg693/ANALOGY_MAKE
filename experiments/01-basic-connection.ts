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

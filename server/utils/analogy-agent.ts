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
      systemPrompt: ANALOGY_SYSTEM_PROMPT,
      checkpointer,
    })
  }
  return _agent
}

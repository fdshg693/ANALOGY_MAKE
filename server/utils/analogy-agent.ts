import { ChatOpenAI } from "@langchain/openai"
import { createAgent } from "langchain"
import { SqliteSaver } from "@langchain/langgraph-checkpoint-sqlite"
import { TavilySearch } from "@langchain/tavily"
import { mkdirSync } from "node:fs"
import { ANALOGY_SYSTEM_PROMPT } from "./analogy-prompt"
import { logger } from "./logger"

const DB_PATH = "./data/langgraph-checkpoints.db"

let _agent: ReturnType<typeof createAgent> | null = null

export async function getAnalogyAgent() {
  if (!_agent) {
    logger.agent.info('Initializing agent...')
    const config = useRuntimeConfig()

    const model = new ChatOpenAI({
      model: "gpt-4.1-mini",
      temperature: 0.7,
      apiKey: config.openaiApiKey,
    })

    const tools: any[] = []
    if (config.tavilyApiKey) {
      tools.push(new TavilySearch({
        maxResults: 3,
        tavilyApiKey: config.tavilyApiKey,
      }))
      logger.agent.info('Tavily Search enabled (maxResults: 3)')
    } else {
      logger.agent.info('Tavily Search disabled (NUXT_TAVILY_API_KEY not set)')
    }

    mkdirSync("./data", { recursive: true })
    const checkpointer = SqliteSaver.fromConnString(DB_PATH)

    _agent = createAgent({
      model,
      tools,
      systemPrompt: ANALOGY_SYSTEM_PROMPT,
      checkpointer,
    })

    logger.agent.info('Agent initialized', { model: 'gpt-4.1-mini', tools: tools.length, dbPath: DB_PATH })
  }
  return _agent
}

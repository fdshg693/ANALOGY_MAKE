import { Annotation, StateGraph, START, END, messagesStateReducer } from "@langchain/langgraph"
import { SqliteSaver } from "@langchain/langgraph-checkpoint-sqlite"
import { ChatOpenAI } from "@langchain/openai"
import { TavilySearch } from "@langchain/tavily"
import type { BaseMessage } from "@langchain/core/messages"
import type { RunnableConfig } from "@langchain/core/runnables"
import type { ThreadSettings, SearchSettings } from "./thread-store"
import { DEFAULT_SEARCH_SETTINGS } from "./thread-store"
import { DB_PATH } from "./db-config"
import {
  ABSTRACTION_PROMPT,
  CASE_SEARCH_PROMPT,
  SOLUTION_PROMPT,
  FOLLOWUP_PROMPT,
  buildSystemPrompt,
} from "./analogy-prompt"
import { logger } from "./logger"

// ステート定義
const AnalogyState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: messagesStateReducer,
    default: () => [],
  }),
  currentStep: Annotation<string>({
    reducer: (_prev, next) => next,
    default: () => "initial",
  }),
  abstractedProblem: Annotation<string>({
    reducer: (_prev, next) => next,
    default: () => "",
  }),
})

// RuntimeConfig キャッシュ
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
    model: "gpt-4.1-mini",
    temperature: 0.7,
    apiKey: config.openaiApiKey,
  })
}

export interface SearchResult {
  title: string
  url: string
  content: string
}

// Tavily Search 直接呼び出し
async function performSearch(query: string, search: SearchSettings): Promise<SearchResult[]> {
  if (!search.enabled) {
    logger.agent.info("Tavily Search skipped (disabled by settings)")
    return []
  }
  const config = getRuntimeConfig()
  if (!config.tavilyApiKey) {
    logger.agent.info("Tavily Search skipped (API key not set)")
    return []
  }
  try {
    const tavily = new TavilySearch({
      maxResults: search.maxResults,
      searchDepth: search.depth,
      tavilyApiKey: config.tavilyApiKey,
    })
    const results = await tavily.invoke({ query })
    logger.agent.info("Tavily Search completed", {
      query: query.slice(0, 50),
      depth: search.depth,
      maxResults: search.maxResults,
    })
    if (results && typeof results === "object" && "error" in results) {
      logger.agent.warn("Tavily Search returned error", { error: String(results.error) })
      return []
    }
    if (results && typeof results === "object" && Array.isArray((results as { results?: unknown }).results)) {
      const items = (results as { results: Array<{ title?: unknown; url?: unknown; content?: unknown }> }).results
      return items
        .filter((r) => typeof r?.title === "string" && typeof r?.url === "string" && typeof r?.content === "string")
        .map((r) => ({ title: r.title as string, url: r.url as string, content: r.content as string }))
    }
    return []
  } catch (e) {
    logger.agent.warn("Tavily Search failed", { error: e instanceof Error ? e.message : "Unknown" })
    return []
  }
}

// ルーティング関数
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

// ノード: 課題の抽象化
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

// ノード: 事例検索・提示
async function caseSearchNode(state: typeof AnalogyState.State, config: RunnableConfig) {
  const settings = config?.configurable?.settings as ThreadSettings | undefined
  const search = settings?.search ?? DEFAULT_SEARCH_SETTINGS
  const searchResults = await performSearch(state.abstractedProblem, search)
  const model = getModel()

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

// ノード: 解決策生成
async function solutionNode(state: typeof AnalogyState.State, config: RunnableConfig) {
  const settings = config?.configurable?.settings as ThreadSettings | undefined
  const model = getModel()
  const result = await model.invoke([
    { role: "system", content: buildSystemPrompt(SOLUTION_PROMPT, settings) },
    ...state.messages,
  ])
  return {
    messages: [result],
    currentStep: "completed",
  }
}

// ノード: フォローアップ対応
async function followUpNode(state: typeof AnalogyState.State, config: RunnableConfig) {
  const settings = config?.configurable?.settings as ThreadSettings | undefined
  const model = getModel()
  const result = await model.invoke([
    { role: "system", content: buildSystemPrompt(FOLLOWUP_PROMPT, settings) },
    ...state.messages,
  ])
  return {
    messages: [result],
  }
}

// グラフ構築
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

// シングルトン
let _compiledGraph: ReturnType<ReturnType<typeof buildAnalogyGraph>["compile"]> | null = null

export async function getAnalogyAgent() {
  if (!_compiledGraph) {
    logger.agent.info("Initializing analogy graph...")
    const checkpointer = SqliteSaver.fromConnString(DB_PATH)
    const graph = buildAnalogyGraph()
    _compiledGraph = graph.compile({ checkpointer })
    logger.agent.info("Analogy graph initialized", { dbPath: DB_PATH })
  }
  return _compiledGraph
}

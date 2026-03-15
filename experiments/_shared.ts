import "dotenv/config"
import { ChatOpenAI } from "@langchain/openai"

export const model = new ChatOpenAI({
  model: "gpt-4.1-mini",
  temperature: 0.7,
})

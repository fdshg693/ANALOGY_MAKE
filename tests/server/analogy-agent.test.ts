import { describe, it, expect, vi } from 'vitest'
import { HumanMessage, AIMessage } from '@langchain/core/messages'

// analogy-agent モジュールは useRuntimeConfig を遅延呼び出しする前提。
// ただしインポート時に Nuxt の auto-import を参照するコードパスが動く可能性に備えてスタブ。
vi.stubGlobal('useRuntimeConfig', () => ({ openaiApiKey: 'test-key', tavilyApiKey: 'test-tavily-key' }))

import { deriveCurrentStep } from '../../server/utils/analogy-agent'

describe('deriveCurrentStep', () => {
  it('空配列 → "initial"', () => {
    expect(deriveCurrentStep([])).toBe('initial')
  })

  it('末尾が HumanMessage → "initial"', () => {
    const msgs = [
      new AIMessage('応答'),
      new HumanMessage('次の質問'),
    ]
    expect(deriveCurrentStep(msgs)).toBe('initial')
  })

  it('末尾が AIMessage かつ additional_kwargs.searchResults あり → "awaiting_selection"', () => {
    const ai = new AIMessage({
      content: '類似事例です',
      additional_kwargs: {
        searchResults: [{ title: 't', url: 'https://a.test', content: 'c' }],
      },
    })
    expect(deriveCurrentStep([new HumanMessage('質問'), ai])).toBe('awaiting_selection')
  })

  it('末尾が AIMessage かつ searchResults なし → "completed"', () => {
    const ai = new AIMessage('解決策を提示')
    expect(deriveCurrentStep([new HumanMessage('質問'), ai])).toBe('completed')
  })

  it('末尾が AIMessage かつ searchResults が空配列 → "completed"', () => {
    const ai = new AIMessage({
      content: '解決策を提示',
      additional_kwargs: { searchResults: [] },
    })
    expect(deriveCurrentStep([new HumanMessage('質問'), ai])).toBe('completed')
  })
})

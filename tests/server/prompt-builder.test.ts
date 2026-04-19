import { describe, it, expect } from 'vitest'
import { buildSystemPrompt } from '../../server/utils/analogy-prompt'

describe('buildSystemPrompt', () => {
  const basePrompt = 'テスト用ベースプロンプト'

  it('settings が undefined の場合、basePrompt をそのまま返す', () => {
    expect(buildSystemPrompt(basePrompt)).toBe(basePrompt)
  })

  it('standard 粒度でカスタム指示なしの場合、basePrompt をそのまま返す', () => {
    const result = buildSystemPrompt(basePrompt, {
      granularity: 'standard',
      customInstruction: '',
    })
    expect(result).toBe(basePrompt)
  })

  it('concise 粒度の場合、回答スタイル指示を付加する', () => {
    const result = buildSystemPrompt(basePrompt, {
      granularity: 'concise',
      customInstruction: '',
    })
    expect(result).toBe(
      basePrompt +
        '\n\n## 回答スタイル\n簡潔に箇条書きで回答してください。要点のみを述べ、冗長な説明は避けてください。',
    )
  })

  it('detailed 粒度の場合、回答スタイル指示を付加する', () => {
    const result = buildSystemPrompt(basePrompt, {
      granularity: 'detailed',
      customInstruction: '',
    })
    expect(result).toBe(
      basePrompt +
        '\n\n## 回答スタイル\n具体例と背景説明を含めて詳しく回答してください。',
    )
  })

  it('カスタム指示がある場合、追加指示セクションを付加する', () => {
    const result = buildSystemPrompt(basePrompt, {
      granularity: 'standard',
      customInstruction: 'やさしい言葉で説明してください',
    })
    expect(result).toBe(
      basePrompt + '\n\n## 追加指示\nやさしい言葉で説明してください',
    )
  })

  it('粒度指示とカスタム指示の両方を付加する（concise + custom）', () => {
    const result = buildSystemPrompt(basePrompt, {
      granularity: 'concise',
      customInstruction: '英語で回答して',
    })
    expect(result).toBe(
      basePrompt +
        '\n\n## 回答スタイル\n簡潔に箇条書きで回答してください。要点のみを述べ、冗長な説明は避けてください。' +
        '\n\n## 追加指示\n英語で回答して',
    )
  })

  it('空白のみのカスタム指示は無視する', () => {
    const result = buildSystemPrompt(basePrompt, {
      granularity: 'standard',
      customInstruction: '   \n\t  ',
    })
    expect(result).toBe(basePrompt)
  })

  it('standard 粒度 + カスタム指示ありの場合、カスタム指示のみ付加する', () => {
    const result = buildSystemPrompt(basePrompt, {
      granularity: 'standard',
      customInstruction: '3文以内で回答してください',
    })
    expect(result).toBe(
      basePrompt + '\n\n## 追加指示\n3文以内で回答してください',
    )
  })
})

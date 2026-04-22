import { describe, it, expect, vi, afterEach } from 'vitest'
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

  describe('systemPromptOverride (dev)', () => {
    afterEach(() => {
      vi.unstubAllEnvs()
    })

    it('dev 環境で systemPromptOverride がある場合、ベースプロンプトの先頭に追記する', () => {
      vi.stubEnv('NODE_ENV', 'development')
      const result = buildSystemPrompt(basePrompt, {
        granularity: 'standard',
        customInstruction: '',
        systemPromptOverride: 'デバッグ用前置き',
      })
      expect(result).toBe(`デバッグ用前置き\n\n---\n\n${basePrompt}`)
    })

    it('dev 環境で空白のみの systemPromptOverride は無視する', () => {
      vi.stubEnv('NODE_ENV', 'development')
      const result = buildSystemPrompt(basePrompt, {
        granularity: 'standard',
        customInstruction: '',
        systemPromptOverride: '   \n\t  ',
      })
      expect(result).toBe(basePrompt)
    })

    it('本番環境では systemPromptOverride を無視する', () => {
      vi.stubEnv('NODE_ENV', 'production')
      const result = buildSystemPrompt(basePrompt, {
        granularity: 'standard',
        customInstruction: '',
        systemPromptOverride: '本番での上書き試行',
      })
      expect(result).toBe(basePrompt)
    })

    it('dev 環境で granularity / カスタム指示と systemPromptOverride が併存する', () => {
      vi.stubEnv('NODE_ENV', 'development')
      const result = buildSystemPrompt(basePrompt, {
        granularity: 'concise',
        customInstruction: 'カスタム',
        systemPromptOverride: '前置き',
      })
      const expectedBase =
        basePrompt +
        '\n\n## 回答スタイル\n簡潔に箇条書きで回答してください。要点のみを述べ、冗長な説明は避けてください。' +
        '\n\n## 追加指示\nカスタム'
      expect(result).toBe(`前置き\n\n---\n\n${expectedBase}`)
    })
  })
})

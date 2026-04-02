# ver12 実装計画: Web検索連携（Tavily Search）

事前リファクタリング不要（既存の `createAgent` にツールを追加するだけで構造変更なし）。

## 変更対象ファイル一覧

| ファイル | 変更内容 |
|---|---|
| `package.json` | `@langchain/tavily` 依存追加 |
| `nuxt.config.ts` | `runtimeConfig.tavilyApiKey` 追加 |
| `.env.example` | `NUXT_TAVILY_API_KEY` 追加 |
| `server/utils/analogy-agent.ts` | TavilySearch ツールをエージェントに追加 |
| `server/utils/analogy-prompt.ts` | Web検索ツール活用の指示を追加 |
| `tests/server/chat.test.ts` | runtimeConfig スタブに `tavilyApiKey` 追加 |

## 実装詳細

### 1. パッケージ追加

```bash
pnpm add @langchain/tavily
```

`@langchain/tavily` は `@langchain/community` の TavilySearchResults の後継パッケージ。ネイティブモジュールを含まないため `nitro.externals.external` への追加は不要。

### 2. `nuxt.config.ts` — runtimeConfig 拡張

```typescript
runtimeConfig: {
  openaiApiKey: '',
  tavilyApiKey: '',  // 追加
}
```

環境変数 `NUXT_TAVILY_API_KEY` が自動的にマッピングされる（Nuxt の慣行）。

### 3. `.env.example` — テンプレート更新

```
NUXT_TAVILY_API_KEY=tvly-your-key-here
```

を追記。

### 4. `server/utils/analogy-agent.ts` — ツール追加

```typescript
import { TavilySearch } from "@langchain/tavily"

// getAnalogyAgent() 内:
const tools: any[] = []
if (config.tavilyApiKey) {
  tools.push(new TavilySearch({
    maxResults: 3,
    apiKey: config.tavilyApiKey,
  }))
}

_agent = createAgent({
  model,
  tools,
  systemPrompt: ANALOGY_SYSTEM_PROMPT,
  checkpointer,
})
```

- `maxResults: 3` — 類似事例の補助として3件で十分。過多な検索結果はトークン消費を増やすだけ
- `apiKey` は `useRuntimeConfig()` 経由で取得
- `config.tavilyApiKey` が falsy の場合はツールなし（ver11 と同等の動作）でフォールバック

### 5. `server/utils/analogy-prompt.ts` — プロンプト拡張

ステップ3の記述を拡張し、Web検索ツールの活用を強く推奨する指示を追加する。

変更前（ステップ3 部分）:
```
### ステップ3: 類似事例の提示
抽象化した概念に類似する**他分野の事例**を3〜5個提示してください。
- 元の課題とは異なる分野から選ぶこと（例: 生物の形態模倣（バイオミミクリー）、建築、経済、自然現象、スポーツなど）
- 各事例について、なぜ類似しているかを一文で説明する
- 番号付きリストで提示する
```

変更後:
```
### ステップ3: 類似事例の提示
抽象化した概念に類似する**他分野の事例**を3〜5個提示してください。

**Web検索ツールの活用**: 類似事例を提示する前に、必ずWeb検索ツール（tavily_search）を使って関連する事例や最新の情報を検索してください。検索結果から得られた実在の事例を優先的に取り上げ、あなたの内部知識と組み合わせて事例の幅と鮮度を向上させてください。

- 元の課題とは異なる分野から選ぶこと（例: 生物の形態模倣（バイオミミクリー）、建築、経済、自然現象、スポーツなど）
- 各事例について、なぜ類似しているかを一文で説明する
- 番号付きリストで提示する
```

「必ず」と記述するが、ReActエージェントの自律判断のため厳密な強制ではない（ROUGH_PLAN「検索実行の動作定義」参照）。プロンプトで強く推奨することで、大半のケースで検索が実行されることを期待する。

### 6. テスト更新

`tests/server/chat.test.ts` の runtimeConfig スタブを更新:

```typescript
vi.stubGlobal('useRuntimeConfig', () => ({
  openaiApiKey: 'test-key',
  tavilyApiKey: 'test-tavily-key',  // 追加
}))
```

エージェントはモック済みのため、Tavily ツールの実際の動作テストは不要（エージェント内部のツール呼び出しはモックの外側）。`analogy-agent.ts` の単体テストを新規追加する場合は、`@langchain/tavily` のモックが必要になるが、現時点では既存テストの維持のみとする。

## リスク・不確実性

1. **`@langchain/tavily` パッケージの安定性**: 比較的新しいパッケージ（`@langchain/community` からの分離）。API が変更される可能性は低いが、型定義の不備がある可能性がある。`pnpm add` 後に型チェックを実施して確認する。

2. **ストリーミングとツール呼び出しの互換性**: 現在の `chat.post.ts` は `streamMode: "messages"` で `AIMessageChunk` のみを処理している。ツール呼び出し時に `ToolMessage` や `AIMessageChunk` の `tool_calls` プロパティが混在する可能性がある。`chunk instanceof AIMessageChunk && typeof chunk.content === 'string' && chunk.content` のフィルタで問題ないか、実際の動作で確認が必要。

3. **Tavily API キー未設定時の動作**: `NUXT_TAVILY_API_KEY` が未設定の場合、`TavilySearch` のコンストラクタでエラーになる可能性がある。→ **キー未設定時は `tools: []` でフォールバックする防御コードを追加する**。Tavily は補助機能であり、キーが未設定でもアプリはLLM内部知識のみで動作すべき。実装: `config.tavilyApiKey` が truthy の場合のみ TavilySearch を生成し、`tools` 配列に追加する。

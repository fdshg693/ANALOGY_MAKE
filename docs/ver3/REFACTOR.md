# ver3 リファクタリング計画

## 概要

LangChain 統合にあたり、実験コードからの資産移行とサーバー環境の整備を行う。

## 変更点

### 1. Nuxt runtimeConfig に OPENAI_API_KEY を追加

実験では `dotenv` で `.env` を読み込んでいたが、Nuxt サーバーでは `runtimeConfig` を使う。

**`nuxt.config.ts`:**

```typescript
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  runtimeConfig: {
    openaiApiKey: '',  // NUXT_OPENAI_API_KEY 環境変数から自動取得
  },
})
```

- Nuxt は `NUXT_OPENAI_API_KEY` 環境変数を `runtimeConfig.openaiApiKey` に自動マッピングする
- `.env` に `NUXT_OPENAI_API_KEY=sk-xxx` を追加（既存の `OPENAI_API_KEY` と併存）

### 2. アナロジープロンプトの抽出

`experiments/03-analogy-prompt.ts` にハードコードされている `ANALOGY_SYSTEM_PROMPT` を `server/utils/` に移動し、サーバー API から利用可能にする。

**`server/utils/analogy-prompt.ts`（新規）:**

実験で検証済みのプロンプト定数をそのまま移動。

### 3. `.env.example` の更新

```
OPENAI_API_KEY=sk-your-key-here
NUXT_OPENAI_API_KEY=sk-your-key-here
```

### 4. 実験コード 02 のアプローチ A 削除

`experiments/02-memory-management.ts` から不採用のアプローチ A（手動メッセージ管理）のコードを削除し、採用されたアプローチ B（MemorySaver）のみ残す。

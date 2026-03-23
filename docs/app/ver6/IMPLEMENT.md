# ver6 実装計画: Markdownレンダリングの導入

## 1. パッケージ追加

```bash
pnpm add marked dompurify
pnpm add -D @types/dompurify
```

- `marked` — Markdown → HTML 変換
- `dompurify` — HTML サニタイズ（XSS 対策）
- `@types/dompurify` — TypeScript 型定義

## 2. `ChatMessage.vue` の変更

変更対象ファイル: `app/components/ChatMessage.vue`

### 2.1 script セクション

```vue
<script setup lang="ts">
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps<{
  role: 'user' | 'assistant'
  content: string
  isError?: boolean
}>()

const renderedHtml = computed(() => {
  if (props.role !== 'assistant') return ''
  const html = marked.parse(props.content) as string
  if (import.meta.client) {
    return DOMPurify.sanitize(html)
  }
  return html
})
</script>
```

**ポイント:**
- `marked.parse()` は同期処理。`content` prop が変わるたびに computed が再評価されるため、ストリーミング中もリアルタイムでレンダリングが反映される
- `marked.parse()` の戻り値は `string | Promise<string>` だが、async オプションを有効にしない限り `string` が返る。`as string` でキャスト
- `DOMPurify.sanitize()` は `import.meta.client` ガードで SSR 時のエラーを回避。初回 SSR では messages 配列が空なので実質的に呼ばれないが、安全策として明示的にガードする
- `isError` の場合も Markdown レンダリングは適用する（エラーメッセージ内の `⚠` 等はプレーンテキストなので影響なし）

### 2.2 template セクション

```vue
<template>
  <div class="chat-message" :class="[role, { error: isError }]">
    <span class="role-label">{{ role === 'user' ? 'You' : 'AI' }}</span>
    <div v-if="role === 'assistant'" class="message-content markdown-body" v-html="renderedHtml"></div>
    <div v-else class="message-content">{{ content }}</div>
  </div>
</template>
```

**ポイント:**
- assistant メッセージのみ `v-html` + `markdown-body` クラスでリッチ表示
- user メッセージは従来通りテキスト補間（`{{ content }}`）でプレーンテキスト表示
- `v-if` / `v-else` で分岐。同じ `message-content` クラスを共有しつつ、assistant のみ `markdown-body` を追加

### 2.3 style セクション

既存の `.message-content` から `white-space: pre-wrap` を削除し、ユーザーメッセージ用と Markdown 用のスタイルを分離する。

```css
/* 既存を変更 */
.message-content {
  line-height: 1.5;
}

/* ユーザーメッセージ: 従来通り pre-wrap */
.chat-message.user .message-content {
  white-space: pre-wrap;
}

/* Markdown レンダリング用タイポグラフィ */
.message-content.markdown-body :deep(h1),
.message-content.markdown-body :deep(h2),
.message-content.markdown-body :deep(h3) {
  margin-top: 0.75rem;
  margin-bottom: 0.25rem;
  font-weight: 600;
  line-height: 1.3;
}

.message-content.markdown-body :deep(h1) { font-size: 1.25rem; }
.message-content.markdown-body :deep(h2) { font-size: 1.1rem; }
.message-content.markdown-body :deep(h3) { font-size: 1rem; }

.message-content.markdown-body :deep(p) {
  margin: 0.5rem 0;
}

.message-content.markdown-body :deep(ul),
.message-content.markdown-body :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.message-content.markdown-body :deep(li) {
  margin: 0.25rem 0;
}

.message-content.markdown-body :deep(strong) {
  font-weight: 600;
}

.message-content.markdown-body :deep(code) {
  background-color: rgba(0, 0, 0, 0.06);
  padding: 0.15rem 0.35rem;
  border-radius: 0.25rem;
  font-size: 0.9em;
  font-family: 'Consolas', 'Monaco', monospace;
}

.message-content.markdown-body :deep(pre) {
  background-color: rgba(0, 0, 0, 0.06);
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 0.5rem 0;
}

.message-content.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
}

.message-content.markdown-body :deep(blockquote) {
  border-left: 3px solid #d1d5db;
  padding-left: 0.75rem;
  margin: 0.5rem 0;
  color: #6b7280;
}

/* 先頭・末尾のマージン除去（メッセージバブル内の余白調整） */
.message-content.markdown-body :deep(> :first-child) {
  margin-top: 0;
}

.message-content.markdown-body :deep(> :last-child) {
  margin-bottom: 0;
}
```

**ポイント:**
- `:deep()` を使用して `v-html` で挿入される子要素に scoped CSS を適用
- `white-space: pre-wrap` はユーザーメッセージにのみ適用（`.chat-message.user .message-content`）
- 先頭・末尾要素の margin を除去し、メッセージバブル内の余白を自然にする
- コードブロック（`pre > code`）は背景色 + 角丸で視覚的に区別。シンタックスハイライトはスコープ外

## 3. 変更しないファイル

- `app/pages/index.vue` — props インターフェースは不変のため変更不要
- `app/components/ChatInput.vue` — 無関係
- `server/` 配下 — 無関係
- `nuxt.config.ts` — 設定変更不要

## 4. 検証手順

1. `pnpm dev` でアプリを起動
2. AIに質問を送信し、応答がリスト・見出し・太字等のMarkdownでリッチ表示されることを確認
3. ストリーミング中にMarkdownが逐次レンダリングされることを確認
4. ユーザーメッセージがプレーンテキストのままであることを確認
5. エラー発生時（サーバー停止等でテスト）にエラー表示が正常に動作することを確認
6. 自動スクロールがストリーミング中に正常に動作することを確認
7. `npx nuxi typecheck` で型エラーがないことを確認
8. `pnpm build` でビルドが成功することを確認

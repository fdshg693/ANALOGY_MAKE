# Task 1: 実装計画 - チャットUI + モックAPI

## ファイル構成

```
app/
├── app.vue                  # 変更: NuxtPage に切り替え
├── pages/
│   └── index.vue            # 新規: チャットページ
└── components/
    ├── ChatMessage.vue      # 新規: メッセージ1件の表示
    └── ChatInput.vue        # 新規: 入力欄 + 送信ボタン
server/
└── api/
    └── chat.post.ts         # 新規: POST /api/chat エンドポイント
```

---

## 1. APIルート: `server/api/chat.post.ts`

### インターフェース

```ts
// リクエストボディ
interface ChatRequest {
  messages: Array<{
    role: 'user' | 'assistant'
    content: string
  }>
}

// レスポンス
interface ChatResponse {
  message: {
    role: 'assistant'
    content: string
  }
}
```

### 実装方針

- `defineEventHandler` で POST ハンドラを定義
- `readBody` でリクエストボディを取得
- バリデーション: `messages` が配列であること、最後のメッセージが `user` ロールであることを確認
- モック応答: ユーザーの最新メッセージをエコーする形式で返す
  - 例: `「{ユーザーのメッセージ}」を受け取りました。（モック応答）`
- エラー時は `createError` で適切なHTTPステータスを返す

```ts
export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  if (!body.messages?.length) {
    throw createError({ statusCode: 400, statusMessage: 'messages is required' })
  }

  const lastMessage = body.messages[body.messages.length - 1]

  if (lastMessage.role !== 'user') {
    throw createError({ statusCode: 400, statusMessage: 'Last message must be from user' })
  }

  // モック応答（後続タスクでLangChain連携に差し替え）
  return {
    message: {
      role: 'assistant' as const,
      content: `「${lastMessage.content}」を受け取りました。\n\nこれはモック応答です。後続タスクでAIによるアナロジー思考に置き換わります。`,
    },
  }
})
```

---

## 2. チャットページ: `app/pages/index.vue`

### 状態管理

```ts
interface Message {
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<Message[]>([])
const isLoading = ref(false)
```

### 送信処理 `sendMessage(input: string)`

1. `input` が空文字なら何もしない
2. `messages` にユーザーメッセージを追加
3. `isLoading = true`
4. `$fetch('/api/chat', { method: 'POST', body: { messages } })` を呼び出す
5. レスポンスの `message` を `messages` に追加
6. `isLoading = false`
7. エラー時はコンソールに出力し `isLoading = false`

### テンプレート構造

```vue
<template>
  <div class="chat-page">
    <header class="chat-header">
      <h1>Analogy AI</h1>
    </header>

    <main class="chat-messages" ref="messagesContainer">
      <ChatMessage
        v-for="(msg, i) in messages"
        :key="i"
        :role="msg.role"
        :content="msg.content"
      />
      <!-- ローディング表示 -->
      <div v-if="isLoading" class="loading-indicator">
        考え中...
      </div>
    </main>

    <ChatInput :disabled="isLoading" @send="sendMessage" />
  </div>
</template>
```

### 自動スクロール

- `messagesContainer` の ref を取り、`messages` の変更を `watch` する
- `nextTick` 後に `scrollTop = scrollHeight` で最下部にスクロール

### スタイル

- `chat-page`: `height: 100dvh`, `display: flex`, `flex-direction: column`
- `chat-messages`: `flex: 1`, `overflow-y: auto`, `padding: 1rem`
- `chat-header`: 上部固定バー、アプリ名を表示

---

## 3. メッセージコンポーネント: `app/components/ChatMessage.vue`

### Props

```ts
defineProps<{
  role: 'user' | 'assistant'
  content: string
}>()
```

### テンプレート

```vue
<template>
  <div class="chat-message" :class="role">
    <span class="role-label">{{ role === 'user' ? 'You' : 'AI' }}</span>
    <div class="message-content">{{ content }}</div>
  </div>
</template>
```

### スタイル方針

- `user` メッセージ: 右寄せ、青系の背景
- `assistant` メッセージ: 左寄せ、グレー系の背景
- `role-label`: 小さめのフォントでロールを表示
- `message-content`: `white-space: pre-wrap` で改行を保持

---

## 4. 入力コンポーネント: `app/components/ChatInput.vue`

### Props / Emits

```ts
defineProps<{
  disabled: boolean
}>()

const emit = defineEmits<{
  send: [content: string]
}>()
```

### 内部状態

```ts
const input = ref('')
```

### 送信処理

- `input` が空（trim後）なら何もしない
- `emit('send', input.value.trim())` を発火
- `input` をクリア

### テンプレート

```vue
<template>
  <form class="chat-input" @submit.prevent="handleSubmit">
    <input
      v-model="input"
      type="text"
      placeholder="メッセージを入力..."
      :disabled="disabled"
    />
    <button type="submit" :disabled="disabled || !input.trim()">
      送信
    </button>
  </form>
</template>
```

### スタイル方針

- `chat-input`: 下部固定、`display: flex`, `gap: 0.5rem`, `padding: 1rem`
- `input`: `flex: 1`, 十分な高さ
- `button`: 送信ボタン、disabled時はグレーアウト

---

## 実装順序

1. `server/api/chat.post.ts` — APIが先にあればブラウザのdevtoolsで動作確認できる
2. `app/app.vue` の書き換え — `<NuxtPage />` に切り替え
3. `app/components/ChatMessage.vue` — 表示用コンポーネント
4. `app/components/ChatInput.vue` — 入力用コンポーネント
5. `app/pages/index.vue` — 全体を組み立てるページ
6. 動作確認 — `pnpm dev` でブラウザ確認

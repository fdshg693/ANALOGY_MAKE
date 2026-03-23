# ver9 実装計画

## 概要

`useChat` composable に `AbortController` ベースの中断機能を追加し、`ChatInput` のボタンをストリーミング中に「停止」へ切り替える。

## 実装順序

### Step 1: `app/composables/useChat.ts` — abort 機能の追加

#### 変更内容

1. composable のスコープに `AbortController` インスタンスを保持する変数を追加

```ts
let abortController: AbortController | null = null
```

2. `sendMessage` 内で `fetch` 呼び出し前に `AbortController` を生成し、`signal` を `fetch` に渡す

```ts
abortController = new AbortController()

const response = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: input, threadId: threadId.value }),
  signal: abortController.signal,
})
```

3. `abort()` 関数を追加

```ts
function abort(): void {
  abortController?.abort()
}
```

4. `catch` ブロックで `AbortError` を通常エラーと区別する

```ts
} catch (error) {
  if (error instanceof DOMException && error.name === 'AbortError') {
    // 中断: 部分テキストを保持、エラー扱いにしない
    return
  }
  // 既存の通信エラーハンドリング
  console.error('Chat error:', error)
  // ...
}
```

注意: `AbortError` 発生時は `return` するが、`finally` ブロックは実行されるため `isLoading` / `isStreaming` のリセットは保証される。

5. `return` に `abort` を追加

```ts
return { messages, isLoading, isStreaming, threadId, sendMessage, abort }
```

### Step 2: `app/components/ChatInput.vue` — 停止ボタンの実装

#### 変更内容

1. props に `isStreaming` を追加

```ts
defineProps<{
  disabled: boolean
  isStreaming: boolean
}>()
```

2. emits に `abort` を追加

```ts
const emit = defineEmits<{
  send: [content: string]
  abort: []
}>()
```

3. テンプレートのボタンを条件分岐

```html
<!-- ストリーミング中: 停止ボタン -->
<button
  v-if="isStreaming"
  type="button"
  class="stop-button"
  @click="emit('abort')"
>
  停止
</button>

<!-- 通常時: 送信ボタン -->
<button
  v-else
  type="submit"
  :disabled="disabled || !input.trim()"
>
  送信
</button>
```

4. 停止ボタン用のスタイルを追加

```css
.chat-input .stop-button {
  padding: 0.75rem 1.5rem;
  background-color: #ef4444;
  color: #fff;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  cursor: pointer;
}
```

設計判断: 停止ボタンは `type="button"` にしてフォーム送信を防ぐ。`disabled` にはしない（常にクリック可能）。赤色 (`#ef4444`) で送信ボタンと視覚的に区別する。

### Step 3: `app/pages/index.vue` — abort の受け渡し

#### 変更内容

1. `useChat()` から `abort` を追加で分割代入

```ts
const { messages, isLoading, isStreaming, sendMessage, abort } = useChat()
```

2. `ChatInput` に `isStreaming` と `@abort` を追加

```html
<ChatInput
  :disabled="isLoading"
  :is-streaming="isStreaming"
  @send="sendMessage"
  @abort="abort"
/>
```

### Step 4: `tests/composables/useChat.test.ts` — テストの修正・追加

#### 既存テストの修正

正常系テストの `fetch` 引数 assertion に `signal` を追加:

```ts
expect(mockFetch).toHaveBeenCalledWith('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'テスト入力', threadId: 'mock-uuid' }),
  signal: expect.any(AbortSignal),
})
```

#### 新規テストケース

```ts
it('abort — ストリーミング中の中断で部分テキストが保持される', async () => {
  // 実際のフロー: fetch が成功 → parseSSEStream 内で reader.read() が AbortError を投げる
  // テストでは parseSSEStream モック内で onToken 後に AbortError を throw してシミュレート
  vi.mocked(parseSSEStream).mockImplementation(async (_stream, callbacks) => {
    callbacks.onToken('部分テ')
    throw new DOMException('The operation was aborted.', 'AbortError')
  })

  mockFetch.mockResolvedValue({
    ok: true,
    body: 'mock-stream',
  })

  const { messages, isLoading, isStreaming, sendMessage } = useChat()

  await sendMessage('テスト')

  // 部分テキストが保持されている（エラー扱いではない）
  expect(messages.value[1].content).toBe('部分テ')
  expect(messages.value[1].isError).toBeUndefined()
  expect(isLoading.value).toBe(false)
  expect(isStreaming.value).toBe(false)
})
```

設計判断: 実際の中断フローでは `fetch` 成功後に `parseSSEStream` 内の `reader.read()` が `AbortError` を throw する。テストでは `parseSSEStream` モック内で `onToken` を呼んだ後に `AbortError` を throw することで、「部分テキスト受信後の中断」を忠実にシミュレートする。`abort()` 関数自体の呼び出しは不要（`AbortController.abort()` → `DOMException` の伝播は DOM API の責務であり、ユニットテストの範囲外）。

## 動作フロー

```
通常時:
  [メッセージを入力...]  [送信]  ← disabled=false, isStreaming=false
  ↓ 送信クリック
  [メッセージを入力...]  [送信]  ← disabled=true (isLoading=true)
  ↓ 最初のトークン受信
  [メッセージを入力...]  [停止]  ← isStreaming=true → 停止ボタンに切替
  ↓ 停止クリック
  abort() → AbortController.abort() → fetch 中断
  ↓ finally ブロック
  [メッセージを入力...]  [送信]  ← isLoading=false, isStreaming=false
```

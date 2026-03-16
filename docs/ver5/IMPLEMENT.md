# ver5 実装計画: SSEエラーハンドリングとエラーUI改善

## 設計方針

### エラー表示方式の決定

**採用**: assistantメッセージ内にエラーを表示する（インライン方式）

- エラー専用の表示領域は設けず、assistantメッセージの `content` にエラーテキストを設定する
- `isError` フラグで通常メッセージと区別し、ChatMessage コンポーネントでスタイルを切り替える
- ストリーミング途中のエラー: 途中テキストを保持し、末尾にエラーメッセージを改行付きで付記する

### 2つのエラー経路の整理

| 経路 | 発生条件 | 処理 |
|---|---|---|
| SSE `error` イベント | サーバー側エラー（OpenAI API障害等） | エラーメッセージをassistantメッセージに設定、ループ脱出 |
| `catch` ブロック | ネットワーク障害、HTTP非200、パースエラー等 | エラーメッセージをassistantメッセージに設定 |

両経路とも最終的にassistantメッセージの `isError = true` を設定し、`content` にエラー情報を含める。

### `done` イベントの処理

`done` イベント受信時に `break` でループを脱出する。現状は `ReadableStream` の終了 (`done: true`) に依存しているが、明示的な `done` 処理により:
- サーバーがストリームをcloseする前に完了を確定できる
- `done` 後に不要なデータが流れても無視できる

---

## 変更1: `app/pages/index.vue` — Message インターフェース拡張

```typescript
interface Message {
  role: 'user' | 'assistant'
  content: string
  isError?: boolean  // 追加
}
```

## 変更2: `app/pages/index.vue` — SSEパーサーのイベントハンドリング追加

現在の `eventType === 'token'` ブロック（59-63行目）の後に `done` と `error` の処理を追加する。

```typescript
// 既存: token イベント処理
if (eventType === 'token' && data) {
  if (!isStreaming.value) isStreaming.value = true
  const parsed = JSON.parse(data)
  assistantMessage.content += parsed.content
}

// 追加: done イベント処理
if (eventType === 'done') {
  break  // while ループを脱出
}

// 追加: error イベント処理
if (eventType === 'error' && data) {
  const parsed = JSON.parse(data)
  const errorText = `\n\n⚠ エラーが発生しました: ${parsed.message}`
  if (assistantMessage.content) {
    assistantMessage.content += errorText
  } else {
    assistantMessage.content = errorText.trimStart()
  }
  assistantMessage.isError = true
  break  // while ループを脱出
}
```

**注意**: `for...of` ループ内の `break` は内側のループしか脱出しないため、`done`/`error` イベントでは外側の `while` ループを脱出する仕組みが必要。フラグ変数 `streamDone` を導入し、`for` ループ後に `if (streamDone) break` を追加する。

```typescript
let streamDone = false

while (true) {
  const { done, value } = await reader.read()
  if (done) break

  buffer += decoder.decode(value, { stream: true })
  const events = buffer.split('\n\n')
  buffer = events.pop()!

  for (const eventStr of events) {
    // ... パース処理 ...

    if (eventType === 'token' && data) {
      if (!isStreaming.value) isStreaming.value = true
      const parsed = JSON.parse(data)
      assistantMessage.content += parsed.content
    }

    if (eventType === 'done') {
      streamDone = true
      break
    }

    if (eventType === 'error' && data) {
      const parsed = JSON.parse(data)
      const errorText = `\n\n⚠ エラーが発生しました: ${parsed.message}`
      if (assistantMessage.content) {
        assistantMessage.content += errorText
      } else {
        assistantMessage.content = errorText.trimStart()
      }
      assistantMessage.isError = true
      streamDone = true
      break
    }
  }

  if (streamDone) break
}
```

## 変更3: `app/pages/index.vue` — catch ブロックの改善

現在の `catch` ブロック（70-75行目）を変更し、空メッセージを削除する代わりにエラーメッセージを表示する。

```typescript
// 現状
catch (error) {
  console.error('Chat error:', error)
  const lastMsg = messages.value[messages.value.length - 1]
  if (lastMsg?.role === 'assistant' && !lastMsg.content) {
    messages.value.pop()
  }
}

// 変更後
catch (error) {
  console.error('Chat error:', error)
  if (!assistantMessage.isError) {
    const errorText = '\n\n⚠ 通信エラーが発生しました。もう一度お試しください。'
    if (assistantMessage.content) {
      assistantMessage.content += errorText
    } else {
      assistantMessage.content = errorText.trimStart()
    }
    assistantMessage.isError = true
  }
}
```

**ポイント**: `!assistantMessage.isError` ガードにより、SSE `error` イベントで既にエラー処理済みの場合は `catch` で二重にエラーメッセージを追加しない。

## 変更4: `app/pages/index.vue` — フォールバックメッセージの調整

67-69行目の空コンテンツフォールバックを、`isError` が設定されていない場合のみに制限する。

```typescript
// 現状
if (!assistantMessage.content) {
  assistantMessage.content = '（応答を取得できませんでした）'
}

// 変更後
if (!assistantMessage.content && !assistantMessage.isError) {
  assistantMessage.content = '（応答を取得できませんでした）'
}
```

## 変更5: `app/components/ChatMessage.vue` — エラースタイルの追加

### Props 追加

```typescript
defineProps<{
  role: 'user' | 'assistant'
  content: string
  isError?: boolean  // 追加
}>()
```

### テンプレート変更

```html
<div class="chat-message" :class="[role, { error: isError }]">
```

### スタイル追加

```css
.chat-message.error {
  background-color: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}
```

## 変更6: `app/pages/index.vue` — ChatMessage への isError props 伝播

テンプレートの ChatMessage 呼び出しに `isError` を追加する。

```html
<ChatMessage
  v-for="(msg, i) in messages"
  :key="i"
  :role="msg.role"
  :content="msg.content"
  :is-error="msg.isError"
/>
```

---

## 変更ファイル一覧

| ファイル | 変更内容 |
|---|---|
| `app/pages/index.vue` | Message型拡張、SSEパーサー改善、catchブロック改善、props伝播 |
| `app/components/ChatMessage.vue` | isError props追加、エラースタイル追加 |

## 影響範囲

- サーバーサイド (`chat.post.ts`) の変更は不要（既に3種のイベントを送信済み）
- 正常系のストリーミング動作に影響なし（既存の `token` 処理はそのまま）
- 新規ファイルの追加なし

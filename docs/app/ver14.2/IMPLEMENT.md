# ver14.2 IMPLEMENT — ストリーミング表示のレンダリング最適化

## 方針

**タイムベーススロットリング方式**を採用する。

ストリーミング中の Markdown レンダリング（`marked.parse()` + `DOMPurify.sanitize()`）を一定間隔（80ms）で間引く。ストリーミング完了時には即座に最終レンダリングを行う。

### 方式選定の理由

| 方式 | 利点 | 欠点 | 判定 |
|---|---|---|---|
| **A. requestAnimationFrame** | ブラウザのフレームレートに自然に合う | ~16ms（60fps）は Markdown パースにはまだ頻繁すぎる | ✗ |
| **B. タイムベーススロットリング** | 間隔を自由に調整可能。80ms で ~12回/秒は滑らかかつ軽量 | タイマー管理が必要 | **✓ 採用** |
| **C. ストリーミング中は生テキスト表示** | 最も軽量 | ストリーミング中のリッチ表示がなくなり UX が低下 | ✗ |

### スロットリング間隔: 80ms

- 80ms = ~12.5 回/秒のレンダリング。テキストの流れが滑らかに見える最低ライン
- 500 トークンのレスポンスで: 500回 → 約40回に削減（~92% 削減）
- 名前付き定数 `RENDER_THROTTLE_MS` として定義し、後から調整可能にする

## 変更対象ファイル

| ファイル | 変更種別 | 概要 |
|---|---|---|
| `app/components/ChatMessage.vue` | 変更 | スロットリングロジック追加 |
| `app/pages/index.vue` | 変更 | `isStreaming` prop の受け渡し |

## 詳細設計

### 1. `app/components/ChatMessage.vue`

#### Props 変更

```typescript
// 変更前
const props = defineProps<{
  role: 'user' | 'assistant'
  content: string
  isError?: boolean
}>()

// 変更後
const props = defineProps<{
  role: 'user' | 'assistant'
  content: string
  isError?: boolean
  isStreaming?: boolean
}>()
```

#### レンダリングロジック変更

現在の `computed` ベースの即時レンダリングを、`ref` + `watch` ベースのスロットリングに置き換える。

```typescript
// 変更前
const renderedHtml = computed(() => {
  if (props.role !== 'assistant') return ''
  const html = marked.parse(props.content) as string
  if (import.meta.client) {
    return DOMPurify.sanitize(html)
  }
  return html
})

// 変更後
const RENDER_THROTTLE_MS = 80

const renderedHtml = ref('')
let throttleTimer: ReturnType<typeof setTimeout> | null = null

function renderMarkdown() {
  const html = marked.parse(props.content) as string
  if (import.meta.client) {
    renderedHtml.value = DOMPurify.sanitize(html)
  } else {
    renderedHtml.value = html
  }
}

// content 変更の監視（スロットリング付き）
watch(() => props.content, () => {
  if (props.role !== 'assistant') return

  if (!props.isStreaming) {
    // ストリーミング中でない: 即時レンダリング（履歴ロード時等）
    if (throttleTimer) {
      clearTimeout(throttleTimer)
      throttleTimer = null
    }
    renderMarkdown()
    return
  }

  // ストリーミング中: スロットリング
  if (!throttleTimer) {
    throttleTimer = setTimeout(() => {
      throttleTimer = null
      renderMarkdown()
    }, RENDER_THROTTLE_MS)
  }
}, { immediate: true })

// ストリーミング終了時: 最終レンダリング
watch(() => props.isStreaming, (current, previous) => {
  if (previous && !current) {
    if (throttleTimer) {
      clearTimeout(throttleTimer)
      throttleTimer = null
    }
    renderMarkdown()
  }
})

// クリーンアップ
onBeforeUnmount(() => {
  if (throttleTimer) {
    clearTimeout(throttleTimer)
  }
})
```

#### 動作の流れ

1. **ストリーミング中**: `content` が毎トークン更新されるが、`renderMarkdown()` は最大 80ms に1回しか実行されない
2. **ストリーミング完了**: `isStreaming` が `false` になった瞬間に即座に最終レンダリングを実行。未処理のタイマーはキャンセル
3. **履歴ロード時**: `isStreaming` が `false` なので即時レンダリング（既存動作を維持）
4. **コンポーネント破棄時**: タイマーをクリーンアップ

### 2. `app/pages/index.vue`

ChatMessage への `isStreaming` prop 追加。最後のメッセージかつ `isStreaming` が `true` の場合のみ渡す。

```vue
<!-- 変更前 -->
<ChatMessage
  v-for="(msg, i) in messages"
  :key="i"
  :role="msg.role"
  :content="msg.content"
  :is-error="msg.isError"
/>

<!-- 変更後 -->
<ChatMessage
  v-for="(msg, i) in messages"
  :key="i"
  :role="msg.role"
  :content="msg.content"
  :is-error="msg.isError"
  :is-streaming="isStreaming && i === messages.length - 1"
/>
```

この条件式の正当性:
- `isStreaming` が `true` の時、ストリーミング中のメッセージは常に `messages` 配列の最後の要素（`useChat.ts` の `sendMessage` で assistant メッセージを末尾に追加してからストリーミング開始）
- それ以外のメッセージには `false` が渡され、即時レンダリング（既存動作）

## 不完全 Markdown の扱い

スロットリングにより Markdown レンダリングの頻度が ~12回/秒に抑えられるため、不完全 Markdown による表示崩れの「ちらつき」は大幅に軽減される。追加の Markdown 修復ロジック（未閉じフェンスの自動閉鎖等）は本バージョンでは実装しない。

理由:
- `marked` は不完全な入力に対してもベストエフォートで HTML を生成する
- スロットリングにより崩れの表示時間が短縮される（最大 80ms 後に次のレンダリングで修正）
- Markdown 修復ロジックはパース前に毎回走るため、新たなパフォーマンスコストになりうる

## 自動スクロールへの影響

`index.vue` の自動スクロールウォッチャーは `messages` の `content.length` を監視しており、毎トークンで発火する。Markdown レンダリングがスロットリングされても、`scrollHeight` は直近のレンダリング結果に基づくため、スクロール追従に若干の遅延（最大 80ms）が生じるが、体感上は問題ない。自動スクロールロジック自体は変更しない。

## テスト方針

ChatMessage.vue のコンポーネントテストは現在存在しない（テスト環境が Node で、コンポーネントテストには happy-dom 環境が必要）。本変更ではスロットリングロジックがコンポーネント内に閉じているため、新規テストファイルの追加は行わない。

既存テストへの影響:
- `tests/composables/useChat.test.ts`: 変更なし（`useChat` に変更がないため）
- その他テスト: 変更なし

品質検証は手動で行う:
- ストリーミング中にテキストが滑らかに流れるか
- ストリーミング完了時に Markdown が正しくレンダリングされるか
- 履歴ロード時に表示が崩れないか
- スレッド切り替え時のクリーンアップが正しく動作するか

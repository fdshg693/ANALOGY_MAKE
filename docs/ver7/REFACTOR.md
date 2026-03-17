# ver7 リファクタリング計画

## 1. SSEパーサーの切り出し

### 対象

`app/pages/index.vue` の `sendMessage()` 内、35〜87行目のSSEパース処理。

### 内容

`app/utils/sse-parser.ts` を新規作成し、ReadableStream を消費してSSEイベントをコールバックで通知する純粋関数として切り出す。

- Vue（ref等）に依存しない純粋な async 関数
- `index.vue` は切り出した関数を呼び出す形に書き換え
- 動作に変更なし（リファクタリングのみ）

### 理由

テスト可能にするため。現状では Vue コンポーネント内にロジックが埋め込まれており、ユニットテストが困難。

## 2. `chat.post.ts` の明示的インポート追加

### 対象

`server/api/chat.post.ts` で auto-import されている h3 関数（`readBody`, `createError`, `defineEventHandler`）と server util（`getAnalogyAgent`）。

### 内容

auto-import に頼っている関数を明示的に import 文として追加する。

```typescript
// 追加するインポート
import { createEventStream, readBody, createError, defineEventHandler } from 'h3'
import { getAnalogyAgent } from '../utils/analogy-agent'
```

### 理由

Vitest から直接 import してテストする際、Nitro の auto-import 解決が効かないため。明示的インポートにすることでテスト時のモック設定が簡潔になる。動作への影響なし。

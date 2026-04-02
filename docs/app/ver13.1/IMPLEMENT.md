# ver13.1 実装計画: サーバーサイドログの追加

## 方針

- `console.log` / `console.warn` / `console.error` ベース（外部ライブラリ不使用）
- モジュール別プレフィックス（`[agent]`, `[chat]`, `[thread]`, `[history]`）でログをフィルタリング可能にする
- 共通のロガーユーティリティを `server/utils/logger.ts` に新規作成し、各モジュールから利用

## 変更対象ファイル

| ファイル | 変更内容 |
|---|---|
| `server/utils/logger.ts` | **新規作成** — ロガーユーティリティ |
| `server/utils/analogy-agent.ts` | エージェント初期化ログ追加 |
| `server/api/chat.post.ts` | チャット API・タイトル生成ログ追加 |
| `server/utils/thread-store.ts` | DB 初期化・スレッド操作ログ追加 |
| `server/api/chat/history.get.ts` | 履歴取得ログ追加 |

`server/api/threads.get.ts` は単純な一覧取得のみのため変更しない。

---

## 1. `server/utils/logger.ts`（新規作成）

モジュール別のプレフィックス付きロガーを提供する。

```typescript
function createLogger(module: string) {
  const prefix = `[${module}]`
  return {
    info: (...args: unknown[]) => console.log(prefix, ...args),
    warn: (...args: unknown[]) => console.warn(prefix, ...args),
    error: (...args: unknown[]) => console.error(prefix, ...args),
  }
}

export const logger = {
  agent: createLogger('agent'),
  chat: createLogger('chat'),
  thread: createLogger('thread'),
  history: createLogger('history'),
}
```

設計判断:
- Nuxt の auto-import により `server/utils/` 内のエクスポートは API Routes から直接利用可能
- ただし、本プロジェクトでは h3 の明示的インポート方針をとっているため（CURRENT.md「h3 明示的インポート」参照）、ロガーも明示的にインポートする

---

## 2. `server/utils/analogy-agent.ts` — エージェント初期化ログ

追加箇所と内容:

### 初期化開始（`getAnalogyAgent()` の `if (!_agent)` ブロック冒頭）

```typescript
logger.agent.info('Initializing agent...')
```

### Tavily ツール構成（tools 配列構築後）

```typescript
if (config.tavilyApiKey) {
  // 既存のツール追加コード
  logger.agent.info('Tavily Search enabled (maxResults: 3)')
} else {
  logger.agent.info('Tavily Search disabled (NUXT_TAVILY_API_KEY not set)')
}
```

### 初期化完了（`createAgent` 呼び出し後）

```typescript
logger.agent.info('Agent initialized', { model: 'gpt-4.1-mini', tools: tools.length, dbPath: DB_PATH })
```

---

## 3. `server/api/chat.post.ts` — チャット API ログ

### リクエスト受信（バリデーション通過後、`getAnalogyAgent()` 呼び出し前）

```typescript
logger.chat.info('Request received', { threadId: body.threadId, messageLength: body.message.length })
```

### ストリーミング開始（`agent.stream()` 呼び出し後）

```typescript
logger.chat.info('Streaming started', { threadId: body.threadId })
```

### ストリーミングループ内 — ツール呼び出し検出（既存の `if` 条件の `else` 分岐に追加）

現在、`AIMessageChunk` 以外のチャンク（`ToolMessage` 等）は無視されている。ツール利用を検出するログを追加する:

```typescript
for await (const [chunk, _metadata] of stream) {
  if (chunk instanceof AIMessageChunk && typeof chunk.content === 'string' && chunk.content) {
    // 既存のトークン送信コード
  } else if (!(chunk instanceof AIMessageChunk)) {
    logger.chat.info('Tool activity detected', { type: chunk.constructor.name, threadId: body.threadId })
  }
}
```

判断: `AIMessageChunk` で `content` が配列型の場合（tool_use ブロック含む）もあるが、これは頻度が高くログノイズになるため、`AIMessageChunk` 以外のメッセージ型（`ToolMessage` など）のみをログ対象とする。

### ストリーミング完了（`done` イベント送信時）

```typescript
logger.chat.info('Streaming completed', { threadId: body.threadId, responseLength: fullResponse.length })
```

### ストリーミングエラー（catch ブロック内）

```typescript
logger.chat.error('Streaming failed', { threadId: body.threadId, error: message })
```

### タイトル生成（`generateTitle` 関数内）

```typescript
// 関数冒頭
logger.chat.info('Title generation started', { threadId })

// 成功時（title が truthy の場合）
logger.chat.info('Title generated', { threadId, title })

// catch ブロック（現在サイレント）
logger.chat.warn('Title generation failed', { threadId, error: e instanceof Error ? e.message : 'Unknown error' })
```

catch ブロックの変更: 現在の空 catch を `catch (e)` に変更し、エラーメッセージをログに出力する。動作（サイレントに失敗してもアプリは継続）は変更しない。

---

## 4. `server/utils/thread-store.ts` — DB・スレッド操作ログ

### DB 初期化（`getDb()` の `if (!_db)` ブロック内）

```typescript
logger.thread.info('Database initialized', { path: DB_PATH, mode: 'WAL' })
```

### `upsertThread()` — スレッド登録/更新

```typescript
logger.thread.info('Thread upserted', { threadId })
```

### `updateThreadTitle()` — タイトル更新

```typescript
logger.thread.info('Thread title updated', { threadId, title })
```

`getThreads()` と `getThreadTitle()` は読み取り専用のため、ログ対象外とする（頻繁に呼ばれるためノイズになる）。

---

## 5. `server/api/chat/history.get.ts` — 履歴取得ログ

### リクエスト受信（バリデーション通過後）

```typescript
logger.history.info('History requested', { threadId })
```

### 取得完了（messages フィルタリング後）

```typescript
logger.history.info('History loaded', { threadId, messageCount: messages.length })
```

### エラー発生（catch ブロック、現在サイレント）

```typescript
logger.history.warn('History load failed', { threadId, error: e instanceof Error ? e.message : 'Unknown error' })
```

現在の空 catch を `catch (e)` に変更し、エラーをログに出力する。動作（空配列を返す）は変更しない。

---

## 出力イメージ

サーバー起動後、初回チャット送信時の想定ログ出力:

```
[thread] Database initialized { path: './data/langgraph-checkpoints.db', mode: 'WAL' }
[agent] Initializing agent...
[agent] Tavily Search enabled (maxResults: 3)
[agent] Agent initialized { model: 'gpt-4.1-mini', tools: 1, dbPath: './data/langgraph-checkpoints.db' }
[chat] Request received { threadId: 'abc-123', messageLength: 42 }
[thread] Thread upserted { threadId: 'abc-123' }
[chat] Streaming started { threadId: 'abc-123' }
[chat] Tool activity detected { type: 'ToolMessage', threadId: 'abc-123' }
[chat] Streaming completed { threadId: 'abc-123', responseLength: 1523 }
[chat] Title generation started { threadId: 'abc-123' }
[chat] Title generated { threadId: 'abc-123', title: '新幹線の騒音対策' }
```

## テスト方針

- 既存テストへの影響: ログ追加は副作用（console 出力）のみで、関数の入出力を変更しないため、既存テストは修正不要
- ログ自体のテスト: 不要（console 出力のテストはコスト対効果が低い）
- `catch (e)` への変更（history.get.ts, chat.post.ts の generateTitle）: 既存テストで catch パスが検証されていれば影響なし。catch の変数追加のみで動作は同一

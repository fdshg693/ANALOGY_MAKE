# ver14.4 IMPLEMENT

事前リファクタリング不要。既存の `logger.ts` インターフェースを拡張する形で対応する。

---

## 1. 永続ログ機能

### 変更対象

`server/utils/logger.ts`（16行 → 約60行に拡張）

### 有効化条件

`process.env.NODE_ENV !== 'production'` の場合にファイル出力を有効化する。追加の環境変数フラグは設けない（開発環境では常に有効）。

### 設計

現在の `createLogger` を拡張し、console出力に加えてファイル書き込みを行う。

**ログファイル**:
- パス: `logs/app-YYYY-MM-DD.log`（日付ローテーション）
- `logs/` ディレクトリは `.gitignore` に追加
- ディレクトリはモジュール初期化時に `mkdirSync` で自動作成

**フォーマット**: JSON Lines（1行1エントリ、後からのパース・検索が容易）

```
{"ts":"2026-04-03T12:00:00.000Z","module":"chat","level":"info","msg":"Request received","ctx":{"threadId":"xxx","messageLength":42}}
```

**書き込み方式**: `fs.appendFileSync` を使用。ログ量は少量（1リクエストあたり数行）なので、非同期ストリームの複雑さは不要。

### 実装詳細

```typescript
import { appendFileSync, mkdirSync } from 'node:fs'

const LOG_DIR = './logs'
const isFileLoggingEnabled = process.env.NODE_ENV !== 'production'

if (isFileLoggingEnabled) {
  mkdirSync(LOG_DIR, { recursive: true })
}

function getLogFilePath(): string {
  const date = new Date().toISOString().slice(0, 10) // YYYY-MM-DD
  return `${LOG_DIR}/app-${date}.log`
}

function writeToFile(module: string, level: string, msg: string, ctx?: Record<string, unknown>) {
  const entry = JSON.stringify({
    ts: new Date().toISOString(),
    module,
    level,
    msg,
    ...(ctx && { ctx }),
  })
  appendFileSync(getLogFilePath(), entry + '\n')
}

function createLogger(module: string) {
  const prefix = `[${module}]`
  return {
    info: (msg: string, ctx?: Record<string, unknown>) => {
      console.log(prefix, msg, ctx ?? '')
      if (isFileLoggingEnabled) writeToFile(module, 'info', msg, ctx)
    },
    warn: (msg: string, ctx?: Record<string, unknown>) => {
      console.warn(prefix, msg, ctx ?? '')
      if (isFileLoggingEnabled) writeToFile(module, 'warn', msg, ctx)
    },
    error: (msg: string, ctx?: Record<string, unknown>) => {
      console.error(prefix, msg, ctx ?? '')
      if (isFileLoggingEnabled) writeToFile(module, 'error', msg, ctx)
    },
  }
}
```

**シグネチャ変更**: 現在の `(...args: unknown[])` から `(msg: string, ctx?: Record<string, unknown>)` に変更する。既存の呼び出し箇所はすべてこの形式で使用されているため（例: `logger.chat.info('Request received', { threadId: body.threadId })`）、互換性の問題はない。

### 追加ログポイント

履歴不具合の調査に必要な情報を追加で記録する:

**`history.get.ts`** に追加:
- `rawMessages` の件数と各メッセージの型名（`constructor.name`）を記録
- `isInstance` フィルタリング前後の件数差を記録

```typescript
logger.history.info('Raw messages from snapshot', {
  threadId,
  count: rawMessages.length,
  types: rawMessages.map((m: any) => m?.constructor?.name ?? typeof m),
})
```

---

## 2. SQLite 調査CLIツール

### 新規ファイル

`experiments/inspect-db.ts`

### 使用方法

```bash
npx tsx experiments/inspect-db.ts threads                # スレッド一覧
npx tsx experiments/inspect-db.ts history <threadId>      # メッセージ履歴の整形表示
npx tsx experiments/inspect-db.ts checkpoints <threadId>  # チェックポイント一覧（生データ）
```

### 依存

`better-sqlite3`（既存依存）と `tsx`（既存devDependency）のみ。新規ライブラリ不要。

### 実装詳細

```typescript
import Database from 'better-sqlite3'

const DB_PATH = './data/langgraph-checkpoints.db'

function main() {
  const [command, arg] = process.argv.slice(2)
  const db = new Database(DB_PATH, { readonly: true })

  switch (command) {
    case 'threads':
      listThreads(db)
      break
    case 'history':
      if (!arg) { console.error('Usage: history <threadId>'); process.exit(1) }
      showHistory(db, arg)
      break
    case 'checkpoints':
      if (!arg) { console.error('Usage: checkpoints <threadId>'); process.exit(1) }
      showCheckpoints(db, arg)
      break
    default:
      console.log('Commands: threads, history <threadId>, checkpoints <threadId>')
  }

  db.close()
}
```

**`threads` コマンド**: `threads` テーブルから全スレッドを取得し、テーブル形式で表示。

**`history` コマンド**:
1. `checkpoints` テーブルから該当 threadId の最新チェックポイントを取得
2. `checkpoint` BLOB を JSON パースし `channel_values.messages` を抽出
3. 各メッセージの `type`（human/ai）と `content` を整形表示

```typescript
function showHistory(db: Database.Database, threadId: string) {
  const row = db.prepare(
    `SELECT checkpoint, type FROM checkpoints
     WHERE thread_id = ? AND checkpoint_ns = ''
     ORDER BY checkpoint_id DESC LIMIT 1`
  ).get(threadId) as { checkpoint: Buffer; type: string } | undefined

  if (!row) { console.log('No checkpoints found'); return }

  const data = JSON.parse(row.checkpoint.toString())
  const messages = data.channel_values?.messages ?? []

  for (const msg of messages) {
    const role = msg.type === 'human' ? 'USER' : 'AI'
    const content = typeof msg.content === 'string'
      ? msg.content.slice(0, 200)
      : JSON.stringify(msg.content).slice(0, 200)
    console.log(`[${role}] ${content}`)
    console.log('---')
  }
}
```

**`checkpoints` コマンド**: 指定 threadId の全チェックポイントを時系列で表示。各チェックポイントのID・タイムスタンプ・メタデータ（source, step）を表示。

---

## 3. `.gitignore` 更新

`logs/` を `.gitignore` に追加する。

---

## 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---|---|---|
| `server/utils/logger.ts` | 修正 | ファイル出力機能を追加 |
| `server/api/chat/history.get.ts` | 修正 | デバッグ用ログポイント追加 |
| `experiments/inspect-db.ts` | 新規 | SQLite調査CLIツール |
| `.gitignore` | 修正 | `logs/` を追加 |

## リスク・不確実性

- **チェックポイントのBLOB形式**: `@langchain/langgraph-checkpoint-sqlite` の内部シリアライゼーション形式に依存する。メジャーバージョンアップ時にフォーマットが変わる可能性があるが、現時点ではJSON形式であることを確認済み。CLIツール側で読み取りエラー時のフォールバック（生バイナリのhex表示）を設ける。

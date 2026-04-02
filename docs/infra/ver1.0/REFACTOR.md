# ver1.0 リファクタリング計画

## R1: DB パス定義の共通化

### 背景

`DB_PATH` と `mkdirSync` のディレクトリ作成が `analogy-agent.ts` と `thread-store.ts` の2箇所に重複している。
本番環境向けのパス切り替えを導入する際に、片方だけ修正する見落としリスクがある。

### 対象ファイル

| ファイル | 現状 |
|---|---|
| `server/utils/analogy-agent.ts` | `const DB_PATH = './data/langgraph-checkpoints.db'` + `mkdirSync('./data', ...)` |
| `server/utils/thread-store.ts` | `const DB_PATH = './data/langgraph-checkpoints.db'` + `mkdirSync('./data', ...)` |

### 変更内容

新規ファイル `server/utils/db-config.ts` を作成し、DB パスとディレクトリ初期化を一元管理する:

```typescript
import { mkdirSync } from 'node:fs'
import { dirname } from 'node:path'

const DB_DIR = process.env.NODE_ENV === 'production'
  ? '/home/data'
  : './data'

export const DB_PATH = `${DB_DIR}/langgraph-checkpoints.db`

// ディレクトリが存在しない場合に作成（起動時1回のみ）
mkdirSync(DB_DIR, { recursive: true })
```

`analogy-agent.ts` と `thread-store.ts` から `DB_PATH` 定義と `mkdirSync` 呼び出しを削除し、`db-config.ts` からインポートする。

### リスク

- 低: 変更箇所は定数の移動のみ。ロジックの変更なし
- `mkdirSync` がモジュール読み込み時に実行されるが、Nitro のサーバー初期化フローでは問題なし（現在も関数呼び出し時に毎回実行されている）

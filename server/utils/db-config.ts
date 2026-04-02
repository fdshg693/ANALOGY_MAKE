import { mkdirSync } from 'node:fs'

const DB_DIR = process.env.NODE_ENV === 'production'
  ? '/home/data'
  : './data'

export const DB_PATH = `${DB_DIR}/langgraph-checkpoints.db`

// ディレクトリが存在しない場合に作成（起動時1回のみ）
mkdirSync(DB_DIR, { recursive: true })

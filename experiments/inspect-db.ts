import Database from 'better-sqlite3'

const DB_PATH = './data/langgraph-checkpoints.db'

function listThreads(db: Database.Database) {
  const rows = db.prepare('SELECT * FROM threads ORDER BY updated_at DESC').all()
  if (rows.length === 0) {
    console.log('No threads found')
    return
  }
  console.table(rows)
}

function showHistory(db: Database.Database, threadId: string) {
  const row = db.prepare(
    `SELECT checkpoint FROM checkpoints
     WHERE thread_id = ? AND checkpoint_ns = ''
     ORDER BY checkpoint_id DESC LIMIT 1`
  ).get(threadId) as { checkpoint: Buffer } | undefined

  if (!row) {
    console.log('No checkpoints found')
    return
  }

  try {
    const data = JSON.parse(row.checkpoint.toString())
    const messages = data.channel_values?.messages ?? []

    if (messages.length === 0) {
      console.log('No messages in checkpoint')
      return
    }

    for (const msg of messages) {
      const role = msg.type === 'human' ? 'USER' : 'AI'
      const content = typeof msg.content === 'string'
        ? msg.content.slice(0, 200)
        : JSON.stringify(msg.content).slice(0, 200)
      console.log(`[${role}] ${content}`)
      console.log('---')
    }
  } catch {
    console.error('Failed to parse checkpoint data. Raw hex (first 200 bytes):')
    console.log(row.checkpoint.subarray(0, 200).toString('hex'))
  }
}

function showCheckpoints(db: Database.Database, threadId: string) {
  const rows = db.prepare(
    `SELECT checkpoint_id, checkpoint_ns, type, metadata
     FROM checkpoints
     WHERE thread_id = ?
     ORDER BY checkpoint_id ASC`
  ).all(threadId) as { checkpoint_id: string; checkpoint_ns: string; type: string; metadata: string }[]

  if (rows.length === 0) {
    console.log('No checkpoints found')
    return
  }

  for (const row of rows) {
    let meta: Record<string, unknown> = {}
    try { meta = JSON.parse(row.metadata) } catch { /* ignore */ }
    console.log(`ID: ${row.checkpoint_id} | NS: ${row.checkpoint_ns || '(root)'} | Type: ${row.type}`)
    console.log(`  source: ${meta.source ?? 'N/A'} | step: ${meta.step ?? 'N/A'}`)
    console.log('---')
  }
}

function main() {
  const [command, arg] = process.argv.slice(2)
  const db = new Database(DB_PATH, { readonly: true })

  try {
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
  } finally {
    db.close()
  }
}

main()

import { appendFileSync, mkdirSync } from 'node:fs'

const LOG_DIR = './logs'
const isFileLoggingEnabled = process.env.NODE_ENV !== 'production'

if (isFileLoggingEnabled) {
  mkdirSync(LOG_DIR, { recursive: true })
}

function getLogFilePath(): string {
  const date = new Date().toISOString().slice(0, 10)
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

export const logger = {
  agent: createLogger('agent'),
  chat: createLogger('chat'),
  thread: createLogger('thread'),
  history: createLogger('history'),
}

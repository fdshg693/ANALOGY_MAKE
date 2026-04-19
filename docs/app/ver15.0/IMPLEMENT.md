# ver15.0 IMPLEMENT — 動的設定システム & AI回答粒度切り替え

事前リファクタリング不要。現在のアーキテクチャ（ノード別プロンプト定数 + StateGraph + thread-store シングルトン）は、設定の動的注入にそのまま対応可能。

## 変更対象ファイル一覧

| ファイル | 種別 | 概要 |
|---|---|---|
| `server/utils/thread-store.ts` | 変更 | `settings` カラム追加、設定 CRUD 関数追加 |
| `server/api/threads/[id]/settings.get.ts` | 新規 | スレッド設定取得 API |
| `server/api/threads/[id]/settings.put.ts` | 新規 | スレッド設定更新 API |
| `server/utils/analogy-prompt.ts` | 変更 | `buildSystemPrompt()` ヘルパー追加 |
| `server/utils/analogy-agent.ts` | 変更 | ノード関数に config パラメータ追加、設定に基づくプロンプト構築 |
| `server/api/chat.post.ts` | 変更 | 設定読み込み → configurable 経由で渡す |
| `app/composables/useSettings.ts` | 新規 | スレッド設定の状態管理 |
| `app/components/SettingsPanel.vue` | 新規 | 設定パネル UI |
| `app/pages/index.vue` | 変更 | 設定ボタン・設定パネル統合 |
| テストファイル（複数） | 新規/変更 | 各変更のテスト |

## 型定義

`server/utils/thread-store.ts` に追加:

```typescript
export interface ThreadSettings {
  granularity: 'concise' | 'standard' | 'detailed'
  customInstruction: string
}

export const DEFAULT_SETTINGS: ThreadSettings = {
  granularity: 'standard',
  customInstruction: '',
}
```

## 1. バックエンド: 設定ストレージ

### `server/utils/thread-store.ts`

#### DB スキーマ変更

`getDb()` 内で `ALTER TABLE` を実行して `settings` カラムを追加する。SQLite の `ALTER TABLE ADD COLUMN` は既存テーブルに安全に適用できる（カラムが存在しなければ追加、既存なら無視）。

```typescript
// getDb() 内、CREATE TABLE の後に追加
try {
  _db.exec(`ALTER TABLE threads ADD COLUMN settings TEXT NOT NULL DEFAULT '{}'`)
} catch {
  // カラム既存なら無視（SQLite は IF NOT EXISTS をサポートしない）
}
```

#### 新規関数

```typescript
/** スレッド設定を取得（未設定ならデフォルト値） */
export function getThreadSettings(threadId: string): ThreadSettings {
  const db = getDb()
  const row = db.prepare('SELECT settings FROM threads WHERE thread_id = ?').get(threadId) as { settings: string } | undefined
  if (!row?.settings || row.settings === '{}') return { ...DEFAULT_SETTINGS }
  try {
    return { ...DEFAULT_SETTINGS, ...JSON.parse(row.settings) }
  } catch {
    return { ...DEFAULT_SETTINGS }
  }
}

/** スレッド設定を更新 */
export function updateThreadSettings(threadId: string, settings: ThreadSettings): void {
  const db = getDb()
  db.prepare("UPDATE threads SET settings = ?, updated_at = datetime('now') WHERE thread_id = ?")
    .run(JSON.stringify(settings), threadId)
  logger.thread.info('Thread settings updated', { threadId })
}
```

### `server/api/threads/[id]/settings.get.ts`（新規）

```typescript
// GET /api/threads/:id/settings
export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id is required' })
  return getThreadSettings(id)
})
```

### `server/api/threads/[id]/settings.put.ts`（新規）

```typescript
// PUT /api/threads/:id/settings
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id is required' })
  const body = await readBody(event)
  // バリデーション: granularity は 'concise' | 'standard' | 'detailed' のみ許可
  const validGranularity = ['concise', 'standard', 'detailed']
  const granularity = validGranularity.includes(body.granularity) ? body.granularity : 'standard'
  const customInstruction = typeof body.customInstruction === 'string' ? body.customInstruction.slice(0, 500) : ''
  const settings: ThreadSettings = { granularity, customInstruction }
  updateThreadSettings(id, settings)
  return settings
})
```

`customInstruction` は 500 文字上限（プロンプトインジェクション対策として過度に長い入力を防止）。

## 2. バックエンド: 動的プロンプト注入

### `server/utils/analogy-prompt.ts`

既存の4定数（`ABSTRACTION_PROMPT`, `CASE_SEARCH_PROMPT`, `SOLUTION_PROMPT`, `FOLLOWUP_PROMPT`）はそのまま維持。新たに `buildSystemPrompt()` ヘルパーを追加する。

```typescript
import type { ThreadSettings } from './thread-store'

const GRANULARITY_INSTRUCTIONS: Record<string, string> = {
  concise: '\n\n## 回答スタイル\n簡潔に箇条書きで回答してください。要点のみを述べ、冗長な説明は避けてください。',
  detailed: '\n\n## 回答スタイル\n具体例と背景説明を含めて詳しく回答してください。',
}

/** ベースプロンプトに粒度設定・カスタム指示を付加する */
export function buildSystemPrompt(basePrompt: string, settings?: ThreadSettings): string {
  if (!settings) return basePrompt
  let prompt = basePrompt
  const instruction = GRANULARITY_INSTRUCTIONS[settings.granularity]
  if (instruction) prompt += instruction
  const custom = settings.customInstruction?.trim()
  if (custom) prompt += `\n\n## 追加指示\n${custom}`
  return prompt
}
```

- `standard` はエントリなし → ベースプロンプトのまま
- `abstraction` ノードにはスタイル指示を適用しない（抽象化は常に簡潔であるべきため）

### `server/utils/analogy-agent.ts`

ノード関数に `config` パラメータ（`RunnableConfig`）を追加し、`config.configurable?.settings` から設定を読み取る。

```typescript
import type { RunnableConfig } from '@langchain/core/runnables'
import { buildSystemPrompt } from './analogy-prompt'

// abstraction ノードは粒度設定を適用しない（常に簡潔に抽象化）
async function abstractionNode(state: typeof AnalogyState.State) {
  // 変更なし
}

async function caseSearchNode(state: typeof AnalogyState.State, config: RunnableConfig) {
  const settings = config?.configurable?.settings as ThreadSettings | undefined
  // ...
  const fullSystemPrompt = buildSystemPrompt(
    `${CASE_SEARCH_PROMPT}\n\n${contextMessage}`,
    settings
  )
  // ...
}

async function solutionNode(state: typeof AnalogyState.State, config: RunnableConfig) {
  const settings = config?.configurable?.settings as ThreadSettings | undefined
  const model = getModel()
  const result = await model.invoke([
    { role: "system", content: buildSystemPrompt(SOLUTION_PROMPT, settings) },
    ...state.messages,
  ])
  // ...
}

async function followUpNode(state: typeof AnalogyState.State, config: RunnableConfig) {
  const settings = config?.configurable?.settings as ThreadSettings | undefined
  const model = getModel()
  const result = await model.invoke([
    { role: "system", content: buildSystemPrompt(FOLLOWUP_PROMPT, settings) },
    ...state.messages,
  ])
  // ...
}
```

### `server/api/chat.post.ts`

`stream()` 呼び出し前に設定を読み込み、`configurable` に含める。

```typescript
import { getThreadSettings } from '../utils/thread-store'

// stream 呼び出し時
const settings = getThreadSettings(body.threadId)

const stream = await agent.stream(
  { messages: [new HumanMessage(body.message)] },
  {
    configurable: {
      thread_id: body.threadId,
      settings,  // 追加
    },
    streamMode: "messages",
  },
)
```

## 3. フロントエンド

### `app/composables/useSettings.ts`（新規）

```typescript
export interface ThreadSettings {
  granularity: 'concise' | 'standard' | 'detailed'
  customInstruction: string
}

const DEFAULT_SETTINGS: ThreadSettings = {
  granularity: 'standard',
  customInstruction: '',
}

export function useSettings() {
  const settings = ref<ThreadSettings>({ ...DEFAULT_SETTINGS })
  const isSaving = ref(false)
  let currentThreadId = ''

  async function loadSettings(threadId: string): Promise<void> {
    currentThreadId = threadId
    if (!threadId) {
      settings.value = { ...DEFAULT_SETTINGS }
      return
    }
    try {
      const data = await $fetch<ThreadSettings>(`/api/threads/${threadId}/settings`)
      settings.value = data
    } catch {
      settings.value = { ...DEFAULT_SETTINGS }
    }
  }

  async function saveSettings(): Promise<void> {
    if (!currentThreadId) return
    isSaving.value = true
    try {
      await $fetch(`/api/threads/${currentThreadId}/settings`, {
        method: 'PUT',
        body: settings.value,
      })
    } finally {
      isSaving.value = false
    }
  }

  return { settings, isSaving, loadSettings, saveSettings }
}
```

- `$fetch` は Nuxt の組み込みユーティリティ（auto-import される）
- `loadSettings` はスレッド切り替え時に呼ばれる
- `saveSettings` は設定変更時に明示的に呼ばれる（自動保存ではなく、ユーザーが変更 → 保存ボタンで確定）

### `app/components/SettingsPanel.vue`（新規）

Props: `settings: ThreadSettings`, `isSaving: boolean`
Emits: `update:settings`, `save`

#### Emit タイミング

- `update:settings`: プリセットボタンクリック時・カスタム指示入力時に即時 emit（ローカル状態を親に反映）
- `save`: 保存ボタンクリック時に emit（サーバーへの永続化をトリガー）

#### UI 構成

```
┌─ 設定パネル ─────────────────────────┐
│ 回答粒度: [簡潔] [標準●] [詳細]      │
│                                       │
│ カスタム指示:                         │
│ ┌─────────────────────────────────┐   │
│ │                                 │   │
│ └─────────────────────────────────┘   │
│                            [保存]     │
└───────────────────────────────────────┘
```

- プリセットボタン: 3つの `<button>` で選択状態を視覚的に表示（アクティブ: 青背景）
- カスタム指示: `<textarea>`（2〜3行、placeholder: 「例: 英語で回答して」）
- 保存ボタン: 設定をサーバーに送信
- Scoped CSS でスタイリング

### `app/pages/index.vue`

#### 変更点

1. **ヘッダーに設定ボタン追加**: `<h1>Analogy AI</h1>` の右に歯車ボタン
2. **設定パネルのトグル表示**: `showSettings` ref で開閉制御
3. **`useSettings()` の統合**: スレッド切り替え時に `loadSettings()` も呼ぶ

```html
<header class="chat-header">
  <h1>Analogy AI</h1>
  <button class="settings-toggle" @click="showSettings = !showSettings">
    &#9881;
  </button>
</header>

<SettingsPanel
  v-if="showSettings"
  :settings="settings"
  :is-saving="isSaving"
  @update:settings="settings = $event"
  @save="saveSettings"
/>
```

スレッド切り替え・新規作成時:
```typescript
function handleSelectThread(threadId: string) {
  setActiveThread(threadId)
  switchThread(threadId)
  loadSettings(threadId)  // 追加
}

function handleNewThread() {
  const newId = createNewThread()
  switchThread(newId)
  loadSettings(newId)  // 追加（前のスレッドの設定残留を防止）
}
```

## 4. テスト

### 新規テスト

| ファイル | 内容 |
|---|---|
| `tests/server/thread-settings.test.ts` | `getThreadSettings`, `updateThreadSettings` の CRUD テスト |
| `tests/server/settings-api.test.ts` | settings GET/PUT API のバリデーション・正常系テスト |
| `tests/server/prompt-builder.test.ts` | `buildSystemPrompt()` の各粒度・カスタム指示の結合テスト |

### 既存テスト変更

| ファイル | 変更内容 |
|---|---|
| `tests/server/chat.test.ts` | `configurable` に `settings` が含まれることの確認 |

## リスク・不確実性

### LangGraph ノード関数の config パラメータ

LangGraph.js のノード関数は `(state, config: RunnableConfig)` のシグネチャで `config` を受け取れるが、`configurable` に任意のカスタムキー（`settings`）を含めた場合の挙動を実装時に検証する必要がある。`thread_id` と同列に渡すため、チェックポイント機構との干渉がないかを確認する。

**リスク低**: `configurable` は辞書型であり、LangGraph は `thread_id` を読み取るがそれ以外のキーは無視する設計。ただし、LangGraph 側で `configurable` のスキーマバリデーションが追加された場合に壊れる可能性がある。

**対策**: 実装時に `settings` を `configurable` に含めてストリーム実行し、正常動作を確認する。問題があれば、node 関数内で直接 `getThreadSettings()` を呼ぶフォールバックに切り替える。

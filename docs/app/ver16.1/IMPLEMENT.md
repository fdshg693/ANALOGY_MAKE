# ver16.1 IMPLEMENT — 動作確認便利化（エコーモード + システムプロンプト上書き）

## 0. 方針サマリ

2 つの機能を同一バージョンで実装する:

1. **エコーモード**: `ThreadSettings.responseMode = 'ai' | 'echo'` を追加。`echo` のとき `chat.post.ts` で LangGraph をバイパスし、ユーザー入力を小分けに SSE 配信、かつ `agent.updateState()` でチェックポインターに永続化
2. **システムプロンプト上書き**: `ThreadSettings.systemPromptOverride: string` を追加。`buildSystemPrompt()` がベースプロンプトの先頭に追記する。**開発環境のみ有効**（サーバー側 `process.env.NODE_ENV !== 'production'` で最終判定、Vitest で `vi.stubEnv` により制御可能）

事前リファクタリングなし（既存 `ThreadSettings` JSON 方式・`buildSystemPrompt()` シグネチャがそのまま使える）。

## 1. データモデル変更

### 1.1 `server/utils/thread-store.ts`

`ThreadSettings` インターフェースに 2 フィールドを追加:

```typescript
export type ResponseMode = 'ai' | 'echo'

export interface ThreadSettings {
  granularity: 'concise' | 'standard' | 'detailed'
  customInstruction: string
  search: SearchSettings
  // ver16.1 追加
  responseMode: ResponseMode
  systemPromptOverride: string
}
```

`DEFAULT_SETTINGS` を更新:

```typescript
export const DEFAULT_SETTINGS: ThreadSettings = {
  granularity: 'standard',
  customInstruction: '',
  search: { ...DEFAULT_SEARCH_SETTINGS },
  responseMode: 'ai',
  systemPromptOverride: '',
}
```

`getThreadSettings()` の段階マージも `responseMode` / `systemPromptOverride` のフォールバックを含むよう更新（既存のスプレッドで自動フォールバック、型のみ追加）。

**マイグレーション戦略**: `getThreadSettings()` は既存スレッドの JSON を `Partial<ThreadSettings>` として扱い、不足フィールドは `DEFAULT_SETTINGS` から補完する。SQLite のスキーマ変更は不要（`settings TEXT` は JSON 文字列のまま）。

### 1.2 `app/composables/useSettings.ts`

同じ 2 フィールドをフロント側の型に追加。デフォルト値も一致させる（ver16.0 までの流儀通り、サーバー/クライアントで型重複定義）。

## 2. バリデーション（サーバー側）

### 2.1 `server/api/threads/[id]/settings.put.ts`

```typescript
const validResponseMode = ['ai', 'echo']
const responseMode: ResponseMode = validResponseMode.includes(body.responseMode)
  ? body.responseMode
  : 'ai'

// 本番環境では systemPromptOverride を常に空文字に正規化（UI 迂回防止）
const isDev = process.env.NODE_ENV !== 'production'
const systemPromptOverride = isDev && typeof body.systemPromptOverride === 'string'
  ? body.systemPromptOverride.slice(0, 2000)
  : ''

const settings: ThreadSettings = {
  granularity,
  customInstruction,
  search,
  responseMode,
  systemPromptOverride,
}
```

**決定事項**:

- `systemPromptOverride` の最大長: **2000 文字**（`customInstruction` の 500 文字より長め。システムプロンプト丸ごと貼り付けを想定）
- 本番で `systemPromptOverride` を送信された場合: **黙殺**（エラーにはせず、空文字で保存）。クライアント側の UI 非表示と合わせた二重防御
- 不正な `responseMode` 値: デフォルト `'ai'` にフォールバック（`granularity` と同じ流儀）
- **環境判定**: `process.env.NODE_ENV !== 'production'` を採用。理由は下記 3.2 参照

## 3. プロンプト上書き

### 3.1 `server/utils/analogy-prompt.ts`

`buildSystemPrompt()` のシグネチャを拡張（`systemPromptOverride` は**オプショナル**で追加）:

```typescript
export function buildSystemPrompt(
  basePrompt: string,
  settings?: Pick<ThreadSettings, 'granularity' | 'customInstruction'> & {
    systemPromptOverride?: string
  },
): string {
  if (!settings) return basePrompt
  let prompt = basePrompt

  // 粒度 → カスタム指示（既存）
  const instruction = GRANULARITY_INSTRUCTIONS[settings.granularity]
  if (instruction) prompt += instruction
  const custom = settings.customInstruction?.trim()
  if (custom) prompt += `\n\n## 追加指示\n${custom}`

  // ver16.1: システムプロンプト上書き（dev のみ）
  const override = settings.systemPromptOverride?.trim()
  if (process.env.NODE_ENV !== 'production' && override) {
    prompt = `${override}\n\n---\n\n${prompt}`
  }

  return prompt
}
```

**決定事項**:

- **配置**: ベースプロンプトの**先頭**に追記（ROUGH_PLAN 準拠）。区切りに `\n\n---\n\n` を挟む
- **dev ガード**: `process.env.NODE_ENV !== 'production'` で最終判定。サーバー側で有効なのでクライアント側での改変では迂回不能
- **既存 `settings?` 型パラメータの拡張**: `systemPromptOverride` は**オプショナル**で追加。呼び出し元（`analogy-agent.ts` の各ノード）は `settings` 全体を渡しているため型互換、かつ `prompt-builder.test.ts` の既存テスト（`{ granularity, customInstruction }` の 2 フィールド渡し）も型エラーにならない

### 3.2 環境判定方式の決定（サーバー側・フロント側で使い分け）

| 場所 | 採用する判定 | 理由 |
|---|---|---|
| サーバー側（`settings.put.ts`, `analogy-prompt.ts`） | `process.env.NODE_ENV !== 'production'` | Vitest の Node 環境で `vi.stubEnv('NODE_ENV', 'production')` により制御可能。既存テストパターンと整合。Nitro `node-server` プリセットでも `NODE_ENV` は Azure App Service 側で `production` が注入される |
| フロント側（`SettingsPanel.vue`） | `import.meta.dev` | Vite のビルド時定数。production ビルドで `false` に置き換えられテンプレート側から UI が消える。フロント側はテストしない（観点 7 再掲）ため `import.meta.dev` のテスト制御問題は発生しない |

**サーバー側で `import.meta.dev` を避ける理由**: `analogy-prompt.ts` は純粋な TypeScript ユーティリティとして Vitest の Node 環境から直接 import される。`import.meta.dev` は Vite/Nitro のビルドパイプライン経由でなければ `undefined` になり、かつ Vitest では `import.meta` はモジュール固有のため `vi.stubGlobal` では制御できない。テストで production 挙動を確認する「本番では上書きスキップ」ケースが成立しないため、`process.env.NODE_ENV` に統一する。

**フロント側 UI のみ `import.meta.dev` を使う理由**: SettingsPanel のテストは書かない方針（観点 7）なので制御問題は発生せず、Vite のビルド時定数として `v-if="isDev"` が production ビルドで DOM から完全に除去される利点（tree-shaking）を優先する。

## 4. エコーモード

### 4.1 `server/api/chat.post.ts`

`upsertThread(body.threadId)` の後、`getThreadSettings()` で分岐:

```typescript
// 既存: upsertThread はエコー・AI 両方で呼ばれる（この位置を変更しない）
upsertThread(body.threadId)

const settings = getThreadSettings(body.threadId)

if (settings.responseMode === 'echo') {
  await handleEchoResponse(body.threadId, body.message, eventStream)
  return
}

// 既存: agent.stream(...) パス
```

**重要**: `upsertThread` は分岐前（既存コードの 24 行目）で呼ばれ続けるため、エコーモードでもスレッドの `updated_at` は更新される。エコー分岐内で再度呼ぶ必要はない。

### 4.2 `handleEchoResponse` ヘルパ（同ファイル内 or `server/utils/echo-response.ts`）

```typescript
async function handleEchoResponse(
  threadId: string,
  userMessage: string,
  eventStream: ReturnType<typeof createEventStream>,
): Promise<void> {
  try {
    // 1. token SSE を小分けに配信（ストリーミング体験を再現）
    const chunks = chunkText(userMessage, 8)  // 8文字単位
    for (const chunk of chunks) {
      await eventStream.push({ event: 'token', data: JSON.stringify({ content: chunk }) })
      await sleep(30)  // 30ms 間隔
    }

    // 2. チェックポインターへ永続化（通常フローと同様に履歴として残る）
    const agent = await getAnalogyAgent()
    await agent.updateState(
      { configurable: { thread_id: threadId } },
      { messages: [new HumanMessage(userMessage), new AIMessage(userMessage)] },
    )

    // 3. done 配信
    await eventStream.push({ event: 'done', data: '{}' })

    // 4. タイトル生成は既存ロジックに揃える（エコーでも初回ならタイトル生成）
    //   → エコーの場合は AI 呼び出しをスキップし、ユーザー入力の先頭10文字をタイトルにする軽量版
    const currentTitle = getThreadTitle(threadId)
    if (currentTitle === '新しいチャット' || currentTitle === null) {
      updateThreadTitle(threadId, userMessage.slice(0, 10))
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    logger.chat.error('Echo response failed', { threadId, error: message })
    await eventStream.push({ event: 'error', data: JSON.stringify({ message }) })
  }
}

function chunkText(text: string, size: number): string[] {
  const chunks: string[] = []
  for (let i = 0; i < text.length; i += size) chunks.push(text.slice(i, i + size))
  return chunks.length ? chunks : ['']
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
```

### 4.3 決定事項

| 項目 | 決定 | 理由 |
|---|---|---|
| 永続化方式 | `agent.updateState()` で `[HumanMessage, AIMessage]` を追加 | 既存の `SqliteSaver` を再利用、`history.get.ts` が変更不要 |
| チャンク単位 | 8 文字固定（日本語で 2〜4 語相当） | 見た目のストリーミング感が出る最小粒度。LLM token 感に近い |
| 間隔 | 30 ms | 100 文字の入力で約 400ms。人間の入力速度より速く、UI 確認に十分 |
| 検索結果 | 配信しない | ROUGH_PLAN 通り、エコーモードは検索 OFF 相当 |
| タイトル自動生成 | エコー時は LLM を使わず入力先頭 10 文字を流用 | AI 呼び出しゼロのポリシーを守る |
| `currentStep` の扱い | `updateState` で変更しない（既存 state を維持） | AI モードに戻したとき整合性を保つ（途中スレッドでエコーを使っても次回 AI 応答が破綻しない） |

### 4.4 リスク・不確実性

- **R1: `agent.updateState()` の仕様 + SQLite 往復での型復元**: LangGraph の `updateState` API で `messagesStateReducer` 経由で `HumanMessage`/`AIMessage` を追加できるかはプロジェクト未使用。さらに `additional-kwargs-sqlite` ISSUE が示す通り、SQLite から復元したメッセージの `.type` プロパティが `'human'` / `'ai'` として正しく戻るかも未検証（`history.get.ts` はこれに依存）
  - **検証タイミング**: 実装ステップ 4 完了後に dev サーバーで 1 往復確認（「エコーで 1 回送信 → リロード → 履歴に表示される」）
  - **フォールバック**: 動かない場合、エコーモードを「永続化なし・純粋 SSE 返却」に切り替える（`agent.updateState` 呼び出しを削除）
  - **フォールバック時のユーザー影響**: エコー送信中は UI に表示されるが、**ページリロード後に該当会話が消える**（`history.get.ts` から読み出されない）。これは UI 動作確認の用途では許容範囲（デプロイ確認後にブラウザを閉じれば消えて良い一時的な履歴）。ただし混乱を避けるため、フォールバック採用時は設定パネルに「エコーモード: リロードで消えます」の注記を追加、かつ新 ISSUE を起票
  - **判定基準**: dev 1 往復で履歴復元が成功 → フォールバック不要。失敗 → 即フォールバック（ver16.1 内で対応、追加の調査バージョンは切らない）
- **R2: `responseMode` を途中で切り替えたときの挙動**: `currentStep` が `awaiting_selection` のときにエコーモード→AI モードで戻ると、ユーザーの「選択」として扱われて solution ノードが走る可能性がある
  - **対応**: テスト側で「エコー送信 → AI で新規会話を続ける」フローを 1 ケース追加して期待挙動を明示
  - **ドキュメント**: MEMO.md に注意書き（「エコーで会話を続けると LangGraph の currentStep がユーザーメッセージ上で停滞する」）

## 5. フロントエンド

### 5.1 `app/components/SettingsPanel.vue`

2 セクション追加:

```vue
<!-- 応答モード -->
<div class="settings-section">
  <label class="settings-label">応答モード:</label>
  <div class="granularity-buttons">
    <button
      v-for="opt in responseModeOptions"
      :key="opt.value"
      :class="['granularity-btn', { active: settings.responseMode === opt.value }]"
      @click="selectResponseMode(opt.value)"
    >
      {{ opt.label }}
    </button>
  </div>
</div>

<!-- システムプロンプト上書き（開発環境のみ） -->
<div v-if="isDev" class="settings-section">
  <label class="settings-label">システムプロンプト上書き（開発のみ）:</label>
  <textarea
    class="custom-instruction"
    :value="settings.systemPromptOverride"
    placeholder="各ノードのシステムプロンプト先頭に追記されます"
    rows="4"
    @input="updateSystemPromptOverride"
  />
</div>
```

```typescript
const responseModeOptions: { value: ThreadSettings['responseMode']; label: string }[] = [
  { value: 'ai', label: 'AI' },
  { value: 'echo', label: 'エコー' },
]

const isDev = import.meta.dev  // ビルド時定数

function selectResponseMode(value: ThreadSettings['responseMode']) {
  emit('update:settings', { ...props.settings, responseMode: value })
}

function updateSystemPromptOverride(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:settings', { ...props.settings, systemPromptOverride: target.value })
}
```

**決定事項**:

- 応答モード UI は既存の粒度ボタンと同じデザイン（CSS 再利用）
- システムプロンプト上書きは `isDev` が false なら DOM から消える（production ビルドで Vue テンプレート側から除去）
- 文字数カウンターは今回不要（UX 改善は別 ISSUE）

### 5.2 `app/pages/index.vue`

変更なし想定。`SettingsPanel` が `responseMode` / `systemPromptOverride` を扱うだけで、チャット表示側は変更不要。

## 6. テスト計画

### 6.1 追加 / 変更するテスト

| ファイル | 追加ケース | 既存ケース修正 |
|---|---|---|
| `tests/server/thread-store.test.ts` | `responseMode` / `systemPromptOverride` の永続化・デフォルト値・旧スレッド互換（不足フィールド補完） | `DEFAULT_SETTINGS` を直接比較しているケースの期待値を新フィールド込みに更新 |
| `tests/server/settings-api.test.ts` | PUT で `responseMode` バリデーション（不正値→`ai`）、`systemPromptOverride` の 2000 文字切り詰め、**本番環境で空文字化**（`vi.stubEnv('NODE_ENV', 'production')` で制御） | 既存の PUT ケース（77〜85 行目周辺）の `ThreadSettings` 完全一致アサーション、および冒頭モック `getThreadSettings.mockReturnValue(...)`（20〜27 行目）を新フィールド（`responseMode: 'ai'`, `systemPromptOverride: ''`）込みに更新 |
| `tests/server/prompt-builder.test.ts` | `systemPromptOverride` ありの場合に先頭に追記される（dev 環境）、`vi.stubEnv('NODE_ENV', 'production')` 下ではスキップされる、空文字では追記されない | `systemPromptOverride` をオプショナル `?: string` で追加するため、既存ケース（`{ granularity, customInstruction }` 2 フィールド渡し）は型エラーにならず変更不要 |
| `tests/server/chat.test.ts` | エコーモード時: `mockGraph.stream` が呼ばれない、`mockGraph.updateState` が `HumanMessage + AIMessage` 1 セットで呼ばれる、`token` / `done` SSE が順に送られる、`search_results` は送られない、タイトル生成で LLM が呼ばれない | `mockGraph` に `updateState: vi.fn()` を追加（既存モックの拡張） |
| `tests/server/thread-settings.test.ts` | `getThreadSettings` の段階マージで `responseMode` / `systemPromptOverride` が DEFAULT で補われる（既存スレッドの互換） | 既存の「デフォルト設定を返す」系ケースの期待値を新フィールド込みに更新。また 131 行目付近の `updateThreadSettings('thread-1', { granularity, customInstruction })` のような**部分的 `ThreadSettings` 引数渡しは型エラーになる**ため、`search` / `responseMode` / `systemPromptOverride` を含む完全な `ThreadSettings` を構築して渡す形に修正 |

**環境変数モックパターン**（テスト共通）:

```typescript
import { vi, beforeEach, afterEach } from 'vitest'

// 本番環境を模擬
beforeEach(() => { vi.stubEnv('NODE_ENV', 'production') })
afterEach(() => { vi.unstubAllEnvs() })
```

### 6.2 テストしないこと

- フロント側 `isDev` 判定（ビルド時定数のため実効テスト困難。UI スナップショットはやらない）
- エコーモードのチャンク分割アルゴリズム単体テスト（ヘルパ関数として分離する場合は最小ケース 1 つのみ）
- 実 DB への永続化（既存テスト同様、`thread-store` はモック）

### 6.3 テスト期待値の見込み

ver16.0 時点: 10 ファイル 93 ケース
ver16.1 目標: 10 ファイル 103〜108 ケース（+10〜15 ケース）

## 7. 実装順序

1. **データモデル拡張**（型追加 + 既存テスト期待値更新、テスト通過）
   - `thread-store.ts` の `ThreadSettings` / `DEFAULT_SETTINGS`
   - `useSettings.ts` の型・デフォルト
   - `thread-store.test.ts` の追加ケース
   - **既存テスト更新**: `thread-settings.test.ts`, `settings-api.test.ts` の `DEFAULT_SETTINGS` 参照 / `ThreadSettings` 完全一致アサーションを新フィールド込みに修正（これを先にやらないとステップ 1 で既存テストが red）
2. **バリデーション**
   - `settings.put.ts` の `responseMode` / `systemPromptOverride` 処理
   - `settings-api.test.ts` の追加ケース
3. **プロンプト上書き**
   - `analogy-prompt.ts` の `buildSystemPrompt` 拡張
   - `prompt-builder.test.ts` の追加ケース
4. **エコーモード（バックエンド）**
   - `chat.post.ts` の分岐 + `handleEchoResponse`
   - `chat.test.ts` のエコー系ケース
5. **設定パネル UI**
   - `SettingsPanel.vue` に 2 セクション追加
   - 既存の useSettings 保存パスで機能することを確認
6. **typecheck / 全テスト実行**
7. **手動確認の推奨項目 MEMO 化**
   - デプロイ後に `getState-timing` / `additional-kwargs-sqlite` ISSUES の動作確認もユーザーに依頼（エコーモードで永続化パスを通ることで `updateState → getState` の往復も同時に検証できる）

## 8. リスク・不確実性

| # | リスク | 影響度 | 対応 |
|---|---|---|---|
| R1 | `agent.updateState()` で会話履歴に追加できるか実機未検証 | 中 | 4.4 参照。フォールバックは「履歴保存なし」方針 |
| R2 | `responseMode` 切り替え時の `currentStep` 整合性 | 低 | MEMO に制限事項として記載。実害が出たら ISSUE 化 |
| R3 | 環境判定（サーバー `NODE_ENV` / フロント `import.meta.dev` 併用）の整合 | 低 | **確定事項**: サーバー側は `process.env.NODE_ENV !== 'production'` に統一（3.2 節）。フロント UI は `import.meta.dev`。両者の意味（production で無効化）は一致する |
| R4 | エコーモードの SSE 30ms/8 文字がコスト的に問題（長文入力でタイムアウト等） | 低 | 1 万文字なら 37.5 秒。サーバー側で `max 1000 文字`の入力制限を `chat.post.ts` のバリデーションに追加してもよい（今回は対象外、ISSUE 化の判断は手動確認後） |
| R5 | 本番デプロイ時に `systemPromptOverride` が過去データとして DB に残る可能性 | 低 | `settings.put.ts` が本番では空文字で上書きするため、次回保存で自動クリーン。`buildSystemPrompt` も dev ガードで無視するため影響なし |

## 9. やらないこと（再掲）

- エコー応答への遅延・エラー注入オプション
- エコーモード専用エンドポイント
- ノード単位のプロンプト差し替え
- システムプロンプトプリセット保存
- 入力文字数制限の追加（別 ISSUE 候補）
- `getState-timing` / `additional-kwargs-sqlite` ISSUES のコード修正（デプロイ後に手動確認する運用事項、MEMO で言及するにとどめる）

## 10. 関連 ISSUES の扱い

- **完了対象**: `ISSUES/app/medium/動作確認便利化.md` — 本バージョン完了時に削除
- **参考（手動確認で close 可能）**: `ISSUES/app/medium/getState-timing.md` / `additional-kwargs-sqlite.md` — 16.1 デプロイ後のユーザー手動確認を MEMO.md に記載して引き継ぐ

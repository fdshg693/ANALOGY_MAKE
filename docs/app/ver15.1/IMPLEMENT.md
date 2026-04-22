# ver15.1 IMPLEMENT — 検索設定の動的切り替え

## 全体像

`ThreadSettings` に `search` サブオブジェクトを追加し、`performSearch()` がそれを参照してTavilyパラメータを動的に変更する。UI では `SettingsPanel.vue` に検索設定セクションを追加する。

## 変更対象ファイル一覧

| 種別 | パス | 主な変更 |
|---|---|---|
| 変更 | `server/utils/thread-store.ts` | `ThreadSettings` 型に `search` 追加、`DEFAULT_SETTINGS` 更新 |
| 変更 | `server/utils/analogy-agent.ts` | `performSearch()` が `SearchSettings` を引数で受け取り、Tavily パラメータに反映。`caseSearchNode` から設定を渡す |
| 変更 | `server/api/threads/[id]/settings.put.ts` | `search` フィールドのバリデーション追加 |
| 変更 | `app/composables/useSettings.ts` | `ThreadSettings`・`DEFAULT_SETTINGS` の型を拡張 |
| 変更 | `app/components/SettingsPanel.vue` | 検索設定セクション（トグル・セレクト・セレクト）を追加 |
| 変更 | `tests/server/thread-store.test.ts` | デフォルト値・JSON往復テストを更新 |
| 変更 | `tests/server/thread-settings.test.ts` | `ThreadSettings` 型変更への対応、`toEqual(DEFAULT_SETTINGS)` の影響確認、後方互換テスト追加 |
| 変更 | `tests/server/settings-api.test.ts` | PUT の `search` バリデーションテストを追加 |
| 変更 | `tests/server/prompt-builder.test.ts` | 必要に応じて更新（検索設定がプロンプトに影響しないことの確認は不要） |
| 新規 | `tests/server/perform-search.test.ts` | `performSearch` の OFF / パラメータ反映テスト（※実装可否は後述リスクを参照） |

新規追加コンポーネント・composable は作成しない。

## 型定義の拡張

### `ThreadSettings` の新しい形（サーバー側：`server/utils/thread-store.ts`）

```ts
export interface SearchSettings {
  enabled: boolean
  depth: 'basic' | 'advanced'
  maxResults: number  // 1〜10
}

export interface ThreadSettings {
  granularity: 'concise' | 'standard' | 'detailed'
  customInstruction: string
  search: SearchSettings
}

export const DEFAULT_SEARCH_SETTINGS: SearchSettings = {
  enabled: true,
  depth: 'basic',
  maxResults: 3,
}

export const DEFAULT_SETTINGS: ThreadSettings = {
  granularity: 'standard',
  customInstruction: '',
  search: { ...DEFAULT_SEARCH_SETTINGS },
}
```

### `getThreadSettings()` の後方互換

既存の `getThreadSettings` は `{ ...DEFAULT_SETTINGS, ...JSON.parse(row.settings) }` でマージしているが、**ネストしたオブジェクトのマージはシャローで上書きされる**。ver15.0 以前のレコード（`search` フィールドを含まない）を読むと `search` が未定義にならないよう、以下のように段階マージに変更する:

```ts
const parsed = JSON.parse(row.settings) as Partial<ThreadSettings>
return {
  ...DEFAULT_SETTINGS,
  ...parsed,
  search: { ...DEFAULT_SEARCH_SETTINGS, ...(parsed.search ?? {}) },
}
```

### フロント側（`app/composables/useSettings.ts`）

同じ `ThreadSettings` 型定義を同期的に更新。型の重複定義は ver15.0 時点の構造をそのまま踏襲する（一元化は scope 外）。`DEFAULT_SETTINGS` も `search` フィールドを含めて更新。

## サーバー側: 検索実行の改修（`server/utils/analogy-agent.ts`）

### `performSearch()` のシグネチャ変更

現状:
```ts
async function performSearch(query: string): Promise<string>
```

変更後:
```ts
async function performSearch(query: string, search: SearchSettings): Promise<string>
```

動作:
1. `search.enabled === false` → 即座に `""` を返す（ログ: `"Tavily Search skipped (disabled by settings)"`）
2. `config.tavilyApiKey` が未設定 → 従来どおり `""` を返す（ログ変更なし）
3. Tavily 呼び出し時に `maxResults: search.maxResults`、`searchDepth: search.depth` を渡す
   - `TavilySearch` コンストラクタまたは `invoke` 時のオプションに `searchDepth` を渡す形を、ライブラリの型に合わせて選ぶ（リスク節で後述）

### `caseSearchNode` からの呼び出し

```ts
const settings = config?.configurable?.settings as ThreadSettings | undefined
const search = settings?.search ?? DEFAULT_SEARCH_SETTINGS
const searchResults = await performSearch(state.abstractedProblem, search)
```

`analogy-agent.ts` から `DEFAULT_SEARCH_SETTINGS` を import する（`thread-store.ts` で export するものを再利用）。

### `caseSearchNode` のコンテキストメッセージ

検索 OFF 時 or API キー未設定時は従来どおり `"(検索結果なし)"` をコンテキストに含める。LLM は既にこのケースを想定してプロンプト構築されているため、特別な分岐は不要。

## サーバー側: API バリデーション（`server/api/threads/[id]/settings.put.ts`）

PUT リクエストボディに対するバリデーションを強化:

```ts
const search: SearchSettings = {
  enabled: typeof body.search?.enabled === 'boolean' ? body.search.enabled : DEFAULT_SEARCH_SETTINGS.enabled,
  depth: body.search?.depth === 'advanced' ? 'advanced' : 'basic',
  maxResults: (() => {
    const n = Number(body.search?.maxResults)
    if (!Number.isInteger(n)) return DEFAULT_SEARCH_SETTINGS.maxResults
    return Math.min(10, Math.max(1, n))
  })(),
}
const settings: ThreadSettings = { granularity, customInstruction, search }
```

方針:
- 不正値は例外を投げずにデフォルトにフォールバック（既存の `granularity` の扱いに合わせる）
- `maxResults` は 1〜10 にクランプ（UI のセレクトレンジと一致）

## フロント側: `SettingsPanel.vue` の UI 追加

既存の「回答粒度」「カスタム指示」セクションの間（または下）に、新セクション「検索設定」を追加する:

```html
<div class="settings-section">
  <label class="settings-label">Web検索:</label>
  <div class="search-row">
    <label class="toggle">
      <input type="checkbox" :checked="settings.search.enabled" @change="updateSearch({ enabled: ($event.target as HTMLInputElement).checked })" />
      有効
    </label>

    <select :value="settings.search.depth" :disabled="!settings.search.enabled" @change="updateSearch({ depth: ($event.target as HTMLSelectElement).value as SearchSettings['depth'] })">
      <option value="basic">basic</option>
      <option value="advanced">advanced</option>
    </select>

    <select :value="settings.search.maxResults" :disabled="!settings.search.enabled" @change="updateSearch({ maxResults: Number(($event.target as HTMLSelectElement).value) })">
      <option v-for="n in 10" :key="n" :value="n">{{ n }}件</option>
    </select>
  </div>
</div>
```

`updateSearch` ヘルパーで部分更新を集約:

```ts
function updateSearch(patch: Partial<SearchSettings>) {
  emit('update:settings', {
    ...props.settings,
    search: { ...props.settings.search, ...patch },
  })
}
```

スタイリング方針:
- 既存の `.granularity-btn` 等の配色に合わせる（青 `#3b82f6` をアクセント、`.settings-label` を再利用）
- 1行3要素を横並び（flex, gap 0.5rem）、狭幅時は折り返し許可
- 無効時のセレクトは `:disabled` の標準スタイル（追加 CSS 不要）

UX 判断:
- トグル OFF でも深度・件数セレクトを画面には残す（次回 ON 時に設定を保持していることを視覚的に示す）が、`disabled` でグレーアウト

## テスト計画

### `tests/server/thread-store.test.ts` / `tests/server/thread-settings.test.ts`

設定系のテストは `thread-settings.test.ts` に集約されているため、主な更新は同ファイルで行う:

- `DEFAULT_SETTINGS.search` が `{ enabled: true, depth: 'basic', maxResults: 3 }` であることを確認
- `getThreadSettings(threadId)` の後方互換テスト: `search` を含まない旧 JSON 文字列を直接 `UPDATE` で注入したあとで `getThreadSettings` を呼ぶと、`DEFAULT_SEARCH_SETTINGS` がマージされて返ることを確認（段階マージの検証）
- `updateThreadSettings` → `getThreadSettings` の往復で `search` が保存・復元されることを確認
- 既存の `toEqual(DEFAULT_SETTINGS)` 系テスト・`updateThreadSettings(..., { granularity, customInstruction })` 呼び出しは、`search` を含む型への変更で壊れるため修正（`DEFAULT_SETTINGS` 比較は自動で追従するが、テストデータは明示的に `search` を付与する or `DEFAULT_SEARCH_SETTINGS` をスプレッド）

`thread-store.test.ts` 側は基本的な CRUD テストに閉じている場合が多いため、設定系以外の変更影響がないかを確認するに留める。

### `tests/server/settings-api.test.ts`

- PUT で正常な `search` を送ると保存される
- PUT で `search.depth` が不正（例: `'invalid'`）なら `'basic'` にフォールバック
- PUT で `search.maxResults` が範囲外（`0`, `11`, `'abc'`）なら `1` or `10` or `3` にクランプ/フォールバック
- PUT で `search` 自体を省略すると `DEFAULT_SEARCH_SETTINGS` が適用される

### `tests/server/perform-search.test.ts`（新規、※リスクセクション参照）

可能なら追加。`@langchain/tavily` の `TavilySearch` をモックして:
- `search.enabled === false` → `invoke` が呼ばれず、戻り値が `""`
- `search.enabled === true` → 指定した `searchDepth`・`maxResults` でコンストラクタ or `invoke` が呼ばれる

ライブラリ型の確認（下記リスク節）の結果、モック設計が複雑化する場合は本テストを省略し、代わりに `caseSearchNode` レベルの統合テストを `thread-store` 側のロジックに集約する。

### 既存テストの維持

- ver15.0 で追加した `prompt-builder.test.ts`・`chat.test.ts` 等は、`ThreadSettings` 型変更の影響でテストデータに `search` を含める必要が出る可能性あり。コンパイルエラーが出るテストがあれば、`DEFAULT_SETTINGS` を使う or `search` を明示的に付与する形で最小限に修正する

## リスク・不確実性

### 1. `@langchain/tavily` の API シグネチャ

`@langchain/tavily` 1.2.0 系での `TavilySearch` の `searchDepth` 指定方法にはバリエーションがある:
- コンストラクタオプション（`new TavilySearch({ searchDepth, maxResults, tavilyApiKey })`）
- `invoke` 引数（`tavily.invoke({ query, searchDepth })`）

**対応**: 実装時にまず `node_modules/@langchain/tavily` の型定義を確認する（`pnpm list @langchain/tavily` or `Read` で `dist/*.d.ts` を確認）。コンストラクタ経路が型的に通ればそちらを採用。通らなければ `invoke` 経路を採用。どちらも通らない場合は、`searchDepth` の反映を諦めて `maxResults` のみ実装する（ver15.0 の互換性を崩さない範囲で妥協）。**妥協した場合は MEMO.md に記録**し、ROUGH_PLAN のスコープから外す旨を明示する。

### 2. 既存レコードの後方互換

ver15.0 で保存された `settings` JSON は `{ granularity, customInstruction }` のみで `search` フィールドを持たない。`getThreadSettings()` のマージロジックを段階マージに変更することで対応するが、既存 DB を持つユーザー（= 開発者自身）の挙動確認は `experiments/inspect-db.ts` で可能。実機確認は wrap_up フェーズで任意。

### 3. テスト環境での `@langchain/tavily` モック

`tests/server/perform-search.test.ts` を追加する場合、`@langchain/tavily` を vi.mock で差し替える必要がある。既存テストにはこのモック前例がない（`analogy-agent.ts` 自体が直接テストされていない）。モック設計が重くなる兆候があれば、**このテスト自体を省略**し、API/ストア層のテストで代替する。

### 4. UI のセレクトボックスと `maxResults` の型整合

HTML `<select>` の value は常に文字列。`Number()` 変換を `@change` ハンドラで行う。直接 `v-model.number` を使う選択肢もあるが、既存の実装スタイル（明示的な event ハンドラ経由）に合わせる。

## 影響範囲外の確認

- LangGraph のチェックポイント・`messages` リデューサーには影響しない
- `generateTitle()`（タイトル自動生成）には影響しない（検索設定は読まない）
- `abstraction` / `solution` / `followUp` ノードの挙動は変わらない
- SSE イベントの種類・フォーマットは変わらない
- 既存の `syntax-highlight.md`・`vitest-nuxt-test-utils.md` などの low ISSUES には触れない

## 実装順序（推奨）

1. `thread-store.ts`: 型拡張 + `DEFAULT_SEARCH_SETTINGS` + `getThreadSettings` の段階マージ
2. `thread-store.test.ts` 更新 → テストパス確認
3. `analogy-agent.ts`: `performSearch` シグネチャ変更 + `caseSearchNode` の呼び出し更新
4. `settings.put.ts`: バリデーション追加
5. `settings-api.test.ts` 更新 → テストパス確認
6. `useSettings.ts`: フロント側の型・デフォルト同期
7. `SettingsPanel.vue`: UI 追加
8. 必要に応じて `perform-search.test.ts` 新規追加（ライブラリ型確認後に判断）
9. `npx nuxi typecheck` + `pnpm vitest run` で全体確認

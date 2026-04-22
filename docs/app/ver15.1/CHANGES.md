# ver15.1 変更差分（ver15.0 → ver15.1）

## 概要

ver15.0 で実装した動的設定システムに、検索設定（Web検索 ON/OFF・検索深度・取得件数）の動的切り替え機能を追加した。

---

## バックエンド

### `server/utils/thread-store.ts`

**`ThreadSettings` 型の拡張:**

```typescript
// ver15.0
export interface ThreadSettings {
  granularity: 'concise' | 'standard' | 'detailed'
  customInstruction: string
}
export const DEFAULT_SETTINGS: ThreadSettings = {
  granularity: 'standard',
  customInstruction: '',
}

// ver15.1 — search フィールドを追加
export interface SearchSettings {
  enabled: boolean
  depth: 'basic' | 'advanced'
  maxResults: number
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

**`getThreadSettings()` に段階マージを追加:**

旧レコード（`search` フィールド欠損）の後方互換のため、`search` を独立してスプレッドマージする実装に変更。

```typescript
// ver15.1
return {
  ...DEFAULT_SETTINGS,
  ...parsed,
  search: { ...DEFAULT_SEARCH_SETTINGS, ...(parsed.search ?? {}) },
}
```

---

### `server/api/threads/[id]/settings.put.ts`

**search 設定のバリデーション追加:**

| パラメータ | バリデーションルール |
|---|---|
| `search.enabled` | `boolean` 以外はデフォルト（`true`）にフォールバック |
| `search.depth` | `'advanced'` 以外は `'basic'` にフォールバック |
| `search.maxResults` | 整数かつ 1〜10 にクランプ。非整数・範囲外はデフォルト（`3`） |

---

### `server/utils/analogy-agent.ts`

**`performSearch()` のシグネチャ変更:**

```typescript
// ver15.0
async function performSearch(query: string): Promise<string>
// 常に Tavily 呼び出し（APIキー未設定時のみスキップ）、maxResults: 3 固定

// ver15.1
async function performSearch(query: string, search: SearchSettings): Promise<string>
// search.enabled === false でスキップ
// Tavily コンストラクタに search.depth と search.maxResults を動的に渡す
// ログに depth・maxResults メタを含める
```

**`caseSearchNode` での設定参照:**

```typescript
// ver15.1
const search = settings?.search ?? DEFAULT_SEARCH_SETTINGS
const searchResults = await performSearch(state.abstractedProblem, search)
```

---

### `server/utils/analogy-prompt.ts`

**`buildSystemPrompt` の引数型を狭める（破壊的変更なし）:**

```typescript
// ver15.0
buildSystemPrompt(basePrompt: string, settings?: ThreadSettings): string

// ver15.1 — search フィールドを参照しないため Pick に変更
buildSystemPrompt(basePrompt: string, settings?: Pick<ThreadSettings, 'granularity' | 'customInstruction'>): string
```

`ThreadSettings` は `SearchSettings` のスーパーセットのため、既存の呼び出し元への影響なし。

---

## フロントエンド

### `app/composables/useSettings.ts`

**`ThreadSettings` 型に `search` フィールドを追加（バックエンドの型定義と同期）:**

- `SearchSettings` インターフェースを追加
- `ThreadSettings` に `search: SearchSettings` フィールドを追加
- `DEFAULT_SETTINGS` に `search: { ...DEFAULT_SEARCH_SETTINGS }` を追加

---

### `app/components/SettingsPanel.vue`

**検索設定セクションを追加:**

- `SearchSettings` 型を import に追加
- `updateSearch(patch: Partial<SearchSettings>)` ヘルパー関数を追加（部分更新を集約）
- テンプレートに「Web検索:」セクションを追加:
  - チェックボックス（`search.enabled` トグル）
  - 検索深度セレクト（`basic` / `advanced`、`enabled === false` 時 disabled）
  - 取得件数セレクト（1〜10件、`enabled === false` 時 disabled）
- `searchDepthOptions` / `maxResultsOptions` の静的配列をスクリプト内で定義

---

## テスト

### `tests/server/settings-api.test.ts` に 6 ケース追加

- `search` 省略時のフォールバック
- `search.enabled` が boolean でない場合のフォールバック
- `search.depth` が不正な場合のフォールバック
- `search.maxResults` が 0（下限クランプ）
- `search.maxResults` が 11（上限クランプ）
- `search.maxResults` が非整数（フォールバック）

### `tests/server/chat.test.ts` を更新

`getThreadSettings` のモック戻り値に `search: { enabled: true, depth: 'basic', maxResults: 3 }` を追加して `ThreadSettings` 型変更に追従。`configurable.settings` のアサーションも同様に更新。

### `tests/server/thread-settings.test.ts` に 2 ケース追加

- 旧レコード（`search` フィールド欠損）からの後方互換読み取り
- 部分的な `search` フィールド（一部キーのみ）の段階マージ

---

## 合計テスト数

| バージョン | テストファイル | テストケース |
|---|---|---|
| ver15.0 | 9 ファイル | 79 ケース |
| ver15.1 | 10 ファイル | 87 ケース |

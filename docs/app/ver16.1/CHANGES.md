# ver16.1 CHANGES — 動作確認便利化（エコーモード + システムプロンプト上書き）

前バージョン: ver16.0（Tavily 検索結果の UI 可視化）

## 変更ファイル一覧

| ファイル | 種別 | 概要 |
|---|---|---|
| `server/utils/thread-store.ts` | 変更 | `ThreadSettings` に `responseMode` / `systemPromptOverride` を追加 |
| `server/utils/analogy-prompt.ts` | 変更 | `buildSystemPrompt()` に `systemPromptOverride` 先頭追記を追加 |
| `server/api/chat.post.ts` | 変更 | エコーモード分岐 + `handleEchoResponse()` / `chunkText()` / `sleep()` ヘルパを追加 |
| `server/api/threads/[id]/settings.put.ts` | 変更 | `responseMode` バリデーション・`systemPromptOverride` の本番正規化を追加 |
| `app/composables/useSettings.ts` | 変更 | フロント側 `ThreadSettings` 型に `responseMode` / `systemPromptOverride` を追加 |
| `app/components/SettingsPanel.vue` | 変更 | 応答モード選択 UI・システムプロンプト上書きテキストエリア（dev のみ）を追加 |
| `tests/server/chat.test.ts` | 変更 | エコーモード系テストを 4 ケース追加、`mockGraph` に `updateState` モック追加 |
| `tests/server/prompt-builder.test.ts` | 変更 | `systemPromptOverride` 関連テストを 4 ケース追加 |
| `tests/server/settings-api.test.ts` | 変更 | `responseMode` / `systemPromptOverride` バリデーション系テストを 4 ケース追加、既存アサーション更新 |
| `tests/server/thread-settings.test.ts` | 変更 | 新フィールドのデフォルト補完テストを 2 ケース追加、既存期待値を新フィールド込みに更新 |

テスト: 93 ケース → 107 ケース（+14 ケース）

## 変更内容の詳細

### 1. `ThreadSettings` データモデル拡張（`thread-store.ts` / `useSettings.ts`）

`ThreadSettings` インターフェースに 2 フィールドを追加:

```typescript
export type ResponseMode = 'ai' | 'echo'

export interface ThreadSettings {
  granularity: 'concise' | 'standard' | 'detailed'
  customInstruction: string
  search: SearchSettings
  responseMode: ResponseMode      // 追加
  systemPromptOverride: string    // 追加
}
```

`DEFAULT_SETTINGS` も `responseMode: 'ai'` / `systemPromptOverride: ''` でデフォルト化。  
既存スレッドの JSON に新フィールドがなくてもスプレッドマージ済みのため、マイグレーション不要。

### 2. エコーモード（`chat.post.ts`）

`settings.responseMode === 'echo'` のとき LangGraph をバイパスし `handleEchoResponse()` に処理を移譲:

- ユーザー入力を **8 文字単位・30ms 間隔** で `token` SSE として配信（ストリーミング表示の確認に使用）
- `agent.updateState()` で `[HumanMessage, AIMessage]` をチェックポインター（SQLite）に永続化
- タイトル生成は LLM を使わず入力先頭 10 文字を流用（AI 呼び出しゼロのポリシー）
- `search_results` イベントは送信しない（エコーモードは検索 OFF 相当）
- `upsertThread()` は分岐前に呼ばれるため、エコーモードでもスレッドの `updated_at` は更新される

**注意**: `agent.updateState()` による永続化が本番環境で正常に機能するか（LangGraph SQLite 往復）は手動確認が必要（MEMO.md R1 参照）。動かない場合は「履歴保存なし」のフォールバックへ切り替える。

**制限事項**: エコーで `currentStep = awaiting_selection` の状態のまま AI モードに戻すと、次の AI 応答が「選択」として解釈され `solution` ノードに流れる。これは設計上許容（MEMO.md R2 参照）。

### 3. システムプロンプト上書き（`analogy-prompt.ts`）

`buildSystemPrompt()` のシグネチャを拡張し、`systemPromptOverride` をオプショナルで追加:

```typescript
export function buildSystemPrompt(
  basePrompt: string,
  settings?: Pick<ThreadSettings, 'granularity' | 'customInstruction'> & {
    systemPromptOverride?: string
  },
): string
```

`process.env.NODE_ENV !== 'production'` かつ `systemPromptOverride` が非空のとき、ベースプロンプトの**先頭**に `${override}\n\n---\n\n` として追記。

### 4. サーバー側バリデーション（`settings.put.ts`）

- `responseMode`: 不正値は `'ai'` にフォールバック
- `systemPromptOverride`: 最大 2000 文字に切り詰め。**本番環境では空文字に正規化**（UI 迂回防止の二重防御）

### 5. フロントエンド（`SettingsPanel.vue`）

2 セクションを追加:

- **応答モード**: `AI` / `エコー` の選択ボタン（既存の粒度ボタンと同デザイン）
- **システムプロンプト上書き**: `import.meta.dev` で開発環境のみ表示。production ビルドで DOM から完全除去される

## API変更

なし（エンドポイント・レスポンス形式の変更なし）。`PUT /api/threads/:id/settings` のリクエストボディが `responseMode` / `systemPromptOverride` フィールドを受け付けるようになったが、後方互換（省略時はデフォルト値を使用）。

## 技術的判断

### 環境判定の使い分け

| 場所 | 採用 | 理由 |
|---|---|---|
| サーバー側（`settings.put.ts`, `analogy-prompt.ts`） | `process.env.NODE_ENV !== 'production'` | Vitest で `vi.stubEnv('NODE_ENV', 'production')` により本番挙動を機械検証可能 |
| フロント側（`SettingsPanel.vue`） | `import.meta.dev` | Vite ビルド時定数。production ビルドで DOM 除去（tree-shaking）の恩恵あり。フロントのテストは対象外のため `import.meta.dev` の制御問題は発生しない |

### ISSUES対応状況

- `ISSUES/app/medium/動作確認便利化.md` — 本バージョンで**完了・削除済み**
- `ISSUES/app/medium/getState-timing.md` / `additional-kwargs-sqlite.md` — デプロイ後の手動確認で close 可能（エコーモードの `updateState → getState` 往復で同時に検証できる）。現状維持

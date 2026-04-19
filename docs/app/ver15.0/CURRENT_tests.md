# テスト現況

## テストファイル一覧

| ファイル | 行数 | テストケース数 | 備考 |
|---|---|---|---|
| `tests/utils/sse-parser.test.ts` | 168 | 8 | SSE パーサー |
| `tests/composables/useChat.test.ts` | 241 | 11 | switchThread 含む |
| `tests/composables/useThreads.test.ts` | 166 | 13 | `importFresh` パターン |
| `tests/server/thread-store.test.ts` | 86 | 8 | `createRequire` で CJS モック回避。ver14.4 で `appendFileSync` モック追加 |
| `tests/server/threads.test.ts` | 46 | 2 | threads API |
| `tests/server/chat.test.ts` | 215 | 6 | ver15.0 で `configurable.settings` の確認テスト追加 |
| `tests/server/chat-history.test.ts` | 156 | 6 | ver14.5 で `type` プロパティベースに更新 |
| `tests/server/prompt-builder.test.ts` | 81 | 8 | ver15.0 新規。`buildSystemPrompt()` の各粒度・カスタム指示の結合テスト |
| `tests/server/settings-api.test.ts` | 98 | 6 | ver15.0 新規。settings GET/PUT API のバリデーション・正常系テスト |
| `tests/server/thread-settings.test.ts` | 89 | 10 | ver15.0 新規。`getThreadSettings`, `updateThreadSettings` の CRUD テスト |

## 合計

- **1,346行**、**78テストケース**（ver14.0 時点: 986行・57テストケースから増加）

## テスト戦略の特記事項

- **Vitest `environment: 'node'`**: ブラウザ API 依存なし
- **`importFresh` パターン**: composable のモジュールスコープシングルトン状態をテスト間で分離
- **`createRequire(import.meta.url)`**: `better-sqlite3`（CJS モジュール）のモック解決を回避
- **`node:fs` モック**: `logger.ts` のファイル出力のため `appendFileSync` をモック（ver14.4〜）

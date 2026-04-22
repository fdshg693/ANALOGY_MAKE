# テスト現況（ver16.0）

## テストファイル一覧

| ファイル | 行数 | テストケース数 | 備考 |
|---|---|---|---|
| `tests/utils/sse-parser.test.ts` | 168 | 8 | SSE パーサー（ver16.0 で変更なし） |
| `tests/composables/useChat.test.ts` | 241 | 11 | switchThread 含む（ver16.0 で変更なし） |
| `tests/composables/useThreads.test.ts` | 166 | 13 | `importFresh` パターン（ver16.0 で変更なし） |
| `tests/server/thread-store.test.ts` | 86 | 8 | `createRequire` で CJS モック回避（ver16.0 で変更なし） |
| `tests/server/threads.test.ts` | 46 | 2 | threads API（ver16.0 で変更なし） |
| `tests/server/chat.test.ts` | 314 | 9 | ver16.0 で 3 ケース追加（search_results SSE） |
| `tests/server/chat-history.test.ts` | 239 | 9 | ver16.0 で 3 ケース追加（searchResults 展開・後方互換） |
| `tests/server/prompt-builder.test.ts` | 81 | 8 | `buildSystemPrompt()` のテスト（ver16.0 で変更なし） |
| `tests/server/settings-api.test.ts` | 98 | 12 | settings GET/PUT API テスト（ver16.0 で変更なし） |
| `tests/server/thread-settings.test.ts` | 89 | 12 | `getThreadSettings`, `updateThreadSettings` テスト（ver16.0 で変更なし） |

## 合計

- **10 ファイル**、**93 テストケース**（ver15.1: 10ファイル・87ケースから増加）

## ver16.0 追加テスト

### `tests/server/chat.test.ts`（3ケース追加）

`POST /api/chat` の `search_results` SSE イベントの送信挙動を検証:

- `最終メッセージに searchResults があれば search_results イベントを送信` — `agent.getState()` がモックで `{ additional_kwargs: { searchResults: [...] } }` を返した場合、`search_results` イベントが `done` 前に push される
- `最終メッセージに searchResults が無ければ search_results イベントを送らない` — searchResults が空または未存在の場合、`search_results` イベントは push されない
- `エラー時は search_results イベントを送らない` — ストリームエラー時は `error` イベントのみ送信

### `tests/server/chat-history.test.ts`（3ケース追加）

`GET /api/chat/history` での `searchResults` 展開を検証:

- AI メッセージの `additional_kwargs.searchResults` が有効な場合、レスポンスの `messages[i].searchResults` に展開される
- `additional_kwargs.searchResults` の要素が型ガードを通過しない不正形式の場合はフィルタアウト（後方互換）
- `additional_kwargs` 自体がない旧形式のメッセージは `searchResults` フィールドなしで返る

## テスト戦略の特記事項（ver16.0）

- **`performSearch` / `caseSearchNode` の単体テスト新設は見送り**: どちらもモジュール外に export されておらず、外部 API（`chat.test.ts` の search_results SSE 検証、`chat-history.test.ts` の additional_kwargs 展開）での検証で代替。ver15.1 の前例と整合
- その他の戦略（`environment: 'node'`、`importFresh`、`createRequire`、`node:fs` モック）は ver15.x から継続

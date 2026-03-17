# ver8 タスク概要

## 対応方針

ISSUES/high に未解決課題なし。MASTER_PLAN (PHASE1.5) の次タスクを進める。

## 対応内容: useChat composable の切り出し

PHASE1.5 項目1「composable + SSEパーサー切り出し」の残り部分。
SSEパーサー (`app/utils/sse-parser.ts`) はver7で切り出し済みのため、本バージョンでは **`useChat` composable の切り出し** に集中する。

### 背景

現在の `index.vue`（152行）にはメッセージ管理・送信処理・ストリーミング状態管理・エラーハンドリングのロジックが同居している。
PHASE1.5 の後続タスク（応答キャンセル機能）や PHASE2（マルチスレッド管理）を見据えると、チャットロジックを composable に分離しておく必要がある。

### 提供される機能

- **`app/composables/useChat.ts`** を新設し、以下のリアクティブ状態と関数をエクスポートする:
  - `messages` — チャット履歴（`ref<Message[]>`）
  - `isLoading` — 送信中フラグ
  - `isStreaming` — ストリーミング中フラグ
  - `threadId` — 会話スレッドID
  - `sendMessage(input: string)` — メッセージ送信＋SSEストリーム処理

- **`index.vue` の簡素化** — ロジックを `useChat` に委譲し、テンプレート・自動スクロール・スタイルのみを残す（約60〜70行に縮小）

- **`Message` 型の共有化** — `Message` インターフェースを composable からエクスポートし、コンポーネント間で共有可能にする

- **composable のテスト** — `tests/composables/useChat.test.ts` を新設し、状態遷移・エラーハンドリング・SSEパーサー連携をテストする

### スコープ外

- 応答キャンセル機能（ver9 以降）
- ストリーミング表示の改善（ver9 以降）
- `ChatInput` や `ChatMessage` の変更
- 既存テストの変更（SSEパーサーテスト・チャットAPIテスト）

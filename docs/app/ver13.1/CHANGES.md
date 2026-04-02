# ver13.1 変更内容: サーバーサイドログの追加

対応課題: `ISSUES/app/high/logging.md`

## 変更ファイル一覧

| ファイル | 種別 | 概要 |
|---|---|---|
| `server/utils/logger.ts` | **新規** | モジュール別プレフィックス付きロガーユーティリティ |
| `server/utils/analogy-agent.ts` | 変更 | エージェント初期化ログ追加（4箇所） |
| `server/api/chat.post.ts` | 変更 | チャットAPI・タイトル生成ログ追加（8箇所） |
| `server/utils/thread-store.ts` | 変更 | DB初期化・スレッド操作ログ追加（3箇所） |
| `server/api/chat/history.get.ts` | 変更 | 履歴取得ログ追加（3箇所） |

## 変更内容の詳細

### ロガーユーティリティの新規作成

`server/utils/logger.ts` に `console.log` / `console.warn` / `console.error` ベースのロガーを新規作成。外部ライブラリは使用せず、モジュール別プレフィックス（`[agent]`, `[chat]`, `[thread]`, `[history]`）でフィルタリング可能にした。

```typescript
export const logger = {
  agent: createLogger('agent'),
  chat: createLogger('chat'),
  thread: createLogger('thread'),
  history: createLogger('history'),
}
```

各モジュールから明示的にインポートして使用する（プロジェクトの h3 明示的インポート方針に準拠）。

### エージェント初期化ログ（`analogy-agent.ts`）

- 初期化開始
- Tavily Search の有効/無効状態
- 初期化完了（モデル名・ツール数・DBパスを出力）

### チャットAPIログ（`chat.post.ts`）

- リクエスト受信（threadId, messageLength）
- ストリーミング開始/完了（responseLength）
- ツール呼び出し検出（`AIMessageChunk` 以外のメッセージ型を検出時）
- ストリーミングエラー
- タイトル生成の開始/完了/失敗

### DB・スレッド操作ログ（`thread-store.ts`）

- DB初期化（パス、WALモード）
- スレッド upsert
- タイトル更新

読み取り専用操作（`getThreads`, `getThreadTitle`）はログ対象外（頻繁呼び出しによるノイズ回避）。

### 履歴取得ログ（`history.get.ts`）

- リクエスト受信
- 取得完了（messageCount）
- 取得失敗

### エラーハンドリングの改善

以下の2箇所で、空の `catch` ブロックを `catch (e)` に変更し、エラーメッセージをログ出力するようにした。動作（エラー時にサイレントに継続）は変更なし。

- `chat.post.ts` の `generateTitle` 関数
- `chat/history.get.ts` の catch ブロック

## 技術的判断

- **外部ログライブラリ不使用**: 現時点では console ベースで十分。ログローテーションやログレベル制御が必要になった段階で導入を検討する。
- **ログ対象の選定**: コア機能の動作確認に必要な箇所のみ。読み取り専用の頻繁な呼び出し（スレッド一覧取得など）はノイズ回避のため除外。
- **`AIMessageChunk` 以外のみツール検出対象**: `AIMessageChunk` で `content` が配列型（tool_use ブロック含む）の場合は頻度が高くノイズになるため、`ToolMessage` 等の別メッセージ型のみをログ対象とした。

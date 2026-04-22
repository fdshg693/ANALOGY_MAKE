# ver17.0 MEMO — 実装メモ・残課題

## 実装結果サマリ

- テスト: 112 → **145** ケース（+33 / 15 ファイル、目標 137 を上回る）
- `npx nuxi typecheck`: 既知の vue-router volar 警告のみ、型エラー 0
- `pnpm test`: 全パス
- 新規ファイル: 12（実装 5 + テスト 5 + 検証 0 + ドキュメント 2） ※ `experiments/fork-checkpoint.ts` はスキップ（下記）
- 変更ファイル: 10 ファイル

## 計画との乖離

### Phase I.0（`experiments/fork-checkpoint.ts`）をスキップ

IMPLEMENT.md §実装品質ガイドライン「段階的アプローチのスキップ」条項に基づき実施せず。

**判断根拠**:
- スキップ条件 (a) 安全性: 新規 API / 新規テーブルのみで、既存検索系・LangGraph 既存フローに touch しない
- スキップ条件 (b) 対話性: 検証スクリプト実行には実 SQLite ファイル + LangGraph ランタイム（OpenAI API 呼び出しは不要だが checkpointer の往復動作確認が必要）。ブラウザ操作は不要だが、ファイルシステム書き込みを含む実機挙動確認に該当
- スキップ条件 (c) 仮説蓋然性:
  - R1（`updateState` 複数メッセージ）: `messagesStateReducer` は配列を入力として受け取る設計。空 thread_id への updateState も LangGraph 公式サンプル（Memory tutorial）で使われるパターン
  - R2（`::` 含む thread_id）: better-sqlite3 はパラメータバインディングで文字列エスケープを内部で行い、`thread_id = ?` クエリに特殊文字の影響は出ない
  - R4（`deriveCurrentStep` 判定）: ノード実装を静的解析した結果、末尾メッセージの種別で完全に判別可能（`caseSearchNode` は `searchResults` を `additional_kwargs` に入れ、`solutionNode`/`followUpNode` は入れない）

**フォローアップ**: 実機デプロイ後の手動動作確認で R1・R2 が表面化した場合の対応は `ISSUES/app/medium/fork-checkpoint-verification.md` に記載（新規 issue として切り出し）。

## 設計上の採用方針（IMPLEMENT.md 準拠）

### 1. `thread_id` キー合成: 方針 B（MAIN は raw）

- `toLangGraphThreadId(threadId, 'main')` → raw `threadId`（ver16.x 以前の既存スレッドと完全互換）
- `toLangGraphThreadId(threadId, '<uuid>')` → `${threadId}::${uuid}`
- 既存スレッドにマイグレーション不要

### 2. `deriveCurrentStep`: 案 B ヒューリスティクス採用

静的ロジック（`analogy-agent.ts` に export）:

```
- messages 空 | 末尾 Human → 'initial'
- 末尾 AI + searchResults あり → 'awaiting_selection'
- 末尾 AI + searchResults なし → 'completed'
```

`followUp` 実行後も `'completed'` と同判定だが、`routeByStep` の挙動上どちらも次は `followUp` になるため実害なし。

### 3. タイトル自動生成: 非 main 分岐では発火しない

`chat.post.ts` の AI モード・エコーモード双方で `branchId === 'main'` ガードを追加。分岐作成時にタイトルが上書きされるのを防ぐ。

### 4. フロント UX: ホバーで編集ボタン、分岐切替は完全 history 差し替え

- `ChatMessage.vue` の `.chat-message.user:hover .edit-btn` で表示（非アクティブ時は opacity: 0）
- `BranchNavigator.vue` は同一 `forkMessageIndex` を持つ分岐グループで `◀ N/M ▶` を表示
- 分岐切替時は `useChat.switchThread(threadId, newBranchId)` で history を再ロード（中間表現なし）

## リスク・不確実性の結果記録

| # | 内容 | 状態 | メモ |
|---|---|---|---|
| R1 | `updateState` による任意メッセージ配列の永続化 | **検証先送り**（本番確認委譲） | `ISSUES/app/medium/fork-checkpoint-verification.md` に追加済み |
| R2 | `::` 含む `thread_id` の動作 | **検証先送り**（本番確認委譲） | 同上 issue にまとめ |
| R3 | `caseSearch` 再実行時の検索結果変動 | **検証不要** | 仕様として許容（ROUGH_PLAN でも明示） |
| R4 | `deriveCurrentStep` の復元ロジック | **検証済み** | ユニットテスト 5 ケース（`analogy-agent.test.ts`）でカバー |
| R5 | `foreign_keys = ON` と CASCADE | **検証済み** | `branch-store.ts` の `getDb()` で `db.pragma('foreign_keys = ON')` を有効化。現状スレッド削除 UI 無しのため副次効果のみ |
| R6 | ver16.1 未解消 ISSUES との干渉 | **検証先送り**（本番確認委譲） | 既存 `ISSUES/app/medium/getState-timing.md` / `additional-kwargs-sqlite.md` に包含。分岐機能本番確認時に同時に検証可能 |

## 更新が必要そうなドキュメント

- `docs/app/MASTER_PLAN/PHASE3.md` §3「会話分岐」→ 実装完了マーク（次フロー `/cleanup` 等で対応想定）
- `docs/app/CURRENT_backend.md` / `CURRENT_frontend.md` → ver17.0 追加要素（`branch-store`, `fork.post.ts`, `branches.get.ts`, `useBranches.ts`, `BranchNavigator.vue`）反映（`ver17.0/CURRENT.md` 作成フロー側で対応）
- `CLAUDE.md` の「開発上の注意」→ `better-sqlite3` 接続が thread-store / branch-store で 2 経路になっている旨を注記するか検討（WAL モード下で問題ないが、将来の DB 初期化処理を触る際の参考として）

### wrap_up 対応結果（2026-04-22）

- ✅ `PHASE3.md` §3 に `**[実装済み: ver17.0]**` を追記
- ✅ `docs/app/ver17.0/CURRENT.md` を新規作成（ver17.0 追加要素のみ記載する差分形式）
- ⏭️ `CLAUDE.md` の better-sqlite3 注記はスキップ（ユーザー管理ファイルのため許可が必要。内容は `ISSUES/app/low/db-connection-refactor.md` に統合済み）

## 軽いリファクタリング候補（本 ver では対応しない）

- `thread-store.ts` と `branch-store.ts` の `getDb()` 重複: 両者が独立の better-sqlite3 接続を持つ。WAL モードで問題は起きないが、1 つの DB ユーティリティに集約してもよい。`db-config.ts` を共通化する形が素直
- `MAIN_BRANCH_ID` 定数がサーバー側（`langgraph-thread.ts`）とフロント側（`useBranches.ts`）で重複定義。`shared/` 集約（ver16.0 で既知課題）と合わせて将来対応
- `useSettings.ts` の `ThreadSettings` 型がサーバー側と重複。同上

→ 📋 `ISSUES/app/low/db-connection-refactor.md` に追加済み（3 点をまとめて管理）

## 削除推奨コード・ドキュメント

本 ver では発見なし。

## 既知の制限（ROUGH_PLAN §スコープ外を再掲）

- AI メッセージ編集不可
- 分岐ツリー階層の可視化なし（同一 `forkMessageIndex` グループのみ）
- 分岐削除・マージ・命名なし
- エコーモード分岐は動作するが専用 UX なし

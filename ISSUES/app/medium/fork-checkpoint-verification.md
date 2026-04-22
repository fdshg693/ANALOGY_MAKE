# fork-checkpoint-verification — 会話分岐の LangGraph チェックポイント挙動未検証

## 概要

ver17.0 で追加した会話分岐機能は、LangGraph checkpointer（SqliteSaver）に対して以下 2 つの未検証ポイントがある。AUTO モード（無人）での実装フェーズでは、実 SQLite + LangGraph ランタイムを起こす検証スクリプト（IMPLEMENT.md 計画の `experiments/fork-checkpoint.ts`）の実行をスキップしたため、実機デプロイ時の手動確認が必要。

## 本番発生時の兆候

### 1. `updateState` による任意メッセージ配列の永続化（R1）

- **兆候**: 分岐作成（POST /api/chat/fork）後、新分岐の history を GET /api/chat/history で取得しても、親から slice したはずのメッセージ 0..N が復元されない / 部分的にしか復元されない
- **ログ**: `fork.post.ts` の `Branch forked` ログに `copiedMessages: N` は記録されるが、その後の `agent.getState` が空配列を返す場合に相当
- **再現手順**: 1) 通常会話を 3 往復以上進める 2) ユーザーメッセージ（index=2 等）をホバーして「編集」→ 別の文言で送信 3) `◀ 2/2 ▶` で元の分岐に戻す or 新分岐の history をリロード

### 2. `::` 含む `thread_id` キーの動作（R2）

- **兆候**: 分岐作成後、`stream` / `getState` が `${threadId}::${newBranchId}` キーでヒットせず、空の state から会話が始まる（main 分岐と同じ位置から再生成される / メッセージが空）
- **確認コマンド**: `sqlite3 data/threads.db "SELECT DISTINCT thread_id FROM checkpoints"` で `::` を含むキーが存在するかを確認

## 対応方針

### R1 が発生した場合

- **Plan A**: `messagesStateReducer` のカスタム reducer を導入し「初回のみ完全上書き」挙動を明示的に実装
- **Plan B**: メッセージを 1 件ずつ順に `updateState({ messages: [m] })` ループで流し込む方式に切り替え（保守性は落ちるが確実）
- **Plan C（最終手段）**: 分岐 API で「新 thread_id に state コピー」を諦め、独自の分岐テーブルで会話履歴を別管理 → LangGraph を `CompiledGraph.invoke` ではなく低レベル API で直接呼ぶ。スコープが膨らむため最終手段

### R2 が発生した場合

- セパレータを `:::` や `|` 等に変更し、`toLangGraphThreadId` の実装のみを差し替える（1 行変更）
- それでも駄目なら、branch_id 単位の独立テーブルにしてハッシュ化した thread_id を使う

## 影響範囲

- ver17.0 新規機能のみ（分岐作成 → 切替 → 履歴表示）
- 既存の main 分岐（`branchId = 'main'`）は `toLangGraphThreadId` が raw threadId を返すため影響なし（ver16.x までと完全同値）

## 関連

- `docs/app/ver17.0/IMPLEMENT.md` §リスク・不確実性 R1 / R2 / R6
- `docs/app/ver17.0/MEMO.md`
- 既存 `ISSUES/app/medium/getState-timing.md` / `additional-kwargs-sqlite.md` と同時検証可能（デプロイ後 1 回の手動テストで 3 つまとめて close できる）

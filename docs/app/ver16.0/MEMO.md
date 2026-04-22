# ver16.0 MEMO

## 実装結果サマリー

IMPLEMENT.md に沿って、Tavily 検索結果を構造化して AI メッセージの `additional_kwargs.searchResults` に添付、SSE の新規 `search_results` イベントで配信、UI に折りたたみで表示する機能を実装完了。全テスト 93 件グリーン。typecheck も exit 0。

## 計画との乖離

### 1. `tests/server/search-results.test.ts` の新設を見送り

IMPLEMENT.md では `performSearch` / `caseSearchNode` の単体テストを新規作成する案があったが、以下の理由で見送り:

- `performSearch` も `caseSearchNode` もモジュール外に export されておらず、テスト用に export を増やすと内部構造をテストに漏らすことになる
- 同等の動作は `tests/server/chat.test.ts`（search_results SSE の送信 / 非送信 / エラー時挙動）と `tests/server/chat-history.test.ts`（additional_kwargs.searchResults の展開 / 不正形式のフィルタ / 旧形式の後方互換）の拡張で外側から検証している
- ver15.1 で `perform-search.test.ts` を「モック設計 ROI が低い」として省略した前例と整合する

将来、検索結果に対する変換ロジックが複雑化したら単体テスト化する。

### 2. 「検索中…」フィードバック

IMPLEMENT.md の「初期リリースでは含めない」判断どおり実装なし。既存 `isLoading` / `考え中...` で十分カバーできている。

## リスク・不確実性の処理

### 1. `agent.getState()` のタイミング（中）

**検証先送り → 📋 ISSUES/app/medium/getState-timing.md に追加済み**。単体テストレベルでは `getState` をモックしているため、「ストリーム完了直後のスナップショットに最新 AIMessage が含まれるか」という LangGraph 実機挙動は検証していない。

- 本番発生時の兆候: `search_results` イベントが送られるべきケースで送られない / 古いメッセージの結果が送られる
- 対応方針: chat.post.ts の `snapshot read failed` ログは出ないが結果が空になる現象を観察したら、IMPLEMENT.md のフォールバック（`streamMode: ["messages", "updates"]` で updates ストリームから拾う）に切り替える
- 影響範囲: 検索結果の UI 表示のみ。チャット機能本体には影響しない

### 2. LangChain `AIMessage.additional_kwargs` の SQLite シリアライズ（中）

**検証先送り → 📋 ISSUES/app/medium/additional-kwargs-sqlite.md に追加済み**。`@langchain/langgraph-checkpoint-sqlite` の内部が任意の `additional_kwargs` を保持できるかは実機検証が必要。

- 本番発生時の兆候: スレッド切り替え→再読み込み後に `searchResults` が消える
- 対応方針: `AnalogyState` に `searchResults: Annotation<SearchResult[]>` を新設して state 経由で永続化。履歴復元時は snapshot.values.searchResults を読む（IMPLEMENT.md 記載のフォールバック）
- 影響範囲: 履歴復元時の UI 表示のみ。ライブ配信は SSE で送っているため影響しない

### 3. Tavily `invoke()` 戻り値の型判別（低）

**検証済み（コードレベル）**。`"error" in results` で失敗弁別、`results.results` の配列性で成功弁別、どちらも当てはまらなければ空配列にフォールバック。加えて `try/catch` で例外も空配列に落とす。実機での失敗パターンの検証は不要と判断（多重のフォールバックで安全）。

### 4. SSE `search_results` の UI 描画タイミング（低）

**検証先送り → ⏭️ ISSUES追加不要**。実機確認でのみ違和感が判断可能。問題が存在するかどうか自体が不明確であり、対応方針も具体化されていないため、実機デプロイ後に違和感を確認した時点で初めて ISSUES 化すれば十分と判断。

### 5. `search_results` イベントのバッファリング順序（低）

**検証不要**。h3 の EventStream は単一コネクションのシリアル出力なので、push 順序 = 受信順序。サーバ側で `done` の前に `search_results` を push しており、さらにクライアント側 `parseSSEStream` でも `done` 処理（`return`）の前に `search_results` の dispatch ブロックを配置しているため、理論的には順序逆転しない。

## ドキュメント更新の提案

- `docs/app/ver16.0/CURRENT.md` / `CURRENT_backend.md` / `CURRENT_frontend.md` — 別フローで更新予定のため本 MEMO では記載不要
- `docs/app/MASTER_PLAN.md` の PHASE3 項目2 を「完了」としてマーク（別フロー）
- `CLAUDE.md` への追加は不要と判断（既存アーキテクチャの自然な拡張）

## 古いドキュメント・コードの提案

特になし。

# agent.getState() のタイミング問題（ver16.0 先送り）

## 概要

`agent.getState()` をストリーム完了直後に呼ぶ設計だが、LangGraph 実機において「最新 AIMessage がスナップショットに含まれるか」が単体テスト（モック）では検証できていない。

## 本番発生時の兆候

- `search_results` SSE イベントが送られるべきケースで送られない
- 古いメッセージの検索結果が送られる
- `chat.post.ts` の `snapshot read failed` ログは出ないが結果が空になる

## 対応方針

`streamMode: ["messages", "updates"]` で updates ストリームから searchResults を拾う方式に切り替える（`IMPLEMENT.md` 記載のフォールバック）。

## 影響範囲

検索結果の UI 表示のみ。チャット機能本体には影響しない。

## 人間確認

検索機能のUI表示、再ロードでの保持は確認済。
それ以上のことを確認すればいいのかは、上から読み取れない
# AIMessage.additional_kwargs の SQLite シリアライズ未検証（ver16.0 先送り）

## 概要

`@langchain/langgraph-checkpoint-sqlite` が任意の `additional_kwargs`（`searchResults` など）を保持できるかは実機検証が必要。現時点では未検証。

## 本番発生時の兆候

- スレッド切り替え → 再読み込み後に `searchResults` が消える（折りたたみカードが表示されなくなる）

## 対応方針

`AnalogyState` に `searchResults: Annotation<SearchResult[]>` を新設して state 経由で永続化し、履歴復元時は `snapshot.values.searchResults` を読む方式に切り替える（`IMPLEMENT.md` 記載のフォールバック）。

## 影響範囲

履歴復元時の UI 表示のみ。ライブ配信は SSE で送っているため影響しない。

---
status: ready
assigned: ai
priority: low
---
# db-connection-refactor — better-sqlite3 接続の統合とコード重複解消

## 概要

ver17.0 時点で、以下 3 つのコード重複が存在する。いずれも機能的な問題はないが、将来の DB 初期化処理変更時の保守コストになり得る。

## 重複箇所

### 1. `getDb()` 重複（`thread-store.ts` vs `branch-store.ts`）

- 両ファイルが独立した better-sqlite3 接続（`let _db`）を持つ
- WAL モード下でマルチ接続は問題ないが、DB パスや PRAGMA 設定の一元管理ができていない
- **提案**: `server/utils/db.ts` 等の共通モジュールに `getDb()` を集約し、両 store からインポートする形に統合

### 2. `MAIN_BRANCH_ID` 定数の重複

- サーバー側: `server/utils/langgraph-thread.ts`
- フロント側: `app/composables/useBranches.ts`
- **提案**: `shared/constants.ts` 等に移動（ver16.0 からの既知課題「shared/ 集約」と合わせて対応）

### 3. `ThreadSettings` 型の重複

- サーバー側: `server/utils/thread-store.ts`
- フロント側: `app/composables/useSettings.ts`
- **提案**: `shared/types.ts` に統合（上記 shared/ 集約対応と同時に実施）

## 優先度

Low。WAL モードで動作上の問題なし。将来 DB 初期化処理を触る際や shared/ 集約を実施する際に合わせて対応すれば十分。

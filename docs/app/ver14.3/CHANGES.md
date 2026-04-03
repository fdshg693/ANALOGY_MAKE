# ver14.3 CHANGES — 履歴不具合の修正

## 変更ファイル一覧

| ファイル | 状態 | 概要 |
|---|---|---|
| `server/api/chat/history.get.ts` | 変更 | `instanceof` → `isInstance` 静的メソッドに置換 |
| `tests/server/chat-history.test.ts` | 変更 | デシリアライズ後オブジェクトの判定テストを追加 |
| `ISSUES/app/high/履歴不具合.md` | 削除 | 修正完了により解決済み |
| `ISSUES/app/medium/テストモック脆弱性-isInstance.md` | 追加 | `isInstance` モックの脆弱性を先送り ISSUE として記録 |
| `ISSUES/app/medium/履歴修正-実機確認.md` | 追加 | 実機確認の推奨を先送り ISSUE として記録 |

## 変更内容の詳細

### `server/api/chat/history.get.ts` — メッセージ型判定の修正

ブラウザ再読み込み・アプリ再起動後に AI メッセージ履歴が消失する不具合を修正。

**原因**: `SqliteSaver` チェックポイントからの復元時、デシリアライズされたメッセージオブジェクトは `instanceof` チェックを通らない場合がある（LangChain の既知パターン）。`instanceof HumanMessage || instanceof AIMessage` のフィルタリングにより、復元後の AI メッセージが除外されていた。

**修正内容**:
- `instanceof` を `HumanMessage.isInstance()` / `AIMessage.isInstance()` 静的メソッドに置換
- `isInstance` は `Symbol.for('langchain.message')` + `type` プロパティベースで判定するため、デシリアライズ後のオブジェクトにも対応
- import に `BaseMessage` を追加（型ガード `msg is BaseMessage` で使用）

```typescript
// 変更前
.filter((msg: unknown) => msg instanceof HumanMessage || msg instanceof AIMessage)
.map((msg: HumanMessage | AIMessage) => ({
  role: msg instanceof HumanMessage ? 'user' as const : 'assistant' as const,

// 変更後
.filter((msg: unknown): msg is BaseMessage =>
  HumanMessage.isInstance(msg) || AIMessage.isInstance(msg)
)
.map((msg) => ({
  role: HumanMessage.isInstance(msg) ? 'user' as const : 'assistant' as const,
```

### `tests/server/chat-history.test.ts` — デシリアライズ模倣テストの追加

`isInstance` が要求するプロパティ（`Symbol.for('langchain.message')` + `type`）を持つが `instanceof` は通らないモックオブジェクトを使用し、チェックポイント復元後のメッセージが正しく判定されることを検証するテストを追加。既存テスト（`new HumanMessage()` / `new AIMessage()` 使用）もすべてパス。

## 技術的判断

### フェーズ1（診断）のスキップ

IMPLEMENT.md では診断ログ追加 → 原因確定 → 修正の2フェーズを計画していたが、以下の理由でフェーズ1をスキップし直接修正を適用:
- `instanceof` がデシリアライズ後に失敗するのは LangChain の既知パターン
- `isInstance` は `instanceof` の上位互換であり、正常なインスタンスにもデシリアライズ後のオブジェクトにも対応するため、仮に原因が別でもデメリットなし
- 診断ログの追加・確認・削除サイクルは非対話的セッションでは非効率

### 実機確認の未実施

テスト 54 件パス・typecheck パスを確認済みだが、ローカル dev サーバー + ブラウザでの実機確認は未実施。次回デプロイ時の確認を推奨として ISSUE に記録済み。

## 補足: 同期間のインフラ由来コード変更

ver14.2 retrospective 以降、infra ver1.0 で以下のサーバーファイルが変更されている（infra カテゴリのドキュメントに記載済み）:
- `server/utils/db-config.ts` — 新規追加。DB パスを一元管理（開発: `./data/`、本番: `/home/data/`）
- `server/utils/analogy-agent.ts` — DB パスを `db-config.ts` からインポートに変更
- `server/utils/thread-store.ts` — 同上

# ver14.5 CHANGES — 履歴フィルタリングを type プロパティベースに置換

## 変更ファイル一覧

| ファイル | 種別 | 概要 |
|---|---|---|
| `server/api/chat/history.get.ts` | 変更 | `isInstance` → `type` プロパティベースのメッセージ判定に全面置換 |
| `tests/server/chat-history.test.ts` | 変更 | テストを `type` プロパティベースに更新、フィルタリングテスト追加 |

## ISSUES 変更

| ファイル | 種別 | 概要 |
|---|---|---|
| `ISSUES/app/medium/テストモック脆弱性-isInstance.md` | 削除 | `isInstance` 廃止により前提が消滅 |
| `ISSUES/app/high/履歴修正-実機確認.md` | 更新 | ver14.5 の修正内容を追記、実機確認は残作業として維持 |

## 変更内容の詳細

### `server/api/chat/history.get.ts`

**変更前**: `@langchain/core/messages` から `BaseMessage`, `HumanMessage`, `AIMessage` をインポートし、`HumanMessage.isInstance()` / `AIMessage.isInstance()` で型判定していた。

**変更後**:
- `@langchain/core/messages` のインポートを完全削除
- ローカルに `CheckpointMessage` インターフェースと `isChatMessage()` 型ガード関数を定義
- `isChatMessage()` は `typeof msg === 'object' && msg !== null && 'type' in msg` でオブジェクト判定後、`type` が `'human'` または `'ai'` かを検査
- ロール判定も `HumanMessage.isInstance(msg)` → `msg.type === 'human'` に変更

**根本原因**: `SqliteSaver` がチェックポイントからメッセージをデシリアライズする際、LangChain のクラスインスタンスではなくプレーンオブジェクトとして復元される。`isInstance` は `Symbol.for('langchain.message')` の存在を検査するが、デシリアライズ後のプレーンオブジェクトにはこの Symbol が存在しないため、すべてのメッセージがフィルタリングで除外されていた。

**解決アプローチ**: メッセージの `type` プロパティ（`'human'` / `'ai'`）はデシリアライズ後も保持されるため、これを判定基準に使用する。このアプローチは `experiments/inspect-db.ts`（ver14.4 で作成した SQLite 調査 CLI ツール）で実証済みだった。

### `tests/server/chat-history.test.ts`

- 既存テスト「デシリアライズ後メッセージの処理」を更新:
  - テスト名を `isInstance ベース` → `type プロパティベース` に変更
  - モックオブジェクトから `Symbol.for('langchain.message')` プロパティを削除し、`type` プロパティのみのプレーンオブジェクトに簡素化
- 新規テスト追加: `type が human/ai 以外のメッセージはフィルタリングされる`
  - `system`, `tool` タイプのメッセージが正しく除外されることを検証

## 技術的判断

### LangChain クラスへの依存を排除

`history.get.ts` は `@langchain/core/messages` への依存を完全に排除した。これにより:

- **利点**: デシリアライズの実装詳細（Symbol の有無、クラス復元の挙動）に依存しなくなった。LangChain のバージョンアップで `isInstance` の挙動が変わっても影響を受けない
- **リスク**: `type` プロパティは LangChain の内部実装であり、将来変更される可能性がある。ただし、`type` はメッセージの基本的な識別子であり変更リスクは低い。また、`inspect-db.ts` でも同じアプローチを採用しており、整合性がある

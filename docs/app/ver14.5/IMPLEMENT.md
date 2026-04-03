# ver14.5 IMPLEMENT

## 概要

履歴不具合の根本原因を特定し修正する。ver14.4 で整備した調査基盤（永続ログ + SQLite CLI）を活用する。

## 仮説（尤度順）

### H1: チェックポイントデシリアライズ後のメッセージが `isInstance` チェックを通過しない

**根拠**:
- `inspect-db.ts` が `msg.type` プロパティでメッセージ種別を判定できている → チェックポイントにはデータは保存されている
- `SqliteSaver` のデシリアライズが LangChain のクラスインスタンスを完全に復元できず、プレーンオブジェクト（`type` プロパティは存在するが `Symbol.for('langchain.message')` がない）を返す可能性
- `isInstance` は Symbol プロパティに依存しており、プレーンオブジェクトには存在しない → フィルタで全メッセージが除外される

**確認方法**:
1. ローカルでアプリを起動し、会話を実施
2. スレッド切り替え or ページリロードで履歴取得を発生させる
3. `logs/app-YYYY-MM-DD.log` を確認:
   - `Raw messages from snapshot` ログの `types` フィールドが `Object` か `HumanMessage`/`AIMessage` かを確認
   - `Messages filtered out` の warn ログが出力されているか確認
4. `npx tsx experiments/inspect-db.ts history <threadId>` でチェックポイントにデータが存在することを確認

### H2: メッセージの `content` が非文字列（配列型）

**根拠**:
- LangChain のメッセージは `content` が `string | Array<{type, text}>` の場合がある
- `history.get.ts:37` で `typeof msg.content === 'string' ? msg.content : ''` としており、配列の場合は空文字列になる

**確認方法**:
- ログの `rawMessages` の content 型を確認

### H3: フロントエンド側の表示問題

**根拠**: 弱い。API が正しく返しても `useChat.ts:23` の `data.messages?.length` チェックが何らかの理由で失敗する可能性

**確認方法**: ブラウザの DevTools で `/api/chat/history` のレスポンスを直接確認

## 実装計画

### フェーズ1: 調査（コード変更なし）

1. ローカル開発環境でアプリを起動（`pnpm dev`）
2. 新規スレッドで会話を実施（1往復以上）
3. ページリロードまたはスレッド切り替えで履歴取得をトリガー
4. 以下を確認:
   - ブラウザ: 履歴が表示されるか
   - ログファイル: `types` フィールドの値、フィルタリング warn の有無
   - CLI ツール: チェックポイント内のメッセージ件数・内容
5. 結果を `MEMO.md` に記録

### フェーズ2: 修正

仮説 H1 が確認された場合の修正内容:

#### 変更ファイル: `server/api/chat/history.get.ts`

`isInstance` ベースのフィルタリングを、`type` プロパティベースに変更する。

**変更前** (L32-38):
```typescript
const messages = rawMessages
  .filter((msg: unknown): msg is BaseMessage =>
    HumanMessage.isInstance(msg) || AIMessage.isInstance(msg)
  )
  .map((msg) => ({
    role: HumanMessage.isInstance(msg) ? 'user' as const : 'assistant' as const,
    content: typeof msg.content === 'string' ? msg.content : '',
  }))
```

**変更後**:
```typescript
interface CheckpointMessage {
  type: string
  content: unknown
}

function isChatMessage(msg: unknown): msg is CheckpointMessage & { type: 'human' | 'ai' } {
  return (
    typeof msg === 'object' &&
    msg !== null &&
    'type' in msg &&
    ((msg as CheckpointMessage).type === 'human' || (msg as CheckpointMessage).type === 'ai')
  )
}

const messages = rawMessages
  .filter(isChatMessage)
  .map((msg) => ({
    role: msg.type === 'human' ? 'user' as const : 'assistant' as const,
    content: typeof msg.content === 'string' ? msg.content : '',
  }))
```

**理由**:
- `type` プロパティは LangChain メッセージの基本属性であり、シリアライズ・デシリアライズを経ても保持される
- `inspect-db.ts` が同じアプローチで正常動作している実績あり
- `isInstance` は `instanceof` の代替として ver14.3 で導入されたが、`SqliteSaver` のデシリアライズ方式によっては Symbol プロパティが復元されない可能性がある
- 型ガード関数により `any` を使わず型安全性を維持する

#### 不要になるインポートの削除

`isInstance` チェックを廃止すると、以下のインポートは不要になる:
- `BaseMessage`, `HumanMessage`, `AIMessage` from `@langchain/core/messages`

現コードではこれら3つは `isInstance` チェックのみに使用されており、型注釈やログでは使用されていないため削除する。

#### 実装前の事前確認

修正着手前に、`new HumanMessage('test').type` の値が `'human'` であることを確認する（REPL またはテストスクリプトで）。これにより、クラスインスタンスが `type` プロパティ経由でも正しく判定できることを保証する。

### フェーズ3: テスト更新

#### 変更ファイル: `tests/server/chat-history.test.ts`

既存テストの更新:

1. **「isInstance ベースの型チェックでデシリアライズ後メッセージを正しく処理」テスト** (L102-133):
   - テスト名を「type プロパティベースの型チェックでデシリアライズ後メッセージを正しく処理」に変更
   - モックオブジェクトから `Symbol.for('langchain.message')` を削除し、`type` プロパティのみで動作することを検証

2. **既存テスト「チェックポイントにメッセージあり → 正しいフォーマットで返却」** (L52-80):
   - `new HumanMessage()` / `new AIMessage()` を使用 → これらは `type` プロパティを持つので、変更後も通過するはず。ただし確認が必要

3. **追加テスト案**:
   - `type` が `'human'` / `'ai'` 以外のメッセージ（`'system'` など）が正しくフィルタリングされることの確認

### フェーズ4: 検証

1. 既存テストの全通過: `pnpm test`
2. ローカル実機確認:
   - 新規会話 → ページリロード → 履歴表示の確認
   - スレッド切り替え → 元のスレッドに戻る → 履歴表示の確認
   - 複数往復の会話 → 全メッセージが復元されることの確認
3. ログ確認: フィルタリング warn が出力されなくなったことの確認

## 他の仮説が確認された場合

- **H2 の場合**: `content` の型チェックを拡張し、配列型の場合はテキスト部分を結合して返す
- **H3 の場合**: フロントエンドのデバッグログ追加 → 問題箇所を特定して修正
- **いずれの仮説も当てはまらない場合**: 調査結果を `MEMO.md` に記録し、`ISSUES/app/high/履歴修正-実機確認.md` を更新

## リスク・不確実性

- **根本原因が想定と異なる可能性**: 調査フェーズで仮説が棄却された場合、修正内容が大きく変わる。その場合は ROUGH_PLAN のスコープ調整基準に従い、本バージョンを調査結果の記録に留める
- **`type` プロパティの安定性**: `type` は LangChain の内部プロパティであり、メジャーバージョンアップで変更される可能性がある。ただし `isInstance` も同様のリスクがあり、`type` の方がシリアライズ耐性が高い
- **`SqliteSaver` のバージョン依存**: デシリアライズの挙動は `@langchain/langgraph-checkpoint-sqlite` のバージョンに依存する。現在のバージョン（^1.0.1）での動作を確認する

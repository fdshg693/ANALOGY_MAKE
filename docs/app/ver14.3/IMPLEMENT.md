# ver14.3 IMPLEMENT — 履歴不具合の修正

## 原因分析

### 問題の再現条件
1. チャットで会話を行う（HumanMessage + AIMessage が生成される）
2. ブラウザ再読み込みまたはアプリ再起動
3. `GET /api/chat/history` で履歴を取得
4. 人間メッセージは表示されるが、AIメッセージが消失

### 原因仮説: `instanceof` による型チェック

`server/api/chat/history.get.ts` (line 26) で `instanceof` を使ってメッセージをフィルタリングしている:

```typescript
.filter((msg: unknown) => msg instanceof HumanMessage || msg instanceof AIMessage)
```

チェックポイントからの復元時、`SqliteSaver` は以下のフローでデシリアライズする:
1. `JsonPlusSerializer._loads()` → `_reviver()` を再帰呼び出し
2. LangChain オブジェクト（`lc === 1`）は `load(JSON.stringify(revivedObj))` で復元（`jsonplus.js` line 47）
3. `load()` は `@langchain/core/load` のデシリアライザで、動的インポートによりクラスインスタンスを復元

`@langchain/core` のコピーは1つのみ（pnpm 確認済み）であり、`load()` が正しく動作すれば `instanceof` は通るはずである。しかし、`load()` がデシリアライズに失敗するケース（AIMessage の `response_metadata`, `usage_metadata` 等の複雑なプロパティが原因など）では plain object が返る可能性がある。

### なぜ HumanMessage は通るのか（未確定）

現時点では正確な理由は不明。診断フェーズで確認する。可能性:
- HumanMessage はより単純な構造のため `load()` の復元が成功しやすい
- あるいは、HumanMessage も実際には `instanceof` を通っておらず、別の原因で表示されているように見えている

### 別仮説: チェックポイントに AIMessage が保存されていない

`instanceof` の問題ではなく、そもそも `agent.getState()` で取得したチェックポイントに AIMessage が含まれていない可能性もある。`streamMode: "messages"` 使用時のチェックポイント書き込みに問題がある場合や、`messagesStateReducer` の動作に問題がある場合が考えられる。

## 修正方針

### フェーズ1: 診断（原因の確定）

#### Step 1: 診断ログの追加

`history.get.ts` にフィルタリング前のメッセージの型情報をログ出力し、原因を特定する。

```typescript
logger.history.info('Raw messages inspection', {
  threadId,
  count: rawMessages.length,
  types: rawMessages.map((msg: unknown, i: number) => ({
    index: i,
    getType: typeof (msg as any)?._getType === 'function'
      ? (msg as any)._getType()
      : 'no _getType',
    constructor: (msg as any)?.constructor?.name ?? 'unknown',
    hasMessageSymbol: Symbol.for('langchain.message') in (msg as any ?? {}),
    hasType: 'type' in (msg as any ?? {}),
    type: (msg as any)?.type,
    hasContent: 'content' in (msg as any ?? {}),
  })),
})
```

このログにより以下が判明する:
- **メッセージ数**: AIメッセージがチェックポイントに存在するか
- **`_getType()`**: メソッドが機能するか（"human" / "ai" が返るか）
- **`constructor.name`**: HumanMessage / AIMessage / AIMessageChunk / Object のいずれか
- **`MESSAGE_SYMBOL`**: `Symbol.for('langchain.message')` がセットされているか（`isInstance` が使えるか）
- **`type` プロパティ**: デシリアライズ後に `type: "human"` / `type: "ai"` が存在するか

#### Step 2: 診断結果に基づく方針決定

| 診断結果 | 意味 | 対応 |
|---|---|---|
| AIメッセージが `rawMessages` に存在しない | チェックポイント保存の問題 | 別の調査が必要（ver14.3 のスコープ拡大） |
| AIメッセージあり、`_getType()` = "ai"、`constructor` ≠ AIMessage | デシリアライズは部分的に成功、`instanceof` が失敗 | フェーズ2 の修正を適用 |
| AIメッセージあり、`hasMessageSymbol` = true、`type` = "ai" | デシリアライズ成功だが `instanceof` 失敗 | フェーズ2 の修正を適用 |
| AIメッセージあり、plain object（`_getType` なし、Symbol なし） | `load()` が完全に失敗 | ダックタイピングによるフォールバック |

### フェーズ2: 修正

#### Step 3: `instanceof` から `isInstance` 静的メソッドへの置き換え

`@langchain/core/messages` の各クラスは `isInstance` 静的メソッドを提供している（`instanceof` より堅牢）:

| メソッド | 実装 | 特徴 |
|---|---|---|
| `BaseMessage.isInstance(obj)` | `Symbol.for('langchain.message') in obj` + `isMessage(obj)` | グローバルSymbol使用、モジュールコピー間で動作 |
| `HumanMessage.isInstance(obj)` | `BaseMessage.isInstance(obj) && obj.type === "human"` | Human + HumanMessageChunk 両対応 |
| `AIMessage.isInstance(obj)` | `BaseMessage.isInstance(obj) && obj.type === "ai"` | AI + AIMessageChunk 両対応 |

注: `isBaseMessage()` / `isHumanMessage()` / `isAIMessage()` 関数は deprecated（`isInstance` 使用推奨）

##### 変更対象: `server/api/chat/history.get.ts`

**変更前:**
```typescript
import { HumanMessage, AIMessage } from '@langchain/core/messages'
// ...
const messages = rawMessages
  .filter((msg: unknown) => msg instanceof HumanMessage || msg instanceof AIMessage)
  .map((msg: HumanMessage | AIMessage) => ({
    role: msg instanceof HumanMessage ? 'user' as const : 'assistant' as const,
    content: typeof msg.content === 'string' ? msg.content : '',
  }))
```

**変更後:**
```typescript
import { BaseMessage, HumanMessage, AIMessage } from '@langchain/core/messages'
// ...
const messages = rawMessages
  .filter((msg: unknown): msg is BaseMessage =>
    HumanMessage.isInstance(msg) || AIMessage.isInstance(msg)
  )
  .map((msg) => ({
    role: HumanMessage.isInstance(msg) ? 'user' as const : 'assistant' as const,
    content: typeof msg.content === 'string' ? msg.content : '',
  }))
```

ポイント:
- `isInstance` は `Symbol.for('langchain.message')` + `type` プロパティベースで判定
- `instanceof` と異なり、デシリアライズ後のオブジェクトにも対応
- `HumanMessage.isInstance` が `BaseMessage.isInstance` を内包するため、別途 `BaseMessage.isInstance` チェックは不要

##### フォールバック（診断で plain object と判明した場合）

`isInstance` も通らない場合は、ダックタイピングで対応:

```typescript
const messages = rawMessages
  .filter((msg: unknown): msg is { type: string; content: string } => {
    const m = msg as any
    return m != null && typeof m === 'object' &&
      typeof m.content === 'string' &&
      (m.type === 'human' || m.type === 'ai')
  })
  .map((msg) => ({
    role: msg.type === 'human' ? 'user' as const : 'assistant' as const,
    content: msg.content,
  }))
```

このフォールバックは診断結果次第で使用する。初期実装では `isInstance` を採用し、動作しない場合のみフォールバックに切り替える。

#### Step 4: テストの更新

`tests/server/chat-history.test.ts` に以下を追加:

```typescript
it('isInstance ベースの型チェックでデシリアライズ後メッセージを正しく処理', async () => {
  vi.mocked(getQuery).mockReturnValue({ threadId: 'thread-1' })

  // チェックポイントからの復元を模倣:
  // isInstance が要求するプロパティを持つが、instanceof は通らないオブジェクト
  const SYM = Symbol.for('langchain.message')
  const mockHumanMsg = {
    [SYM]: true,
    type: 'human',
    content: 'ユーザーメッセージ',
  }
  const mockAIMsg = {
    [SYM]: true,
    type: 'ai',
    content: 'AI応答メッセージ',
  }

  mockGraph.getState.mockResolvedValue({
    values: {
      messages: [mockHumanMsg, mockAIMsg],
    },
  })

  const result = await handler({} as any)

  expect(result).toEqual({
    messages: [
      { role: 'user', content: 'ユーザーメッセージ' },
      { role: 'assistant', content: 'AI応答メッセージ' },
    ],
  })
})
```

注: このテストのモックは `isInstance` の実装詳細（`Symbol.for('langchain.message')` + `type` プロパティ）に依存している。LangChain のバージョンアップ時にモック構造の見直しが必要になる可能性がある。

既存テスト（`new HumanMessage()` / `new AIMessage()` を使用）は `isInstance` でも正しく動作する（クラスインスタンスには `MESSAGE_SYMBOL` と `type` が設定されるため）。テスト実行で確認する。

#### Step 5: 診断ログの削除

修正が確認できたら、Step 1 で追加した診断ログを削除する。

## 変更ファイル一覧

| ファイル | 変更内容 | フェーズ |
|---|---|---|
| `server/api/chat/history.get.ts` | 診断ログ追加 | フェーズ1 |
| `server/api/chat/history.get.ts` | `instanceof` → `isInstance` に置換 + 診断ログ削除 | フェーズ2 |
| `tests/server/chat-history.test.ts` | デシリアライズ模倣テスト追加 | フェーズ2 |
| `ISSUES/app/high/履歴不具合.md` | 修正・動作確認後に削除 | フェーズ2 |

## リスク・不確実性

1. **根本原因の確定ができていない**: `instanceof` が原因という仮説は蓋然性があるが、診断ログで確認するまでは確定ではない。チェックポイント自体に AIMessage が保存されていない可能性もあり、その場合は `streamMode: "messages"` とチェックポイントの相互作用を調査する追加タスクが必要
2. **`isInstance` の前提条件**: `isInstance` は `Symbol.for('langchain.message')` の存在を要求する。`load()` が完全に失敗して plain object を返す場合は `isInstance` も通らず、ダックタイピングへのフォールバックが必要
3. **テストモックの脆弱性**: 追加テストのモックは `isInstance` の内部実装に依存しており、`@langchain/core` のバージョンアップで破綻する可能性がある
4. **ISSUE 完了確認の定義**: ローカルで動作確認後に ISSUE を閉じるが、Azure 本番環境でも再現確認が望ましい（ただし Azure デプロイは本バージョンのスコープ外とし、次回デプロイ時に確認）

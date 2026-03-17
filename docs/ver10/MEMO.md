# ver10 実装メモ

## 計画との乖離

### SqliteSaver.setup() は protected

`IMPLEMENT.md` では `await checkpointer.setup()` を呼ぶ計画だったが、`SqliteSaver.setup()` は protected メソッドのため外部から呼び出せない。実際には checkpointing メソッド呼び出し時に自動で setup が実行されるため、`setup()` 呼び出しを省略した。`getAnalogyAgent()` は async のまま維持（将来の拡張性のため）。

### ReactAgent.getState() は never 型（@internal）

`langchain` の `createAgent` が返す `ReactAgent` では `getState()` が `@internal` として `never` 型で公開されている。ランタイムでは LangGraph の `CompiledStateGraph` 経由で動作するため、`(agent as any).getState()` で型アサーションして利用した。

### import.meta.client のテスト方法

`import.meta.client` は ES モジュールごとに独立した `import.meta` オブジェクトに属するため、テストファイルから代入しても `useChat.ts` には反映されない。`vitest.config.ts` の `define` オプションで `import.meta.client` を `globalThis.__NUXT_CLIENT__` にコンパイル時置換することで解決した。

## 更新が必要そうなドキュメント

- ✅ `CLAUDE.md` の技術スタック表: メモリ行を `SqliteSaver（SQLite永続化、@langchain/langgraph-checkpoint-sqlite）` に更新済み
- ✅ `CLAUDE.md` の「やらないこと」: 「会話履歴の永続化（DBへの保存）」を削除済み

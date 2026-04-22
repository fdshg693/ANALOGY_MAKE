# ver17.0 完了時点のコード現況

ver16.1（エコーモード・システムプロンプト上書き）を経て、PHASE3 項目3「会話分岐（メッセージ編集）」を追加した状態。
ユーザーが過去メッセージを編集して会話を分岐させ、`◀ 1/N ▶` ナビで分岐を切り替えられる。

- [CURRENT_backend.md](CURRENT_backend.md) — サーバーサイド（API Routes、エージェント、プロンプト、ストレージ）
- [CURRENT_frontend.md](CURRENT_frontend.md) — フロントエンド（コンポーネント、Composables、ユーティリティ）
- [CURRENT_tests.md](CURRENT_tests.md) — テストファイル一覧・テストケース数

## 依存パッケージバージョン

ver16.0 から変更なし（ver17.0 では新規パッケージ追加なし）:

| パッケージ | バージョン |
|---|---|
| nuxt | ^4.4.2 |
| vue | ^3.5.30 |
| vue-router | ^5.0.3 |
| @langchain/core | ^1.1.32 |
| @langchain/openai | ^1.2.13 |
| @langchain/langgraph | ^1.2.2 |
| @langchain/langgraph-checkpoint-sqlite | ^1.0.1 |
| @langchain/tavily | ^1.2.0 |
| langchain | ^1.2.32 |
| better-sqlite3 | ^12.8.0 |
| marked | ^17.0.4 |
| dompurify | ^3.3.3 |
| vitest（dev） | ^4.1.0 |
| happy-dom（dev） | ^20.8.4 |
| @types/better-sqlite3（dev） | ^7.6.13 |
| dotenv（dev） | ^17.3.1 |
| tsx（dev） | ^4.21.0 |

## 設定・構成ファイル

ver15.0 から変更なし。詳細は ver15.0/CURRENT.md を参照。

## ISSUES 管理

### medium（中優先度）

| ファイル | 内容 |
|---|---|
| `動作確認便利化.md` | エコーモード・システムプロンプトカスタマイズ（PHASE3 項目4） |
| `getState-timing.md` | ver16.0 追加: ストリーム完了直後 `agent.getState()` で最新 AIMessage が取れるか未検証 |
| `additional-kwargs-sqlite.md` | ver16.0 追加: `AIMessage.additional_kwargs` が SQLite に正しく永続化されるか未検証 |
| `fork-checkpoint-verification.md` | ver17.0 追加: `updateState` 複数メッセージ初期化・`::` 含む thread_id の実機動作未検証 |

### low（低優先度）

| ファイル | 内容 |
|---|---|
| `syntax-highlight.md` | コードブロックのシンタックスハイライト |
| `vitest-nuxt-test-utils.md` | `@nuxt/test-utils` 導入 |
| `db-connection-refactor.md` | ver17.0 追加: thread-store / branch-store の `getDb()` 重複・`MAIN_BRANCH_ID` 重複定義・`useSettings.ts` の型重複（`shared/` 統合と合わせて将来対応） |

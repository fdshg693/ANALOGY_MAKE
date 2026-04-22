# ver16.0 完了時点のコード現況

ver15.1（検索設定の動的切り替え）を経て、PHASE3 項目2「検索結果の可視化」を追加した状態。
Tavily 検索結果をフロントエンドに SSE で配信し、アシスタントメッセージに折りたたみ UI で表示する。スレッド切り替え時の履歴復元にも対応。

- [CURRENT_backend.md](CURRENT_backend.md) — サーバーサイド（API Routes、エージェント、プロンプト、ストレージ）
- [CURRENT_frontend.md](CURRENT_frontend.md) — フロントエンド（コンポーネント、Composables、ユーティリティ）
- [CURRENT_tests.md](CURRENT_tests.md) — テストファイル一覧・テストケース数

## 依存パッケージバージョン

ver15.0 から変更なし（ver16.0 では新規パッケージ追加なし）:

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

### low（低優先度）

| ファイル | 内容 |
|---|---|
| `syntax-highlight.md` | コードブロックのシンタックスハイライト |
| `vitest-nuxt-test-utils.md` | `@nuxt/test-utils` 導入 |

# experiments/

**目的**: 実装前の仮説検証・隔離試行・長時間コマンドの検討。`scripts/` がプロダクション自動化に対して、ここは一時的・使い捨ての実験置き場。

`research` workflow（`scripts/claude_loop_research.yaml`）の `/experiment_test` step から直接書き込まれることが想定される正式な配置先。

## 規約

1. **既存依存で足りる場合**: プロジェクトルートの `package.json` / `pnpm-lock.yaml` / `.venv` をそのまま使う
2. **新しい依存が必要な場合**: `experiments/{slug}/` のサブディレクトリを切り、そこに閉じる（ルートの依存を増やさない）
3. **残すスクリプト**: 先頭コメントに以下 2 点を必須:
   - 何を確かめるためか（目的）
   - いつ削除してよいか（削除条件: 「実装統合されたら削除」「ver16.2 以降不要」等）
4. **使い捨てスクリプト**: 本人が本ループ内で消すのであれば規約 3 は免除

## 既存ファイル

| ファイル | 目的 | 状態 |
|---|---|---|
| `_shared.ts` | ChatOpenAI の共通初期化（langchain 系スクリプト用） | 残す |
| `01-basic-connection.ts` | LangChain 基本接続の確認 | 残す（learning 用） |
| `02-memory-management.ts` | LangGraph checkpoint memory の挙動確認 | 残す（learning 用） |
| `inspect-db.ts` | SQLite ローカル DB のダンプ | 残す（dev サポート） |

（既存 4 本は ver16.0 時点ではコメントヘッダ規約に未準拠。破壊的変更は入れないが、今後編集する機会があれば規約 3 のヘッダを追加すること。）

## `scripts/` との棲み分け

- `scripts/` = CI / 自動化の一部として他 SKILL が呼ぶ production コード
- `experiments/` = 試行錯誤・検証・再現スクリプト。他 SKILL が参照しない

## 実行方法

TypeScript は `tsx` で実行する（`pnpm install -g tsx` か `npx tsx <script>`）。

```bash
npx tsx experiments/01-basic-connection.ts
```

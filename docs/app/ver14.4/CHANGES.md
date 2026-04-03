# ver14.4 CHANGES

## 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---|---|---|
| `server/utils/logger.ts` | 修正 | ファイル出力機能を追加（開発環境限定） |
| `server/api/chat/history.get.ts` | 修正 | 履歴不具合調査用のデバッグログポイント追加 |
| `experiments/inspect-db.ts` | 新規 | SQLite調査CLIツール |
| `tests/server/thread-store.test.ts` | 修正 | `node:fs` モックに `appendFileSync` を追加 |
| `.claude/SKILLS/imple_plan/SKILL.md` | 修正 | 段階的アプローチのスキップ条件を追加 |
| `.claude/SKILLS/split_plan/SKILL.md` | 修正 | 小規模タスク時の IMPLEMENT.md 簡潔化ガイドラインを追加 |

## 変更内容の詳細

### 1. 永続ログ機能（`server/utils/logger.ts`）

`createLogger` を拡張し、コンソール出力に加えてファイル書き込みを行うようにした。

- **有効化条件**: `process.env.NODE_ENV !== 'production'` の場合のみファイル出力が有効
- **ログファイルパス**: `logs/app-YYYY-MM-DD.log`（日付ローテーション）
- **フォーマット**: JSON Lines（1行1エントリ）
- **書き込み方式**: `fs.appendFileSync`（同期書き込み）
- **シグネチャ変更**: `(...args: unknown[])` → `(msg: string, ctx?: Record<string, unknown>)`。既存呼び出し箇所はすべてこの形式だったため互換性問題なし
- `logs/` ディレクトリはモジュール初期化時に `mkdirSync` で自動作成

### 2. 履歴デバッグログ（`server/api/chat/history.get.ts`）

履歴不具合の原因特定のため、以下のログポイントを追加:

- `rawMessages` の件数と各メッセージの `constructor.name` を記録
- `isInstance` フィルタリング前後の件数差がある場合に warn ログを出力

### 3. SQLite調査CLIツール（`experiments/inspect-db.ts`）

SQLite データベースの内容を直接確認できるCLIツールを新規作成。

```bash
npx tsx experiments/inspect-db.ts threads                # スレッド一覧
npx tsx experiments/inspect-db.ts history <threadId>      # メッセージ履歴の整形表示
npx tsx experiments/inspect-db.ts checkpoints <threadId>  # チェックポイント一覧
```

- `better-sqlite3` で DB を readonly オープン
- チェックポイントの BLOB を JSON パースし、メッセージを `[USER]`/`[AI]` 形式で表示
- パース失敗時は生バイナリの hex を表示するフォールバックあり

### 4. テストモック修正（`tests/server/thread-store.test.ts`）

`logger.ts` に `appendFileSync` のインポートが追加されたことで、`node:fs` のモック定義にも `appendFileSync: vi.fn()` を追加する必要が生じた。トップレベルの `vi.mock` と `importFresh` 内の `vi.doMock` の両方を修正。

### 5. SKILL プロセス改善

**`imple_plan/SKILL.md`**: 段階的アプローチ（診断→修正など）が計画されている場合に、条件を満たせば前段階をスキップして直接修正できるルールを追加。

**`split_plan/SKILL.md`**: 小規模タスク時の `IMPLEMENT.md` について、記述量をコード変更量の2〜3倍程度に抑え、核心の変更内容と理由に絞る簡潔化ガイドラインを追加。

## 技術的判断

- **ログの同期書き込み**: `appendFileSync` を採用。ログ量が少量（1リクエストあたり数行）であるため、非同期ストリームの複雑さを避けた。
- **`.gitignore` 更新のスキップ**: IMPLEMENT.md では `logs/` を `.gitignore` に追加する計画だったが、既に `logs` および `*.log` のエントリが存在していたため変更不要だった。

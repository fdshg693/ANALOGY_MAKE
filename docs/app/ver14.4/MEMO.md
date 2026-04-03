# ver14.4 MEMO

## 計画との乖離

### .gitignore の更新がスキップ
IMPLEMENT.md では `.gitignore` に `logs/` を追加する計画だったが、既に `logs` および `*.log` のエントリが存在していたため変更不要だった。

### テストの修正が追加で必要だった
`logger.ts` のシグネチャ変更（`node:fs` から `appendFileSync` を追加インポート）により、`tests/server/thread-store.test.ts` の `node:fs` モックに `appendFileSync: vi.fn()` の追加が必要だった。IMPLEMENT.md の変更ファイル一覧には含まれていなかったが、既存テストを壊さないために修正を実施。

## 残課題

- `ISSUES/app/medium/テストモック脆弱性-isInstance.md` — ver14.3 で記録された先送り ISSUE。今回の `node:fs` モック修正も同様のパターン（モジュール全体をモックする際に新しいエクスポートが追加されると壊れる）であり、根本的にはモック戦略の見直しが望ましい。

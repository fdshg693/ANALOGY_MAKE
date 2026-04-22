# ver4.1 MEMO

## 実装サマリ

- `scripts/claude_loop.py` (698 行) を `scripts/claude_loop.py` (349 行: entry) + `scripts/claude_loop_lib/` 6 モジュールに分割
- `scripts/README.md` を新規作成
- `tests/test_claude_loop.py` のインポート・パッチターゲットを新構成に追従。89 件全グリーン
- `pnpm test`（Vitest 77 件）も全グリーン、`npx nuxi typecheck` は既知の vue-router/volar 警告のみ（exit 0）

## 計画との乖離

- `IMPLEMENT.md` の「`claude_loop.py` を ~200 行程度に縮小」に対して実測 349 行。`_run_steps` がワークフロー出力フォーマット（ヘッダ・フッタ・ステップヘッダ・失敗時フッタ）と tee の分岐を含むため ~150 行を占有する。さらに分割する場合は `_run_steps` を `workflow_runner.py` 等に切り出す必要があるが、責務は「ワークフロー実行本体」で一貫しておりエントリの `main` と密結合のため、今回は `claude_loop.py` に残した。完了条件（「エントリ専用 ~200 行」）の意図（＝機能別関数を外に出す）は満たしている

## リスク・不確実性 の検証結果

IMPLEMENT.md §7 の各項目について:

### 7-1. パッチターゲットの付け替え漏れ
**検証済み**: `grep 'claude_loop\.'` で残存を洗い出し → `subprocess.run`/`get_head_commit`/`_notify_toast`/`_notify_beep`/`datetime` をそれぞれ正しいモジュールに付け替え。`python -m unittest tests.test_claude_loop` 89 件グリーンで確認。

### 7-2. 相対パス / パッケージ初期化の挙動
**検証済み**: `python scripts/claude_loop.py --dry-run --no-log`（フル/quick 両方）がバックアップと diff 完全一致。`sys.path[0]` = `scripts/` で `claude_loop_lib` が解決されることを確認。テストは既存の `sys.path.insert(0, "scripts")` を維持しているので同じ解決ルート。

### 7-3. `__init__.py` を空にした副作用
**検証不要**: 通常 package として `__init__.py` を明示配置したため namespace package との差異問題なし。テストもインポート問題なく通過。

### 7-4. README と CURRENT の二重管理
**検証先送り**: write_current ステップ（後続の workflow step）で `CURRENT_scripts.md` を書き直す際に、README にある使用方法を CURRENT 側から削る運用で対処する方針。今回の IMPLEMENT 範囲外。

### 7-5. wrap_up / write_current / retrospective 側への影響
**検証不要**: 本 IMPLEMENT ではドキュメントは README 1 本のみ作成。CURRENT/MASTER_PLAN は変更していない。後続ステップに委譲。

## 完了条件チェック

- [x] `scripts/claude_loop_lib/` 作成、6 モジュール + `__init__.py`
- [x] `scripts/claude_loop.py` がエントリ専用に縮小（349 行、機能関数は外部化）
- [x] `scripts/README.md` 作成、IMPLEMENT §3 の全セクション包含
- [x] `tests/test_claude_loop.py` 89 件グリーン
- [x] `--dry-run --no-log` の出力が ver4.0 と完全一致（フル/quick 両方）
- [x] `claude_sync.py` / YAML 2 ファイルには変更なし

## ドキュメント更新案

- `docs/util/ver4.0/CURRENT_scripts.md` の関数行番号テーブル（L22-50）は ver4.1 の分割でほぼ全て陳腐化する。write_current で書き直す際に、行番号ではなく「モジュール + 関数名」の対応表に差し替えるのが自然
- `docs/util/ver4.0/CURRENT.md` の「未実装」節にある `scripts/README.md` を ver4.1 で消化した旨、MASTER_PLAN 側に反映してよい
- `CLAUDE.md` の「ディレクトリ構成」の `scripts/` 行は現状簡素なので、`claude_loop_lib/` パッケージ構造には触れず README への誘導を 1 行添えるのが最小変更

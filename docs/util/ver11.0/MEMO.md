# ver11.0 MEMO

## 実装結果サマリ

- `tests/test_claude_loop.py`（1881 行 / 41 クラス）を `scripts/tests/` 配下の 11 ファイルに分割完了。
- `scripts/tests/{__init__.py, _bootstrap.py}` 新設。`_bootstrap.py` で `scripts/` を `sys.path` に追加（重複ガード付き）。
- `scripts/README.md` の「## テスト」節を新コマンド (`python -m unittest discover -s scripts/tests -t .`) に更新。
- 最終検証: 192 件収集・191 pass + 1 fail（pre-existing `test_limit_omitted_returns_all`）、Vitest 15 ファイル 145 件 pass。

## IMPLEMENT.md との乖離

### 1. 段階的アプローチ（Phase B の per-step commit）をスキップ

- **乖離内容**: IMPLEMENT.md §1-7 では Phase B を 11 コミット（クラス群ごと）に分けて積む計画だったが、実装ではサブエージェントで 11 ファイル分割を 1 アクションにまとめた上で、コミットも「Phase A 基盤」「Phase B+C 分割・旧ファイル削除」「Phase D README 更新」の 3 コミット相当（実際は 1 コミットに集約）。
- **理由**: CLAUDE.md「段階的アプローチのスキップ」条件を満たすと判断:
  - (a) 1881 行の機械的な分割で、分割結果が前段階に依存しない（各ファイル独立）
  - (b) per-step commit は自動ワークフローで対話的な管理コストが高い
  - (c) 最終検証で 192 件 / 1 fail の件数一致を確認でき、コピー漏れ・import ミスは検出済み
- **トレードオフ**: 将来 `git bisect` で個別テストクラスの移動起因のバグを切り分けたい場合、本コミット全体を一括で切る必要がある。ただし分割後の挙動は 100% 保全されている（件数・pass/fail 内訳完全一致）ため、実害は小さい。

### 2. `TestYamlSyncOverrideKeys._yaml_path` のパス調整

- **乖離内容**: IMPLEMENT.md §1-3 では「クラス本体を VERBATIM でコピー」と指示していたが、`TestYamlSyncOverrideKeys` の `_yaml_path` メソッドは `Path(__file__).resolve().parent.parent / "scripts" / name` を使っており、ファイル位置が `tests/` → `scripts/tests/` に変わったため 1 階層深くなる。`parent.parent.parent / "scripts" / name` に修正。
- **理由**: `_yaml_path` は対象の YAML ファイル (`claude_loop.yaml` 等) を `scripts/` 配下に探すヘルパであり、テストファイルの物理位置から逆算するため、VERBATIM を維持すると `<repo_root>/tests/scripts/` を探して失敗する。これは構造変更に伴う不可避の適応。

### 3. `test_claude_loop_integration.py` の import 最適化

- **乖離内容**: IMPLEMENT.md §2-4 表で `json`, `subprocess` を stdlib として列挙していたが、実際に 3 クラスが参照するのは `shutil, tempfile, unittest, pathlib, unittest.mock` のみ。未使用 import は除外し、代わりに `TestYamlIntegration` が使う `build_command` (`claude_loop_lib.commands` から) を追加。
- **理由**: import 最小化原則（IMPLEMENT.md §2-4 末尾の「未使用 import を F401 警告が出ないように整理」）に従った結果。

## 関連 ISSUE の次バージョン以降の対応

- `ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md` の本文中に `tests/test_claude_loop.py` / `TestIssueWorklist` への参照あり。本 ISSUE のスコープ外のため本バージョンでは書き換えなかった。**次バージョン以降で本 ISSUE に着手する際、参照先を `scripts/tests/test_issue_worklist.py` に改訂する必要あり**。

## リスク・不確実性の検証結果（IMPLEMENT.md §3 への対応）

### R1: `python -m unittest discover -s scripts/tests -t .` の動作
- **結果**: 検証済み。`scripts/__init__.py` を作らずに動作確認。`discover -s scripts/tests -t .` と `python -m unittest scripts.tests.test_workflow` 形式の両方が動作し、192 件収集に成功。Python 3.13 の implicit namespace package 解決で問題なし。代替案（`scripts/__init__.py` 作成）は不要。

### R2: `__pycache__/test_claude_loop.cpython-313.pyc` の stale キャッシュ
- **結果**: 検証不要と判断。`tests/test_claude_loop.py` は `git rm` で削除されたが、開発者環境の `tests/__pycache__/test_claude_loop.cpython-313.pyc` が残っていても、それは該当 `.py` ファイルが存在しない限り unittest discovery からは拾われない（unittest は `.py` のみを探す）。新コマンドは `scripts/tests/` を見に行くため、旧 pyc が影響する経路は無い。README に新コマンドを明記したので視認性も担保。

### R3: `sys.path` の二重 insert
- **結果**: 検証済み。`_bootstrap.py` 内で `if str(_SCRIPTS_DIR) not in sys.path:` ガードを実装。192 件収集時に sys.path が不正に肥大化しないことを Python の module キャッシュ機構と合わせて担保。

### R4: `test_claude_loop_integration.py` の `@patch` ターゲット文字列
- **結果**: 検証済み。`@patch("claude_loop.subprocess.run")` / `@patch("claude_loop.uuid.uuid4")` / `@patch("claude_loop._find_latest_rough_plan")` はいずれもそのまま動作。`TestRunStepsSessionTracking` / `TestAutoWorkflowIntegration` に含まれる全テストが pass を確認。

### R5: Vitest のテスト探索への干渉
- **結果**: 検証済み。`pnpm test` が 15 ファイル・145 件で正常完走（件数は本 ISSUE 前後で不変）。`scripts/tests/*.py` は Vitest のデフォルト include パターン `**/*.{test,spec}.?(c|m)[jt]s?(x)` にマッチしないため干渉なし。

### R6: 段階移行中の discover 重複検出
- **結果**: 検証不要と判断。本実装では Phase B を段階的ではなく一括で実施し、`tests/test_claude_loop.py` を同一コミット内で削除したため、中間状態での重複検出は発生しない。

## 未修整のリント・テストエラー

- `test_limit_omitted_returns_all` (pre-existing fail) — `ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md` で追跡中。本 ISSUE のスコープ外。
- `npx nuxi typecheck` の vue-router volar 警告は pre-existing（CLAUDE.md「開発上の注意」に既知として記載済み）。本 ISSUE で TypeScript ファイルは一切触っていないため影響なし。

## 更新が必要そうなドキュメント

- `docs/util/ver10.0/CURRENT_tests.md` は旧配置（`tests/test_claude_loop.py`）を前提にした記述。ver11.0 の完了に伴い、次の CURRENT 更新フェーズで `scripts/tests/` 配下の 11 ファイル体系に書き換えが必要（CURRENT 更新は別フローのため本 MEMO では提案のみ）。

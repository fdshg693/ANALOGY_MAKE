# ver7.0 MEMO — issue_worklist.py 導入

## 実装概要

IMPLEMENT.md §1〜§5 の通りに実装完了。

- `scripts/claude_loop_lib/issues.py` を新設（`VALID_STATUS` / `VALID_ASSIGNED` / `VALID_COMBOS` / `extract_status_assigned` を集約）
- `scripts/issue_status.py` をリファクタ: ローカル定数と `_extract_status_assigned` を削除し、`claude_loop_lib.issues` から import する形に置き換え
- `scripts/issue_worklist.py` を新規作成（CLI: `--category` / `--assigned` / `--status` / `--format`）
- `tests/test_claude_loop.py` に `TestExtractStatusAssigned`（3 ケース）と `TestIssueWorklist`（8 ケース）を追加。全 119 テスト成功
- `scripts/README.md` にファイル一覧追記 + `issue_worklist.py` 使い方セクション追加
- `.claude/skills/retrospective/SKILL.md` §3 冒頭に `issue_worklist.py` 呼び出し 2 行を追加（`scripts/claude_sync.py` 経由で書き込み）

## 計画との乖離

### 1. `issue_status.py` から `VALID_*` 定数の import を削除

IMPLEMENT.md §1-2 では「`from claude_loop_lib.issues import VALID_STATUS, VALID_ASSIGNED, VALID_COMBOS, extract_status_assigned` でインポート」としていたが、リファクタ後の `issue_status.py` 内で `VALID_*` 定数を参照するコードが一切残らないため、実際には `extract_status_assigned` のみを import する形に変更した。Grep で `from issue_status import` / `issue_status.VALID` 系の外部依存が無いことを確認済み（未使用 import の追加を避けた）。

### 2. `sys.stdout` の UTF-8 強制

IMPLEMENT.md には記載が無かったが、Windows 既定の `cp932` で `--category app` を実行すると em-dash（`—`）を含む ISSUE タイトルで `UnicodeEncodeError` になるため、`issue_worklist.py` 冒頭で `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` を設定した（`sys.stderr` も同様）。IMPLEMENT.md §8 の成否判定「4 呼び出しが例外なく終了する」を満たすために必要と判断。

### 3. `.claude/skills/retrospective/SKILL.md` の編集に `claude_sync.py` が必要だった

IMPLEMENT.md §R5 の想定通り、直接 Edit ツールが権限で弾かれたため、`scripts/claude_sync.py export` → `.claude_sync/` 側を Edit → `import` の順で適用した。以降の imple_plan でも `.claude/` 配下を触る場合は同じ手順が必要。

## リスク・不確実性（IMPLEMENT.md §7 のフォローアップ）

- **R1（`_default_category` の argparse 評価順序）**: 検証不要。テストでは全ケースで `--category` 相当値を `collect()` に直接渡しており、`parse_args` を経由しないため影響なし。
- **R2（`issue_status.py` のテスト不在）**: 検証済み。`TestExtractStatusAssigned` で `extract_status_assigned` の単体挙動を 3 ケース検証し、`issue_status.py` 本体は手動スモーク（全カテゴリ / util / 存在しないカテゴリ）で変更前と同じ出力になることを確認した。
- **R3（日本語タイトル抽出）**: 検証済み。実際の `ISSUES/util/medium/issue-review-rewrite-verification.md` および `ISSUES/app/medium/*` で `# タイトル` 形式が正しく拾えることを CLI 実行で確認。
- **R4（stderr warning のテスト）**: 検証済み。`io.StringIO` を `sys.stderr` に patch する標準手法で `TestIssueWorklist.test_priority_mismatch_emits_warning_and_uses_dir` と `TestExtractStatusAssigned.test_invalid_combo_emits_warning` が通る。
- **R5（`.claude/` 編集権限）**: 検証済み。直接 Edit が失敗したため `claude_sync.py` 経由に切替で対応（上記「計画との乖離」§3 参照）。

## 未解決・保留

なし。

## 動作確認

- `python -m unittest tests.test_claude_loop` → 119 tests OK（新規 11 ケース含む）
- `pnpm test`（Vitest）→ 145 tests OK
- `npx nuxi typecheck` → 既知の vue-router / volar MODULE_NOT_FOUND エラー（CLAUDE.md に「ビルド・実行に影響なし」と明記済みの既存事象）。本バージョンは Python ファイルのみ変更のため回帰ではない。
- CLI スモーク:
  - `python scripts/issue_status.py` / `python scripts/issue_status.py util` → 変更前と同じ出力
  - `python scripts/issue_worklist.py` → `[util]` 1 件出力
  - `python scripts/issue_worklist.py --format json` → 整形 JSON
  - `python scripts/issue_worklist.py --category app` → 6 件出力（em-dash 問題なし）
  - `python scripts/issue_worklist.py --assigned human --status need_human_action` → `(no matching issues)`

## 更新が必要そうなドキュメント

- `docs/util/MASTER_PLAN/PHASE6.0.md` → §1 / §4 が本バージョンで完了した旨をチェック済みに更新すると進捗把握しやすい（`/wrap_up` または `/write_current` で対応する想定）
- `docs/util/ver6.0/CURRENT_scripts.md` → `issue_worklist.py` の項目追加が必要（`/write_current` で対応）
- `docs/util/ver6.0/CURRENT_tests.md` → `TestIssueWorklist` / `TestExtractStatusAssigned` の追加反映（`/write_current` で対応）

## 次バージョンへの申し送り（ver7.1 / PHASE6.0 §2）

- `/issue_plan` SKILL 新設時に `!`バックティックで `python scripts/issue_worklist.py --format json` を冒頭展開する形で利用する
- `claude_loop_lib/issues.py` の `extract_status_assigned` は戻り値が 4-tuple（`status, assigned, fm, body`）。ROUGH_PLAN frontmatter の自動生成などで `fm["priority"]` / body 参照が必要になる箇所で再利用可能

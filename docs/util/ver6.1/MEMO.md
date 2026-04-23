# ver6.1 MEMO — parse_frontmatter 共通化

## 実装結果

- `scripts/claude_loop_lib/frontmatter.py` を新設（42 行、docstring 込み）
- `scripts/claude_loop_lib/feedbacks.py` を共通関数呼び出しにリファクタ（42 行 → 26 行）
- `scripts/issue_status.py` の旧 `parse_frontmatter(path)` を `_extract_status_assigned(path)` にリネームし、中身を共通関数呼び出しに置換
- `tests/test_claude_loop.py` に `TestParseFrontmatter` クラスを追加（5 ケース）

## 動作確認結果

- `python scripts/issue_status.py` 出力: 変更前後で diff 完全一致
- `python scripts/issue_status.py util` 出力: 変更前後で diff 完全一致
- `python -m unittest tests.test_claude_loop`: 108 tests OK（追加 5 ケース含む）
- `pnpm test` (vitest): 145 tests passed
- `npx nuxi typecheck`: exit 0（vue-router volar 警告は既知）

## 計画との乖離

なし。IMPLEMENT.md の §1〜§5 に沿って実装完了。

### import パスについて

IMPLEMENT §4 で「`sys.path` 調整が必要な可能性あり」と挙げられていた `issue_status.py` のインポートは、`sys.path.insert(0, str(Path(__file__).resolve().parent))` を追加して `from claude_loop_lib.frontmatter import parse_frontmatter` が通ることを確認した（`E402` は `# noqa` で抑制）。

## リスク・不確実性の検証結果

IMPLEMENT.md §リスク・不確実性 の 3 項目:

1. **import パス調整** → 検証済み。`sys.path.insert` 方式で `python scripts/issue_status.py` 動作確認 OK（diff 完全一致）
2. **feedback テストの挙動同一性** → 検証済み。`TestParseFeedbackFrontmatter` 6 ケース全通過
3. **警告メッセージの消失** → 検証済み（警告が出ていた挙動は意図的に廃止）。`issue_status.py` の「YAML parse failed」警告は消えたが、frontmatter 破損時は `raw / human` フォールバックされるため運用影響は軽微。今後 YAML 破損を検知したい場合は `issue_status.py` 側で `fm is None` かつ「先頭 `---` あり」を判定するヘルパーを追加する案あり（本バージョンではやらない）

## 後続バージョンへの申し送り

- PHASE6.0（ver7.0 メジャー）で `scripts/issue_worklist.py` を追加する際、同じ `parse_frontmatter` を再利用できる
- ISSUE `parse-frontmatter-shared-util.md`（low）は解消済み。`wrap_up` 時に `ISSUES/util/done/` へ移動推奨

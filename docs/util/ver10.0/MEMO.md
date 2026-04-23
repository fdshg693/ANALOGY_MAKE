---
version: ver10.0
phase: imple_plan 完了時点
---

# MEMO: util ver10.0 — workflow YAML step 単位 system prompt / model override

## 計画との乖離

- なし。`IMPLEMENT.md` §6 の実装順序にほぼ沿って実装。`OVERRIDE_STRING_KEYS` / `ALLOWED_STEP_KEYS` / `ALLOWED_DEFAULTS_KEYS` 定数化、`get_steps` / `resolve_defaults` 拡張、`build_command` の `--system-prompt` / `--append-system-prompt` 拡張、descriptor の存在ビット表示、3 本 YAML の sync コメント拡張、`scripts/README.md` 更新を完了
- IMPLEMENT.md §3-2 の `TestOverrideInheritanceMatrix` で「`step.None` は `defaults` 値を継承する」ケースは、`get_steps()` が `None` を strip する設計のため `_UNSET`（キー欠如）と同等になる。テストもこの実態に合わせて「step 未指定 → defaults 採用」を verify する形にした

## リスク・不確実性（IMPLEMENT.md §5 への対応）

- **5-1. CLI フラグ仕様の前提**: 検証先送り。理由は ver10.0 では新キーを既存 YAML に実値投入しないため未顕在化。本番発生時の対応方針は README §「override 可能なキー」の「Claude CLI が当該フラグをサポートする必要あり」注記で利用者へ周知済み。`ISSUES/util/medium/cli-flag-compatibility-system-prompt.md` に追加
- **5-2. `--append-system-prompt` の二重引数化**: 検証不要。既存挙動を維持しており本実装で悪化させていない。PHASE7.0 §3 で auto_args 整理時に解消する設計のため独立対応不要
- **5-3. 未知キー拒否の破壊的変更性**: 検証済み。新規追加した `TestYamlSyncOverrideKeys` で既存 3 本 YAML が新仕様の許容キー集合内に収まることを確認。エラーメッセージに `Allowed keys:` を含めて移行容易性を担保済み
- **5-4. `system_prompt` 利用時の影響**: 検証先送り。ver10.0 では実値投入なし。README §「override 可能なキー」で「通常は `append_system_prompt` を使うこと」と明記済み。本番発生時は CLAUDE.md 自動読込み等の挙動が失われる兆候が出るため、利用者がロールバック判断可能
- **5-5. テスト追加によるテスト数増加**: 検証済み。`scripts/README.md` の「現状 103 件」を「現状 192 件」に更新済み（実測 192 件、追加 32 件）
- **5-6. descriptor 行のフォーマット変更**: 検証済み。`scripts/README.md` 「ログフォーマット」節を新パート (`SystemPrompt: set` / `AppendSystemPrompt: set`) に対応するよう更新済み

## 既知の問題

- **`tests.test_claude_loop.TestIssueWorklist.test_limit_omitted_returns_all` が pre-existing で fail**: 本実装より前から存在する失敗（`git stash` 状態でも再現確認済み）。本ワークフローのスコープ外のため対応せず。次回別ワークフローで対応推奨

## ドキュメント更新の提案

- 今回 README §「YAML ワークフロー仕様」を大幅拡張したが、override キー一覧表と継承ルールは将来 PHASE7.0 §2 (validation) や §8 (`/retrospective`) でも参照されるはず。各 SKILL ドキュメント（`/imple_plan` 等）から README へ参照リンクを追加する余地あり（次バージョン以降で検討）

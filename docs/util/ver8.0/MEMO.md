# ver8.0 MEMO — `/issue_plan` SKILL 新設 + `/split_plan` 責務縮小 + `/quick_plan` 削除

## 実装サマリ

IMPLEMENT.md の計画通り、以下 9 件を変更:

1. `.claude/skills/issue_plan/SKILL.md` 新規作成
2. `.claude/skills/split_plan/SKILL.md` 大規模縮小（現状把握・ISSUE 選定・ROUGH_PLAN.md 作成 を削除、REFACTOR/IMPLEMENT 作成 + plan_review_agent review に限定）
3. `.claude/skills/quick_plan/SKILL.md` 削除
4. `.claude/skills/issue_review/SKILL.md` 「位置づけ」「呼び出し元との同期」を `/issue_plan` に更新
5. `.claude/skills/meta_judge/WORKFLOW.md` §1・§2 のステップ列と §2 保守注意を更新
6. `scripts/claude_loop.yaml` 先頭に `/issue_plan` ステップ追加（6 ステップに）
7. `scripts/claude_loop_quick.yaml` 先頭を `/quick_plan` → `/issue_plan` に差し替え
8. `scripts/README.md` ステップ列挙・件数・`continue` 使い分けガイドを更新
9. `ISSUES/README.md` `/split_plan` / `/quick_plan` 参照を `/issue_plan` に更新

`.claude/` 配下の編集は `scripts/claude_sync.py export` → `.claude_sync/` 編集 → `import` の手順で実施。`import_claude()` の全置換動作により `quick_plan/` の削除も正しく伝搬した（R1 対処通り）。

## 計画との乖離

なし。IMPLEMENT.md §1 の変更ファイル一覧・手順に沿って実施。コミット戦略（§10）のみ、`.claude/` と `scripts/` で分割せず単一コミットにまとめた（変更が論理的に密結合で、YAML と SKILL 定義の整合性を保った状態で履歴に残すことを優先）。

## リスク・不確実性の検証結果

### R1: `claude_sync.py` 全置換動作に起因する作業漏れリスク — **検証済み**

- `export` 実行前に `git status .claude/` で想定外の差分がないことを確認
- `.claude/` の編集はすべて `.claude_sync/` 経由で実施
- `import` 後の `git status` で想定通り（新規 `issue_plan/`、削除 `quick_plan/`、3 ファイル変更）になっていることを確認

### R2: `/split_plan` の `continue` 取り扱い — **検証先送り**

- ver8.0 では `/issue_plan` → `/split_plan` 間を新規セッションで運用する方針を採用
- 実運用での検証が必要なため、次回以降のワークフロー実行で観察する
- `ISSUES/util/medium/issue-plan-split-plan-handoff-verification.md` に追加済み
- 先送り理由: 実ワークフロー実行をしないと IMPLEMENT.md 起こしの質が判定できない

### R3: ISSUE レビューフェーズの所属先 — **検証済み**

- `.claude/skills/issue_review/SKILL.md` の「位置づけ」「呼び出し元との同期」セクションを `/issue_plan` 参照に更新（IMPLEMENT 7-3 通り）
- `split_plan` / `quick_plan` への参照は残らず

### R4: `tests/test_claude_loop.py` の YAML 構造依存 — **検証済み**

- YAML 変更前: `python -m unittest tests.test_claude_loop` 119 件パス
- YAML 変更後: 119 件パス（破綻なし）
- `pnpm test` も 145 件パス
- テストは YAML の `steps:` 構造に対するハードコード期待値を持っておらず、`split_plan` は feedbacks の step 名例として登場するのみで問題なし

### R5: `/issue_plan` 内で `issue_worklist.py --format json` の出力が巨大化するケース — **検証先送り**

- ver8.0 時点では util 1 件、app 数件程度のため、件数制限は不要
- 肥大化が顕在化した際の対応案（`--limit` オプション追加）を準備
- `ISSUES/util/low/issue-worklist-json-context-bloat.md` に追加済み
- 先送り理由: ISSUE 件数が閾値を超えてから対処する方が、過剰設計を避けられる

### R6: `/issue_plan` 単独実行のしづらさ — **検証先送り**

- `scripts/claude_loop_issue_plan.yaml` の新規作成は PHASE6.0 §3（ver8.1 以降）の範囲
- 本バージョンでは手動確認（`--max-step-runs 1`）で代替
- `ISSUES/util/low/issue-plan-standalone-yaml.md` に追加済み
- 先送り理由: MASTER_PLAN 上で分離された作業であり、ver8.0 スコープを守るため

## 追加確認事項

### YAML 妥当性

```bash
python -c "import yaml; yaml.safe_load(open('scripts/claude_loop.yaml', encoding='utf-8')); yaml.safe_load(open('scripts/claude_loop_quick.yaml', encoding='utf-8')); print('OK')"
# → OK
```

### `.claude/` の最終差分

```
 M .claude/SKILLS/issue_review/SKILL.md
 M .claude/SKILLS/meta_judge/WORKFLOW.md
 D .claude/SKILLS/quick_plan/SKILL.md
 M .claude/SKILLS/split_plan/SKILL.md
?? .claude/SKILLS/issue_plan/
```

想定通り。`claude_sync.py import` で完全置換され、`quick_plan/` の削除も伝搬している。

## 更新が必要そうなドキュメント

- `docs/util/MASTER_PLAN/PHASE6.0.md` — PHASE6.0 §2 の実装状況を「実装済み」に更新 → **wrap_up で対応完了**
- `docs/util/MASTER_PLAN.md` — PHASE6.0 行のインライン説明文を更新 → **wrap_up で対応完了**
- `docs/util/ver7.0/CURRENT_skills.md` — 旧 `/split_plan` / `/quick_plan` の責務記述が古くなるが、ver8.0 の `CURRENT.md` 新規作成（`/write_current`）で新版として記述するため旧版の修正は不要 → **/write_current に委任（対応不要）**

## 未解消・先送り項目

- R2 / R5 / R6 は ISSUES に独立ファイル化済み（上記参照）
- `tests/test_claude_loop.py` への `--workflow auto` 分岐テスト追加（PHASE6.0 §5 / ver8.1 以降）
- `scripts/claude_loop.py` の `--workflow auto` 導入（PHASE6.0 §3 / ver8.1 以降）

## テスト結果

- `python -m unittest tests.test_claude_loop`: 119 件 全パス
- `pnpm test`: 15 ファイル / 145 件 全パス
- `npx nuxi typecheck`: 既知の vue-router volar 警告のみ（CLAUDE.md 記載通り、ビルド・実行に影響なし）

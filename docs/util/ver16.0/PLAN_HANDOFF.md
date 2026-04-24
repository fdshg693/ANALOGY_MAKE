---
workflow: full
source: master_plan
---

# ver16.0 PLAN_HANDOFF — `/split_plan` 以降への引き継ぎ

## ISSUE レビュー結果

- 走査対象: `ISSUES/util/{high,medium,low}/*.md` 全件
- `review/ai` 件数: 0 件（前バージョン ver15.6 で対象 ISSUE が既に `done/` へ移動済み）
- 状態遷移: なし
- 本ループでは `issue_review` SKILL 挙動の実動作確認機会なし（`issue-review-rewrite-verification.md` は継続持ち越し）

## ISSUE 状態サマリ（util カテゴリ）

| priority | ready/ai | review/ai | need_human_action/human | raw/ai | raw/human |
|---|---|---|---|---|---|
| high | 0 | 0 | 0 | 0 | 0 |
| medium | 1 | 0 | 0 | 0 | 0 |
| low | 1 | 0 | 0 | 2 | 0 |

- medium ready/ai: `issue-review-rewrite-verification.md`（util 単体で消化不能、app/infra 起動待ち）
- low ready/ai: `toast-persistence-verification.md`（Windows 実機目視が必須、AUTO ヘッドレス不可）
- low raw/ai: `rules-paths-frontmatter-autoload-verification.md` / `scripts-readme-usage-boundary-clarification.md`

## 選定理由・除外理由

### 選定理由: PHASE8.0 §1 を ver16.0 の着手対象に選んだ理由

1. **ready/ai プールが AUTO モードで消化不能に固着**: 現在の ready/ai 2 件はどちらも構造的カリオーバー（medium は別カテゴリ起動待ち、low は Windows 実機必須）で、ver15.5 以降 3 バージョン連続で据え置かれている。AUTO モード下で純粋な ISSUE 消化を続けても、これらは次バージョンでも繰り返し除外される見込みで、util カテゴリの運用停滞を招く
2. **MASTER_PLAN 次項目が明確に残存**: PHASE8.0 骨子は既に作成済み（3 節構成、ver16.0〜ver16.2 の 3 段階実装を明示）。ver15.4 RETROSPECTIVE §3 で「PHASE8.0 の必要性は ver15.5〜ver15.7 あたりで再評価」と提示されており、本バージョンがまさにその再評価点に該当
3. **`research` workflow の必要性は既に PHASE8.0 本文に積上済み**: 現行 `full` / `question` では「実装前調査」を正式 step として扱えていないという課題が PHASE8.0 §1-1 に明記されており、`--workflow auto` の選定粒度改善にも直結する
4. **§1 の独立完走性**: PHASE8.0 §2（deferred execution）や §3（token/cost 計測）に依存せず、§1 単独で器として機能する設計（8 step workflow + 2 新 SKILL）。ver16.0 が完走すれば単体で価値を出せる

### 除外理由: 採用しなかった選択肢

- **ISSUES 消化のみに倒す**: ready/ai プールが AUTO モード下で消化不能に固着しているため、更なるカリオーバー累積を招くだけで進展なし。`direction-check-ver16.0.md` の起票まで考えたが、PHASE8.0 骨子が既に存在し選定根拠が十分なため、直接 PHASE8.0 §1 へ倒す判断
- **PHASE8.0 §2 と §1 を同時に扱う**: §2 は deferred execution の request schema / resume 経路 / 二重実行防止など独立した設計論点を持ち、§1 と束ねると `/split_plan` のスコープが膨張する。PHASE8.0 本文も「ver16.0〜ver16.2 の 3 段階」を明示しているためそれに従う
- **raw/ai 2 件を ready 昇格して消化**: `raw → review → ready` は `issue_review` SKILL 外の triage 責務であり、AUTO モードで AI が勝手に promote する運用は SKILL 契約違反。raw/ai はユーザー triage 待ちとして据え置く
- **新 SKILL 2 件を分けて ver16.0a / ver16.0b に切る**: `research_context` と `experiment_test` は同一 workflow 内で連続する前後 step であり、artifact（`RESEARCH.md` / `EXPERIMENT.md`）の責務境界を同時に設計しないと混ざる。片方だけ先行実装は手戻りリスクが高いため 1 バージョンで同時導入する

## 関連 ISSUE / 関連ファイル / 前提条件

### 関連 ISSUE

- `ISSUES/util/medium/issue-review-rewrite-verification.md` — 継続持ち越し、本バージョンでも消化不能
- `ISSUES/util/low/toast-persistence-verification.md` — 継続持ち越し、本バージョンでも消化不能
- `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md` — raw/ai、本バージョン未着手
- `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md` — raw/ai、本バージョン未着手

### 関連ファイル（本版で触る想定）

**新規作成:**
- `scripts/claude_loop_research.yaml`
- `.claude/skills/research_context/SKILL.md`
- `.claude/skills/experiment_test/SKILL.md`
- `experiments/README.md`
- `docs/util/ver16.0/REFACTOR.md` / `IMPLEMENT.md` / `MEMO.md` / `CURRENT.md`

**変更:**
- `scripts/claude_loop.py`
- `scripts/claude_loop_lib/workflow.py`
- `scripts/claude_loop_lib/validation.py`
- `.claude/skills/issue_plan/SKILL.md`
- `.claude/skills/split_plan/SKILL.md`
- `.claude/skills/imple_plan/SKILL.md`
- `.claude/SKILLS/meta_judge/WORKFLOW.md`
- `.claude/rules/scripts.md`
- `scripts/README.md` / `scripts/USAGE.md`
- `scripts/tests/test_claude_loop_cli.py`
- `scripts/tests/test_claude_loop_integration.py`
- `docs/util/MASTER_PLAN/PHASE8.0.md`（§1 を実装済みに更新）
- `docs/util/MASTER_PLAN.md`（PHASE8.0 §1 実装済み注記）

### 前提条件（PHASE8.0 本文 §前提条件より継承）

- PHASE7.1 までで `question` / `scout` / `quick` / `full` と `--workflow auto` 分岐が安定（ver15.0〜15.4 で済）
- `scripts/claude_loop.py` が `ROUGH_PLAN.md` frontmatter の `workflow:` を読んで後続 YAML を切り替える基盤（ver11.0 以降で済）
- `continue: true` / `claude -r <session-id>` の session 継続基盤（ver5.0 で済）
- `.claude/SKILLS/use-tavily/` の存在（`research_context` の外部調査前提、既存）
- `experiments/` ディレクトリ（既存、運用ルールのみ新設）
- `scripts/tests/` の CLI / workflow / integration テスト基盤（既存）

## 後続 step への注意点

### `/split_plan` への注意点

1. **事前リファクタリング `REFACTOR.md` の焦点**: `scripts/claude_loop_lib/workflow.py` と `validation.py` の `workflow` 値分岐が `quick` / `full` リテラル直書きになっていないか先に確認する。値リスト駆動に寄せる軽微な整理を入れてから `research` 値追加の差分を小さく保つ流れが望ましい。ただし過剰整理は避け、`research` 追加で実際に重複する箇所のみ先行整理に限定する。

2. **8 step 構成の妥当性検証**: `/issue_plan → /split_plan → /research_context → /experiment_test → /imple_plan → /wrap_up → /write_current → /retrospective` の 8 段が本当に必要か、`/research_context` と `/experiment_test` のどちらかが省略可能な workflow variant を設けるべきか、を IMPLEMENT.md で検討する。現時点の判断としては 2 step 固定で進め、省略可否は ver16.1 以降の運用実績で評価する方針。

3. **auto 選定条件の粒度**: `/issue_plan` SKILL への条件追記は曖昧にすると `full` との境界が溶ける。PHASE8.0 §1-1 に挙げられている 4 条件（外部仕様確認 / 実装方式実験絞込 / 長時間検証 / 隔離環境試行）のうち、**いずれかを含む** 判定にするか、**複数含む場合のみ** research に倒すかを IMPLEMENT で確定する。現時点の方針は「いずれか 1 つ」だが、full で十分な課題まで research に流れるリスクあり。plan_review_agent でこの粒度を必ずレビューさせる。

4. **artifact 命名**: `RESEARCH.md` / `EXPERIMENT.md` の名前は PHASE8.0 本文でも「（仮称）」扱い。既存の `ROUGH_PLAN.md` / `IMPLEMENT.md` / `MEMO.md` 命名との整合（全部大文字スネーク、接尾辞なし）は守りつつ、確定名を IMPLEMENT.md 冒頭で明示する。

5. **`question` / `research` の責務境界**: docs / SKILL / README で以下 3 点を明示する必要あり — (a) 最終成果物がコード変更か報告書か、(b) `QUESTIONS/` キューに乗るか `ISSUES/` キューに乗るか、(c) 実行 workflow が報告書作成で終わるか実装まで進むか。`/split_plan` ではこの境界定義を `IMPLEMENT.md` の専用節として取り上げる。

6. **deferred execution（§2）との将来接続点**: 本版スコープ外だが、`/experiment_test` から将来 deferred execution を呼び出せるよう、SKILL の責務記述で「長時間コマンドの扱い」欄を空けておく（ver16.1 で埋める前提）。現時点では「長時間コマンドは本 step 内の同期実行に限定する」と明記し、ver16.1 での拡張ポイントであることをコメントで残す。

### `/imple_plan` への注意点

- テスト追加は `test_claude_loop_cli.py` の `--workflow research` 引数テスト + `test_claude_loop_integration.py` の 8 step 完走テストを最優先で実装する。新 SKILL 2 件の内部 prompt 挙動の自動テストは過剰（SKILL 本文の内容テストは人間レビュー領域）

- `.claude/skills/research_context/SKILL.md` / `experiment_test/SKILL.md` は新規作成となるため、既存 SKILL（`/issue_plan` / `/split_plan` / `/imple_plan`）の節構成・見出し粒度・箇条書きスタイルを模倣して揃える

- `experiments/README.md` は新規作成だが、`scripts/README.md` との棲み分けを明示（scripts = production 自動化、experiments = 一時 / 隔離）

- PHASE8.0 §1-2 の完了条件 5 項目を `IMPLEMENT.md` 末尾に転記し、`/wrap_up` で 1 項目ずつ達成判定できるようにする

### 既知の未解決論点（`/split_plan` で決める）

- `auto` での research 選定条件を「4 条件いずれか 1 つ」vs「複数条件同時」のどちらにするか
- `/research_context` と `/experiment_test` を個別 workflow variant として分離（research-only-research / research-only-experiment）できるようにするか、2 step 固定とするか
- `RESEARCH.md` / `EXPERIMENT.md` の最低要求節（問い・根拠・結論・未解決点 / 再現手順・結果・判断）を SKILL 側に強制するか、空テンプレだけ提供してユーザー任せにするか
- `test_claude_loop_integration.py` で research workflow 8 step を end-to-end で走らせる際、各 SKILL の Claude 呼び出しを mock にするか、実際に `claude` CLI を呼び出すか（既存方式踏襲が基本）

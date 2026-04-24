---
workflow: research
source: master_plan
---

# PLAN_HANDOFF: util ver16.1

## ISSUE レビュー結果

- ready/ai に遷移: **1**
  - `ISSUES/util/low/toast-persistence-verification.md`（`review / ai` → `ready / ai`、`reviewed_at: "2026-04-24"`）
- need_human_action/human に遷移: 0
- 追記した `## AI からの依頼`: 0

遷移判断の一次資料: `.claude/skills/issue_review/SKILL.md` §2 判定基準。本件は「再現手順 / 期待動作 / 影響範囲」3 点が揃っていること、および人間追記で AI 側作業（薄いテストスクリプト切り出し）が明示されていることから `ready / ai` を採用。

## ISSUE 状態サマリ

| status / assigned | 件数 |
|---|---|
| ready / ai | 2 |
| review / ai | 0 |
| need_human_action / human | 0 |
| raw / human | 0 |
| raw / ai | 2 |

内訳:
- `ready / ai` (2): `ISSUES/util/medium/issue-review-rewrite-verification.md` / `ISSUES/util/low/toast-persistence-verification.md`
- `raw / ai` (2): `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md` / `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md`

## 選定理由・除外理由

### 採用: PHASE8.0 §2（deferred execution）

- MASTER_PLAN（`docs/util/MASTER_PLAN/PHASE8.0.md` §実装進捗テーブル）で **ver16.1 に明示的に割当済**
- ver16.0 RETROSPECTIVE §3「次バージョン推奨」でも「ver16.1 メジャー扱い」で本節に倒すことが選択済
- FEEDBACKS handoff（`FEEDBACKS/handoff_ver16.0_to_next.md`）でユーザーが同方針を明示支持

### 除外: 持ち越し ISSUE 4 件の消化

除外根拠:
- `ready / ai` 2 件（`issue-review-rewrite-verification.md` / `toast-persistence-verification.md`）はいずれも util カテゴリ単独では消化不能な構造的カリオーバー（前者は `app` / `infra` 側の review/ai ISSUE 出現待ち、後者は人間の Windows 実機目視検証待ち）。ver16.1 でも同じ判定が再現されるため据え置き
- `raw / ai` 2 件は triage 未実施。本版では「ver16.1 着手前にユーザー triage を促すか、そのまま据え置くか」を悩みどころとして提示された（`FEEDBACKS/handoff_ver16.0_to_next.md`）が、AUTO 運用中にユーザー triage を挟む仕組みがないため据え置き判断
- 本版スコープに ISSUE 消化を混ぜると PHASE8.0 §2 の焦点が散るリスクがあり、`source: master_plan` / `source: issues` を混在させないルール（`/issue_plan` SKILL の判断基準「どちらの、どのような内容を対応するのか明確に」）にも抵触する

### 除外: PHASE8.0 §3（token/cost 計測）

- MASTER_PLAN で ver16.2 に割当済
- §2 の deferred execution 経路が安定してから `duration` と `cost` を別軸で扱う設計が成立する（PHASE8.0 §3-1 で明記）ため、§2 を先行確定させる順序が妥当

### 除外: 新 PHASE 骨子作成

- PHASE8.0 は §2 / §3 が未着手。PHASE 単位での次候補が発生するのは PHASE8.0 完走（ver16.2 終了）以降
- ver16.0 RETROSPECTIVE §1 で「新 PHASE 骨子の必要性: 現時点で不要」と確定済

### 除外: 4 バージョン連続持ち越し対応（`status: need_human_action` 振り直し）

- FEEDBACKS handoff で「ver16.2 以降で検討」と提案されており、ver16.1 スコープ外

### 除外: YAML sync 契約の生成元 1 箇所化

- ver16.0 RETROSPECTIVE §2 改善候補で提起済だが、「§2 で YAML が更に増えた場合のみ優先度を上げる」判断。本版の YAML 変更は `claude_loop_research.yaml` の effort 調整のみで、新 YAML 追加は発生しない見込み

## 関連 ISSUE / 関連ファイル / 前提条件

### 関連 MASTER_PLAN / 仕様書

- `docs/util/MASTER_PLAN/PHASE8.0.md` §2（`yaruこと` 第 2 節、完了条件、リスク・不確実性、ファイル変更一覧のうち §2 関連行）
- `docs/util/MASTER_PLAN/PHASE8.0.md` §前提条件（session 継続・`continue: true` / `claude -r <session-id>` の既存基盤）

### 関連 ISSUES

- **本版で消化する ISSUE は 0 件**（PHASE8.0 §2 着手のため）
- 持ち越し参照用: `ISSUES/util/medium/issue-review-rewrite-verification.md` / `ISSUES/util/low/toast-persistence-verification.md` / `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md` / `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md`

### 関連ファイル（想定変更 / 参照）

想定変更対象:
- `scripts/claude_loop.py`
- `scripts/claude_loop_lib/deferred_commands.py`（新規）
- `scripts/claude_loop_lib/logging_utils.py`
- `scripts/claude_loop_lib/validation.py`
- `scripts/claude_loop_lib/workflow.py`（必要があれば）
- `scripts/claude_loop_research.yaml`（`/write_current` effort 調整）
- `scripts/tests/test_deferred_commands.py`（新規）
- `scripts/tests/test_claude_loop_integration.py`
- `scripts/README.md` / `scripts/USAGE.md`
- `experiments/deferred-execution/`（新規、方式比較用）

参照専用:
- `scripts/claude_loop.yaml` / `scripts/claude_loop_quick.yaml` / `scripts/claude_loop_question.yaml` / `scripts/claude_loop_scout.yaml` / `scripts/claude_loop_issue_plan.yaml`（YAML sync 契約 6 ファイルのうち他 5 本）
- `.claude/rules/scripts.md` §3（YAML 同期対象リスト）
- `experiments/README.md`（規約）
- `docs/util/ver16.0/CURRENT_scripts.md`（session 継続周りの現況）

### 前提条件

- PHASE7.1 までの workflow 基盤（`question` / `scout` / `quick` / `full` / `research` 分岐、`--workflow auto` 2 段実行）が安定していること（ver16.0 RETROSPECTIVE で full 走行の健全性は確認済）
- `continue: true` / `claude -r <session-id>` による session 継続機構が既に存在すること
- `experiments/` ディレクトリが存在し、`experiments/README.md` で依存隔離・削除条件コメントのルールが既に明文化されていること（ver16.0 で追加済）
- research workflow の 8 step（`claude_loop_research.yaml`）は本版で **初めて実走**する。self-apply のため、workflow 自体の挙動不具合に遭遇した場合は IMPLEMENT.md で分岐対応を検討

## 後続 step への注意点

### `/split_plan` への申し送り

1. **IMPLEMENT.md §0（未解決論点）に解消対象として明示的に列挙すべき項目**（後続 `/research_context` / `/experiment_test` のインプット）:
   - 既存の `claude -r <session-id>` 起動経路と「deferred 完了後の resume 呼び出し」が session ID レイヤで競合しないか（`scripts/claude_loop.py` の session 管理コードを要確認）
   - registered command request の file layout（JSON schema / YAML / 単一 dir per request / queue dir 配下のファイル命名規則）
   - 結果ファイルの巨大化に備えた「先頭サマリ抽出」の規約（固定バイト数 / 行数 / 正規表現ベース / sidecar .meta.json のどれを正式採用するか）
   - `experiments/` 配下に方式比較を残す際の命名（`experiments/deferred-execution/{variant}/` 階層で分けるか、`experiments/deferred-execution/NOTES.md` に集約するか）
   - 本番 `ISSUES/` / `QUESTIONS/` / `FEEDBACKS/` / `logs/workflow/` と queue を共有しないための隔離ディレクトリ配置

2. **REFACTOR.md の軽度事前整理候補**:
   - `scripts/claude_loop.py` の実行ライフサイクル（session 継続・step 切替・コマンド生成）を `claude_loop_lib/workflow.py` 側へ寄せる余地を確認し、deferred 分岐の差し込み箇所を 1 関数に閉じられる状態にする
   - 本格リファクタは避け、deferred 分岐の責務境界が曖昧になる箇所のみ最小整理にとどめる

3. **`workflow: research` 自己適用に関する留意点**:
   - ver16.1 自身が `research` workflow で走る。つまり本版の `/research_context` / `/experiment_test` が実走する **初のケース**
   - self-apply のため、`RESEARCH.md` / `EXPERIMENT.md` artifact の 4 節必須構造（問い / 収集した証拠 / 結論 / 未解決点 — 検証した仮説 / 再現手順 / 結果 / 判断）が形式的に守られているか、次ループ retrospective で厳しめに確認予定

### `/research_context` への申し送り

- 調査対象候補: `claude -r <session-id>` の CLI 挙動（stdin/stdout / 環境変数 / 終了コードの扱い）、既存 `scripts/claude_loop.py` の session 継続ロジック、Python 側で外部コマンドを実行し結果を保存する既存 idiom（`subprocess.run` vs `asyncio.create_subprocess_exec` vs 独立プロセス wrapper）
- 「repo 内コード・既存 docs・過去 version docs を先に確認し、足りない場合のみ use-tavily」の原則を厳守
- 成果物: `docs/util/ver16.1/RESEARCH.md`（4 節必須）

### `/experiment_test` への申し送り

- 実験対象候補: 専用 fixture ディレクトリでの request 登録 → 実行 → resume の 1 経路最小実装、失敗時 cleanup 挙動、結果ファイル巨大化時の抽出挙動
- `experiments/deferred-execution/` 配下に閉じる。ルート依存は増やさない。スクリプト先頭に「何を確かめるためか / いつ削除してよいか」コメント必須
- 成果物: `docs/util/ver16.1/EXPERIMENT.md`（4 節必須）

### `/imple_plan` への申し送り

- `RESEARCH.md` / `EXPERIMENT.md` を **必ず** インプットとして読むこと（research workflow の契約）
- 調査 / 実験結果により ROUGH_PLAN の想定成果物から外れる判断が発生した場合、`MEMO.md` に乖離理由を残す（MASTER_PLAN §1-1 で明示）
- PHASE8.0 §2-3 完了条件 5 項目の全てを IMPLEMENT.md の完了条件にコピーしてチェックリスト化する

### `/write_current` への申し送り

- **本版は minor version のため `CURRENT.md` は新規作成せず `CHANGES.md` を作成する**（プロジェクト規約）
- ただし ver16.0 で分割された `CURRENT_scripts.md` / `CURRENT_skills.md` には deferred execution 関連の節追記が発生する可能性あり。`CHANGES.md` から該当 CURRENT_*.md への追記リンクを張る形を推奨
- **effort を medium → high に引き上げ済**（本版 `claude_loop_research.yaml` を `/imple_plan` step で更新する前提）。複雑度上昇を想定した事前調整

### `/wrap_up` への申し送り

- PHASE8.0 §2-3 完了条件 5 項目のうち「workflow 自己テストについては『有望な方式と避けるべき方式』が docs / experiments に整理されるが、標準 workflow や CI への常時組み込みまでは行わない」の後半は本版で **実装しない**。完了条件の文面上「整理されるが常時組み込みはしない」である点を wrap_up で正しく ✅ 判定すること

### `/retrospective` への申し送り

- ver16.0 RETROSPECTIVE §3.5 保留メモで「research workflow の 8 step は ver16.1 self-apply 時に評価」と明言済。**本版の retrospective で research workflow の step 構成・model/effort・artifact 必須 4 節の妥当性を本格評価する**こと
- `/write_current` の effort を medium → high に引き上げた効果も併せて評価（CURRENT / CHANGES 生成品質の観察）

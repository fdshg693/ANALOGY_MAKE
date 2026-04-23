# ver15.0 RETROSPECTIVE

PHASE7.1 §1（`issue_scout` workflow 新設）を add-only で実装したメジャーバージョンの振り返り。ver14.0 で導入した §3.5 workflow 評価 / §4.5 handoff 機構の 2 周目適用でもある。

## §1 ドキュメント構成整理

### MASTER_PLAN 状態

- `docs/util/MASTER_PLAN/PHASE7.1.md` は §1 のみ実装済（ver15.0）、§2〜§4 は未着手（ver15.1 以降の想定）。現行 PHASE は**未完走**のため、PHASE8.0 骨子作成は不要。本節はここで確定。
- `PHASE7.1.md` 自体が節ごとに想定バージョン（ver15.0 / 15.1 / 15.2）を明記しているため、次バージョン以降の「何を着手するか」の一次資料として引き続き機能している。新規分割は不要。

### CLAUDE.md / `.claude/rules/` 構成

- ルート `CLAUDE.md` / `.claude/CLAUDE.md` に肥大化の兆しなし。分割不要。
- `.claude/rules/` は `claude_edit.md` / `scripts.md` の 2 ファイル維持。README 集約は「3 ファイル目追加時」という ver14.0 RETRO §1 の判断を継承。
- **即時修正**（本 RETROSPECTIVE §4 の即時適用対象として処理）: `.claude/rules/scripts.md` §3 の「3 ファイル間で同一内容」記述が scout YAML 追加後に未更新だった点を `claude_loop_scout.yaml` を含めた 4 ファイル同期へ改訂済。あわせて `docs/util/ver15.0/CURRENT.md` の該当記述も更新した。

### docs 分割状況

- `CURRENT.md` を親 + `CURRENT_scripts.md` / `CURRENT_skills.md` / `CURRENT_tests.md` に分割する構造（ver14.0 で採用）は本バージョンでも素直に継承できた。scout workflow 追加による増分も親 CURRENT.md に数行で収まり、肥大化していない。構造継続で問題なし。

## §2 バージョン作成の流れの評価

| ステップ | 評価 | コメント |
|---|---|---|
| `/issue_plan` | 良 | ready/ai blocked + raw/ai 着手対象外 + 観察期間満了の 3 点から `source: master_plan / workflow: full` を導出。選定経緯が ROUGH_PLAN.md に明示され判断再現性あり |
| `/split_plan` | 良 | IMPLEMENT.md §リスク表 R1〜R8 が MEMO.md §リスク検証結果と 1:1 対応。`--workflow scout` 一本化の判断（`--scout` フラグを追加しない）を IMPLEMENT.md 側で確定させられた |
| `/imple_plan` | 良 | 12 件の成果物を計画通り add-only で積む。`claude_sync export → edit → import` で SKILL を配置。実行テスト 105 件グリーン・dry-run 完走 |
| `/wrap_up` | 良 | R1/R2 の検証先送りを独立 ISSUE 化（`issue-scout-noise-risk.md`）して追跡可能化。smoke test を unattended で走らせないリスク判断も plan_review_agent で検証済 |
| `/write_current` | 良 | CURRENT.md 4 ファイル分割を継承。scout workflow 追加箇所のみ差分として表現できた |
| `/retrospective`（本ステップ） | 良（2 周目） | §3.5 / §4.5 の 2 周目適用。§3.5 は変更なしのため簡素化、§4.5 は次 ver15.1 の観察項目を具体的に引き継ぎ可能 |

### プロセス上の気付き

- **SKILL 配置パスの大文字小文字ブレ**: ROUGH_PLAN / IMPLEMENT で `.claude/SKILLS/` と記述されたが、実体・validation の参照先は `.claude/skills/`（小文字）。Windows 上は case-insensitive で事なきを得たが、Linux 実行時にはバグになる。次ループの handoff で「SKILL / rule 配置は `.claude/skills/` `.claude/rules/` 小文字表記で統一」とだけ引き継ぐ（即時 rules 化するほど頻発していないため、handoff 1 回で十分）。
- **4 ファイル同期契約の docs と rule のずれ**: `scripts/README.md` / `USAGE.md` は scout 追加と同時に 4 ファイル同期へ更新されたが、`.claude/rules/scripts.md` §3 だけが取り残された。これは scripts.md rule が「詳細は docs 側が一次資料」と謳っているため漏れやすい。今後は「YAML ファイル増減時は rules/scripts.md の同期対象リストも更新する」チェックを implementer 側（SKILL `/imple_plan` 相当）に持たせたい。handoff で提案する。

## §3 次バージョンの種別推奨

### 判定材料

1. **ISSUE 状況**:
   - `ready / ai`: 1 件（`issue-review-rewrite-verification.md`、util 単体消化不能で継続持ち越し）
   - `raw / ai`: 3 件（`issue-scout-noise-risk.md` / `rules-paths-frontmatter-autoload-verification.md` / `scripts-readme-usage-boundary-clarification.md`）
2. **MASTER_PLAN の次項目**: PHASE7.1 §2（`QUESTIONS/` と `question` workflow）想定 = ver15.1、§3（`ROUGH_PLAN.md` / `PLAN_HANDOFF.md` 分離）想定 = ver15.1、§4（run 単位通知）想定 = ver15.2
3. **現行 PHASE 完走状態**: PHASE7.1 は §1 のみ完了、**未完走**。次 PHASE 骨子作成不要。

### 推奨

**次バージョンは ver15.1（マイナー）。2 つの路線が同居する:**

(A) **scout 初回 smoke test + `issue-scout-noise-risk.md` 消化**  
`python scripts/claude_loop.py --workflow scout --category util --max-loops 1` を手動起動し、R1（ノイズ化）/ R2（重複検出閾値）を実観察してクローズ判定する。実装伴わず観察ベースで `done/` 化できれば軽量。

(B) **PHASE7.1 §2〜§3 の本体実装**  
`QUESTIONS/` と `question` workflow 追加、および `ROUGH_PLAN.md` / `PLAN_HANDOFF.md` 分離。§2 単独でも新規 SKILL 追加を伴うため「3 ファイル超」確定で `workflow: full` 相当となるが、PHASE7.1 内の継続節なのでマイナーバージョン（ver15.1）で扱うのが PHASE 構造上自然。

**優先順**: (A) を先に片付ける（1〜2 ループ）→ (B) を ver15.1 or ver15.2 で着手、とする。理由: (A) は scout workflow の本体機能が想定通り動くかの実運用確認であり、その結果が PHASE7.1 §2 設計（重複起票検出ロジックの共通化可否など）にフィードバックされる余地があるため。

**メジャー（ver16.0）昇格条件**: PHASE7.1 が全節完了した時点で PHASE8.0 骨子の要否を判定する。現時点では時期尚早。

## §3.5 workflow prompt / model 評価（2 周目・差分評価）

### 評価対象バージョン: ver15.0

本バージョンで workflow YAML に加えた実質変更は `claude_loop_scout.yaml` の**新規追加**のみ。`claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` の既存 step の prompt / model / effort は一切変更していない。差分評価の対象は **scout step 1 点のみ**。

| step | model | effort | 分類 | 理由・次ループ案 |
|---|---|---|---|---|
| issue_scout（新規） | opus | high | 維持（初回） | 1〜3 件の高価値候補抽出が目的のため品質優先 `opus` / `high`。初回 smoke test までは評価保留。ver15.1 の観察ループ結果を見てから effort 調整を検討 |

既存 step については省略条件（評価材料なし）に該当するため、ver14.0 評価結果を継承する。

### 次ループで試す調整

- **なし**（scout step は smoke test 前で評価材料不足）。ただし ver15.1 smoke test 後に起票ゼロ連発 or ノイズ多発が観察された場合に備えて、handoff で「smoke 後に effort を調整する余地あり」とだけ引き継ぐ。
- `claude_loop_scout.yaml` に `system_prompt` / `append_system_prompt` を付けていない（SKILL.md 本文で制御）点は、他 YAML と同じ方針で統一されており追加調整不要。

## §4 ISSUES 整理

- **削除対象（対応済み）**: なし。本バージョンで直接 `done/` 化できる ISSUE はゼロ。
- **持ち越し**:
  - `ISSUES/util/medium/issue-review-rewrite-verification.md`（`ready / ai`）— util 単体消化不能で継続持ち越し。ver6.0 以来維持。
  - `ISSUES/util/medium/issue-scout-noise-risk.md`（`raw / ai`、ver15.0 新規）— R1/R2 検証先送り分。ver15.1 smoke test 後にクローズ判定。
  - `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md`（`raw / ai`、`reviewed_at: 2026-04-24`）— ver14.0 観察持越し。継続保持。
  - `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md`（`raw / ai`、`reviewed_at: 2026-04-24`）— 同上。継続保持。
- **frontmatter 無し**: util カテゴリには該当なし。

## §4.5 次ループへの handoff

次ループ（ver15.1 `/issue_plan`）向けの補助線を `FEEDBACKS/handoff_ver15.0_to_next.md` に書き出す。内容は以下 3 点に絞る:

1. scout smoke test（A 路線）の実施方法と観察ポイント（R1/R2 クローズ判定基準）
2. PHASE7.1 §2〜§3 を次着手する場合の前提（§1 scout の挙動確認が先）
3. SKILL / rule 配置パス表記を小文字（`.claude/skills/` `.claude/rules/`）で統一するガイド

恒久 rule 化する内容ではないため handoff 1 回で十分。

## §5 まとめ

- PHASE7.1 §1 完了。scout workflow は `--workflow scout` で起動可能、既存 auto / full / quick には自動混入しない。ユニットテスト 105 件グリーン・dry-run 完走。
- 次バージョンは **ver15.1（マイナー）**。scout 初回 smoke test で R1/R2 をクローズした後、PHASE7.1 §2〜§3 へ進む。
- PHASE8.0 骨子作成は PHASE7.1 全節完了まで先送り。
- 本 RETROSPECTIVE で即時適用した変更: `.claude/rules/scripts.md` §3 を 4 ファイル同期に更新、`docs/util/ver15.0/CURRENT.md` の該当記述を改訂。
- handoff: `FEEDBACKS/handoff_ver15.0_to_next.md` に書き出し済。

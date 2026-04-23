---
step: issue_plan
---

## 背景

ver15.0 で PHASE7.1 §1 `issue_scout` workflow を新設した。実装自体は add-only で完了し、dry-run + 105 ユニットテストはグリーン。ただし R1（起票の `raw / ai` ノイズ化）/ R2（重複検出ヒューリスティックの閾値）の 2 リスクは初回 smoke test での実観察が必要であり、`ISSUES/util/medium/issue-scout-noise-risk.md` として先送り起票済。PHASE7.1 は §2〜§4 が未着手（想定 ver15.1〜15.2）。

## 次ループで試すこと（路線の選択）

次バージョン（ver15.1、マイナー推奨）は以下 2 路線の**いずれか**を `/issue_plan` で選ぶ。

### 路線 A（優先）: scout smoke test + `issue-scout-noise-risk.md` 消化

- 実施コマンド: `python scripts/claude_loop.py --workflow scout --category util --max-loops 1`
- 観察ポイント:
  - 起票件数が 0〜3 件に収まるか（上限遵守）
  - 起票内容が既存 `ISSUES/util/done/` と重複していないか（重複検出ヒューリスティックの過検出 / 取りこぼし判定）
  - `frontmatter` の `status: raw` / `assigned: ai` / `priority` / `reviewed_at` が全件付与されているか
- クローズ判定: 上記 3 点いずれもクリアなら `issue-scout-noise-risk.md` を `done/` 化。取りこぼしが見えたら `ready / ai` 昇格して次バージョンで修正。

### 路線 B: PHASE7.1 §2（`QUESTIONS/` + `question` workflow）着手

- 路線 A が完了した後に選ぶ（scout の実挙動が §2 設計にフィードバックされる可能性があるため順序固定）
- 新規 SKILL + 新規 YAML を伴うため `workflow: full` 相当。ただし PHASE7.1 内の継続節なのでマイナーバージョン（ver15.1 or ver15.2）で扱う

判断基準: ready/ai は `issue-review-rewrite-verification.md` 1 件のみで util 単体消化不能のため、scout 観察（A）→ MASTER_PLAN 進行（B）の順が合理的。

## 保留事項

- **SKILL / rule 配置パスの大文字小文字表記統一**: ver15.0 ROUGH_PLAN / IMPLEMENT が `.claude/SKILLS/` と記述した一方、実ファイル・validation 参照先は `.claude/skills/`（小文字）。Windows は case-insensitive で事なきを得たが、Linux 実行時に破綻する。次回 SKILL / rule 追加時は **`.claude/skills/` / `.claude/rules/` 小文字で docs 記述も統一**する。rule 化するほど頻発していないため本 handoff で 1 回引き継ぐ運用で足りる。

- **4 ファイル同期契約の rule と docs のずれ**: ver15.0 では scout YAML 追加時に `scripts/README.md` / `USAGE.md` は 4 ファイル同期へ更新されたが、`.claude/rules/scripts.md` §3 の「3 ファイル」記述だけが取り残された（本 RETROSPECTIVE §4 で即時修正済）。今後 YAML 増減時は「rules/scripts.md §3 の同期対象リストも更新する」ことを `/imple_plan` / `/quick_impl` の暗黙チェックに入れる。必要なら ver15.1 以降で SKILL 本文に明記することも検討。

- **scout workflow の model/effort 調整余地**: `claude_loop_scout.yaml` は現状 `opus` / `high`。smoke test で「起票ゼロ連発」or 「ノイズ多発」が見えた場合、effort 調整で挙動を変えられる可能性がある。評価は路線 A 実施後（§3.5 差分評価の材料が揃う）に `/retrospective` で行う。

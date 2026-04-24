# ver16.1 RETROSPECTIVE — PHASE8.0 §2 deferred execution 実装

本版は `research` workflow の **初の本格 self-apply** ケース。PHASE8.0 §2（deferred execution）を 8 step で完走し、テスト 280→296 全 PASS・計画乖離は 3 件だが全て MEMO §計画との乖離に根拠付き記録済み。

---

## §1 ドキュメント構成

### MASTER_PLAN

- `docs/util/MASTER_PLAN/PHASE8.0.md` は ver16.1 で §2 に ✅ 追記済み。§3（token/cost 計測）が唯一残る
- **新 PHASE 骨子の必要性: 不要**。PHASE8.0 §3（ver16.2 割当）が未着手のまま残るため、PHASE9.0 等の骨子作成は時期尚早。次ループで §3 を終えて初めて「PHASE8.0 完走 → 次 PHASE 検討」のトリガーが立つ

### CLAUDE.md

- 直下 `CLAUDE.md` の `## バージョン管理規則` は ver16.0 で `RESEARCH.md` / `EXPERIMENT.md` 説明が入ったままで、ver16.1 では追加肥大なし
- **分割不要**。ver16.2 で §3（cost 計測）の artifact 説明が入った時点で再評価

### docs カテゴリ別

- 本版は minor のため `CURRENT.md` 新規作成なし、`CHANGES.md` のみ生成（規約どおり）
- `RESEARCH.md` / `EXPERIMENT.md` が初めて実体を持った。4 節必須構造（問い / 収集した証拠 / 結論 / 未解決点 — 検証した仮説 / 再現手順 / 結果 / 判断）は **形式的に遵守**されている
- ただし EXPERIMENT.md §U2/§U3 を「未検証」扱いで先送りした判断は、`/experiment_test` SKILL の「同期実行制約下で nested `claude` を発動しない」という IMPLEMENT §5-5 の明示ガードに救われた形。SKILL 側にもこの制約をはっきり書いておく価値がある（§5 で即時適用を検討）

### ISSUES

- 新規追加: `ISSUES/util/medium/deferred-resume-twice-verification.md`（ver16.2+ の実機検証待ち、`raw/ai`）
- 既存持ち越しは据え置き（§4 で整理）

## §2 バージョン作成の流れ（research workflow 8 step 評価）

### 全体評価

8 step `research` workflow は **計画通り完走**。良く機能した点:

- `/issue_plan` が PHASE8.0 §2 着手を「ver16.0 retrospective 指示 + MASTER_PLAN 割当 + FEEDBACKS handoff 3 点一致」で確定。triage の再現性が高い
- `/split_plan` の `IMPLEMENT.md §0` が未解決論点 5 件を列挙し、後続 `/research_context` と `/experiment_test` への入力として一貫して機能した。**handoff → 未解決論点 → RESEARCH/EXPERIMENT → imple_plan の直列パイプが実働した**のが最大の成果
- `/research_context` が 9 問い × 複数一次資料で「確定 / 部分的 / 未確定」を切り分け、**確定部分のみで実装を進める**判断を明示できた。`--bare` を採用しない根拠（観測バイアス）も RESEARCH.md §E に残った
- `/experiment_test` が同期実行制約下で §U2/§U3 を正しく「未検証」扱いにし、ver16.2+ への先送り ISSUE 起票まで繋げた。**research workflow の自己適用時の安全弁**として機能
- `/imple_plan` が RESEARCH/EXPERIMENT を入力に取り、計画乖離 3 件を全て MEMO.md に記録

### 改善候補

- **`/experiment_test` SKILL の「nested `claude` 呼び出し制約」が暗黙**: 今回は IMPLEMENT.md §5-5 で明示的に制約を書いていたため §U2/§U3 が安全に先送りされたが、SKILL 本体にこの制約がないと次回別テーマで self-apply したときに踏みうる。**§5 で即時適用**
- **`RESEARCH.md` / `EXPERIMENT.md` の分量**: 今回は RESEARCH 242 行・EXPERIMENT 187 行で、`research` workflow 標準 artifact としては過剰ではない。ただ、外部調査量が少ないテーマで `research` を選ぶと逆に「埋めるため」の調査が発生しうる。ver16.2 で cost 計測 step が入る際、`research` の採用基準を SKILL 側で再度絞る検討余地あり（観察マター、今回は即時適用なし）
- **YAML sync 契約**: ver16.0 RETROSPECTIVE で提起済の「6 YAML 手動同期」は本版で踏まずに済んだ（`effort` は sync 対象外）。§3（cost 計測）で `command`/`defaults` に新キーが増える場合は ver16.2 で優先度上げ

## §3 次バージョン推奨

### 材料

1. **ISSUE 状況**: `ready/ai` 2 件は構造的カリオーバー、`raw/ai` 3 件（新規 `deferred-resume-twice-verification.md` 含む）は triage 待ち。util 単独で消化可能な件は **ゼロ**
2. **MASTER_PLAN 次項目**: PHASE8.0 §3（token/cost 計測）が ver16.2 に明示割当
3. **現行 PHASE 完走状態**: PHASE8.0 は §1・§2 完了、§3 のみ残。**次ループで §3 を終えれば PHASE8.0 完走**

### 推奨

**ver16.2（マイナー）**。理由:

- PHASE8.0 §3 着手。MASTER_PLAN で明示割当
- §3 は `logging_utils.py` / 新規 `costs.py` / テスト拡張が中心で、§2 のような新ライフサイクル導入ではない。差分規模は `full` workflow 相当（`research` 必須の外部調査論点は薄い）
- ただし「single-turn で `usage` の取得経路が CLI output と 1 対 1 に紐づくか」は事前調査の価値あり。**軽い `research` 採用の判断は `/issue_plan` に委ねる**（閾値判定が微妙）
- メジャー（ver17.0）は不要。PHASE 単位で major を切る運用に従う

### ISSUE 消化を次ループで試みるか

**試みない**。`ready/ai` 2 件は依然 util 単独消化不能、`raw/ai` 3 件は triage 未実施。§3 着手に集中するほうが run の焦点が明確。

## §3.5 workflow prompt / model 評価

### 評価対象: ver16.1（`claude_loop_research.yaml`、8 step research workflow）— 初の実走

差分評価の対象は **ver16.1 で初めて走った 4 step**: `research_context` / `experiment_test` と、effort 引上げした `write_current`。それ以外（`issue_plan` / `split_plan` / `imple_plan` / `wrap_up` / `retrospective`）は ver16.0 `full` workflow での評価を実質継承。

| step | model | effort | 分類 | 理由・次ループ案 |
|---|---|---|---|---|
| issue_plan | opus | high | 維持 | MASTER_PLAN + retrospective + handoff の 3 点一致で着手判断。effort 維持でよい |
| split_plan | opus | high | 維持 | `IMPLEMENT.md §0` で未解決論点 5 件を列挙、§5 でリスク 5 件を整理。effort 高の価値を出した |
| research_context | opus | high | 維持 | 9 問い × 複数一次資料で「確定 / 部分的 / 未確定」切り分け。effort 下げると一次資料化の精度が落ちる懸念。初走のため**当面維持**、ver16.2 で差分観察 |
| experiment_test | opus | high | 維持 | §U2/§U3 を正しく「未検証」扱い、§U4/§U5 は実測で確定。effort 維持 |
| imple_plan | opus | high | 維持 | RESEARCH/EXPERIMENT を統合し計画乖離 3 件を明示記録。effort 下げる余地なし |
| wrap_up | sonnet | medium | 維持 | 完了条件 5 項目の ✅ 付与のみ。現状で十分 |
| write_current | sonnet | **high**（ver16.0→ver16.1 で引上げ） | 維持 | 本版は minor で `CHANGES.md` のみだが、141 行 + 詳細な技術判断 4 件を生成。effort 引上げの効果あり。**今後 minor でも high 維持**を推奨 |
| retrospective | opus | medium | 維持 | 本 step。粒度妥当 |

### 保留メモ

- `research_context` / `experiment_test` は今回 1 回走っただけ。model 下げ（opus → sonnet）の余地はあるが、**初走 1 サンプルでの下げは危険**。ver16.2 で `research` を再採用した場合（cost 計測の `usage` 経路調査など）に差分観察する
- `write_current` effort high は **他 YAML（`claude_loop.yaml` / `claude_loop_quick.yaml`）にも波及適用すべきか**は別議論。minor が minor らしく薄くまとまるケースでは medium で十分。今回は research 版でのみ引上げ済、他は現状維持

## §4 ISSUES 整理

### 新規追加

- `ISSUES/util/medium/deferred-resume-twice-verification.md`（`raw/ai`、ver16.2+ の実機検証待ち）— deferred 経路が本番発動する初のケースで「2 回目の `claude -r` が history を継承するか」を実測する ISSUE。本版スコープ外として正しく先送り

### 持ち越し（削除せず据え置き）

- `ISSUES/util/medium/issue-review-rewrite-verification.md`（`ready/ai`、util 単独消化不能）
- `ISSUES/util/low/toast-persistence-verification.md`（`ready/ai`、Windows 実機必須）
- `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md`（`raw/ai`、triage 待ち）
- `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md`（`raw/ai`、triage 待ち）

### 削除対象

なし（本版で解決した ISSUE は 0 件）。

### レトロスペクティブでの追記

なし。

## §5 即時適用したスキル変更

### 適用対象

**`.claude/skills/experiment_test/SKILL.md`**: 「同期実行制約下で nested `claude` CLI 呼び出しを発動しない」旨の明示ガードを追記。今回は IMPLEMENT.md §5-5 で明示したため安全に先送りできたが、SKILL 本体にもガードを書いておかないと次回別テーマで self-apply した際に踏みうる。

適用範囲は SKILL 文言の追記のみで、既存手順の再構成は行わない。§4「即時適用してよい変更」の範囲内。

---

## §6 次ループ handoff

`FEEDBACKS/handoff_ver16.1_to_next.md` を別途作成。次ループ `/issue_plan` に引き継ぐのは:

- PHASE8.0 §3（cost 計測）着手方針（`research` 軽採用の判断は `/issue_plan` で閾値判定）
- `write_current` effort high は minor でも効果あり、他 YAML 波及は ver16.2 では保留
- §U2/§U3（二重 resume 実機検証）は ver16.2 deferred 経路の本番発動後に実施可能になる

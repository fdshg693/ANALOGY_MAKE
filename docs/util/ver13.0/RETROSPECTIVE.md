# ver13.0 RETROSPECTIVE — PHASE7.0 §3+§4+§5（legacy `--auto` 撤去・FEEDBACKS 運用ルール・REQUESTS→ISSUES 統合）

## 1. ドキュメント構成整理

### 1-1. `docs/util/MASTER_PLAN.md`

- 1 行サマリ形式維持。PHASE7.0 行は wrap_up で「§1・§2・§3・§4・§5 実装済、§6〜§8 未着手」に更新済
- **再構成提案: なし**

### 1-2. `docs/util/MASTER_PLAN/PHASE7.0.md`

- §1〜§5 完了、§6〜§8 未着手。現行 PHASE は未完走で、残り 3 節分（handoff FEEDBACK / rules 整備 / prompt·model 評価）の余地がある
- **新 PHASE（PHASE8.0）骨子は不要**。PHASE7.0 残節が明確で、`/issue_plan` の次ラウンドが §6 以降を拾える

### 1-3. `CLAUDE.md` の肥大化チェック

- ルート `CLAUDE.md`: ver13.0 で `REQUESTS/` 行削除・`ISSUES` 説明 1 行追記。60 行台維持
- `.claude/CLAUDE.md` は ROLE.md 参照のみで健全
- ver13.0 で追加された「unattended prompt 常時注入 / `mode:` 廃止 / REQUESTS 廃止」挙動は `scripts/USAGE.md` と `scripts/README.md` と `ISSUES/README.md` に記載済。ルート CLAUDE.md への更なる反映は不要
- **分割提案: なし**

### 1-4. ISSUES ディレクトリ健全性

- util カテゴリ 4 件（medium 3 / low 1）。ver13.0 で `feedback-abnormal-exit-integration-test.md` が 1 件追加（§4 で意図的に先送り）、`test-issue-worklist-limit-omitted-returns-all.md` は ver12.1 で消化済 → `done/` へ移動済
- 件数・カテゴリ分布とも閾値未到達
- **構成変更提案: なし**

## 2. バージョン作成の流れの検討

### 2-1. 各ステップの効果

| ステップ | 評価 | コメント |
|---|---|---|
| `/issue_plan` | ◎ | `workflow: full` / `source: master_plan` を frontmatter に記録。ready/ai 1 件（util 単体消化不能、ver6.0 から継続持ち越し）を除外し、PHASE7.0 §3+§4+§5 一括着手を決定。ver12.0 RETROSPECTIVE §3-2 推奨を忠実に踏襲 |
| `/split_plan` | ◎ | IMPLEMENT.md で ①`--auto`/`mode`/`auto_args` 削除（callee→caller の順序注意点を明記） ②FEEDBACKS は現状コードが既に要件を充足済と判明（docstring 追記のみ） ③REQUESTS 削除手順を節ごとに整理。§6 で 8 件のリスクを事前抽出。plan_review_agent で review 実施 |
| `/imple_plan` | ○ | 231 tests OK。IMPLEMENT.md §6 リスク 8 件のうち 7 件「検証済」、1 件「先送り（ISSUE 化）」で収束。**計画乖離 2 件**: ①argparse の `allow_abbrev=True` が `--auto` → `--auto-commit-before` に前方一致してしまう問題（IMPLEMENT.md で未予測）→ `allow_abbrev=False` で対処。②`build_command()` の `--append-system-prompt` 常時注入化に伴う test_commands.py のテスト影響が IMPLEMENT.md §1-3 の予測を超えた（`TestBuildCommandWithFeedbacks` / `TestBuildCommandWithAppendSystemPrompt` の等号比較 / `TestOverrideInheritanceMatrix` など 10 件超が連鎖修正）。MEMO「計画からの乖離」に記録済で事後追跡可能 |
| `/wrap_up` | ◎ | PHASE7.0.md §3/§4/§5 を「実装済（ver13.0）」に更新、MASTER_PLAN.md PHASE7.0 行更新。`feedback-abnormal-exit-integration-test.md` を持ち越し ISSUE として保持 |
| `/write_current` | ◎ | 4 分割構成維持。CURRENT_scripts.md に validation.py の legacy key 検査節を追記、CURRENT_skills.md に SKILL 3 本の REQUESTS 参照除去を反映、CURRENT_tests.md に test_validation.py の 4 新規拒否ケース追加を反映 |
| `/retrospective` | — | 本ステップ |

### 2-2. 流れに対する改善提案

ver13.0 は破壊的変更 3 節の一括着手にもかかわらず大きな構造的問題は観察されなかった。以下は観察した現象と、SKILL 改修の要否判断:

- **a. argparse `allow_abbrev=True` の前方一致トラップ（IMPLEMENT.md §1-3 で未予測）**: CLI フラグ撤去時に「同じ prefix を持つ既存フラグがあると前方一致で silently 吸収される」という挙動は argparse 固有の落とし穴。ただしこの種の落とし穴は「CLI フラグ撤去」場面に限定されており、PHASE7.0 残節（§6〜§8）で再発する可能性は低い。SKILL / rules への汎用化ではなく、**本バージョン MEMO.md §「計画からの乖離」に記録する形で十分**。改修不要
- **b. テスト影響の事前予測不足**: IMPLEMENT.md §1-3 は `test_commands.py` の影響範囲を「数件」と予測したが、実際は 10 件超が連鎖修正になった。根本原因は「flag を『条件付きで付く / 付かない』→『常に付く』に変える変更は、そのフラグの存在・非存在・等号比較を参照する全テストを波及的に書き換える」という構造。これは IMPLEMENT.md §1-3 で **`grep -n "<対象フラグ>" scripts/tests/`** を計画段階で走らせれば事前列挙できる。SKILL（`split_plan/SKILL.md` または IMPLEMENT.md テンプレート）に「削除・変更対象のシンボルを tests/ に grep して影響テストを事前列挙する」を 1 行追記する価値はあるが、**既に `split_plan/SKILL.md` の『既存テストの影響予測』節でほぼ同等の指示がある**（ver12.0 RETROSPECTIVE §2-2-b の cwd 依存教訓の流れ）。今回はその指示に従わなかった実装者側の抜けで、SKILL 側の文言強化は限界効用が低い。改修不要
- **c. リスク列挙 → MEMO 検証マトリクス運用の実効性**: ver12.0 で有効性が示されたパターンが ver13.0 でも継続機能（8 件中 6 件が事前予測通り、1 件（argparse allow_abbrev）が想定外、1 件（test_commands 連鎖）が規模過小見積り）。PHASE7.0 §3〜§5 のような破壊的変更では特に有効。**維持**
- **d. callee→caller 順序の事前宣言**: IMPLEMENT.md §4「実装順序」で `resolve_command_config()` の戻り値 arity 変更は callee と caller を 1 コミットにまとめる必要を明示したのは有効。同様の「戻り値シグネチャ変更を伴う撤去」では踏襲する

### 2-3. 即時適用したスキル変更

**なし**。§2-2 の通り、観察された乖離はいずれも SKILL 側の一般化ではなく個別バージョンの MEMO 記録で吸収するのが妥当。

## 3. 次バージョンの種別推奨

### 3-1. 判定材料 3 点の突合

1. **ISSUE 状況**（`issue_worklist.py` / `issue_status.py` 結果）:
   - `ready / ai`: 1 件 — `ISSUES/util/medium/issue-review-rewrite-verification.md`（util 単体消化不能、ver6.0 から 8 バージョン連続持ち越し）
   - `raw / ai`: 3 件 — `cli-flag-compatibility-system-prompt.md`（medium）、`feedback-abnormal-exit-integration-test.md`（medium、ver13.0 §4 で意図的先送り）、`system-prompt-replacement-behavior-risk.md`（low）
2. **MASTER_PLAN の次項目**: PHASE7.0 §6「`/retrospective` 次ループ FEEDBACK handoff」、§7「`.claude/rules` 整備と `scripts` 向け stable rule 追加」、§8「`/retrospective` での workflow prompt/model 利用評価」が未着手
3. **現行 PHASE 完走状態**: PHASE7.0 §1〜§5 完了、§6〜§8 未着手。PHASE 未完走で、新 PHASE 骨子不要

### 3-2. 推奨

**推奨: ver13.1（マイナー、quick）で `feedback-abnormal-exit-integration-test.md` 消化 → ver14.0（メジャー、full）で PHASE7.0 §6 + §7 + §8 一括着手**

推奨根拠:

- **ver13.1（quick, マイナー）**: `feedback-abnormal-exit-integration-test.md` は ver13.0 §4 で意図的先送りされた integration テスト追加で、変更範囲は `scripts/tests/test_claude_loop_integration.py` + 必要なら軽量 YAML fixture の 1〜2 ファイル。ISSUE 本文に「既存 integration テストのテンポラリ cwd パターンを流用」「プロダクションコードには手を入れない」と明記済で quick 適合（3 ファイル以下 / 数十行）。ver13.0 で FEEDBACKS 異常終了時不変条件を docstring / README / USAGE の明文化のみで担保した状態は CI で invariant 破れを検知できない弱点があり、ver13.1 でコード的担保を補完するのが自然
  - `raw/ai` のまま放置するのではなく、ver13.1 着手前に `/issue_plan` で `status: ready` に昇格させる前提
- **ver14.0（full, メジャー）**: PHASE7.0 §6（retrospective handoff FEEDBACK）・§7（`.claude/rules/scripts.md` 新規作成）・§8（retrospective の workflow prompt/model 評価）は、いずれも `/retrospective` SKILL と `.claude/rules` の構造変更を伴う。§6 と §8 は両方とも `/retrospective` SKILL への指示追加で、§7 は rules ファイルの新規追加＋既存 CLAUDE.md / SKILL 群からの stable 規約の移動を伴う。3 節いずれも `.claude/skills/retrospective/SKILL.md` と `.claude/rules/` を同時に触るため、別バージョンに分けると同ファイルを複数回レビューすることになる。一括処理で「retrospective 強化 × rules 整備」を 1 バージョンで完結させるのが効率的。SKILL・rules 構造変更を伴うためメジャー昇格が妥当
- **raw/ai ISSUES の扱い**:
  - `cli-flag-compatibility-system-prompt.md` → ver13.0 で `--auto` 撤去系統の CLI 整理は完了。本 ISSUE は「override キー → CLI flag 存在チェック」で未実装のまま。ver14.0 §7 の rules 整備と合わせて、scripts 系の CLI flag 存在チェックルールを整備する中で再評価
  - `system-prompt-replacement-behavior-risk.md` → ver14.0 §8 の workflow prompt/model 評価と合わせて再評価候補
  - `feedback-abnormal-exit-integration-test.md` → ver13.1 quick で消化（上記）
- **`issue-review-rewrite-verification.md`** → util 単体消化不能のまま持ち越し継続（8 バージョン連続）。app / infra カテゴリで `/issue_plan` / `/split_plan` を動かす機会があれば消化候補

**代替案 A（採用しない）**: ver13.1 で PHASE7.0 §6 直接着手。欠点は §6 が `/retrospective` SKILL 変更を伴い、同 SKILL は §8 でも同じく変更対象になる。2 バージョン連続で同 SKILL を触ると SKILL diff が追いにくくなる

**代替案 B（採用しない）**: ver13.1 skip して ver14.0 で §6+§7+§8+`feedback-abnormal-exit-integration-test` を一括。欠点は integration テスト追加と SKILL/rules 構造変更が混在してレビュー面で追いにくい。ver12.0→ver12.1→ver13.0 で確立された「quick で単体 ISSUE 消化 → full で MASTER_PLAN 新項目一括」パターンが 3 バージョン連続で機能しており、踏襲が妥当

**代替案 C（採用しない）**: ver14.0 で §6 のみ full 実施、§7・§8 は ver14.1 / ver15.0 に分離。欠点は `/retrospective` SKILL を 3 バージョンに渡って触り続けることになる

→ **最終推奨: ver13.1（quick）で `feedback-abnormal-exit-integration-test` 消化 → ver14.0（full）で PHASE7.0 §6+§7+§8 一括着手**

## 4. 振り返り結果の記録

### 4-1. ISSUES ファイルの整理

- **削除**: なし（ver13.0 は MASTER_PLAN 新項目着手バージョンで ISSUE 消化を伴わない。`feedback-abnormal-exit-integration-test.md` は ver13.0 の副産物として新規作成したが、消化は次バージョン以降）
- **持ち越し**（削除しない、理由記載済）:
  - `ISSUES/util/medium/issue-review-rewrite-verification.md` — util 単体消化不能、持ち越し継続（ver6.0 から 8 バージョン連続）
  - `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md` — ver14.0 §7 rules 整備と合わせて再評価予定（raw のまま）
  - `ISSUES/util/medium/feedback-abnormal-exit-integration-test.md` — ver13.0 §4 意図的先送り。ver13.1 quick で消化予定（§3-2）
  - `ISSUES/util/low/system-prompt-replacement-behavior-risk.md` — ver14.0 §8 prompt/model 評価と合わせて再評価予定（raw のまま）
- **frontmatter 無しファイル**: なし

### 4-2. 即時適用したスキル変更

**なし**（§2-3 のとおり）。

### 4-3. 次バージョン ver13.1 への引き継ぎ

`feedback-abnormal-exit-integration-test.md` 消化時の注意点:

1. **スコープ**: ISSUE 本文の「対応方針 1〜3」に従い、step 失敗時に FEEDBACK が `FEEDBACKS/` 直下に残ることを検証する integration テストを追加。プロダクションコードには手を入れない
2. **変更対象想定**: `scripts/tests/test_claude_loop_integration.py` に新規テストクラス追加 + 必要なら軽量テスト YAML fixture 1 本。2 ファイル / 50 行前後で完結見込み
3. **quick 適合性**: ver12.0 RETROSPECTIVE §2-2-b で既に指摘された cwd 依存を避けるため、既存 `TestRunMainAuto` 等のテンポラリ cwd パターンを流用。subprocess 起動 + `sh -c "exit 1"` 相当の擬似 step で再現する想定
4. **ver13.0 実装との相互作用**: ver13.0 で `--append-system-prompt` が常時注入される仕様に変わったため、テスト内の assertion は「unattended prompt が含まれる」前提で書く。`build_command()` の挙動変更（MEMO §「計画からの乖離」参照）を取り込み済
5. **raw → ready 昇格**: ver13.1 の `/issue_plan` 冒頭で `status: raw → ready` / `reviewed_at` 更新を行うこと

### 4-4. ver14.0（PHASE7.0 §6+§7+§8）への事前メモ

ver13.1 完了後に `/issue_plan` が ROUGH_PLAN を作る際の前提として:

- **§6 `/retrospective` → 次ループ FEEDBACK handoff**: `/retrospective` SKILL に「必要に応じて次のループ向けに `FEEDBACKS/` 配下へファイルを書き出す」指示を追加。handoff 内容は「次に着手すべき ISSUE」「注意点」「workflow 設定見直しメモ」。§4 で確立した「1 ループで 1 回消費 → `FEEDBACKS/done/` 移動」ルールと自然に接続する（追加実装は基本的に SKILL 指示の追記のみで、scripts 系コードは触らない想定）
- **§7 `.claude/rules/scripts.md` 新規作成**: `scripts/**/*` を対象にした stable rule file を追加。`pathlib` 利用、CLI 引数処理、ログ出力、frontmatter / YAML 更新時の作法など「変わりにくい規約」を定義。既存 CLAUDE.md / SKILL にある重複を rules 側へ寄せ、`scripts/README.md` / `scripts/USAGE.md` とは volatile / stable で責務分離する。`.claude/rules/claude_edit.md` が既存のため、`paths:` frontmatter 運用は踏襲
- **§8 `/retrospective` で prompt/model 評価**: 各 step の system prompt / model / temperature が役割に合っていたかを `/retrospective` が評価する。評価結果を「維持」「調整」「削除候補」の形で §6 の FEEDBACK handoff に接続する設計。PHASE7.0 §1 で既に step 別 override 機構を整備済のため、評価結果を YAML への具体的な修正指示へ落とし込む接続が自然
- **`.claude/` 編集手順**: ver13.0 で確認済の `claude_sync export → edit → import` 手順を踏襲。§7 の `.claude/rules/scripts.md` 新規追加も同手順で行う
- **ver14.0 のテスト戦略**: §6〜§8 はいずれも SKILL / rules 変更中心で Python コード変更は最小想定。テストは既存 231 件が通過することを担保する回帰テスト中心でよい。新規テスト追加の必要性は `/split_plan` で判断

### 4-5. 今バージョンからの学び（手法面）

- **破壊的 CLI / schema 変更は callee↔caller を 1 コミットで整合**: IMPLEMENT.md §4「実装順序」で `resolve_command_config()` の戻り値 arity 変更を callee と caller を同一コミットにまとめる方針を明示したのが有効。中間状態で `ImportError` / `ValueError` が発生せず、git bisect での回帰追跡も安定する。PHASE7.0 §6 以降の SKILL 仕様変更では該当しないが、今後の破壊的変更バージョンでは踏襲推奨
- **YAML schema 変更の「二重網」拒否**: `workflow.py:resolve_command_config()` の runtime 保険 + `validation.py` の起動前 frontline の 2 層で旧 YAML を拒否する構造は、片側経路が抜けても他方が捕まえるため安全。ver14.0 §7 で rules 化する候補（「schema 変更時は runtime + validation の二重網」）
- **test_commands.py 連鎖修正の規模予測失敗**: IMPLEMENT.md §1-3 は「flag を『条件付きで付く』→『常に付く』に変える場合のテスト影響」を過小見積りした。今後の類似変更（フラグの存在条件変更）では、計画段階で `grep -n "<対象フラグ>" scripts/tests/` を走らせて影響テストを列挙すべし
- **`raw/ai` ISSUE の昇格タイミング**: ver13.0 で新規作成した `feedback-abnormal-exit-integration-test.md` は raw で作成した。ver13.1 `/issue_plan` 冒頭でレビューし `ready/ai` に昇格させる流れは、ver12.0 RETROSPECTIVE §4-1 で確立したパターンを踏襲する
- **MASTER_PLAN 新項目着手バージョンでの ISSUE 消化ゼロの継続**: ver10.0（§1 単独）/ ver12.0（§2 単独）/ ver13.0（§3+§4+§5 一括）で 3 バージョン連続成功。焦点が保たれ plan_review_agent の承認も軽微対応で済む。PHASE7.0 §6+§7+§8 の ver14.0 でも踏襲推奨

---
name: retrospective
disable-model-invocation: true
user-invocable: true
---

# 役割

あなたは、最新のバージョンアップの結果・結果が出るまでの過程を振り返り、次のバージョンアップに向けて改善点を洗い出す役割を担います。
実装結果は直前のGitコミットとの差分で表されるものとします。

## 1. ドキュメント構成整理
- `docs\{カテゴリ}\MASTER_PLAN.md` への追加・ファイル分割・再構成が必要かの検討・提案
  - `ISSUES` が肥大化しだした場合、ほぼマスタープランが実装済などの場合は、新たなバージョン・構成のマスタープランの作成が有効な可能性があります
- **現行 PHASE 完走時の対応**: `docs/{カテゴリ}/MASTER_PLAN/PHASE{N}.md` の最新 PHASE が「すべて実装済」となった場合、次 PHASE の骨子（`PHASE{N+1}.md`）作成の要否を検討する
  - 新 PHASE の具体化作業（骨子の執筆）は `/retrospective` の責務外。次 `/issue_plan` で判断させる
  - 既存 ISSUES で当面吸収できる場合は、PHASE 新設を焦らず本 RETROSPECTIVE §3 で「次バージョンは ISSUES 消化」と明示する
  - 既存 ISSUES で吸収できない規模のテーマが見えている場合のみ、本 RETROSPECTIVE に PHASE 新設の方向性メモを残す
- `CLAUDE.md` の分割検討・提案
  - 肥大化しないように、サブフォルダ固有の内容はサブフォルダ内の `CLAUDE.md` に分割するなどの方法が考えられます

## 2. バージョン作成の流れの検討

以下のバージョン作成の流れが、どれほど効果的だったかを振り返る。
そのうえで、改善点が考えられる場合は、提案すること。
バージョン作成で活用されている `.claude` 配下のスキル等のファイルをどのように変更することが必要かも提案すること。

### バージョン作成の流れ
- カテゴリ: !`cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app`
- 最新バージョン番号: !`bash .claude/scripts/get_latest_version.sh`
- 最新のバージョン作成の結果が `docs/{カテゴリ}/ver{最新バージョン番号}/` に記載されている

各バージョンは以下の6ステップで作成される（フルワークフロー）。本スキルはステップ6に相当する:

1. `/issue_plan` — 現状把握・ISSUE レビュー・`ROUGH_PLAN.md` と `PLAN_HANDOFF.md` 作成（frontmatter に `workflow: quick | full` / `source: issues | master_plan` を記録）を行った
2. `/split_plan` — `ROUGH_PLAN.md` と `PLAN_HANDOFF.md` を受けて `REFACTOR.md` ・ `IMPLEMENT.md` を作成し、plan_review_agent で実装計画の review を行った
3. `/imple_plan` — 計画に基づいて実装し、`MEMO.md` に実装メモを記載した
4. `/wrap_up` — `MEMO.md` の各項目に対応し、細かい改善を行った
5. `/write_current` — `CURRENT.md` ・ `CLAUDE.md` の作成・更新を行った
6. `/retrospective` — **（本ステップ）** 振り返りを行い、次バージョンへの改善点を整理する

（軽量ワークフロー quick は `/issue_plan → /quick_impl → /quick_doc` の 3 ステップ構成。本スキルは quick には含まれない）

## 3. 次バージョンの種別推奨

次バージョン判定の材料は以下 3 点。どれか一つだけで決めず、3 点を突き合わせて判断する:

1. **ISSUE 状況**（`issue_worklist.py` 結果）: `ready / ai` の件数・優先度・性質
2. **MASTER_PLAN の次項目**: 現行 PHASE に未実装の節が残っているか
3. **現行 PHASE 完走状態**: 最新 PHASE の全節が実装済なら、次 PHASE 骨子作成 or 既存 ISSUES 消化のどちらに寄せるかを明示する

次バージョンの方針を決める前に、AI が着手可能・レビュー待ちの ISSUE を把握する:

- 現在カテゴリの着手候補: !`python scripts/issue_worklist.py`
- 機械可読形式: !`python scripts/issue_worklist.py --format json`

次に予定されるタスク（MASTER_PLAN の次項目、未解決 ISSUES）を踏まえて、次バージョンがメジャー・マイナーのどちらが適切かを推奨する。

- 次のマイナーバージョン候補: !`bash .claude/scripts/get_latest_version.sh next-minor`
- 次のメジャーバージョン候補: !`bash .claude/scripts/get_latest_version.sh next-major`

## 3.5 workflow prompt / model 評価

直前バージョンで実行した workflow YAML（`scripts/claude_loop.yaml` / `scripts/claude_loop_quick.yaml` / `scripts/claude_loop_issue_plan.yaml`）の各 step について、prompt / model / effort の妥当性を評価する。評価は「維持 / 調整 / 削除候補」の 3 分類で記録する。

### 評価観点

各 step について以下を確認する:

1. `system_prompt` / `append_system_prompt` が step 役割に合っているか、長すぎないか、他 step と指示重複していないか
2. `model`（`opus` / `sonnet` / `haiku`）と `effort`（`low` / `medium` / `high` / `xhigh` / `max`）が品質・速度・コストに見合っていたか
3. step 間の `continue: true` / 新規セッション選択が適切だったか

### 分類と記録粒度

- **維持**: 現状で問題なし。1〜2 行で根拠を残す
- **調整**: 現状で軽微な問題あり。分類理由（1〜2 行）＋ 次ループでの具体的な修正案（例: `effort: medium → high`、prompt の一部削除）を添える
- **削除候補**: step 自体または該当設定を外す方向。分類理由と削除後の想定挙動を添える

### 出力先

- 本文（全 step の評価）は `RETROSPECTIVE.md` §8 相当の節に残す
- そのうち「次 1 ループ以内に試す具体的な調整」のみ §4.5 handoff FEEDBACK に転記する。複数バージョンにまたがる検討や、すぐには試さない観察メモは `RETROSPECTIVE.md` に留める（handoff の消費枠を無駄にしない）

### 評価テンプレ例

```markdown
## §8 workflow prompt / model 評価

### 評価対象バージョン: ver{X.Y}

| step | model | effort | 分類 | 理由・次ループ案 |
|---|---|---|---|---|
| issue_plan | opus | high | 維持 | ROUGH_PLAN.md の判断精度良好 |
| split_plan | sonnet | medium | 調整 | IMPLEMENT.md の詳細が浅い。effort → high で試す |
| imple_plan | opus | max | 維持 | 実装品質問題なし |
```

### 省略条件

評価材料がないループ（直前バージョンでモデル変更を試していない / step 実装差分が皆無）は本節を省略してよい。毎ループで形骸的な評価を要求しない。差分評価（直前バージョンから変えた step のみ再評価）を基本姿勢とする。

### 「即時適用」との関係

本節は評価記録であり、YAML / SKILL の実編集は §4.5 handoff → 次ループの `/issue_plan` → ユーザー判断 or AI 編集という経路で行う。評価時点では YAML を直接編集しない（評価と適用の分離）。

## 4. 振り返り結果の記録

- 振り返り結果を `docs/{カテゴリ}/ver{最新バージョン番号}/RETROSPECTIVE.md` に記録する
- スキルへの改善提案がある場合は、提案だけでなく本ステップ内で `.claude/skills/` 配下のファイルを直接編集して即時適用する（次バージョンへの持ち越しを防ぐ）
  - **即時適用してよい変更**: SKILL 内の文言修正・手順追記・判断基準の追加・既存ガイドラインの明確化・SKILL の新規作成・ワークフローステップの追加/削除・エージェント定義の変更など、ほとんど全ての`.claude`配下ファイルや、ワークフロースクリプトの設定ファイル
  - **ユーザー確認が必要な変更**: リスクのあるスクリプトのワークフローへの組み込み、過度に大量の既存ファイルの変更を伴うもの（目安: 計500行以上）、新規追加に関してはユーザー確認は不要
- ISSUES ファイルの整理（PHASE5.0 以降のステータス対応）:
  - **対応済み（実装が完了し、ISSUE の目的を果たした）** → 削除する
  - **持ち越し中（`status: ready / ai` で残してある、`status: need_human_action / human` で人間対応待ち、または明示的に次バージョン以降に先送り宣言したもの）** → 削除しない。MEMO.md / 当 RETROSPECTIVE.md に持ち越し理由を記載
  - frontmatter 無し（`raw / human` 扱い）→ 触らない
  - **レトロスペクティブで追記すべきと判断したもの**: レトロスペクティブで追記すべきと判断したものは、そのまま追記する

## 4.5 次ループへの FEEDBACK handoff

retrospective の成果のうち「次ループで 1 回だけ読ませたい補助線」を `FEEDBACKS/<filename>.md` に書き出し、次ループの `/issue_plan` に引き継ぐ。恒久メモリではない点に注意する（書き出された FEEDBACK は次ループで 1 回だけ消費され、その後 `FEEDBACKS/done/` へ退避される。§4 運用ルールに従う）。

（`PLAN_HANDOFF.md` は plan 段階の判断ログとして同バージョン内に残り、本節 `FEEDBACKS/handoff_*.md` は次ループへの 1 回限りの補助入力。役割が異なるため二重管理にはならない）

### 目的

`RETROSPECTIVE.md` は記録として残り続けるが、次ループの `/issue_plan` が毎回読み直す保証はない。handoff は「retrospective が次ループに強く渡したい 1 回限りの補助入力」だけを抽出する場として機能する。

### 書き出し対象

以下のいずれかに該当するものを 1 ファイルに集約する:

1. 次に着手すべき ISSUE の候補（優先選定の根拠つき）
2. 直前バージョンで保留した判断の継続確認事項
3. workflow 設定（prompt / model / temperature）見直しメモ（§3.5 評価結果との接続点）
4. 次 `/issue_plan` に渡したい注意点・判断のヒント

### 書き出さないケース

「次ループで特に引き継ぐべき内容がない」なら書き出しを省略する。空の handoff / 感想のみの FEEDBACK は禁止（次ループの FEEDBACK 消費枠を無駄にしない）。

### ファイル書式

- **ファイル名**: `FEEDBACKS/handoff_ver{現行バージョン}_to_next.md`（ver14.0 からの handoff なら `FEEDBACKS/handoff_ver14.0_to_next.md`）
- **frontmatter**: `step: issue_plan`（次ループの `/issue_plan` にのみ注入する。retrospective 由来の handoff はほぼ全て issue_plan 向けのため、catch-all ではなく step 限定で書く）
- **本文**: 「## 背景」「## 次ループで試すこと」「## 保留事項」の 3 節を推奨

### 例

```markdown
---
step: issue_plan
---

## 背景

ver{X.Y} の retrospective で、§3.5 評価により `/split_plan` の effort を上げる余地が確認された。

## 次ループで試すこと

- `claude_loop.yaml` の `split_plan` step を `effort: medium → high` で試す
- 併せて `imple_plan` の system_prompt 末尾の重複記述（rules にも書かれている）を削除

## 保留事項

- `cli-flag-compatibility-system-prompt.md` は本バージョンで rules 化済。次ループで done 化判断
```

### 即時適用対象

本節の追記自体が `/retrospective` SKILL 編集であり、§4「即時適用してよい変更」の範囲に含まれる。`scripts/claude_sync.py` 手順（export → edit → import）で反映する。

## 5. Git にコミットする

### 即時適用の検証

コミット前に、本ステップで即時適用したスキル変更が実際にステージングに含まれていることを確認する:

1. `git add` で変更をステージングする
2. `git diff --cached --name-only` を実行し、即時適用対象のファイルが含まれていることを確認する
3. 含まれていない場合は、適用漏れの変更を再度実施してからステージングする

### コミット・プッシュ

- 今回の変更内容を元にコミットメッセージを作成して、コミット・プッシュを行ってください

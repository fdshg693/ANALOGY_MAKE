---
workflow: full
source: master_plan
---

# ver15.0 ROUGH_PLAN — PHASE7.1 §1 `issue_scout` workflow の新設

## ISSUE レビュー結果

- `review / ai` の ISSUE: **0 件**（走査対象なし）
- 状態遷移: なし（書き換え・追記ともに実施せず）
- 対象パス: なし

## ISSUE 状態サマリ（util カテゴリ / ver15.0 着手前時点）

| status × assigned | 件数 | 対象ファイル |
|---|---|---|
| `ready / ai` | 1 | `ISSUES/util/medium/issue-review-rewrite-verification.md` |
| `review / ai` | 0 | — |
| `raw / ai` | 2 | `low/rules-paths-frontmatter-autoload-verification.md` / `low/scripts-readme-usage-boundary-clarification.md` |
| `need_human_action / human` | 0 | — |
| `raw / human` | 0 | — |

- `done/` 配下: 7 件（過去バージョンで処理済）
- `high/`: 空
- 総数: 3 件（`ready` 1 + `raw` 2）

## 背景と選定経緯

### ver14.1 完走後の状態

- ver14.0 で PHASE7.0 §6+§7+§8 を一括完了（retrospective FEEDBACK handoff / `.claude/rules/scripts.md` / workflow prompt/model 評価）
- ver14.1（quick）で handoff 消費による raw/ai 2 件の再評価 → 両件 `done/` 移動。コード変更はゼロ、観察ループとして機能
- ver14.0 RETROSPECTIVE §1 が掲げた「ver14.0 成果の 1〜2 ループ観察」は ver14.0（実装）+ ver14.1（観察込み ISSUE 消化）で 2 ループ消化。handoff 消費機構・§3.5 評価観点・`.claude/rules/` 配置のいずれも破綻報告なし

### util カテゴリの現時点の着手候補

ISSUE 側:

- `ready / ai` 1 件（`issue-review-rewrite-verification.md`）は util 単体では消化不能。app / infra カテゴリで `/split_plan` / `/quick_plan` を動かすタイミングまで持ち越し（ver6.0 以来、ver14.0 / ver14.1 でも継続持ち越しが明記済）。本バージョンでも触らない
- `raw / ai` 2 件（`rules-paths-frontmatter-autoload-verification.md` / `scripts-readme-usage-boundary-clarification.md`）は `/issue_plan` の選定ポリシー上「着手対象外」（`review` 済みでないため）。観察保持として据え置き

MASTER_PLAN 側:

- `docs/util/MASTER_PLAN.md` の進捗表では PHASE7.0 まで全節実装済、PHASE7.1 は **未実装**
- `docs/util/MASTER_PLAN/PHASE7.1.md` §「実装進捗」は §1〜§4 を ver15.0〜ver15.2 の 3 段階に分割済み。§1（`issue_scout` workflow）想定バージョン = **ver15.0**

### なぜ ver14.2 minor ではなく ver15.0 major か

- ready/ai は blocked / raw/ai は着手対象外のため、util 単体で消化可能な small-chunk ISSUE は残っていない
- PHASE7.1 §1 は「新規 SKILL（`.claude/SKILLS/issue_scout/SKILL.md`）+ 新規 workflow YAML（`scripts/claude_loop_scout.yaml`）+ `claude_loop.py` への workflow 入口追加」という **アーキテクチャ拡張** を伴う
- メジャーバージョンアップ条件（`MASTER_PLAN` 新項目着手 / 新規 SKILL 追加によるアーキテクチャ変更）を満たすため ver15.0
- ver14.0 RETRO §3 が「メジャー昇格は PHASE8.0 骨子作成 or handoff/rules 再設計」と述べていた条件のうち、PHASE7.1 §1 は既に骨子（`PHASE7.1.md`）が MASTER_PLAN 側に存在する新項目着手に該当するため、メジャー昇格の妥当性あり

### なぜ PHASE7.1 §2〜§4 を本バージョンに含めないか

PHASE7.1.md は §1〜§4 を ver15.0〜ver15.2 の 3 段階実装として明記しており、本バージョン（ver15.0）は **§1 のみ** にスコープを絞る。

- §2（`QUESTIONS/` と `question` workflow）想定 = ver15.1 → §1 の実運用観察後に着手
- §3（`ROUGH_PLAN.md` / `PLAN_HANDOFF.md` 分離）想定 = ver15.1 → §2 と一緒に
- §4（run 単位通知）想定 = ver15.2 → notify.py 変更は独立性が高いため最後

一度に §1〜§4 を実装すると（a）1 バージョンが肥大化、（b）SKILL 間依存（issue_scout が起票した ISSUE を既存 issue_review が扱えるか、など）の観察機会が失われる、（c）`claude_loop.py` の workflow 入口が 2 種類（scout / question）同時に増えて差分特定が困難、という 3 点で split しておく価値が大きい。

## ver15.0 スコープ（PHASE7.1 §1 のみ）

### この版で達成すること

「能動的に潜在課題を探索し、ISSUE として起票するだけで止める opt-in workflow」を util カテゴリのユーティリティ基盤に追加する。既存 `auto` / `full` / `quick` の挙動は変えない。実装ループの責務は増やさない。

具体的には以下 4 点を満たす状態まで持っていく:

1. **明示実行専用の新 workflow `issue_scout` が存在する**
   - `--workflow scout`（または同等の入口）で起動可能
   - 既存 `--workflow auto` の自動選択ロジックには混入させない
2. **`issue_scout` の 1 run が以下だけを行う**
   - 対象カテゴリのコード / tests / docs / 直近 `RETROSPECTIVE.md` / `MASTER_PLAN.md` / 既存 `ISSUES/` を読む
   - 潜在課題を 1〜3 件抽出し、`ISSUES/{カテゴリ}/{priority}/*.md` に新規起票する
   - run 終了時サマリ（起票件数・パス・タイトル）を出力
3. **起票粒度ルールが定義されている**
   - 原則 `raw / ai` で起票
   - 再現条件・影響範囲・修正方向まで自力で固められた小粒課題のみ `ready / ai` を許可
   - 起票前に既存 `ISSUES/` / 直近 `RETROSPECTIVE.md` / `MASTER_PLAN` を参照して重複・方針既定項目を避ける
4. **起票後の接続性が docs 上で担保されている**
   - 起票された ISSUE が既存 `issue_review` / `issue_plan` の流れに自然に乗ることが確認できる（手順が docs に書かれている）
   - `auto` / `full` / `quick` が `issue_scout` を自動混入させないことが docs 上で明示されている

### 含めない（スコープ外）

- PHASE7.1 §2（`QUESTIONS/` / `question` workflow）→ ver15.1
- PHASE7.1 §3（`ROUGH_PLAN.md` / `PLAN_HANDOFF.md` 分離）→ ver15.1
- PHASE7.1 §4（run 単位通知）→ ver15.2
- `issue_scout` を `auto` へ自動混入させる仕組み
- Question / QUESTIONS / 調査専用出力
- 新規 CLI オプションの追加（`--scout` のような独自フラグ）が真に必要かは IMPLEMENT.md の判断に委ねる（既存 `--workflow <path>` で十分な可能性あり）
- app / infra カテゴリへの `issue_scout` 初回適用（ver15.0 では util 側のインフラ整備に専念）

### ユーザー体験の変化

- 開発者は定期監査や節目のタイミングで `python scripts/claude_loop.py --workflow scout --category util` 等を手動起動し、コード変更なしに潜在課題を ISSUE 化できる
- 通常のループ（`auto` / `full` / `quick`）は今まで通り動き、ユーザーの明示起動がない限り探索 flow は走らない
- 起票された ISSUE は次回 `/issue_plan` 冒頭のレビューフェーズで `review / ai` → `ready / ai` or `need_human_action / human` の既存遷移に載る

## 関連する MASTER_PLAN / 先行成果

### 入力（参照する既存資産）

- `docs/util/MASTER_PLAN/PHASE7.1.md` §「やること 1」— スコープ定義の一次資料
- `docs/util/MASTER_PLAN/PHASE7.1.md` §「やること 1-2 完了条件」— 本バージョンの受け入れ基準
- `docs/util/MASTER_PLAN/PHASE7.1.md` §「ファイル変更一覧」— IMPLEMENT.md 側で参照する変更対象ファイル群の一次資料（`issue_scout` 関連のみ抽出）
- `docs/util/MASTER_PLAN/PHASE7.1.md` §「リスク・不確実性」— IMPLEMENT.md のリスク列挙で再掲・深掘り対象
- `docs/util/ver14.0/RETROSPECTIVE.md` §1・§3 — メジャー昇格判断の経緯
- `docs/util/ver14.0/CURRENT.md` / `CURRENT_scripts.md` / `CURRENT_skills.md` — workflow / SKILL / scripts 構造の現況スナップショット
- `.claude/SKILLS/issue_plan/SKILL.md` / `.claude/SKILLS/issue_review/SKILL.md` — 起票後の接続先 SKILL（ISSUE 起票時の frontmatter 互換性要件）
- `scripts/claude_loop.py` / `scripts/claude_loop_lib/` — workflow 入口の現状実装
- `scripts/claude_loop.yaml` / `scripts/claude_loop_quick.yaml` / `scripts/claude_loop_issue_plan.yaml` — workflow YAML の既存パターン（新 YAML の骨格の参考）
- `scripts/README.md` / `scripts/USAGE.md` — scout workflow の説明追記先
- `ISSUES/README.md` — frontmatter 運用（raw / ready / review / ai / human）の一次資料、scout 起票ルールの補足追記先候補

### 関連 ISSUE パス（本バージョンでは触らない）

- `ISSUES/util/medium/issue-review-rewrite-verification.md`（継続持ち越し）
- `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md`（観察保持）
- `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md`（観察保持）

## workflow 選択の根拠

- **`workflow: full`**: MASTER_PLAN 新項目着手 + 新規 SKILL / 新規 YAML / `claude_loop.py` への入口追加は quick 閾値（3 ファイル / 100 行以下）を確実に超える
- **`source: master_plan`**: ISSUE 起点ではなく `PHASE7.1.md` §1 を出所とするため
- split_plan → imple_plan → wrap_up → write_current → retrospective のフル手順を通す。plan_review_agent による IMPLEMENT.md レビューは本 ROUGH_PLAN ではなく後続 `/split_plan` で実施

## 事前リファクタリング要否

**事前リファクタリング不要**。既存コードは新 workflow 追加を想定した拡張点（`RESERVED_WORKFLOW_VALUES` / `resolve_workflow_value()` / `_resolve_target_yamls` / SKILL ディレクトリ配置規約）を既に持っており、追加変更はこれらの既存パターンの踏襲で済む。構造を変えずに add-only で済むため REFACTOR.md は作成しない。

## 後続 `/split_plan` への引き継ぎ事項

### 判断経緯（本 ROUGH_PLAN の選定ロジック）

- ready/ai は blocked、raw/ai は着手対象外、観察期間は満了 → MASTER_PLAN の次項目に進む決定
- PHASE7.1 §1 を選んだ理由: ver15.0 想定バージョン一致 + `issue_scout` が他 3 節に依存しない独立実装可能な骨子である（§2 Question / §3 PLAN_HANDOFF / §4 通知は SKILL 側または notify.py 側に閉じ、`issue_scout` の ISSUE 起票機能とは独立）

### IMPLEMENT.md で必ず深掘りしてほしいリスク観点

PHASE7.1.md §「リスク・不確実性」のうち、本バージョンで関連する項目は以下 4 点。IMPLEMENT.md §リスク表に展開し、MEMO.md §リスク検証結果でクローズしていく想定:

1. `issue_scout` の判定粒度が粗いと `raw / ai` が増えて `ISSUES/` がノイズ源化する → 起票件数上限・重複検出・起票前チェックリストで抑制
2. 既存 ISSUE と新規起票の重複検出をどう実装するか（タイトル類似 / キーワード一致 / 担当者判断のどれに寄せるか）
3. 探索対象ディレクトリのスコープ（category 単位で閉じるか、リポジトリ全体か）の既定値
4. `issue_scout` 起票後に `issue_review` フェーズに乗せる際の frontmatter 整合（`status` 初期値・`reviewed_at` 付与タイミング）

### 選定から除外した候補と除外理由

- PHASE7.1 §2〜§4 を本バージョンに含める案 → バージョン肥大化・観察機会喪失のため除外（上述「なぜ PHASE7.1 §2〜§4 を本バージョンに含めないか」参照）
- ver14.2 minor で `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md` を処理する案 → raw/ai は `/issue_plan` 選定ポリシー上「着手対象外」、かつ ver14.0 RETRO §3 の観察期間を満了した今は MASTER_PLAN 新項目着手が優先順位として妥当のため除外
- PHASE8.0 骨子作成を本バージョンに含める案 → PHASE7.1 が未着手のまま PHASE8.0 を先行設計するのは不自然、かつ PHASE7.1 §1 の実運用観察結果が PHASE8.0 テーマ選定の入力となるため先送り

## 運用観察（次バージョン以降への引き継ぎ）

本バージョン完走後、ver15.1 `/issue_plan` 向けに以下を `/retrospective` で handoff 候補として検討する:

1. `issue_scout` 初回実行で起票された `raw / ai` の質（シグナル / ノイズ比率）
2. 起票された ISSUE が `issue_review` フェーズで `ready / ai` 昇格可能な粒度だったか
3. `--workflow scout` の起動方法が `claude_loop.py` の既存入口と整合していたか

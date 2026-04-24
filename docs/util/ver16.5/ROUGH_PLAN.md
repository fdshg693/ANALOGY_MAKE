---
workflow: full
source: issues
---

# ver16.5 ROUGH_PLAN — `issue_review` SKILL に `ready/ai` 長期持ち越し再判定ルートを追加

ver16.4 MEMO §後続版引き継ぎ で「次 minor の主眼候補」と明示された `issue-review-long-carryover-redemotion`（ready/ai）を ver16.5 の単一主眼として選定する。本 ISSUE 起票時点（ver16.3）で既に設計提案 3 要素（スキャン対象拡張 / しきい値 2 段階 / 判定ルート）が本文に書き起こされており、ISSUE 本文の推奨に従って「最小構成 = スキャン対象拡張 + 5 バージョン『要再判定』警告のみ」まで切り落として着手する。強制降格（10 バージョンルール）および meta カウンタフィールドの追加は後続版（ver16.6 以降）に委ねる。

## ISSUE レビュー結果

- ready/ai に遷移: 0（本版の review フェーズでは対象ゼロ）
- need_human_action/human に遷移: 0
- 追記した `## AI からの依頼`: 0

走査結果: `status: review` かつ `assigned: ai` の ISSUE は util カテゴリに 0 件。`issue_review` SKILL §1 スキャン規約に従い、現時点では書き換え対象なし。`raw/ai` 2 件（`rules-paths-frontmatter-autoload-verification` / `scripts-readme-usage-boundary-clarification`）は `review` ではないため現行仕様では対象外（本版が実装する長期持ち越し再判定ルートとも別軸のため触れない）。

## ISSUE 状態サマリ

| status / assigned | 件数 |
|---|---|
| ready / ai | 4 |
| review / ai | 0 |
| need_human_action / human | 0 |
| raw / human | 0 |
| raw / ai | 2 |

出典: `python scripts/issue_status.py util`（本 review フェーズ通過後、ver16.4 closeout 直後の状態そのまま）。ver16.4 で ready/ai=5 → 本版開始時 ready/ai=4（ver16.4 で `costs-representative-model-by-max-cost` が done 化）。review フェーズでの状態遷移はゼロ。

選定理由・除外理由の詳細および「長期持ち越し対象」の具体的内訳は `PLAN_HANDOFF.md` に記載。

## バージョン種別の判定

**マイナー（ver16.5）**。根拠:

- MASTER_PLAN の新項目（PHASE9.0 骨子）には着手しない（PHASE8.0 まで全フェーズ実装済。SKILL 拡張ガイドラインの優先順位①「既存 ISSUES の消化を優先」に従う）
- アーキテクチャ変更・新規外部ライブラリ導入・破壊的変更のいずれも無し。`issue_review` SKILL の既存スキャン仕様に「走査対象の条件 1 つを OR 追加」する追補変更
- 実装スコープは SKILL.md 2 本 + `ISSUES/README.md` の計 3 ファイル編集で完結する見込み（Python コード追加なし。scripts 側のロジック変更も含めない）

## ワークフロー選択

**`full`（6 step）**。根拠:

- quick 閾値「3 ファイル以下・100 行以下」を**編集ファイル数は満たすが、行数はボーダーライン**（SKILL.md 2 本への追記は各 30〜50 行、README 追記 20〜30 行で合計 100 行前後）。判定に迷う領域に落ちる
- 変更対象が workflow を駆動する SKILL 本体である。`issue_review` SKILL は `/split_plan` / `/quick_plan` / `/issue_plan` の 3 経路に影響し、拡張仕様の齟齬は以降の全カテゴリ（app / infra / cicd / util）に波及する。設計レビュー（plan_review_agent）を通せる `full` の方が安全側
- 仕様選択に **設計判断余地** が残る: 「N バージョン持ち越し」をどう測定するか（`reviewed_at` の日付差分 vs 持ち越し回数カウンタ vs 既存 ISSUE 生成日との差分）を IMPLEMENT.md で確定させる必要がある。`imple_plan` step を含む full の方が粒度が合う
- `research` 4 条件（外部仕様確認 / 実装方式実験 / 長時間検証 / 隔離環境試行）はいずれも該当しない。外部仕様は不要、実装方式は SKILL.md 内のロジック選定で完結、長時間検証・experiments/ 利用もなし
- SKILL ガイドライン「判断に迷う場合 → 安全側で `full`」を優先適用

## 着手スコープ

### 主眼: `issue_review` SKILL に `ready/ai` 長期持ち越し再判定ルートを追加

対象 ISSUE: `ISSUES/util/low/issue-review-long-carryover-redemotion.md`

提供機能の変化（ユーザー / AI 視点）:

- `/issue_plan` 実行時、`status: ready` かつ `assigned: ai` の ISSUE のうち「長期間着手されていないもの」が出力サマリに「再判定推奨」欄として列挙されるようになる
- 当該 ISSUE の frontmatter 自体は書き換わらない（`status: ready / ai` は維持）。出力サマリで人間 / AI に目視判断を促すに留める
- 実害の例として util カテゴリには現時点で 3 件の長期持ち越し候補が該当する想定（ver6.0 以来の `issue-review-rewrite-verification`、ver15.4 以来の `toast-persistence-verification`、ver16.2 以来の `deferred-resume-twice-verification`）

### 実装骨子（方式は IMPLEMENT.md で確定）

本版で書き換える対象は**仕様書**であり、scripts 側のロジック追加は含めない方針。主な追補内容:

- `.claude/skills/issue_review/SKILL.md` §1 スキャン: 対象条件に「`status: ready` かつ `assigned: ai` かつ『N バージョン以上前から持ち越し』」を OR 追加。しきい値 N の既定値と測定指標（`reviewed_at` の日付差分を第一候補とする方針）を記述
- `.claude/skills/issue_review/SKILL.md` §5 サマリ報告: plan 本文への「再判定推奨」第 3 ブロック書式を追記。frontmatter 書き換えを発生させない旨を明示
- `.claude/skills/issue_plan/SKILL.md`: `issue_review` SKILL をインライン展開している既存ブロックを同期（「呼び出し元との同期」原則に従う）
- `ISSUES/README.md`: ライフサイクル節に「長期持ち越し再判定」フローの 1 節を追加

### やらないこと（本版スコープ外）

- **10 バージョン強制降格ルールの実装**: 当該 ISSUE 本文の「対応方針 §2 しきい値の 2 段階」で 10 バージョンルールも提案されているが、推奨に従い後続版（ver16.6 以降）に委ねる。理由: 機械的降格は false positive 時の手戻りコストが高く、警告フラグの運用結果を 1〜2 版観察してから判断するのが安全
- **`ready/ai` 持ち越し回数カウンタ用の新 frontmatter フィールド追加**: `reviewed_at` 日付差分で代替可能であり、ISSUE 本文内書式を侵襲的に変える追加メタデータは当面入れない
- **判定ルート §3 自動判別の実装**: ISSUE 本文自体が「初回実装は『持ち越し理由の候補を列挙するテンプレート』を `/issue_plan` 出力に含めるだけに留め」と推奨。本版は判別自動化を含めない（テンプレート提示のみ）
- **Python スクリプト新設 / 既存スクリプト改修**: `scripts/issue_worklist.py` や `scripts/issue_status.py` への `ready/ai + 長期持ち越し` 抽出機能の追加は行わない（SKILL.md 内のハンドリングで自己完結させる）
- **他カテゴリ（app / infra / cicd）での観察**: 仕様書変更のみのため挙動は全カテゴリ横断で有効化されるが、他カテゴリでの発火観察は本版スコープに含めず handoff（ver16.6 以降）に委ねる
- **ver16.4 RETROSPECTIVE 相当のループ観察課題**:
  - ver16.3 §3.5 A-4（deferred 3 kind 分離）の実機観察は次 deferred 発火 run で継続
  - `imple_plan` / `experiment_test` の effort 下げ判断は sample 蓄積待ち
  - ver16.2 EXPERIMENT.md 「未検証」マーク解除は次 research workflow 採用時
  - `extract_model_name` 修正の sidecar 反映確認は次回 full / quick run で自然採取
- 他 3 件の ready/ai ISSUE（`deferred-resume-twice-verification` / `issue-review-rewrite-verification` / `toast-persistence-verification`）の個別消化は本版と並行させない（SKILL 本体書き換えとのコンフリクトリスクを避けるため）
- PHASE9.0 骨子作成

## 成果物（想定）

- `docs/util/ver16.5/ROUGH_PLAN.md` — 本ファイル
- `docs/util/ver16.5/PLAN_HANDOFF.md` — full-tier（5 節必須）
- `docs/util/ver16.5/REFACTOR.md` — `/split_plan` step で生成（full ワークフロー必須）
- `docs/util/ver16.5/IMPLEMENT.md` — `/imple_plan` step で生成
- `docs/util/ver16.5/MEMO.md` — `/imple_impl` step の実装メモ
- `docs/util/ver16.5/CHANGES.md` — 前版 (ver16.4) からの変更差分
- `docs/util/ver16.5/RETROSPECTIVE.md` — `/retrospective` step で生成（full 必須）
- `.claude/skills/issue_review/SKILL.md` — §1 / §5 に追補（後続 step で編集）
- `.claude/skills/issue_plan/SKILL.md` — インライン展開箇所の同期（後続 step で編集）
- `ISSUES/README.md` — ライフサイクル節追補（後続 step で編集）
- `ISSUES/util/low/issue-review-long-carryover-redemotion.md` — 消化完了後 `done/` へ移動

`RESEARCH.md` / `EXPERIMENT.md` / `CURRENT.md` は `full` workflow のうち research 条件非該当かつ minor につき生成しない。

## 事前リファクタリング要否

**不要**。`issue_review` SKILL は 100 行未満のシンプルな仕様書で、§1〜§5 の節構成が既に適切に分離されている。追補は §1（スキャン）と §5（サマリ報告）への追加のみで、既存節の分割・統合は生じない見込み。`issue_plan` SKILL 側のインライン展開箇所も現行構造のまま同期追補で足りる。根拠の詳細は `PLAN_HANDOFF.md` §後続 step への注意点に記載。

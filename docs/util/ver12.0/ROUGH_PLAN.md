---
workflow: full
source: master_plan
---

# ver12.0 ROUGH_PLAN — PHASE7.0 §2 起動前 validation の導入

MASTER_PLAN `docs/util/MASTER_PLAN/PHASE7.0.md` §2「起動前 validation で category・YAML・全 step を最後まで検査する」に着手する。ver10.0 で導入した step override（§1）の完了条件③「無効な model 名 / 未解決 prompt 参照 / 型不正な設定値の検出」は本バージョンで吸収する。

## ISSUE レビュー結果

- 対象 (`review / ai`): **0 件**。書き換え対象なし
- 今回の走査では `ISSUES/util/{high,medium,low}/*.md` 配下に `status: review` のファイルは存在せず、`issue_review` SKILL の書き換えロジックは起動していない

## ISSUE 状態サマリ

util カテゴリの frontmatter 分布（5 区分）:

| 組み合わせ | high | medium | low | 合計 |
|---|---|---|---|---|
| `ready / ai` | 0 | 1 | 0 | 1 |
| `review / ai` | 0 | 0 | 0 | 0 |
| `need_human_action / human` | 0 | 0 | 0 | 0 |
| `raw / human` | 0 | 0 | 0 | 0 |
| `raw / ai` | 0 | 2 | 1 | 3 |

内訳:

- `ready / ai` (1): `ISSUES/util/medium/issue-review-rewrite-verification.md`
- `raw / ai` (3):
  - `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md`
  - `ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md`
  - `ISSUES/util/low/system-prompt-replacement-behavior-risk.md`

## 着手方針と出所

- **出所**: `docs/util/MASTER_PLAN/PHASE7.0.md` §2（新 MASTER_PLAN 項目着手）→ `source: master_plan`
- **バージョン種別**: メジャー (`ver12.0`)。PHASE7.0 §2 は「全 workflow YAML を起動前に走査して schema / 参照解決 / 有効設定を検証し、違反時は step 1 を実行せず終了する」という `scripts/claude_loop_lib/` 配下への新規責務追加であり、CLAUDE.md 版管理規則「メジャー = MASTER_PLAN 新項目 / アーキテクチャ変更」に合致
- **ワークフロー**: `full`。MASTER_PLAN 新項目着手 + `scripts/claude_loop_lib/workflow.py` や `commands.py` などコア実行系への新規コード追加のため、`quick` 適用条件（3 ファイル以下 / 100 行以下）を超える

## スコープ（このバージョンで扱うこと）

PHASE7.0 §2-1〜§2-2 の完全実装を目指す。以下を一体のタスクとして扱う:

1. **検証項目の確定**: §2-1 の 5 項目を `scripts/claude_loop_lib/` 配下で実装する validator の責務境界として切り分ける
   - category 名の妥当性（`.claude/CURRENT_CATEGORY` または CLI 指定値）
   - workflow YAML の存在・パース可能性・期待 schema の充足
   - 全 step が参照する SKILL / command / workflow 定義の解決可能性
   - step override 設定（§1 で定義した許容キー）の型・必須値・継承後の有効設定
   - 実行前に判定できる入出力条件（例: 参照先ファイルの存在）
2. **報告方式**: 違反を逐次停止でなく可能な範囲でまとめて列挙し、最初の step を実行せず終了する挙動
3. **`--workflow auto` との接続**: 2 段実行（`claude_loop_issue_plan.yaml` → `full` / `quick`）の双方で validation を実行するか、それとも最初の 1 回のみとするかの方針決定
4. **ver10.0 §1 完了条件③の吸収**: 無効 model 名・未解決 prompt 参照・型不正な設定値が validation 段階で確実に検出されること
5. **テスト**: `scripts/tests/` 配下に正常系（全 YAML がパスする）・異常系（category ミス / YAML schema 違反 / 存在しない step / override 型不正 / 未解決参照）を追加

詳細な実装方式（関数分割・ファイル配置・エラー集約のデータ構造など）は本 ROUGH_PLAN では確定せず、`/split_plan` にて IMPLEMENT.md で設計する。

**事前リファクタリング不要**: 既存 `scripts/claude_loop_lib/workflow.py` の raise-on-first-error 挙動はランタイム防衛として残置し、新規 `validation.py` モジュールを独立レイヤとして追加する。共通定数（`ALLOWED_STEP_KEYS` / `ALLOWED_DEFAULTS_KEYS` / `OVERRIDE_STRING_KEYS`）は `workflow.py` から import して再利用するため、構造リファクタリングは発生しない。

## スコープに含めない事項（明示的除外）

### 併走候補だが本バージョンでは拾わない ISSUES

| ISSUE | 除外理由 |
|---|---|
| `ISSUES/util/medium/issue-review-rewrite-verification.md` (ready/ai) | ver6.0 からの持ち越し。util 単体では消化不能（`app` / `infra` カテゴリで `/split_plan` が `review / ai` ISSUE を処理するタイミングの目視確認が必要）。本バージョンは util カテゴリで起動しており、`review / ai` も 0 件のため、書き換えロジックが走らず検証できない |
| `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md` (raw/ai) | 対応方針 §2 が「PHASE7.0 §2 で根治」と指定。本バージョンの validation 実装で「指定 override キーに対応する Claude CLI flag が利用可能か」の事前チェックを扱うかは `/split_plan` で判断。扱う場合は `raw → ready` へ昇格、扱わない場合は次バージョン以降へ持ち越し |
| `ISSUES/util/low/system-prompt-replacement-behavior-risk.md` (raw/ai) | `--system-prompt` 完全置換の利用者向け注意喚起（予防策は ver10.0 で `scripts/README.md` 追記済）。validation で警告を出すかどうかは判断分岐の一つだが、リスク分類が low でスコープ肥大を避けるため `/split_plan` で扱わなければ次バージョン以降 |
| `ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md` (raw/ai) | pre-existing test failure。ver11.1 MEMO §今後の課題で「ver11.2 で単独処理予定」と記録されているが、本 ROUGH_PLAN は ver12.0 に直行（ver11.2 をスキップ）するため、処理タイミングを ver12.0 以降の quick バージョンで別途拾う必要がある。本バージョンには含めない（PHASE7.0 §2 と無関係、混ぜるとレビュー負荷が跳ねる） |

### その他の非スコープ

- PHASE7.0 §3〜§8（`--auto` 廃止・FEEDBACKS 1 ループ限定化・REQUESTS/ISSUES 統合・`/retrospective` 強化・`.claude/rules` 整備・prompt/model 振り返り）は本バージョンでは扱わない。想定分割は ver10.1 / ver10.2 で段階的に進める計画だが、ver12.0 が §2 で着地した後の進め方は wrap_up / retrospective で再評価する
- workflow YAML 側の記述整備（例: `system_prompt` / `append_system_prompt` の実値投入）は validation 仕様が固まった後の別バージョンで検討

## 関連ファイル（`/split_plan` への引き継ぎ）

### 主要な参照元

- `docs/util/MASTER_PLAN/PHASE7.0.md` — §2 の検証対象（§2-1）と期待挙動（§2-2）、リスク・やらないこと
- `docs/util/ver10.0/CURRENT.md` / `CURRENT_scripts.md` / `CURRENT_skills.md` — §1 実装後の `scripts/claude_loop_lib/` モジュール構成（特に override 継承ロジックの所在）
- `docs/util/ver10.0/IMPLEMENT.md` — §1 実装時の設計判断（override キー許容範囲・型変換・継承順序）

### 主要な変更対象候補（§2 実装時の想定）

- `scripts/claude_loop_lib/workflow.py` — YAML schema 正規化 / 全 step validation / 設定継承の解決（PHASE7.0 §1 実装拠点）
- `scripts/claude_loop.py` — 起動シーケンスへの validation 呼び出し組み込み
- `scripts/claude_loop_lib/commands.py` — step に対応する CLI 引数解決の事前チェック（特に `system_prompt` / `append_system_prompt` 系）
- `scripts/claude_loop_lib/` 配下への新規 validator モジュール追加の可能性（配置は `/split_plan` で判断）
- `scripts/claude_loop.yaml` / `scripts/claude_loop_quick.yaml` / `scripts/claude_loop_issue_plan.yaml` — 検証対象となる現行 workflow YAML（3 本）。validation 実装中に schema 違反が見つかった場合は併せて修正
- `scripts/tests/` 配下 — 異常系テストの追加（`test_workflow.py` などが既存のはず）
- `scripts/README.md` / `scripts/USAGE.md` — 起動前 validation の挙動・エラーメッセージ例の追記

### 判断経緯（選定理由と除外理由）

- **選定理由**: ver11.0 RETROSPECTIVE §3-2 が「ver11.1 で `scripts構成改善` 消化 → ver12.0 で PHASE7.0 §2 着手」を推奨し、ver11.1 で前者が完了済み。`scripts/` 配下のコード分離・README 分割が落ち着いた状態なので、validation 実装時に「新規 validator モジュールをどこに置くか」の配置判断が安定してできる
- **ready/ai ISSUE を拾わなかった理由**: 唯一の `ready / ai` 件である `issue-review-rewrite-verification.md` は「util カテゴリでは検証不可（app / infra カテゴリの `/split_plan` / `/quick_plan` で目視確認が必要）」という構造的制約があり、util ループ内で消化できない。ver11.0 RETROSPECTIVE §4-1 でも「持ち越し継続」と明記されている
- **PHASE7.0 §2 を一括で扱う理由**: §2-1 の 5 検証項目は validator モジュール内で責務が密結合しており、部分実装だと「validation を通っても実行時に落ちる」穴が残る。一括実装して「validation 通過 = 最後まで到達可能」という契約を確立する

## リスクと不確実性（ROUGH_PLAN 段階での粗い見込み）

- **PHASE7.0 §2 のリスク転記**: MASTER_PLAN PHASE7.0 リスク §「起動前 validation で『全 step を検証する』ためには、実行せずに解決できる参照範囲を明確に切り出す必要がある」がそのまま適用される。`/split_plan` で「validation 可能な参照」と「実行時にしか解決できない参照」の境界を早期に確定する必要がある
- **YAML schema の後方互換**: 既存 3 本の workflow YAML が schema 違反として検出される可能性。その場合は本 ROUGH_PLAN スコープ内で YAML 側も修正するか、schema を現行 YAML に合わせて緩めるかの判断が発生
- **`--workflow auto` 2 段実行との相互作用**: `/issue_plan` 先行実行時点で後続の `full` / `quick` YAML をまとめて validation するか、段階ごとに分けるか。前者のほうが安全だが、ROUGH_PLAN 生成前に後続 YAML を validation する意味があるかは要検討

## 成果物（完了時）

- `scripts/claude_loop_lib/` 配下に起動前 validation の実装（配置は `/split_plan` で確定）
- `scripts/claude_loop.py` の起動シーケンスに validation 呼び出しが組み込まれる
- `scripts/tests/` 配下に正常系・異常系の unit test
- `scripts/README.md` / `scripts/USAGE.md` への挙動記述
- PHASE7.0 §2 完了条件（§2-2 の 3 項目）を満たす状態
- PHASE7.0 §1 完了条件③（無効 model 名 / 未解決 prompt 参照 / 型不正設定値の事前検出）が §2 実装で同時に満たされる
- `docs/util/MASTER_PLAN.md` の PHASE7.0 進捗記述を「§1 部分完了・§2 実装済み」へ更新（実作業は wrap_up 以降）

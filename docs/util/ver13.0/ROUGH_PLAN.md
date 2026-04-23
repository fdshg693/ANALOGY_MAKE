---
workflow: full
source: master_plan
---

# ver13.0 ROUGH_PLAN — PHASE7.0 §3+§4+§5：CLI / FEEDBACKS / REQUESTS の一括整理

## ISSUE レビュー結果

- ready/ai に遷移: 0 件
- need_human_action/human に遷移: 0 件
- 追記した `## AI からの依頼`: 0 件

理由: `ISSUES/util/` 配下に `status: review` かつ `assigned: ai` の ISSUE が存在しないため、書き換え対象はゼロ（`python scripts/issue_status.py util` の結果 `review/ai=0` と一致）。`issue_review` SKILL の書き換えロジックは今回も util カテゴリ単体では実動作確認できず、`ISSUES/util/medium/issue-review-rewrite-verification.md`（`ready / ai`）は引き続き app/infra カテゴリ実行時への持ち越し継続（ver6.0 から 7 バージョン連続）。本 ISSUE は util 単体で消化不能なため本バージョンの着手対象から除外する。

## ISSUE 状態サマリ

| status / assigned | 件数 |
|---|---|
| ready / ai | 1 |
| review / ai | 0 |
| need_human_action / human | 0 |
| raw / human | 0 |
| raw / ai | 2 |

内訳（`scripts/issue_status.py util` より）:

- medium: ready/ai=1, raw/ai=1
- low:    raw/ai=1
- high:   (該当なし)

## 前提整理

### 現状把握の根拠

- 現状コードの全景: `docs/util/ver12.0/CURRENT.md`（CURRENT_scripts.md / CURRENT_skills.md / CURRENT_tests.md への分割構成）
- 直前バージョンの差分: `docs/util/ver12.1/CHANGES.md`（`issue_worklist.py` の `total` 計算タイミング修正のみ。本バージョンのスコープとは非衝突）
- 直前 RETROSPECTIVE: `docs/util/ver12.0/RETROSPECTIVE.md` §3-2 が本バージョン (ver13.0, full) で PHASE7.0 §3 + §4 + §5 を一括着手することを推奨

### バージョン種別判定 → メジャー (ver13.0)

以下 2 条件に該当するためメジャー昇格:

- MASTER_PLAN の新項目（PHASE7.0 §3〜§5）に着手する
- `--auto` mode 撤去は CLI / YAML の破壊的仕様変更を伴う

### ワークフロー選択 → `full`

- §3 は CLI 仕様変更・YAML schema 変更・docs/tests 一斉更新を伴うアーキテクチャ変更（`full` 必須条件に該当）
- 変更対象見込みが 3 ファイルを大幅に超える（後述「想定変更対象」参照）
- plan_review_agent によるレビュー価値が高い（後続 `/split_plan` / `/imple_plan` で実施）

### `source: master_plan` を選択した判断経緯

- `ready / ai` の ISSUE は `issue-review-rewrite-verification.md` 1 件のみだが、util 単体では消化不能（ISSUE 本文明記：app/infra カテゴリで `/split_plan` / `/quick_plan` を起動した際に動作確認する必要）
- 他 ISSUE はすべて `raw / ai`（未整理）で `/issue_plan` の着手対象外
- したがって既存 ISSUES 消化ルートは取れず、MASTER_PLAN 新項目ルートに進む
- PHASE7.0 は §1 / §2 完了済、§3〜§8 未着手。現行 PHASE 未完走のため新 PHASE 骨子作成は不要
- ver12.0 RETROSPECTIVE §3-2 が §3+§4+§5 一括着手を推奨（「§3 の CLI 整理と §4・§5 の運用ルール変更は CLAUDE.md / README / SKILL 群の一括更新が必要なため、同バージョンで扱うほうがレビュー負荷のトータル小」との判断）

## スコープ

PHASE7.0 §3・§4・§5 の 3 節を一括で扱う。共通テーマは「CLI と YAML と運用ルールの二重表現を撤廃し、入力チャネルを 1 系統に絞る」こと。3 節いずれも docs / SKILL / CLAUDE.md の参照先一括更新を伴うため、別バージョンに分けるとレビューで同じファイルを何度も触ることになる。一括処理することで、利用者から見た「どこに何を書けばよいか」の説明面を 1 回の整合性確認で済ませる。

### §3：legacy `--auto` mode と対応 YAML 設定の撤去

**ユーザー体験の変化**:

- 利用者は「自動実行にするための別モード」を意識しなくてよくなる。通常実行 (`python scripts/claude_loop.py`) が常に自動挙動を内包する前提に寄せる
- `--auto` を指定した旧呼び出しは黙って無視されず、明示的なエラーまたは移行案内を返す
- CLI ヘルプ / README / workflow YAML 例 / tests / 実装から `--auto` と旧 YAML `mode` 系設定の説明が消え、保守対象が 1 系統に絞られる

**現状の引き継ぎポイント**（`docs/util/ver12.0/RETROSPECTIVE.md` §4-5 より）:

- `scripts/claude_loop.py` 付近で `--auto` フラグを受理し `resolve_mode(config, args.auto)` で `auto_mode` を導出している（実装詳細は `/split_plan` 段で精査）
- YAML 側の `mode` 関連フィールドの取扱い・`scripts/claude_loop_lib/commands.py` の `auto_args` 解決の有無も併せて `/split_plan` 段で精査する

**対象外**:

- `--workflow auto` は `--auto` とは別概念（ver9.0 導入のワークフロー自動選択機構）。撤去対象ではない。混同しないこと

### §4：FEEDBACKS を 1 ループ限定の入力キューとして扱う運用ルール確立

**運用ルールの到達点**:

- 自動読込対象は `FEEDBACKS/` 直下のみ、`FEEDBACKS/done/` 配下は次回 run で自動再読込しない
- 1 ループで読み込まれた FEEDBACK はそのループ終了後に `FEEDBACKS/done/` へ移動する
- 異常終了時の移動有無の仕様を確定する
- FEEDBACK の再利用は人間が `FEEDBACKS/done/` → `FEEDBACKS/` に戻す明示操作を要する

**現状の引き継ぎポイント**（RETROSPECTIVE §4-5 より）:

- `scripts/claude_loop_lib/feedbacks.py` は既に `FEEDBACKS/` 直下を読み、正常完了時に `FEEDBACKS/done/` へ移動する実装が存在する
- §4 で必要な変更は「`FEEDBACKS/done/` 自動再読込の抑止」「異常終了時の移動有無の仕様確定」の 2 点程度で済む見込み
- `/split_plan` 段で現行実装の挙動を先に精査し、追加要件を確定する

### §5：`REQUESTS/AI` / `REQUESTS/HUMAN` の ISSUES 統合

**到達点**:

- docs / SKILL / workflow 説明のどこから見ても、「依頼を書く場所」は `ISSUES/{category}/{priority}/*.md` で一貫する
- `REQUESTS/AI` / `REQUESTS/HUMAN` 前提の説明や分岐は残さない
- 人間向けメモのような用途は ISSUES の `assigned: human` などで吸収する

**現状の引き継ぎポイント**:

- `REQUESTS/AI/` / `REQUESTS/HUMAN/` は現状空（ver12.0 CURRENT.md / RETROSPECTIVE §4-2 で確認済）。主作業は docs / SKILL / CLAUDE.md の「REQUESTS に書く」記述の置換とディレクトリ削除可否判断
- AUTO モード下での既定フォールバック先（現行 CLAUDE.md 系で `REQUESTS/AI/` にリクエストを書き出す指示がある）の置換先を `ISSUES/{カテゴリ}/...` または別の仕組みに切り替える必要があるかを `/split_plan` で確定する

## 想定変更対象（`/split_plan` への引き継ぎ）

以下はあくまで MASTER_PLAN/PHASE7.0 §3〜§5 のファイル変更一覧から §3〜§5 に関連する部分を抜粋したもの。`/split_plan` 段で精査して確定する。

| ファイル / ディレクトリ | 節 | 想定操作 |
|---|---|---|
| `scripts/claude_loop.py` | §3 | `--auto` フラグ受理・`resolve_mode` 呼び出しの削除、旧オプション指定時のエラー化 |
| `scripts/claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` | §3 | 旧 `auto` / `mode` 系フィールド削除 |
| `scripts/claude_loop_lib/commands.py` | §3 | `auto_args` 解決削除、CLI 引数整理 |
| `scripts/claude_loop_lib/workflow.py` | §3 | YAML schema から `mode` 系削除、validation 側の整合維持 |
| `scripts/claude_loop_lib/validation.py` | §3 | ver12.0 で追加した validation が `mode` を参照している場合は併せて追随 |
| `scripts/claude_loop_lib/feedbacks.py` | §4 | `FEEDBACKS/done/` 自動再読込抑止、異常終了時挙動の明文化 |
| `scripts/tests/` 配下 | §3/§4 | `--auto` / `mode` / FEEDBACKS 挙動に関するテストの撤去・更新・追加 |
| `scripts/README.md` / `scripts/USAGE.md` | §3/§4/§5 | CLI 仕様、FEEDBACKS ルール、REQUESTS 廃止の説明更新 |
| `CLAUDE.md`（ルート） | §5 | REQUESTS ではなく ISSUES を参照する運用へ説明更新 |
| `ISSUES/README.md` | §5 | REQUESTS 統合後の起票・分類手順を明文化 |
| `REQUESTS/AI/` / `REQUESTS/HUMAN/` | §5 | 入力源としての廃止（ディレクトリ削除可否は `/split_plan` で判断） |
| `.claude/skills/*/SKILL.md`（`issue_plan` 等、`REQUESTS/AI/` への書き出しを指示しているもの） | §5 | 置換先を ISSUES またはログ等へ切り替え |

## 既存 ISSUES / MASTER_PLAN との関係

### 本バージョンで触れる / 触れない ISSUES

| ISSUE | 扱い | 理由 |
|---|---|---|
| `ISSUES/util/medium/issue-review-rewrite-verification.md` (ready/ai) | **触れない** | util 単体消化不能。app/infra カテゴリ実行時への持ち越し継続（ver6.0 から継続） |
| `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md` (raw/ai) | **触れない（ただし留意）** | `raw` のため `/issue_plan` の着手対象外。ただし §3 CLI 整理のタイミングで関連する箇所に気づいた場合、ISSUE 本文を参考情報として眺める程度にとどめ、スコープは §3〜§5 に限定する |
| `ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md` (削除済) | — | ver12.1 で消化し `done/` へ移動済 |
| `ISSUES/util/low/system-prompt-replacement-behavior-risk.md` (raw/ai) | **触れない** | `raw` のため着手対象外。§3 以降の運用整理で再評価する想定 |

### PHASE7.0 内での位置づけ

- §1 / §2 実装済 → 本バージョン §3 + §4 + §5 実施 → 残り §6 / §7 / §8 は ver13.1 / ver14.0 以降で段階的に扱う（RETROSPECTIVE §3-2 推奨）
- §6（`/retrospective` からの FEEDBACK handoff）は §4 と接続する設計だが、§6 の実装は handoff ルール確立が主題で独立性が高く、今回のスコープから切り出して次バージョン扱いが適切

## `/split_plan` への申し送り

後続 `/split_plan` は本 ROUGH_PLAN.md のみを起点に IMPLEMENT.md / REFACTOR.md を起こせるよう、以下を踏まえて進めること:

1. **スコープ固定**: §3 + §4 + §5 の 3 節のみ。§6〜§8 および ISSUES は本バージョン対象外
2. **現行実装の精査が必要な箇所**:
   - `scripts/claude_loop.py` の `--auto` / `resolve_mode` 周辺の現状依存関係
   - `scripts/claude_loop_lib/feedbacks.py` の現行 `FEEDBACKS/done/` 移動挙動と異常終了時の振る舞い
   - `REQUESTS/AI/` への書き出しを指示している SKILL / CLAUDE.md の箇所網羅（grep で洗い出す）
3. **破壊的変更の移行案内方針**: `--auto` 指定時のエラー文言 / YAML 旧キー検出時の挙動は PHASE7.0 §3-1 方針「黙って無視するのではなく、明示的なエラーまたは移行案内」に従って設計
4. **既存テストへの影響予測**: ver12.0 RETROSPECTIVE §2-2-b の教訓「既存 integration テストの cwd 依存が実装時に顕在化」を踏まえ、`--auto` / `mode` / `FEEDBACKS` を参照しているテスト群を `/split_plan` 段で grep して事前に列挙する
5. **リスク列挙運用の継続**: ver12.0 で有効性が示された「IMPLEMENT.md §6 リスク列挙 → MEMO 検証マトリクス」運用を継続。§3 の破壊的変更は特に事前リスク列挙の効果が高い
6. **plan_review_agent の起動**: `/split_plan` 側で実施（本ステップでは起動しない）

## やらないこと

- §1 / §2 の再修正（完了済）
- §6（`/retrospective` から FEEDBACK handoff）・§7（`.claude/rules` の `scripts` 向け整備）・§8（`/retrospective` での prompt/model 評価）— 次バージョン以降へ
- `ISSUES/util/` 内の既存 ISSUE の消化（util 単体消化不能分 or raw のため）
- `--workflow auto`（別概念）の撤去
- `FEEDBACKS/done/` を自動再読込する仕組みの追加（PHASE7.0「やらないこと」に明記）
- `REQUESTS` を恒久バックログとして残す設計（PHASE7.0「やらないこと」に明記）

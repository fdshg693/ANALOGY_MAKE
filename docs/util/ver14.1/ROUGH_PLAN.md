---
workflow: quick
source: issues
---

# ver14.1 ROUGH_PLAN — raw/ai ISSUE 2 件の再評価（ver14.0 成果の吸収判定）

## ISSUE レビュー結果

- `review / ai` の ISSUE: **0 件**（走査対象なし）
- 状態遷移: なし（書き換え・追記ともに実施せず）
- 対象パス: なし

## ISSUE 状態サマリ（util カテゴリ / ver14.1 着手前時点）

| status × assigned | 件数 | 対象ファイル |
|---|---|---|
| `ready / ai` | 1 | `ISSUES/util/medium/issue-review-rewrite-verification.md` |
| `review / ai` | 0 | — |
| `raw / ai` | 4 | `medium/cli-flag-compatibility-system-prompt.md` / `low/rules-paths-frontmatter-autoload-verification.md` / `low/scripts-readme-usage-boundary-clarification.md` / `low/system-prompt-replacement-behavior-risk.md` |
| `need_human_action / human` | 0 | — |
| `raw / human` | 0 | — |

- `done/` 配下: 5 件（過去バージョンで処理済）
- `high/`: 空
- 総数: 5 件（`ready` 1 + `raw` 4）

## 背景と選定経緯

### ver14.0 までの経緯

- PHASE7.0 §6+§7+§8 を ver14.0 で一括完了。`.claude/rules/scripts.md` 新設、`/retrospective` SKILL §3.5（workflow prompt/model 評価）/ §4.5（handoff）追加。
- ver14.0 RETROSPECTIVE §1: PHASE8.0 骨子作成は ver14.0 成果を 1〜2 ループ観察してから判断（早くて ver14.2 or ver15.0）。当面は「既存 ISSUES 消化 + 運用観察」に寄せる方針。

### ver14.0 handoff の指示

`FEEDBACKS/handoff_ver14.0_to_next.md`（本ループで 1 回消費）は以下を指示:

1. `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md`（raw/ai）を再評価: `.claude/rules/scripts.md` §3（CLI 引数処理）で吸収済か。
2. `ISSUES/util/low/system-prompt-replacement-behavior-risk.md`（raw/ai）を再評価: `/retrospective` SKILL §3.5（workflow prompt / model 評価）で織り込み済か。
3. ver14.1 は **quick ワークフロー候補**（2 件 done 化のみで完結するなら軽量）。
4. 運用観察ポイント: handoff ファイルが実際に 1 回消費されて `FEEDBACKS/done/` へ移動する挙動 / `rules/scripts.md` の `paths:` frontmatter 解釈 / §3.5 評価が形骸化していないか。

### なぜ ready/ai 1 件ではなく raw/ai 2 件を選ぶか

- `ready / ai` の唯一の候補 `issue-review-rewrite-verification.md` は util 単体では消化不能（`app` / `infra` カテゴリで `/split_plan` を動かすタイミングまで継続持ち越し）。handoff §保留事項でも「ver14.1 でも触らない」と明記。
- 一方、handoff で指定された raw/ai 2 件は「ver14.0 の §7 rules 化 / §8 §3.5 追加で吸収済か」の再評価が必要なタイミング。判定結果として `done/` 移動または `ready` 昇格のどちらに倒すかを決めることで、util カテゴリの raw/ai を圧縮できる。

## ver14.1 スコープ

### 対象 ISSUE 2 件の再評価

**A. `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md`**

- 原論点: ver10.0 で追加した `--system-prompt` / `--append-system-prompt` CLI フラグを Claude CLI が実際に受理するか未検証。`unknown option` で落ちる可能性。
- 再評価する観点: `.claude/rules/scripts.md` §3（CLI 引数処理）が以下をどこまで網羅しているか実動作レベルで確認する:
  - argparse を使う（§3 明記）
  - 新規オプション追加時に `parse_args()` と `build_command()` の両方を更新（§3 明記）
  - 廃止オプションは argparse / `validation.py` で明示拒否（§3 明記）
  - YAML 3 本（`claude_loop.yaml` / `_quick.yaml` / `_issue_plan.yaml`）の `command` / `defaults` 同一化（§3 明記）
- 残論点候補（§3 でカバーされていない可能性）: **Claude CLI 自体が外部ツールとして当該フラグを受理するかの起動時検証**。PHASE7.0 §2 `validation.py` の startup validation が YAML override キーの presence/valid のみを検査し、外部 CLI バイナリの `--help` 出力との整合までは見ていない可能性がある。
- 判定ルール:
  - 残論点が実害ゼロ（ver10.0 以降 4 バージョン発生なし / YAML に実値投入なし）と判断できれば `done/` 移動
  - 残論点が具体的に特定でき、かつ rules/SKILL への追記で片付くなら `.claude/rules/scripts.md` に追記して `done/`
  - 残論点が新規実装（`validation.py` への CLI フラグ実在チェック追加 等）を要するなら `ready` 昇格

**B. `ISSUES/util/low/system-prompt-replacement-behavior-risk.md`**

- 原論点: `system_prompt` 指定時は Claude Code のデフォルト system prompt を完全置換するため、CLAUDE.md 自動読込み等の既定挙動が失われる可能性。
- 再評価する観点: `/retrospective` SKILL §3.5 の評価観点 1「`system_prompt` / `append_system_prompt` が step 役割に合っているか、長すぎないか、他 step と指示重複していないか」で、本リスクが実運用で検出できるか確認する。
- 補助: `scripts/README.md` §「override 可能なキー」に「通常は `append_system_prompt` を使うこと」注記済（ver10.0 wrap_up で対応済 — 予防策）。
- 判定ルール:
  - §3.5 評価観点 1 で読み替えにより検出可能（= 不適切な `system_prompt` 使用は評価時にフラグされる）かつ scripts/README.md 注記が残っている → `done/` 移動
  - §3.5 評価観点に「`system_prompt` の使用は原則避ける」旨が暗黙的すぎる場合、§3.5 評価テンプレ例に明示的な 1 行追記でカバー → 追記後 `done/`
  - それ以上の対応（validation.py で `system_prompt` 使用時の警告出力 等）が必要なら `ready` 昇格

### 期待される変更規模

- 判定のみで完結した場合: ISSUE ファイル 2 件を `ISSUES/util/done/` へ移動のみ（`git mv` 相当）
- SKILL / rules への軽微追記が必要な場合: 上記 2 件移動 + `.claude/skills/retrospective/SKILL.md` or `.claude/rules/scripts.md` の数行追加
- いずれのケースも **3 ファイル / 100 行以下** の quick 閾値内に収まる見込み

### quick 判定の根拠

- 判定結果による分岐はあるが、最大でも `done/` 移動 2 件 + SKILL/rules 追記 1 ファイルで 3 ファイル以内
- `review / ai` は 0 件（full 強制条件を満たさない）
- MASTER_PLAN 新項目着手なし / アーキテクチャ変更なし / 新規ライブラリ導入なし
- よって **quick ワークフロー**（`/quick_impl → /quick_doc`）で完結見込み
- 判定過程で「新規実装を伴う `ready` 昇格」が発生した場合は、その場で `full` への切替判断を記録し、`ROUGH_PLAN` を再起動せず quick 内で捌ける範囲に留める（ver14.2 以降に実装本体を委ねる）

## 運用観察（§3.5 handoff #4 由来 — 記録対象）

ver14.0 成果の初運用が ver14.1 ループと重なるため、以下 3 点を `/quick_impl` 以降の作業中に軽く観察し、必要なら MEMO または RETROSPECTIVE 相当の場所に一言残す（本ループでは積極介入しない）:

1. **handoff の 1 回消費挙動**: `FEEDBACKS/handoff_ver14.0_to_next.md` が本ループ完走後 `FEEDBACKS/done/` に移動しているか
2. **`.claude/rules/scripts.md` の `paths: scripts/**/*` frontmatter 解釈**: 本ループで `scripts/` を編集する場面がほぼ無いため直接観測機会は限定的。ver14.0 MEMO §リスク 6 の先送り事項である旨のみ留意
3. **§3.5 評価の形骸化傾向**: 本ループは quick のため §3.5 自体は動かないが、次回 full ループで差分評価基準が機能するか意識する

## スコープ外（ver14.1 では扱わない）

- `ISSUES/util/medium/issue-review-rewrite-verification.md`: util 単体消化不能のため継続持ち越し（handoff §保留事項に従う）
- `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md`: ver14.0 で新規作成した記録系 ISSUE。ver14.1 は観察対象として保持
- `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md`: 同上
- `.claude/rules/README.md` 新設: 現状 rules 2 ファイルで過剰設計。3 ファイル目追加時まで保留
- PHASE8.0 骨子作成: ver14.0 成果の運用観察が 1〜2 ループ分溜まるまで先送り（早くて ver14.2 or ver15.0）

## 関連ファイル

### 入力参照（再評価の根拠となる ver14.0 成果物）

- `.claude/rules/scripts.md` — §3 CLI 引数処理が ISSUE A の吸収判定対象
- `.claude/skills/retrospective/SKILL.md` — §3.5 workflow prompt / model 評価が ISSUE B の吸収判定対象
- `scripts/README.md` §「override 可能なキー」 — ISSUE B の予防策注記（ver10.0 wrap_up 対応済）

### 判定対象

- `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md`
- `ISSUES/util/low/system-prompt-replacement-behavior-risk.md`

### 参考コンテキスト

- `docs/util/ver14.0/RETROSPECTIVE.md` §1・§3・§4・§4.5・§8
- `FEEDBACKS/handoff_ver14.0_to_next.md`
- `docs/util/ver14.0/CURRENT.md`（util カテゴリの現状スナップショット）
- `docs/util/ver14.0/MEMO.md`（リスク §6 `paths:` frontmatter 先送り）

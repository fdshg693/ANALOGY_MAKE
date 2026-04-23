---
workflow: quick
source: issues
---

# ver11.1 ROUGH_PLAN — `scripts/` 構成改善（ワークフロー関連の分離 + README 分割）

`ISSUES/util/medium/scripts構成改善.md` を消化するマイナー（quick）バージョン。ver11.0 の `scripts/tests/` 新設で `scripts/` 配下のテスト側は整理済だが、**プロダクションコード側とドキュメント側は未整理**のため、ver11.0 の記憶が新しいうちに続けて対処する。

## ISSUE レビュー結果

- `status: review` / `assigned: ai` の ISSUE: **0 件**（レビュー対象なし、書き換え不要）

## ISSUE 状態サマリ

`python scripts/issue_status.py util` 実行結果:

| priority | ready/ai | review/ai | need_human_action/human | raw/human | raw/ai |
|---|---|---|---|---|---|
| high | 0 | 0 | 0 | 0 | 0 |
| medium | 2 | 0 | 0 | 0 | 2 |
| low | 0 | 0 | 0 | 0 | 1 |

ready/ai（2 件）:

- `ISSUES/util/medium/issue-review-rewrite-verification.md` — util 単体で消化不能（app / infra ワークフロー起動待ち）、ver6.0 からの持ち越し継続
- `ISSUES/util/medium/scripts構成改善.md` — **本バージョンで着手**

raw/ai（2 件、次バージョン以降で扱う）:

- `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md` — PHASE7.0 §2（ver12.0）で吸収予定
- `ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md` — ver11.2 で単独処理予定

raw/ai（low, 1 件）:

- `ISSUES/util/low/system-prompt-replacement-behavior-risk.md` — PHASE7.0 §2（ver12.0）で吸収予定

## 今回のスコープ

対象 ISSUE: **`ISSUES/util/medium/scripts構成改善.md`**

ISSUE 本文の 3 項目に 1:1 対応する:

### S1. `scripts/` 配下のワークフロー関連コード分離

**現状の問題**: `scripts/` 直下にワークフロー関連ファイル（`claude_loop.py` / `claude_loop*.yaml` / `claude_loop_lib/`）と、ワークフローとは独立した補助スクリプト（`claude_sync.py`）が**混在**している。`issue_status.py` / `issue_worklist.py` も厳密には「ワークフロー外の ISSUES 管理ツール」であり、一次的な関心事が異なる。

**対応方針**:
- **ワークフロー関連（= `claude_loop` 系）** と **その他の補助スクリプト** を論理的に分離する
- 分離の実現方法（サブディレクトリ移動 / 並列配置のまま命名で区別 / etc.）は quick_impl で最小コストの選択肢を採用
- `claude_loop.py` と `claude_loop_lib/` の import 関係は維持すること（ver11.0 IMPLEMENT §1-2 で確定した「`scripts/__init__.py` は作らない」方針を踏襲）
- `.claude/rules/claude_edit.md` / `docs/util/ver11.0/CURRENT_scripts.md` / `scripts/README.md` / `scripts/tests/_bootstrap.py` など、`scripts/claude_sync.py` / `scripts/claude_loop.py` をパスで参照している箇所が複数あるため、パス変更を伴う場合は全参照の更新が必須

**ユーザー体験の変化**:
- 利用者が「ワークフロー本体を触りたい」時と「`.claude/` 同期だけしたい」時で、参照すべきファイル群を分けて把握できるようになる
- CLI 呼び出しコマンド（`python scripts/claude_loop.py` / `python scripts/claude_sync.py` / etc.）の**変更を極力避ける**ことを優先指標とする（利用者の手癖・README 以外のドキュメント参照を壊さない）。後方互換のために shim を置く場合も、重複メンテコストが最小になる方針を取ること

### S2. `scripts/README.md` の分割

**現状の問題**: `scripts/README.md` は 353 行に達し、以下の異なる読者層の情報が 1 ファイルに混在している:

1. **概要把握**（これは何か / 前提条件 / ファイル一覧 / クイックスタート）
2. **CLI 使い方の詳細**（CLI オプション一覧・`--auto` / `--workflow auto` の違い・`issue_worklist.py` 使い方）
3. **YAML 仕様の詳細**（`mode` / `command` / `defaults` / `steps` セクション、継承ルール、`append_system_prompt` 合成順序、`continue` の使い分け / エッジケース、サンプル YAML、`--workflow auto` 分岐仕様）
4. **フル/quick の使い分け**
5. **運用情報**（フィードバック注入機能・ログフォーマット・`claude_sync.py` / `claude_loop.py` のテスト実行）
6. **拡張ガイド**

**対応方針**:
- **「使い方専門ファイル」を 1〜2 ファイル切り出す**。具体的な分割線（案）:
  - `scripts/README.md`（人間向け入り口）: 概要把握 / クイックスタート / フル/quick の使い分け / 運用情報（ログ・フィードバック・`claude_sync.py`）/ 関連ドキュメントへのリンク
  - `scripts/USAGE.md`（使い方専門、仮称）: CLI オプション一覧 + YAML 仕様詳細 + `--workflow auto` 分岐 + `issue_worklist.py` 使い方
- 最終的な分割点・ファイル名は quick_impl で決定。**ただし README 本体は 200 行以下を目標**（肥大化時の再分割しきい値として明示）
- 分割後も、README は人間用ファイルのまま維持する（Claude Code 向け内部情報は `docs/util/` 配下に既に整理済 ＝ `CURRENT_scripts.md` 等、重複させない）

**ユーザー体験の変化**:
- 「まず何か触りたい」人は README だけで完結
- 「CLI オプションを探したい」「YAML の書き方を確認したい」人は USAGE.md に直行
- 既存リンク（`docs/util/ver*/CURRENT_scripts.md` / `.claude/rules/*.md` 等から `scripts/README.md` への参照）は壊さない

### S3. ログの見方・運用注意点の加筆

**現状の問題**: `scripts/README.md` には「ログフォーマット」節で生成ログの構造は書かれているが、**実運用で役立つ観点**（どこを見れば失敗原因が分かる / 繰り返し起きがちなトラブル / 成功ログのどの行を信頼するか）が不足している。

**対応方針**:
- ログ読解の勘所を人間向けに短くまとめて README（または USAGE.md のログ節）に追記
- 含める観点の候補（quick_impl で確定）:
  - どのログ行で「失敗したステップ」を特定するか（`--- end (exit: <非0>, ...` 行の見方）
  - 複数ステップで同じエラーが繰り返される場合の切り分け（`continue: true` のセッション汚染可能性）
  - `Last session (full)` を使った手動再開（`claude -r <uuid>`）の手順
  - `logs/workflow/` のローテーション想定（gitignore 済 / 手動削除）
- **Claude Code 向け内部実装注記は README に書かない**（`docs/util/` 配下に既にあり、重複回避）

## 除外したタスク（なぜ本バージョンで扱わないか）

- **`test-issue-worklist-limit-omitted-returns-all.md`**: ver10.0 RETROSPECTIVE で先送りされ、ver11.0 では参照先を新配置（`scripts/tests/test_issue_worklist.py`）に更新するに留めた pre-existing 失敗。本バージョンの「`scripts/` 構成改善」とはテーマ軸が異なり、並行で拾うと quick のスコープ（3 ファイル以下 / 100 行以下）を超える可能性がある。ver11.2 で単独処理することとし、本バージョンでは保全（既存失敗を悪化させない）のみ
- **`issue-review-rewrite-verification.md`**: util 単体で消化不能（app / infra ワークフロー起動を要する検証）。ver6.0 からの持ち越し継続
- **`cli-flag-compatibility-system-prompt.md` / `system-prompt-replacement-behavior-risk.md`**: PHASE7.0 §2（ver12.0 メジャー）で吸収予定。`--workflow` 選択肢 `quick` が full ワークフローのアーキテクチャ変更に波及するため単独ではなく §2 と同時着手が効率的
- **PHASE7.0 §2「起動前 validation」**: MASTER_PLAN 新項目 + アーキテクチャ変更のためメジャー扱い（ver12.0）。本バージョンの quick スコープ外

## ワークフロー選択の根拠

- 選定 ISSUE 1 件・すべて `ready`・`review` なし → **full 必須条件には当たらない**
- 変更対象は `scripts/` 配下の:
  - （S1）ファイル移動 or 並列配置変更: 最大 1〜3 ファイル
  - （S2）`README.md` 分割: README + 新 USAGE.md の 2 ファイル
  - （S3）README / USAGE.md への加筆: 既存ファイル内編集のみ
  - パス参照更新: `docs/util/` / `.claude/rules/` / `scripts/tests/_bootstrap.py` 等の軽微な差分
- プロダクションコードの**振る舞いは不変**を目標（`claude_loop.py` の CLI 挙動・YAML パース・テスト結果は変化させない）
- → 変更ファイル 3〜5 件程度、1 ファイルあたり数十行程度の差分に収まる見込み → **`workflow: quick` が妥当**

quick ワークフロー構成: `/issue_plan → /quick_impl → /quick_doc`

## 完了条件（DoD）

1. `scripts/` 配下で「ワークフロー関連」と「その他の補助スクリプト」の境界が明示的に分かる構成になっている（ディレクトリ分割 / ファイル命名 / README の記述、いずれでも可）
2. `scripts/README.md` が 200 行以下に縮小し、使い方専門の切り出しファイル（USAGE.md 等）が存在する
3. ログ読解の勘所が README / USAGE.md のいずれかに短くまとまっている
4. 既存の CLI 呼び出し（`python scripts/claude_loop.py ...` / `python scripts/claude_sync.py ...` / `python scripts/issue_status.py` / `python scripts/issue_worklist.py`）がすべて従来どおり動作する（quick_impl で動作確認）
5. `python -m unittest discover -s scripts/tests -t .` が ver11.0 末の状態と同件数・同失敗数（pre-existing `test_limit_omitted_returns_all` のみ失敗）を維持
6. パス変更を伴う場合、参照箇所（`docs/util/ver*/CURRENT_scripts.md` / `.claude/rules/*.md` / `scripts/tests/_bootstrap.py` / ルート `CLAUDE.md`）の更新漏れがない

## 関連ファイル（quick_impl での入口）

- **ISSUE**: `ISSUES/util/medium/scripts構成改善.md`
- **対象コード/ドキュメント**:
  - `scripts/claude_sync.py`（ワークフロー外の補助スクリプト。分離対象の代表例）
  - `scripts/issue_status.py` / `scripts/issue_worklist.py`（ISSUE 管理ツール。ワークフロー中からも呼ばれるため分類判断が要る）
  - `scripts/claude_loop.py` / `scripts/claude_loop_lib/` / `scripts/claude_loop*.yaml`（ワークフロー本体。import パス維持）
  - `scripts/README.md`（分割対象）
  - `scripts/tests/_bootstrap.py`（`sys.path` 操作。`scripts/` 配下の移動がある場合は要確認）
- **参照更新の候補**:
  - `docs/util/ver11.0/CURRENT_scripts.md`（旧版。ver11.1 で新 `CURRENT_scripts.md` を `/quick_doc` が書き起こす）
  - `.claude/rules/claude_edit.md`（`scripts/claude_sync.py` への手順書き。パス変更時は同期が必要）
  - ルート `CLAUDE.md`（`scripts/` の説明行。ファイル構成変更時のみ更新）
- **直前バージョン引き継ぎ**:
  - `docs/util/ver11.0/RETROSPECTIVE.md` §4-4「次バージョン ver11.1 への引き継ぎ」（1〜5 項）
  - `docs/util/ver11.0/CURRENT_scripts.md`（ver11.0 末の構成スナップショット）

## `/quick_impl` への申し送り

- **判断事項**:
  - (a) S1 の実現方式: サブディレクトリ切り出し（例: `scripts/tools/` へ `claude_sync.py` を移動）か、README だけで区別するか。**パス参照更新コストと後方互換性のトレードオフ**で決定。決め手に欠ける場合は「移動しない・README と CURRENT_scripts.md で論理的分離を示す」に倒してよい（振る舞い不変の原則優先）
  - (b) S2 の分割ファイル名: `USAGE.md` 以外（`CLI.md` / `YAML.md` / 2 分割）も候補。**README 200 行目標**と**1 ファイルの自己完結性**で選択
  - (c) S3 の掲載場所: README（概要寄り）か USAGE.md（詳細寄り）か
- **振る舞い不変の検証**:
  - quick_impl の最後に `python -m unittest discover -s scripts/tests -t .` を実行し、件数・失敗数を ver11.0 末と比較すること
  - CLI 4 コマンド（`claude_loop.py --help` / `claude_sync.py --help` / `issue_status.py` / `issue_worklist.py`）が少なくとも `--help` レベルで従来通り起動することを確認
- **パス変更時の網羅チェック**: `scripts/claude_sync.py` / `scripts/claude_loop.py` / `scripts/issue_status.py` / `scripts/issue_worklist.py` を grep で全ファイル走査し、ハードコードされたパス参照を全件更新すること

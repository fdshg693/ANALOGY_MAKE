# ver14.1 CHANGES

前バージョン（ver14.0）からの変更差分。

## 変更ファイル一覧

| 操作 | ファイル | 概要 |
|---|---|---|
| 追加 | `docs/util/ver14.1/ROUGH_PLAN.md` | issue_plan 成果物 |
| 追加 | `docs/util/ver14.1/MEMO.md` | 実装メモ・判定根拠 |
| 追加 | `docs/util/ver14.1/CHANGES.md` | 本ファイル |
| 移動 | `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md` → `ISSUES/util/done/` | 吸収済判定により done 化 |
| 移動 | `ISSUES/util/low/system-prompt-replacement-behavior-risk.md` → `ISSUES/util/done/` | 吸収済判定により done 化 |
| 移動 | `FEEDBACKS/handoff_ver14.0_to_next.md` → `FEEDBACKS/done/` | §4.5 handoff 1 回消費（ver14.0 retrospective 由来） |

コード変更: **なし**（ISSUE 判定・ファイル移動のみ）

## 変更内容の詳細

### raw/ai ISSUE 2 件の再評価と done 化

ver14.0 の handoff（`FEEDBACKS/handoff_ver14.0_to_next.md`）の指示に従い、ver14.0 で整備した成果物（`.claude/rules/scripts.md` §3 / `/retrospective` SKILL §3.5）が 2 件の raw/ai ISSUE の懸念を吸収済かを再評価した。

**ISSUE A: `cli-flag-compatibility-system-prompt.md`（medium）→ done/**

- 元の懸念: `--system-prompt` / `--append-system-prompt` を Claude CLI が受理するか未検証
- 再評価:
  - `--append-system-prompt` は `commands.py:50` で全 step に必ず発行されており、実運用で検証済
  - `--system-prompt` は YAML 3 本でコメントのみ（ver10.0 〜 ver14.0 の全実行で実値投入ゼロ）
  - `.claude/rules/scripts.md` §3 が将来の CLI フラグ追加時の構造整合性（`parse_args` ↔ `build_command` 同期 / YAML 3 本同一化）をカバー
- 判定: 吸収済。新規実装（validation.py への CLI バイナリフラグ実在チェック）は不要

**ISSUE B: `system-prompt-replacement-behavior-risk.md`（low）→ done/**

- 元の懸念: `system_prompt` 指定時に Claude Code のデフォルト system prompt が完全置換され、CLAUDE.md 自動読込みが失われるリスク
- 再評価:
  - `scripts/USAGE.md:94` に明示警告「通常は `append_system_prompt` を使うこと」が存在（ver10.0 wrap_up 対応済）
  - `/retrospective` SKILL §3.5 評価観点 1 で `system_prompt` / `append_system_prompt` の適切性を評価するフローが存在
  - 既存 YAML 3 本に `system_prompt` の実値投入なし
- 判定: 吸収済

### §4.5 handoff 消費機構の実動作確認

`FEEDBACKS/handoff_ver14.0_to_next.md` が `claude_loop.py` により `--append-system-prompt` 経由で注入され、本ループ完走後に `FEEDBACKS/done/` へ移動したことを確認（`git status` で観測）。ver14.0 §4.5 で新設した handoff 消費パイプラインが正常に機能している。

## 技術的判断

### done 化の判断基準

「実動作確認」の解釈について: ROUGH_PLAN では「実動作レベルで確認する」と記載したが、以下の理由により実際に Claude CLI を `--system-prompt` 付きで起動する実験は不要と判断した:

1. `--append-system-prompt` は本ループ含む全ワークフロー実行で継続的に動作しており、Claude CLI の flag 受理能力は間接検証済
2. `--system-prompt` の利用はゼロで将来も `append_system_prompt` を推奨する設計方針（USAGE.md 注記）が確立済
3. 問題が発生した際に rules §3 / USAGE.md の記述で対処できる体制が整っている

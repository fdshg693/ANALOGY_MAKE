---
status: raw
assigned: ai
priority: medium
reviewed_at: "2026-04-24"
---

# deferred execution の resume 経路 / `--bare` 採用判定の実測検証（ver16.2 以降）

## 概要

ver16.1 PHASE8.0 §2 で deferred execution 機構を実装したが、以下 2 点は nested `claude` CLI 起動が `research` workflow の観測バイアス（IMPLEMENT.md §5-5）に抵触するため **未検証のまま本版を closeout** している。

1. 同一 session id に対する 2 回連続 `claude -r <id>` 呼び出しで履歴が継承されるか（分岐しないか）
2. `_execute_resume()`（= `_process_deferred` 内の resume subprocess）で `--bare` を採用すべきか（token 肥大化 / CLAUDE.md 再注入の観点）

RESEARCH.md §A1〜§A6（Anthropic 公式 docs / 公式 repo issue）で一次資料による裏取りは完了しているため、ver16.1 実装自体は `--bare` **なし** で着手済。ただし実機での実走確認を行っていないため、初の deferred 経路発動で問題が顕在化する可能性がある。

## 本番発生時の兆候

- deferred 完了後の resume で履歴が欠落している（Claude が先行 step の成果を「初出情報」として扱う）
- resume prompt 流入量が想定より大きく、OpenAI / Anthropic API コストが跳ねる
- resume 時の Claude の応答品質が明確に劣化

## 対応方針

1. `experiments/deferred-execution/resume-twice/README.md` の草稿手順に従い、外部経路（通常の対話シェル）で実測する:
   - (a) `claude -p "第 1 発話" --session-id <uuid>` を完走
   - (b) `claude -p "第 2 発話" -r <uuid>` を完走
   - (c) `claude -p "第 1 発話を覚えているか答えよ" -r <uuid>` の結果記録
2. 履歴継承確定なら現行実装のまま。継承されないなら IMPLEMENT.md §5-1 fallback（新規 session id + 履歴を明示的に prompt 貼付）に切替
3. `--bare` 採用判定は (i) resume 動作成否 (ii) CLAUDE.md 参照有無 (iii) 実行時間 を比較して決定

## 影響範囲

- `scripts/claude_loop_lib/deferred_commands.py::build_resume_prompt`（resume prompt の前提が変わる）
- `scripts/claude_loop.py::_process_deferred`（resume command 組み立て）
- EXPERIMENT.md §U2/§U3 が「未検証」のまま放置されている状態の解消

## 関連資料

- `docs/util/ver16.1/IMPLEMENT.md` §5-1
- `docs/util/ver16.1/RESEARCH.md` §Q1, §A1〜§A6
- `docs/util/ver16.1/EXPERIMENT.md` §U2, §U3, §U2-note
- `experiments/deferred-execution/resume-twice/README.md`

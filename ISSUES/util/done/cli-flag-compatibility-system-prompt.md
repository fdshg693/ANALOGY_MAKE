---
status: raw
assigned: ai
priority: medium
---
# Claude CLI フラグ互換性検証（`--system-prompt` / `--append-system-prompt`）

## 概要

ver10.0 で workflow YAML の step / defaults で `system_prompt` / `append_system_prompt` を指定可能にしたが、ver10.0 時点では既存 YAML 3 本に実値投入していないため、Claude CLI が当該フラグを実際に受理するか未検証。本番で利用者が指定したタイミングで `unknown option` エラーで落ちる可能性が残る。

## 本番発生時の兆候

- workflow 実行時に `claude` プロセスが「`unknown option '--system-prompt'`」/「`unknown option '--append-system-prompt'`」相当のメッセージを stderr に出力して即座に落ちる
- `scripts/claude_loop.py` の step 実行ログで exit_code が非ゼロ、`--- stdout/stderr ---` セクションに上記エラーが記録される

## 対応方針

1. 兆候発生時は当該 step の YAML から `system_prompt` / `append_system_prompt` を一時撤去して回避
2. PHASE7.0 §2 (起動前 validation, ver10.1 予定) で「指定された override キーに対応する CLI flag が利用可能か」の事前チェックを実装することで根治
3. 環境固有のバージョン差異が判明した場合は `claude --help` 出力をパースして利用可能フラグを検出する仕組みを検討

## 影響範囲

- `scripts/claude_loop_lib/commands.py` の `build_command()` が生成する CLI 引数
- 利用者が能動的に YAML へ新キーを書いた場合のみ顕在化（既存 3 本 YAML には新キーを書いていないため、ver10.0 リリース直後は顕在化しない）

## 由来

- `docs/util/ver10.0/IMPLEMENT.md` §5-1（リスク・不確実性 5-1）
- `docs/util/ver10.0/MEMO.md` で「検証先送り」と記録

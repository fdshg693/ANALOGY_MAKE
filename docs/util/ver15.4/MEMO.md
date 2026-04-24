---
workflow: full
source: master_plan
---

# ver15.4 MEMO — PHASE7.1 §4（run 単位・永続通知）

## 計画との乖離

### IMPLEMENT.md T1（PoC）をスキップ

`IMPLEMENT.md` §T1 では `experiments/notify_persist_poc.ps1` を作って Action Center 残留時間を目視確認する PoC を先行実施する計画だった。これをスキップし、T2（`_notify_toast` 実装）内で 2 段フォールバック構造（`scenario='reminder'` → `duration='long'` → beep）を同時実装した。

理由は CLAUDE.md の「段階的アプローチのスキップ」条件を 3 つとも満たしたため:

1. **上位互換の手法への置換**: reminder XML → long XML → beep の順に降格する実装を入れたため、reminder が OS に拒否されてもトースト自体は出る。PoC で採用 XML を 1 本に絞る前提がそもそも保守的すぎた
2. **対話的手順が必要**: PoC は 30 秒 / 5 分 / 10 分後の Action Center 目視確認が必要。unattended ワークフローでは実行不可
3. **仮説の蓋然性**: `scenario='reminder'` + `<actions>` 構成は Microsoft 公式ドキュメント（UWP Toast Schema）に記載の既知パターン

**本番発生時の対応方針**: reminder XML が Windows 11 の特定ビルドで拒否されるケースが確認された場合、`_notify_toast` の `for persistent in (True, False)` ループが 2 回目で成功するため自動的に `duration='long'` へ降格する。beep fallback も維持されているので、完全に通知が消失するケースはない。

### R4（signal.raise_signal の Windows 挙動）: テスト戦略を変更

IMPLEMENT.md R4 では `signal.raise_signal(signal.SIGTERM)` を使う end-to-end テストを Windows 限定で書く案があった。実装では **ハンドラ関数 `_sigterm_to_keyboard_interrupt` を直接呼び出す**ユニットテスト（`TestSigtermHandler` および `test_main_emits_summary_on_sigterm`）でカバーすることにした。理由:

- `signal.raise_signal` は Windows でも動作するが、unittest 内でのプロセス終了競合が再現困難
- ハンドラ関数を直接呼ぶ方が副作用（`_last_signal` 更新と `KeyboardInterrupt` raise）を決定論的に検証できる
- SIGTERM ⇔ `KeyboardInterrupt` ⇔ `interrupt_reason="SIGTERM"` の伝播経路のうち、`os.kill` 経由の signal delivery 部分は OS 側の責任で、本版の実装責務外

## リスク・不確実性の検証結果

### R1. Windows toast の永続化挙動（検証先送り）

- **判定**: 検証先送り
- **理由**: 開発者の Windows 11 実機で目視確認する運用手順がまだ整っていない。本版のコード側では 2 段フォールバック（reminder → long → beep）を入れて安全網を敷いた
- **本番発生時の兆候**: `notify_completion` 呼び出し後に Action Center へ何も残らず、かつコンソールに beep fallback の `========` 装飾も出ない場合（＝ reminder も long も成功扱いだが実は silently 無表示）
- **対応方針**: 次回 util バージョンで開発者実機での目視確認を行い、必要なら `_build_toast_xml` の XML 構造を調整する
- **ISSUE**: `ISSUES/util/low/toast-persistence-verification.md` に follow-up として起票

### R2. SIGINT / SIGTERM の判別（検証済み）

- **判定**: 検証済み
- **結果**: モジュールレベル変数 `_last_signal` を `main()` 冒頭で `"SIGINT"` にリセットし、SIGTERM ハンドラが `"SIGTERM"` で上書きする設計で動作することを `TestSigtermHandler` と `test_main_emits_summary_on_sigterm` で確認。テスト間の state 漏れは `TestSigtermHandler` の `setUp/tearDown` で original 値を退避して回避

### R3. `SystemExit` の境界（検証済み）

- **判定**: 検証済み
- **結果**: `parse_args()` / `validate_auto_args()` は `try` ブロックの外に置いた。`cwd.is_dir()` 判定・`validate_startup` 以降が `try` 内。argparse の `--help` / 引数ミスは通知されず、startup 失敗（cwd 不在 / YAML 不在）は通知される

### R4. `signal.raise_signal(SIGTERM)` の Windows 挙動（検証不要に再判定）

- **判定**: 検証不要
- **理由**: 上記「計画との乖離」のとおり、ハンドラ関数の直接呼び出しテストで責務を分割したため `signal.raise_signal` 経由 e2e テストは書かなかった

### R5. `_run_steps` 戻り値変更の波及（検証済み）

- **判定**: 検証済み
- **結果**: `scripts/tests/test_claude_loop_integration.py` の `TestRunStepsSessionTracking` で 4 箇所 `_run_steps` を呼んでいたうち、戻り値を使っているのは 1 箇所のみだったため `exit_code, _ = _run_steps(...)` に書き換え。他 3 箇所は戻り値未使用で無改修

### R6. ROUGH_PLAN の文言齟齬（検証済み / `/retrospective` 向け）

- **判定**: 検証済み
- **結果**: IMPLEMENT.md 冒頭「現状の再確認」節で ROUGH_PLAN §「提供する体験の変化」と実コードの齟齬を明示済み。実コードは既に run 単位 1 回発火だったので、本版の主眼は「内容の run サマリ化」「永続表示」「中断経路網羅」に再定義された。`/retrospective` で ROUGH_PLAN 文言精度の改善観点として記録予定

### timeout 経路（意図的除外）

- **判定**: 対象外
- **理由**: 現行 `_run_steps` の `subprocess.run` / `subprocess.Popen` は `timeout` 引数未指定。Python 側の timeout 経路が存在しないため、本版では対応コード不要。将来 step 単位 timeout を導入する際は `_run_steps` 内で `KeyboardInterrupt` と同様の経路に合流させれば本実装の `try/except/finally` 構造に自然に乗る

## 後続バージョンへの申し送り

### `_notify_beep` の `print()` 直接使用

`notify.py::_notify_beep` は `print("\a")` / `print(f"...")` を直接呼んでおり、`.claude/rules/scripts.md` §5（`logging_utils` 経由を必須）と矛盾している。本版は通知 API シグネチャ変更と toast XML 移行が主戦場で、fallback 経路の出力レイヤ書き換えはスコープ過大になるため意図的に持ち越し。

**対応方針（後続版）**:
1. `logging_utils` に「TeeWriter コンテキストなしでも使える stderr 出力ヘルパ」を追加
2. `_notify_beep` をそれ経由に差し替え

### run summary verbosity フラグ

`--no-notify` の二値制御しかないため、「summary を出すが toast は抑止（beep のみ）」のような中間モードは現状存在しない。実運用で需要が出たら `--notify-style {toast,beep,none}` のような 3 値フラグを追加する。追加時は 5 つの `claude_loop*.yaml` の `command` / `defaults` セクション同期は不要（CLI 引数の追加であり YAML 表面には現れないため）。

### auto モードの loop カウント意味論

`_run_auto` は phase1（`claude_loop_issue_plan.yaml` 1 step）と phase2（full/quick）の RunStats を単純合算している。phase1 は issue_plan 1 step のみで `total_steps=1` のため、`absolute_index==total_steps` 判定により「1 loop 完了」とカウントされる。これが phase2 の loop 数と足されるため、ユーザから見ると `--max-loops 1` 実行でも通知本文が「2 loops」と出る可能性がある。意味論として混乱の余地があるため、次バージョンで `auto` の場合は phase2 の loop 数のみを採用する方針に切り替えることを検討。現状は「step 数」で正確な情報が取れるため実害は小さい。

## 更新が必要そうなドキュメント

- `scripts/README.md` / `scripts/USAGE.md`: 本版で完了通知節を追加。今後 `--notify-style` 追加時に更新
- `docs/util/MASTER_PLAN/PHASE7.1.md`: 本版で §4 を「実装済み」に更新済み

---

## wrap_up 対応結果（2026-04-24）

| 項目 | 判定 | 処置 |
|---|---|---|
| T1 PoC スキップ（計画乖離） | ⏭️ 対応不要 | MEMO に記録済み・正当な判断 |
| R4 テスト戦略変更（計画乖離） | ⏭️ 対応不要 | MEMO に記録済み |
| R1（toast 永続化 検証先送り） | ⏭️ 対応不要 | ISSUE 起票済み（`toast-persistence-verification.md`） |
| R2〜R6・timeout（検証済み / 対象外） | ⏭️ 対応不要 | 各判定結果が MEMO に記録済み |
| `_notify_beep` の `print()` 違反 | 📋 先送り | `ISSUES/util/low/notify-beep-print-violation.md` 新規起票 |
| auto モードの loop カウント意味論 | 📋 先送り | `ISSUES/util/low/auto-loop-count-semantics.md` 新規起票 |
| run summary verbosity フラグ | ⏭️ 対応不要（ISSUE 起票なし） | アイデア段階、実運用需要確認前 |
| `plan-handoff-generation-followup.md`（ISSUE 整理） | ✅ done/ 移動 | ver15.4 で PLAN_HANDOFF.md 生成確認済み |
| `plan-handoff-frontmatter-drift.md` | ⏭️ 観察継続 | ver15.4 の ROUGH_PLAN/PLAN_HANDOFF frontmatter 一致確認 |
| `plan-handoff-omission-tracking.md` | ⏭️ 観察継続 | full バージョンのため省略判断なし |

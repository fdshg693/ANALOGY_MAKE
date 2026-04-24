# ver15.4 CHANGES

PHASE7.1 §4（ワークフロー終了通知を「run 単位・手動 dismiss まで残る」仕様に改修）の実装。ver15.3 からの変更差分。これにより PHASE7.1 が全 4 節完走した。

## 変更ファイル一覧

| ファイル | 種別 | 概要 |
|---|---|---|
| `scripts/claude_loop_lib/notify.py` | 変更 | `RunSummary` クラス追加、`notify_completion(RunSummary)` にシグネチャ変更、toast XML を `scenario='reminder' duration='long'` + dismiss アクション構成に差し替え、reminder → long の 2 段フォールバック導入、XML エスケープを `xml.sax.saxutils.escape` に寄せる |
| `scripts/claude_loop.py` | 変更 | `RunStats` plain class 追加、`_run_steps` / `_execute_yaml` / `_run_auto` の戻り値を `(int, RunStats)` タプル化、`main()` を `try/except/finally` 構造化（KeyboardInterrupt / SystemExit 各経路で通知 1 回発火）、SIGTERM ハンドラ `_sigterm_to_keyboard_interrupt` 追加、`_workflow_label_fallback` helper 追加 |
| `scripts/tests/test_notify.py` | 変更 | `RunSummary` の title / message フォーマットテスト、toast XML の scenario / duration 検証、XML エンティティエスケープ検証、reminder → long フォールバック検証、両 variant 失敗時の RuntimeError 検証を追加（全 13 件） |
| `scripts/tests/test_claude_loop_cli.py` | 変更 | `TestMainNotifyRunSummary`（8 ケース: 成功 / 失敗 / KeyboardInterrupt / SIGTERM / --no-notify 3 経路 / --dry-run）、`TestSigtermHandler`、`TestWorkflowLabelFallback` を追加 |
| `scripts/tests/test_claude_loop_integration.py` | 変更 | `_run_steps` 戻り値タプル化に合わせて 1 箇所を `exit_code, _ = _run_steps(...)` へ調整 |
| `scripts/README.md` | 変更 | `notify.py` 行を run サマリ化・永続表示寄り説明に更新、「完了通知（run 単位）」節を新設 |
| `scripts/USAGE.md` | 変更 | `--no-notify` オプション説明を run 単位前提に更新、「完了通知（詳細）」節を新設（成功 / 失敗 / 中断の本文フォーマット table 含む） |
| `docs/util/MASTER_PLAN/PHASE7.1.md` | 変更 | §4 進捗を「未着手」→「実装済み（ver15.4）」に更新 |
| `docs/util/ver15.4/ROUGH_PLAN.md` | 既存（ver15.4 の `/issue_plan` で生成済み） | - |
| `docs/util/ver15.4/PLAN_HANDOFF.md` | 既存（同上） | - |
| `docs/util/ver15.4/IMPLEMENT.md` | 既存（`/split_plan` で生成済み） | - |
| `docs/util/ver15.4/MEMO.md` | 新規 | T1 PoC スキップ理由、リスク R1〜R6 検証結果、後続版への申し送り |
| `docs/util/ver15.4/CHANGES.md` | 新規 | 本ファイル |
| `ISSUES/util/low/toast-persistence-verification.md` | 新規 | R1（Windows toast 永続表示挙動）の実機目視検証 follow-up |

## 変更内容の詳細

### `RunSummary` データ構造の導入

`scripts/claude_loop_lib/notify.py` に `RunSummary` plain class を追加（dataclass 不使用、`.claude/rules/scripts.md` §1 遵守）。フィールド:

- `workflow_label`: `"claude_loop"` / `"claude_loop_quick"` / `"auto(full)"` / `"auto(quick)"` 等
- `result`: `"success"` / `"failed"` / `"interrupted"`
- `duration_seconds`: `time.monotonic()` 差分
- `loops_completed`: 完了 loop 数（`absolute_index == total_steps` をカウント）
- `steps_completed`: 完了 step 数（累計）
- `exit_code`: 非 success 時のみ
- `failed_step`: `result="failed"` 時の step 名
- `interrupt_reason`: `"SIGINT"` / `"SIGTERM"`

`title()` / `message()` メソッドで通知タイトル・本文を組み立てる。

### 通知発火経路の整理

`main()` を以下の構造に再編した:

```python
try:
    signal.signal(signal.SIGTERM, _sigterm_to_keyboard_interrupt)  # best-effort
    # ... execute workflow (exit_code, stats = _run_selected(...)) ...
except KeyboardInterrupt:
    result = "interrupted"; interrupt_reason = _last_signal; exit_code = 130
except SystemExit as e:
    # 記録してから再 raise（CLI exit code を保つ）
finally:
    if not args.no_notify and not args.dry_run:
        notify_completion(RunSummary(...))
```

- `parse_args()` / `validate_auto_args()` は `try` の外（argparse の `--help` / 引数ミスで通知が出ないように）
- `validate_startup` 以降の `SystemExit` は通知対象（startup 失敗を知らせる）
- `KeyboardInterrupt` は再 raise せず `exit_code = 130` を返す（notify が `finally` で動く）
- `SIGTERM` ハンドラはモジュール変数 `_last_signal` を `"SIGTERM"` に書き換えてから `KeyboardInterrupt` を raise。`except KeyboardInterrupt` 側で `_last_signal` を読む

### RunStats 情報伝播

`_run_steps` / `_execute_yaml` / `_run_auto` の戻り値を `int` → `tuple[int, RunStats]` に変更:

- `_run_steps` が step 完了ごとに `stats.completed_steps += 1`、loop 末尾で `stats.completed_loops += 1`、失敗時に `stats.failed_step = step["name"]`
- `_execute_yaml` が YAML パス stem を `stats.workflow_label` にセット
- `_run_auto` が phase1 / phase2 の RunStats を `RunStats.merge` で合算し、label を `"auto(full)"` / `"auto(quick)"` に確定

### Windows toast の永続表示寄り XML

`_notify_toast` を `ToastText02` テンプレート経由から生 XML 組み立てに切り替え:

```xml
<toast scenario='reminder' duration='long'>
  <visual><binding template='ToastGeneric'>
    <text>{title}</text><text>{message}</text>
  </binding></visual>
  <actions>
    <action content='閉じる' arguments='dismiss' activationType='system'/>
  </actions>
</toast>
```

Windows が `reminder` シナリオを拒否した場合、`duration='long'` のみの簡素な XML を再試行する（2 段フォールバック）。両方失敗で `RuntimeError` を raise し、`notify_completion` が beep + console fallback に降格する（3 段構造）。

XML エスケープは `xml.sax.saxutils.escape` を使用し、`<` / `>` / `&` / `"` / `'` を適切に変換する。PowerShell 単一引用符ぶつかりは `'` → `''` の doubling で処理。

### 通知本文の run サマリ化

- 成功: `claude_loop / 2 loops / 12 steps / 14m 32s`
- 失敗: `failed at imple_plan (exit 1) / claude_loop / 1 loop / 3 steps / 4m 11s`
- 中断: `interrupted (SIGINT) at write_current / claude_loop / 1 loop / 5 steps / 7m 02s`

所要時間フォーマットは `claude_loop_lib.logging_utils.format_duration` を再利用。

### PoC スキップとフォールバック構造

IMPLEMENT.md §T1 の Windows 実機 PoC は unattended 実行では実施不可（30 秒〜10 分の目視観察が必要）のためスキップ。代わりに reminder → long → beep の 3 段フォールバックを実装して OS 側の拒否に耐える構造にした。実機目視検証は `ISSUES/util/low/toast-persistence-verification.md` で follow-up 化。

### テストカバレッジ

- `test_notify.py`: 13 件（RunSummary title/message フォーマット、notify_completion の toast→beep 降格、toast XML の scenario / duration / エスケープ / フォールバック / 両 variant 失敗）
- `test_claude_loop_cli.py`: 成功 / 失敗 / KeyboardInterrupt / SIGTERM / `--no-notify` × 3 経路 / `--dry-run` / ハンドラ単体 / label fallback の 12 件を新規追加

既存テスト（`test_claude_loop_integration.py` の `_run_steps` 呼び出し 1 箇所）はタプル化対応の軽微修正のみ。

## 意図的な先送り

- `_notify_beep` の `print()` 直接呼び出し（`.claude/rules/scripts.md` §5 違反）→ 後続版で `logging_utils` に stderr ヘルパを追加してから差し替え
- `auto` モードの loop カウント意味論（phase1 + phase2 単純合算で過大表示される余地）→ 次バージョンで phase2 の loop 数のみを採用する方針を検討
- Windows 実機での toast 残留時間目視確認 → `ISSUES/util/low/toast-persistence-verification.md` で追跡

詳細は `docs/util/ver15.4/MEMO.md` を参照。

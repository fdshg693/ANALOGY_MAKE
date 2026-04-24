---
workflow: research
source: master_plan
---

# REFACTOR: util ver16.1 — PHASE8.0 §2 事前リファクタリング（軽度）

## スコープ

deferred execution の実装（`IMPLEMENT.md`）で `scripts/claude_loop.py` 本体に **「request 検知 → session 外部再開」の分岐**を差し込む前に、step 実行ループの責務を軽く整理する。

本版は **軽度** に留める。大規模リファクタを避け、deferred 分岐の差し込み箇所を 1 関数・数行に閉じられる状態にすることだけを目標とする。

## 対象 / 非対象

### 対象（本 REFACTOR で実施）

1. `scripts/claude_loop.py` の `_run_steps()` 関数（現状 line 528〜668 超の巨大ブロック）から、**1 step 分の実行に相当する処理**を private helper `_execute_single_step()` として抽出する
2. 抽出対象は「command 組み立て → subprocess 起動 → exit code 取得 → step footer 出力 → commit 差分表示」の塊。session ID 管理・feedback 消費・loop 集計は外側（`_run_steps`）に残す
3. 抽出の目的は、後続の `IMPLEMENT.md` §3 で `_execute_single_step()` の戻り値に「deferred request が生成されたか」を追加し、`_run_steps` 側で `claude -r <session-id>` 再呼び出しを挿入しやすくすること

### 非対象（本 REFACTOR では触らない）

- `_run_steps` 全体の構造変更・クラス化・非同期化
- `build_command` / `workflow.py` の interface 改変
- `claude_loop_lib/workflow.py` への `_run_steps` 自体の移譲（ROUGH_PLAN「軽度」の範囲超）
- session 管理ロジック（`previous_session_id` / `effective_continue`）の書き換え
- feedback 消費 / `load_feedbacks` の責務再編
- log 出力系列（`TeeWriter` / `_out`）の interface 変更
- テスト構造（`test_claude_loop_integration.py`）のフィクスチャ再設計

## 抽出後の形

```python
def _execute_single_step(
    *,
    command: list[str],
    command_str: str,
    cwd: Path,
    tee: TeeWriter | None,
    prev_commit: str | None,
    step_start: float,
) -> tuple[int, str | None]:
    """1 step 分の subprocess 実行とフッタ出力。戻り値は (exit_code, new_prev_commit)。"""
    ...
```

- 呼び出し側（`_run_steps`）はループ内で `exit_code, prev_commit = _execute_single_step(...)` と受け取るだけにする
- deferred 分岐は `_run_steps` 側で step 完了後に `scan_pending()` を呼ぶ方式（IMPLEMENT.md §3-3）を採用したため、本 helper の戻り値は 2-tuple のまま確定（tuple 拡張は行わない）

## 変更ファイル

| ファイル | 操作 | 備考 |
|---|---|---|
| `scripts/claude_loop.py` | 変更 | `_execute_single_step()` 抽出。行数としては `_run_steps` の ~30 行を関数化する程度 |

## テスト方針

- 既存 `tests/test_claude_loop_integration.py::TestRunStepsSessionTracking` が pass し続けることで十分（抽出は対外挙動ゼロ変更）
- 新規テストは追加しない（IMPLEMENT.md 側で deferred 実装と合わせて追加）

## 完了条件

- `_execute_single_step` が抽出され、`_run_steps` 側は「session ID 決定 → command 構築 → `_execute_single_step` 呼び出し → feedback 消費 → 次 step へ」の 4 ブロックで読める
- `pnpm` は不要。`python -m unittest discover scripts/tests` が pass
- diff が 50 行程度に収まっている（軽度の目安）

## 手順

1. `scripts/claude_loop.py` の該当ブロック（執筆時点 line 620〜642 相当）を切り出し、private helper として同ファイル内に定義
2. 呼び出し側を置換
3. `python -m unittest discover scripts/tests` を実行し回帰なしを確認
4. 単独コミット `refactor(ver16.1): extract _execute_single_step for deferred split`

---
workflow: full
source: master_plan
---

# ver15.4 IMPLEMENT — PHASE7.1 §4（run 単位・永続通知）

`ROUGH_PLAN.md` のスコープに沿って、`scripts/claude_loop.py` の通知発火点を run 終了時 1 箇所に収束させ、`scripts/claude_loop_lib/notify.py` を「run サマリを受け取り、永続表示寄りの toast を出す」API に拡張する実装手順を定義する。事前リファクタリングは ROUGH_PLAN の判断どおり不要（理由は `PLAN_HANDOFF.md` 経由）。

## 現状の再確認（実装前提の固定）

実装着手前にコードを読み直して確認した事実:

- `notify_completion(title, message)` は既に `main()` 末尾 1 箇所からのみ呼ばれている（`claude_loop.py:377-382`）。**「loop ごとに N 回通知」という ROUGH_PLAN 内の表現は実体としては既に「run 1 回」になっており、本実装の主眼は「内容の run サマリ化」「永続表示」「中断経路網羅」**である。発火点の物理的集約は既に達成済みなので、本版で行うのは _収束経路の補強_ と _情報量の充実_ に絞る。
- 現行の `_execute_yaml` / `_run_steps` は `int`（exit code）のみを返し、loop 数・失敗 step 名・workflow 種別はいずれも main 側に伝わらない。run サマリ化には呼び出し階層全体での情報伝播が必要。
- `KeyboardInterrupt`（Ctrl+C）は捕捉されておらず、SIGINT 時は notify 未発火のままトレースバックで終了する。`raise SystemExit(...)`（不正な cwd / YAML 不在等）も同様に notify をバイパスする。
- 現行 toast は `ToastTemplateType::ToastText02` テンプレートで生成しており、Windows 既定の Action Center 滞留時間（数秒〜数十秒で auto-dismiss）に依存している。`scenario` / `duration` 属性指定経路がない。
- `format_duration` は `logging_utils.py` に既存（再利用）。

## 実装方針（全体像）

1. **run 終了時に唯一の通知発火点を持つ**: `main()` を `try / except / finally` で囲み、`finally` ブロックから `_emit_completion_notification(summary)` を 1 回だけ呼ぶ。`SystemExit` / `KeyboardInterrupt` / その他例外のいずれの経路でも、`--no-notify` / `--dry-run` が立っていない限り通知が出ることを保証する。
2. **run サマリのデータ構造を導入**: `claude_loop_lib/notify.py` に `RunSummary` クラス（plain class、`dataclass` 不使用 — `.claude/rules/scripts.md` §1）を追加し、workflow 種別 / loop 完了数 / step 完了数 / 所要時間 / 結果区分（success / failed / interrupted） / 失敗 step 名 / 終了コードを保持する。
3. **情報を呼び出し階層で伝播**: `_run_steps` / `_execute_yaml` / `_run_auto` / `_run_selected` の戻り値を `(exit_code, run_stats)` の 2 要素タプルに拡張し、`main()` 側で `RunSummary` に集約する。
4. **永続表示寄りの toast XML へ移行**: `_notify_toast` を `ToastText02` テンプレート経由から、生 XML 文字列ベースに切り替える。`<toast scenario="reminder" duration="long">` と `<actions>` の dismiss ボタン 1 個構成で「人が閉じるまで残る」挙動を狙う。`reminder` シナリオは XML に `<actions>` を 1 つ以上含めることが必須。
5. **fallback 経路も run サマリ化**: `_notify_beep` も `(title, message)` API のまま残し、`notify_completion(summary)` 内で title/message を組み立ててから呼ぶ構造に統一。

## タイムライン

実装は概念的に 5 段階に分ける。先頭の PoC で OS 不確実性を潰してから内部 API を確定する順序。

### T1. PowerShell toast 永続化 PoC（先頭タスク）

**目的**: `<toast scenario="reminder" duration="long">` + dismiss ボタン構成が、開発者の Windows 11 環境で「人が閉じるまで Action Center に残る」挙動を取れることを実機で確認する。OS 仕様の不確実性は API 設計より前に潰す。

**手順**:

1. `experiments/notify_persist_poc.ps1`（一時ファイル、コミット不要）を作成し、以下 3 パターンを順に表示して比較:
   - 現行: `ToastText02` テンプレート（auto-dismiss）
   - パターン A: `<toast duration="long">` のみ（`reminder` シナリオなし）
   - パターン B: `<toast scenario="reminder">` + `<actions><action content="閉じる" arguments="dismiss" activationType="system"/></actions>`
2. 各パターン表示後、Action Center を開いて 30 秒・5 分・10 分後にも残っているか目視確認する。
3. 最も「閉じるまで残る」挙動が得られた XML を採用案として T2 の `_notify_toast` 実装テンプレートに反映する。
4. パターン B が動作する場合はそれを採用。動作しない（XML パースエラー / シナリオ未対応）場合はパターン A にフォールバックし、`MEMO.md` に OS 制約を記録する。

**完了条件**: 採用 XML 文字列が確定し、PoC スクリプトの実行結果（残留時間）を `MEMO.md` の「PoC 結果」節に 3〜5 行で記録する。

### T2. `notify.py` の API 拡張

**ファイル**: `scripts/claude_loop_lib/notify.py`

**変更点**:

1. `RunSummary` クラスを追加:

   ```python
   class RunSummary:
       def __init__(
           self,
           workflow_label: str,        # 例: "claude_loop_full" / "claude_loop_quick" / "claude_loop_issue_plan" / "claude_loop_auto(full)"
           result: str,                 # "success" | "failed" | "interrupted"
           duration_seconds: float,
           loops_completed: int,        # 完了 loop 数（部分実行含む）
           steps_completed: int,        # 完了 step 数（累計）
           exit_code: int | None = None,
           failed_step: str | None = None,    # result="failed" のとき step 名
           interrupt_reason: str | None = None,  # result="interrupted" のとき "SIGINT" 等
       ) -> None: ...

       def title(self) -> str: ...    # "Workflow Complete" / "Workflow Failed" / "Workflow Interrupted"
       def message(self) -> str: ...  # 1〜2 行の本文
   ```

   - `title()` / `message()` は呼び出し側で組み立てロジックを重複させないためのヘルパ。
   - `message()` のフォーマット例（success）: `"full / 2 loops / 12 steps / 14m 32s"`
   - `message()` のフォーマット例（failed）: `"failed at imple_plan (exit 1) / 1 loop / 3 steps / 4m 11s"`
   - `message()` のフォーマット例（interrupted）: `"interrupted (SIGINT) at write_current / 1 loop / 5 steps / 7m 02s"`
   - `format_duration` を `logging_utils` から import して再利用（重複定義しない）。

2. `notify_completion(summary: RunSummary) -> None` にシグネチャを変更:

   ```python
   def notify_completion(summary: RunSummary) -> None:
       title = summary.title()
       message = summary.message()
       try:
           _notify_toast(title, message)
       except Exception:
           _notify_beep(title, message)
   ```

   - 旧 API（`title, message` の 2 引数）は本版で削除する。`scripts/` 配下の唯一の呼び出し元は `claude_loop.py:380-382` のみで、本版で同時に書き換えるため互換 shim は不要。

3. `_notify_toast(title: str, message: str)` を T1 で確定した XML テンプレートに書き換える。**Gate**: T1 PoC が完了し採用 XML が `MEMO.md` に記録されるまで本サブタスクには着手しない。PoC 結果次第で XML 構造が変わるため、先行着手は手戻りリスクが高い。

   ```python
   xml = (
       f"<toast scenario='reminder' duration='long'>"
       f"  <visual>"
       f"    <binding template='ToastGeneric'>"
       f"      <text>{safe_title}</text>"
       f"      <text>{safe_message}</text>"
       f"    </binding>"
       f"  </visual>"
       f"  <actions>"
       f"    <action content='閉じる' arguments='dismiss' activationType='system'/>"
       f"  </actions>"
       f"</toast>"
   )
   ```

   PowerShell 側は `XmlDocument` をロードしてから `ToastNotification` を生成する形に切り替える。引用符ぶつかり回避のため、PowerShell コマンド側を `"..."` でラップし XML 内は `'...'` に統一する。`title` / `message` 内の XML エンティティ（`<` / `>` / `&` / `"` / `'`）のエスケープには **標準ライブラリの `xml.sax.saxutils.escape`**（quote エスケープ含む拡張版は `xml.sax.saxutils.quoteattr` または `escape(s, {'"': '&quot;', "'": '&apos;'})`）を使用する。3rd-party 依存追加は禁止（`.claude/rules/scripts.md` §1）のため、自前正規表現や手動置換ではなく標準モジュールに寄せる。

4. `_notify_beep(title, message)` は API・本文フォーマット（区切り線 + 2 行）ともに維持する。**規約遵守の意図的先送り**: 現行 `_notify_beep` は `print("\a")` / `print(f"...")` を直接呼んでおり、`.claude/rules/scripts.md` §5（`print()` 直接使用禁止、`logging_utils` 経由を必須）と矛盾する。本版は通知 API シグネチャ変更と toast XML 移行が主戦場で、fallback 経路の出力レイヤ書き換えはスコープ過大になるため意図的に持ち越す。`MEMO.md` に「`_notify_beep` の `print()` を `logging_utils` 経由（または `sys.stderr.write`）に切り替える follow-up」を明記し、後続バージョンで `logging_utils` 側に「TeeWriter コンテキストなしでも使える stderr 出力ヘルパ」を追加してから差し替える方針を残す。

### T3. `claude_loop.py` の制御フロー整理

**ファイル**: `scripts/claude_loop.py`

**変更点**:

1. **戻り値の拡張**: `_run_steps` / `_execute_yaml` / `_run_auto` / `_run_selected` の戻り値型を `tuple[int, RunStats]` に変更。`RunStats` は **`claude_loop.py` 内のローカル plain class として確定** する（`notify.py` には置かない）。理由は依存方向を `claude_loop.py → notify.py` の単方向に保ちたいため — `notify.py` は配信レイヤとして `RunSummary`（公開用 immutable サマリ）のみを知り、`claude_loop.py` は `RunStats`（内部集計用 mutable 構造）を `main()` 内で `RunSummary` に変換する責務を持つ。`RunStats` は `completed_count`、`completed_loops`、`failed_step`、`workflow_label` を保持する。

   - `_run_steps` 内で `completed_count` は既存（line 406）。`completed_loops` は `step_iter` を回しながら「`absolute_index == total_steps` を踏むたびに +1」で算出。`failed_step` は exit_code != 0 検出時に `step["name"]` を記録。
   - `_run_auto` は phase1 / phase2 の RunStats を合算する（合算ロジックは新規 helper `_merge_stats`）。

2. **workflow_label の決定**: `main()` 内で `resolved` の値から workflow ラベルを決定する関数 `_workflow_label(resolved: str | Path) -> str` を追加。
   - `resolved == "auto"` のとき、phase2 の `phase2_kind` を後付けで `"auto(full)"` / `"auto(quick)"` に追記する必要があるため、`_run_auto` 内で workflow_label を最終確定させて RunStats 経由で main へ返す。
   - YAML パスの場合は `Path(resolved).stem`（例: `"claude_loop_quick"`）を採用。

3. **`main()` の `try / except / finally` 化**:

   ```python
   def main() -> int:
       args = parse_args()
       # ... validation ...
       workflow_start = time.monotonic()
       result = "success"
       exit_code = 0
       interrupt_reason: str | None = None
       stats = RunStats()
       try:
           exit_code, stats = _run_selected_or_log(...)
           if exit_code != 0:
               result = "failed"
       except KeyboardInterrupt:
           result = "interrupted"
           interrupt_reason = "SIGINT"
           exit_code = 130
       except SystemExit as e:
           # SystemExit(int) や SystemExit("msg") を素通しする
           # notify は finally で出すが、再 raise する
           result = "failed" if (isinstance(e.code, int) and e.code != 0) else result
           exit_code = e.code if isinstance(e.code, int) else 1
           raise
       finally:
           if not args.no_notify and not args.dry_run:
               total_duration = time.monotonic() - workflow_start
               summary = RunSummary(
                   workflow_label=stats.workflow_label or _workflow_label_fallback(resolved),
                   result=result,
                   duration_seconds=total_duration,
                   loops_completed=stats.completed_loops,
                   steps_completed=stats.completed_steps,
                   exit_code=exit_code if result != "success" else None,
                   failed_step=stats.failed_step,
                   interrupt_reason=interrupt_reason,
               )
               notify_completion(summary)
       return exit_code
   ```

   - `parse_args()` 失敗（argparse の `SystemExit(2)`）は `try` の外なので通知されない。これは意図通り（ユーザ操作ミス段階で通知は不要）。
   - `validate_startup` 等の `SystemExit` は `try` の中に入れるため通知対象。`stats` は空（`RunStats()`）のままで、サマリ本文は「failed at startup / 0 loops / 0 steps / 0s」相当となる。
   - `SystemExit` を捕まえても再 raise することで、CLI exit code は従来どおり。

4. **SIGTERM ハンドラの登録**: Windows でも `signal.SIGTERM` は登録可能（Python の `signal` モジュールは Windows で SIGTERM を SIGINT 同様に扱える）。`main()` 冒頭で `signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt))` を入れる。これで `KeyboardInterrupt` 経路に合流させ、通知発火を保証。実装上は明示的なハンドラ関数を定義（lambda の throw は読みづらいため）:

   ```python
   def _sigterm_to_keyboard_interrupt(signum, frame):
       raise KeyboardInterrupt
   signal.signal(signal.SIGTERM, _sigterm_to_keyboard_interrupt)
   ```

   `interrupt_reason` は `KeyboardInterrupt` 単独からは SIGINT/SIGTERM の判別ができないため、ハンドラ側で `"SIGTERM"` をモジュールレベル変数に書き込み、`except KeyboardInterrupt` 側で読み出す方式にする（`_last_signal: str | None = "SIGINT"` を初期値、SIGTERM 受信時のみ上書き）。

   **timeout 経路の扱い（意図的除外）**: 現行 `_run_steps` 内の `subprocess.run` / `subprocess.Popen` 呼び出しはいずれも `timeout` 引数未指定で、Python 側からの timeout 経路は存在しない（外部 OS の SIGTERM / SIGKILL は R2 の signal 経路に合流）。したがって本版では「timeout 経路の収束」のために追加コードは不要。将来 step 単位 timeout（`subprocess.TimeoutExpired` の捕捉）を導入する際は、`_run_steps` 内で `KeyboardInterrupt` と同様の経路に合流させれば本実装の `try/except/finally` 構造に自然に乗る設計になっている。本判断を `MEMO.md` に「PHASE7.1 §4 完了条件のうち timeout は現行コードに発火源がないため意図的に対象外」と記録する。

5. **既存 `notify_completion("Workflow Complete", ...)` 呼び出しの削除**: 旧 2 引数呼び出しはすべて `finally` 内の新呼び出しに置き換える。重複発火がないことを `grep` で確認。

### T4. テスト追加

**ファイル**: `scripts/tests/test_notify.py`（拡張）と `scripts/tests/test_claude_loop_cli.py`（拡張、`main()` の通知発火経路を検証）。

**追加テスト**:

1. `test_notify.py`:
   - `test_run_summary_message_success_format`: `RunSummary(result="success", workflow_label="full", loops_completed=2, steps_completed=12, duration_seconds=872.0)` の `message()` が `"full / 2 loops / 12 steps / 14m 32s"` を返す。
   - `test_run_summary_message_failed_includes_step_and_exit`: `result="failed", failed_step="imple_plan", exit_code=1` の `message()` に `"imple_plan"` と `"exit 1"` が含まれる。
   - `test_run_summary_message_interrupted_includes_reason`: `result="interrupted", interrupt_reason="SIGINT"` の `message()` に `"SIGINT"` が含まれる。
   - `test_run_summary_title_by_result`: `title()` が "Workflow Complete" / "Workflow Failed" / "Workflow Interrupted" を返し分ける。
   - `test_notify_completion_passes_summary_strings_to_toast`: `notify_completion(summary)` が `_notify_toast(summary.title(), summary.message())` を呼ぶ（mock）。
   - `test_toast_xml_contains_scenario_and_duration`: `_notify_toast(...)` が組み立てる PowerShell コマンドに `scenario='reminder'` と `duration='long'` が含まれる（subprocess.run mock の引数を assert）。
   - `test_toast_escapes_xml_entities`: `_notify_toast("a<b>", "x&y")` が PowerShell コマンドに `&lt;` / `&gt;` / `&amp;` を含み、生 `<` / `&` を含まない。
   - 既存 `test_toast_escapes_single_quotes` は新 XML テンプレートでも維持されるよう更新（`it''s done` ではなく XML 構造に合わせた quote エスケープ確認に書き換え）。

2. `test_claude_loop_cli.py`（または新規 `test_main_notify.py`）:
   - `test_main_emits_summary_on_success`: `main()` 正常終了時に `notify_completion` が `RunSummary(result="success", ...)` で 1 回呼ばれる。
   - `test_main_emits_summary_on_failure`: `_run_selected` を mock して `(1, RunStats(failed_step="x"))` を返させ、`RunSummary(result="failed", failed_step="x", exit_code=1)` で 1 回呼ばれる。
   - `test_main_emits_summary_on_keyboard_interrupt`: `_run_selected` が `KeyboardInterrupt` を raise する mock で、`RunSummary(result="interrupted", interrupt_reason="SIGINT", exit_code=130)` で呼ばれ、`SystemExit(130)` で終わる。
   - `test_main_emits_summary_on_sigterm`: `signal.raise_signal(signal.SIGTERM)` を `_run_selected` の mock 内で送り、`interrupt_reason="SIGTERM"` で呼ばれる。Windows でのみ実行（`@unittest.skipUnless(sys.platform == "win32", ...)` を付ける — Linux でも SIGTERM は使えるが、本実装が Windows 前提のため）。
   - `test_main_no_notify_flag_suppresses`: `--no-notify` 指定時は失敗・成功・中断いずれでも `notify_completion` が呼ばれない。
   - `test_main_dry_run_suppresses`: `--dry-run` 指定時も同様。
   - `test_main_workflow_label_quick`: `--workflow quick` で `RunSummary.workflow_label == "claude_loop_quick"`。
   - `test_main_workflow_label_auto_full`: `_run_auto` の戻り値 `RunStats` に `workflow_label="auto(full)"` をセットした mock を用意し、`main()` がその値を `RunSummary.workflow_label` に伝播させて `notify_completion` を呼ぶことを assert する（`main()` のラベル伝播経路の検証）。`_run_auto` 内部で phase2 種別から `"auto(full)"` / `"auto(quick)"` をどう決定するかは独立した単体テスト `test_run_auto_label_full` / `test_run_auto_label_quick`（既存 `TestAutoWorkflowIntegration` クラスに追加）でカバーする。テスト責務を「main の伝播」と「auto 内の決定ロジック」に分割することで、mock 範囲を最小化する。

   既存テスト群は subprocess.run / uuid.uuid4 を mock する確立されたパターンを持つので、それを踏襲。`signal.signal` を mock する場合は `setUp/tearDown` で original を退避する。

### T5. docs 同期

**ファイル**:
- `scripts/README.md`: `notify.py` の行（line 39）を `notify_completion(RunSummary)（toast→beep フォールバック、run サマリ化・永続表示寄り）` に更新。run 単位通知の節（既存「ログ出力・自動コミット…」の段落直後あたり）に 5〜7 行で「workflow 全体終了時に 1 回だけ通知」「成功/失敗/中断の区分とタイミング」「Windows toast の永続表示挙動」を追記。
- `scripts/USAGE.md`: line 40 周辺の `--no-notify` 説明に「multi-loop / 中断時も含め run 終了時 1 回のみ発火」「通知本文に workflow 名・loop 数・所要時間・失敗 step を含む」「Windows では Action Center に dismiss まで残る」を 3 行追記。
- `docs/util/MASTER_PLAN/PHASE7.1.md`: §4 進捗表（line 12）の「未着手 | ver15.2」を「実装済み | ver15.4」に更新。

### T6. YAML / rules 同期

ROUGH_PLAN §スコープ#5 のとおり `--no-notify` / `--dry-run` の挙動は破壊しない。**新規 CLI フラグの追加は本版では不要**（run サマリ化は内部リファクタで完結し、CLI 表面には現れない）。したがって 5 つの `claude_loop*.yaml` の `command` / `defaults` セクション同期は本版の作業対象外。

ただし、後続バージョンで「run summary verbosity」のような新フラグを追加する案が残ったら、その時点で 5 YAML 同期を実施する旨を `MEMO.md` に残す。

## 影響範囲（変更ファイル一覧）

| ファイル | 操作 | 理由 |
|---|---|---|
| `scripts/claude_loop_lib/notify.py` | 変更 | `RunSummary` 追加、`notify_completion` シグネチャ変更、toast XML を永続表示寄りに差し替え、XML エスケープ helper 追加 |
| `scripts/claude_loop.py` | 変更 | 戻り値タプル化、`main()` の try/except/finally 化、SIGTERM ハンドラ、workflow_label 決定 |
| `scripts/tests/test_notify.py` | 変更 | RunSummary・新 toast XML・XML エスケープのテスト追加、既存 quote エスケープテスト更新 |
| `scripts/tests/test_claude_loop_cli.py` | 変更 | `main()` 経由の通知発火（成功/失敗/中断/no-notify/dry-run/workflow_label）テスト追加 |
| `scripts/README.md` | 変更 | `notify.py` 説明を run サマリ化対応に更新、通知仕様節を追記 |
| `scripts/USAGE.md` | 変更 | `--no-notify` 説明を run 単位前提に書き換え |
| `docs/util/MASTER_PLAN/PHASE7.1.md` | 変更 | §4 進捗表を「実装済み（ver15.4）」へ |
| `docs/util/ver15.4/MEMO.md` | 追加 | T1 PoC の OS 挙動メモ、timeout 経路扱い、後続版で検討する verbosity フラグ案 |
| `docs/util/ver15.4/CHANGES.md` | 追加（後続 step） | 後続 `/wrap_up` / `/imple_plan` で作成 |

## リスク・不確実性

PHASE7.1 §4 は OS 通知仕様と Python シグナル処理という、テスト環境では再現しづらい層に触れるため、以下を事前に明示する。

### R1. Windows toast の永続化挙動が OS バージョン / フォーカス支援設定で変わる

- **不確実性の中身**: `<toast scenario="reminder" duration="long">` + dismiss ボタン構成は、Windows 11 の最新ビルドでは Action Center に長時間残るが、フォーカス支援が「優先度の高い通知のみ」に設定されているとそもそもトーストが表示されない可能性がある。Windows 10 の旧ビルドでは `scenario="reminder"` をサポートせず、XML パースエラーで失敗するケースが報告例にある（型定義文書なし）。
- **緩和策**: T1 PoC で開発者の実環境で動作確認を取り、動かない場合は `duration="long"` 単独 / 旧 `ToastText02` への自動フォールバックを `_notify_toast` 内に組み込む（try/except でスキーマ違いを検出し、より単純な XML へ降格させる）。`_notify_beep` の最終 fallback は維持。
- **検証手段**: PoC スクリプトを開発者の実機で目視。CI では実機 GUI がないため自動検証は不可能と割り切り、XML 文字列の構造のみを unit test で検証する。

### R2. `KeyboardInterrupt` 経路で SIGINT / SIGTERM の判別が困難

- **不確実性の中身**: Python の `signal.signal` で SIGTERM ハンドラから `KeyboardInterrupt` を投げる方式は、`except KeyboardInterrupt` 側で「どのシグナルから来たか」を直接判別できない。モジュールレベル変数で間接的に伝える方式は、テスト時に状態が前テストから漏れるリスクがある。
- **緩和策**: モジュールレベル変数（`_last_signal: str = "SIGINT"`）の初期化を `main()` 冒頭で必ず行い、テストの `setUp` で同様にリセットする helper を `tests/_bootstrap.py` の延長として追加。または、`signal.signal` 戻り値で original handler を保持して `tearDown` で復元する unittest mixin を作る。
- **代替案**: SIGTERM ハンドラから直接 `notify_completion` を呼んで `os._exit(143)` する設計も検討したが、`finally` 経路に統一する設計と整合しないため不採用。

### R3. `SystemExit` を捕まえる経路の境界が曖昧

- **不確実性の中身**: `parse_args()` の argparse 内部 `SystemExit` まで通知対象に含めると、`-h` / `--help` 表示時にも通知が発火する。逆に `validate_startup` の `SystemExit` を通知対象から外すと、設定ミス系の早期失敗が通知されない。
- **緩和策**: `parse_args()` を `try` の外に出し、`validate_startup` 以降を `try` 内に置く。これで「ユーザがコマンドラインを書き間違えた段階」と「実行を試みて失敗した段階」が明確に分離される。本判断を `MEMO.md` の決定事項節に記録。

### R4. テストでの `signal.raise_signal(SIGTERM)` の Windows 挙動

- **不確実性の中身**: `signal.raise_signal(signal.SIGTERM)` は Python 3.8+ で利用可能だが、Windows での挙動は `os.kill(os.getpid(), signal.SIGTERM)` 経由と微妙に異なるケースがある（プロセスが即時終了してテストフレームワークが結果を回収できないリスク）。
- **緩和策**: SIGTERM の伝播ロジックは「ハンドラ関数 `_sigterm_to_keyboard_interrupt` を直接呼び出す」単体テストでカバーし、`signal.raise_signal` 経由の end-to-end は `@unittest.skipUnless` で条件付き / `@unittest.skip` で先送りも許容する。本トレードオフを `MEMO.md` に記録。

### R5. `_run_steps` の戻り値変更が他テストに波及

- **不確実性の中身**: `_run_steps` は既存テスト群（`test_claude_loop_integration.py` の `TestRunStepsSessionTracking` など）が `int` 戻り値前提でアサートしている。タプル化すると一括書き換えが必要。
- **緩和策**: タプル化前に `grep -rn "_run_steps" scripts/tests/` で呼び出し元を全列挙し、影響範囲を T3 着手時点で確認。書き換えは機械的でレビュー負荷は低い。

### R6. ROUGH_PLAN 内「loop ごとに N 回通知」記述との齟齬

- **不確実性の中身**: 本実装に着手する前にコードを読み直したところ、現行 `notify_completion` は既に main 末尾 1 箇所からのみ呼ばれており、「loop ごとに N 回通知される」状態にはなっていない。ROUGH_PLAN §「提供する体験の変化」の該当行は実態と乖離している。
- **緩和策**: 本 IMPLEMENT.md 冒頭「現状の再確認」節で齟齬を明示し、本版の主眼を「内容の run サマリ化」「永続表示」「中断経路網羅」に再定義した。MASTER_PLAN §4 期待挙動とは齟齬がないため、最終成果物としては問題ない。`/retrospective` 段で ROUGH_PLAN の文言精度の改善観点として記録する。

## 完了条件

- 単一 run（`--max-loops 1`）の正常終了で run サマリ通知が 1 回出る
- multi-loop run（`--max-loops 2` 以上）の正常終了で通知が 1 回だけ出る（途中 loop で発火しない）
- step 失敗時に「失敗 step 名と終了コード」が通知本文に含まれる
- Ctrl+C 中断時に「interrupted (SIGINT)」を含む通知が 1 回出て、exit code 130 で終了する
- SIGTERM 受信時に「interrupted (SIGTERM)」を含む通知が 1 回出る（テストはハンドラ直接呼び出しで検証）
- `--no-notify` / `--dry-run` 指定時はいずれの経路でも通知が出ない
- Windows Action Center で通知が auto-dismiss されにくい挙動が PoC で確認できる
- `scripts/README.md` / `scripts/USAGE.md` / `docs/util/MASTER_PLAN/PHASE7.1.md` が新仕様と整合
- 既存テスト全件 + 新規テスト全件パス（`python -m pytest scripts/tests/`）

## 参照

- ROUGH_PLAN.md / PLAN_HANDOFF.md（ver15.4 同ディレクトリ）
- MASTER_PLAN: `docs/util/MASTER_PLAN/PHASE7.1.md` §4
- 現行通知実装: `scripts/claude_loop_lib/notify.py`
- 現行制御フロー: `scripts/claude_loop.py:336-385`（`main` 周辺）
- スクリプト規約: `.claude/rules/scripts.md`

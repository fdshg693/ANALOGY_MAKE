---
workflow: research
source: master_plan
---

# IMPLEMENT: util ver16.1 — PHASE8.0 §2 deferred execution

本版は `workflow: research`。`/research_context` と `/experiment_test` は本ドキュメント、とくに §0（未解決論点）と §リスク・不確実性、そして §3-3（方式候補）を入力として読む前提で書いている。「実験判断待ち」とマークされた項目は `EXPERIMENT.md` の結果をもって `/imple_plan` 段で確定する。

---

## §0. 未解決論点（`/research_context` / `/experiment_test` が解消する対象）

以下 5 項目は ROUGH_PLAN / PLAN_HANDOFF で持ち越された論点。各項目に「何を / どのソースで / どう確認するか」を明記する。

### 0-1. 既存 session 継続経路と deferred resume の競合可能性

- **問い**: `scripts/claude_loop.py` の現行 session 管理（`previous_session_id` + `-r session_id` の継続、`continue: true` flag、`--start > 1` 時の `continue_disabled`）と、deferred 完了後に発生する「workflow を一旦終了 → 外部プロセスが `claude -r <session-id>` で再起動」の経路が両立するか。
- **ソース**: (a) `scripts/claude_loop.py` line 541〜567（`effective_continue` 解決）・line 569〜573（`build_command` への session 渡し）・line 665〜668（`previous_session_id = session_id` 更新）、(b) `scripts/claude_loop_lib/commands.py::build_command` の `-r` フラグ付与ロジック、(c) Claude Code CLI の `--session-id` / `-r` の挙動（`scripts/USAGE.md` に記述あれば優先、なければ `claude --help` / 公式 docs）。
- **確認方法**: (i) 現行コードを静的に読解し、session ID が「実プロセス終了後」に消えるのか in-process 変数のみに留まるのかを特定。(ii) deferred resume を想定した一連フローを図に起こし、「同一 session ID に対する 2 回目の `claude -r` 実行」が許容されるかを experiment で検証する必要があれば `EXPERIMENT.md` で実測。

### 0-2. registered command request の file layout / schema

- **問い**: request file の配置場所・命名・形式（YAML / JSON）・必須フィールドをどう定めるか。
- **ソース**: (a) 既存の queue 運用（`ISSUES/{category}/{priority}/` / `QUESTIONS/{category}/{priority}/` / `FEEDBACKS/*.md` + `FEEDBACKS/done/`）の frontmatter + markdown 形式、(b) `scripts/claude_loop_lib/feedbacks.py::load_feedbacks` の読み取り規約（glob 非再帰・`done/` 除外）、(c) `scripts/claude_loop_lib/frontmatter.py::parse_frontmatter` の共通基盤。
- **確認方法**: 既存 queue 3 種の frontmatter+本文方式に合わせる案と、`.json` sidecar を併用する案を比較。Python 側の再読み込み・Claude 側の書き出しやすさの両面で、どちらが事故を減らすかを `RESEARCH.md` でまとめる。schema フィールド候補は §2-2 に暫定列挙する（確定は `/imple_plan`）。

### 0-3. 巨大結果ファイルの先頭サマリ抽出規約

- **問い**: stdout/stderr が数十 MB に膨れた場合、resume 時に Claude へ渡す「追加情報」をどの形で制約するか。
- **ソース**: (a) Claude Code CLI への追加 prompt 経由で渡せる実効長（`claude -r -p "..."` の長さ制約）、(b) 既存 `logging_utils.py::TeeWriter` のログ整形、(c) OS レベルの「先頭 N 行 / 末尾 N 行 / 正規表現抽出」標準的 idiom。
- **確認方法**: 候補 4 案（A: 固定バイト数の head/tail / B: 固定行数の head+tail / C: sidecar `.meta.json` に `{exit_code, size_bytes, line_count, head_excerpt, tail_excerpt}` / D: 呼び出し元が明示的に `summary_extractor` を指定）を `RESEARCH.md` で比較。`EXPERIMENT.md` で C 案 + head/tail 行数を実測して最終案を決める（**実験判断待ち**）。

### 0-4. `experiments/` 配下の方式比較の置き方

- **問い**: 複数方式（fixture / worktree / 模擬 queue / wrapper script / file watcher）の試行記録を `experiments/deferred-execution/` の下にどう配置するか。
- **ソース**: (a) `experiments/README.md` §規約（依存隔離 / 削除条件コメント）、(b) 既存 `experiments/` 直下 4 ファイルの置き方。
- **確認方法**: 方式ごとに `experiments/deferred-execution/{variant}/` を切る案と、`experiments/deferred-execution/NOTES.md` に集約する案を比較。本版は deferred 実装本体を含むため、`{variant}/` を切って各方式を独立スクリプト化する方が後続 retrospective で見通しがよい。`EXPERIMENT.md` で最終採用変種を 1 つに絞り込み、落選方式は削除条件コメント付きで残す。

### 0-5. 本番 queue との隔離ディレクトリ配置

- **問い**: deferred request / result を `ISSUES/` / `QUESTIONS/` / `FEEDBACKS/` / `logs/workflow/` と共有せず、どこに置くか。
- **ソース**: ROUGH_PLAN「本番 `ISSUES/` / `QUESTIONS/` / `FEEDBACKS/` / `logs/workflow/` と queue を共有しない原則」、PLAN_HANDOFF §後続 step への注意点 1.
- **確認方法**: 候補 (A: repo ルート直下 `DEFERRED/` / B: `data/deferred/`（`data/` は gitignore 済）/ C: `logs/deferred/`）を比較。本番 queue と名前が衝突しない・diff を汚さない・ユーザーが実ファイルを見やすいの 3 点で評価。`RESEARCH.md` で 1 案を推薦し、`/imple_plan` で確定。

---

## §1. 目的（再掲）

PHASE8.0 §2-3 完了条件 5 項目（checklist 用にそのままコピー）:

- [ ] 1 件の registered command set を、登録 → 外部実行 → 結果保存 → request 削除 → session 再開まで **無人で** 完走できる
- [ ] 結果ファイルだけを見て、何のコマンドが走ったか・成功したか・出力が大きいかを判断できる
- [ ] 90 秒ごとの見守りや Claude の長時間待機なしで、インフラ作業や重い検証を run に取り込める
- [ ] 失敗時も orphan request が残らず、resume 時に必要な情報が欠けない
- [ ] workflow 自己テストについては「有望な方式と避けるべき方式」が docs / experiments に整理されるが、標準 workflow や CI への常時組み込みまでは行わない

---

## §2. アーキテクチャ（方向性）

### 2-1. 全体シーケンス

```
[claude_loop.py]
  step N 実行
    └─ subprocess で claude -p "..." 起動
        └─ Claude が /<skill> を実行する途中で
             deferred_commands.register(...) 経由の markdown request file を書く
             (例: DEFERRED/<request_id>.md を frontmatter + body で書き込み)
        └─ Claude はそのまま終了 (exit 0)

  _run_steps は step 完了後に DEFERRED/ を走査
    ├─ request なし → 次 step へ（従来どおり）
    └─ request あり →
          (a) 各 request を順に外部実行 (subprocess.run)
          (b) 結果ファイル DEFERRED/results/<request_id>.result + .meta.json を保存
          (c) request file を DEFERRED/done/ に移動
          (d) resume prompt を組み立てて claude -r <session_id> -p "<resume_prompt>" を起動
               (=「次 step」として再実行するのではなく、同じ session を追加入力で続ける)
          (e) resume が正常終了したら、workflow を通常の step N+1 へ継続
```

ポイント:
- **deferred 分岐の差し込み先**は REFACTOR.md で抽出した `_execute_single_step()` の戻り値に `deferred: bool` を追加し、`_run_steps` 側で request 走査 → 再開を行う 1 か所
- registered command は **request schema を満たす構造化 markdown** とし、自由記述 shell スクリプトを埋め込まない（ROUGH_PLAN で明記）
- resume は **新規 session ID を発行せず** `previous_session_id` をそのまま使う（既存の `continue: true` と同じ経路）

### 2-2. Request schema（暫定）

`DEFERRED/<request_id>.md`:

```markdown
---
request_id: <uuid4>
source_step: <step name, e.g. "research_context">
session_id: <Claude session id>
cwd: <absolute or repo-relative path>
expected_artifacts:
  - <path>
  - <path>
timeout_sec: <int | null>
note: |
  (resume 時に Claude に渡す補足メモ。短く保つ)
---

# Commands

```bash
<command line 1>
<command line 2>
```
```

本文の fenced code block の各行が「順次実行するコマンド」。1 request 内のコマンドは **順次実行**（前段が失敗したら後続はスキップ）。schema validation は `claude_loop_lib/validation.py` に追加。

> ※ YAML/JSON か markdown+frontmatter かは §0-2 で最終決定。本暫定案は「既存 queue と同形式（frontmatter+body）で統一」を優先した案。

### 2-3. Result ファイル仕様（暫定）

`DEFERRED/results/<request_id>.meta.json`:

```json
{
  "request_id": "...",
  "source_step": "research_context",
  "session_id": "...",
  "commands": ["..."],
  "started_at": "2026-04-24T18:00:00",
  "ended_at":   "2026-04-24T18:03:12",
  "duration_sec": 192,
  "exit_codes": [0, 0, 127],
  "overall_exit_code": 127,
  "stdout_bytes": 4823091,
  "stdout_path": "DEFERRED/results/<request_id>.stdout.log",
  "stderr_bytes": 12890,
  "stderr_path": "DEFERRED/results/<request_id>.stderr.log",
  "head_excerpt": "...", 
  "tail_excerpt": "..."
}
```

- **単体で「何が走ったか / 成功か / 出力が大きいか」が判定可能** （完了条件 2 を満たす）
- 巨大 stdout は別ファイル化し、meta には excerpt のみ（完了条件 2 + §0-3）
- excerpt の行数は **実験判断待ち**（§0-3、`EXPERIMENT.md` で決定）

### 2-4. Resume prompt（暫定）

```
<previous workflow context...>

DEFERRED EXECUTION COMPLETED:
- request: DEFERRED/done/<request_id>.md
- result meta: DEFERRED/results/<request_id>.meta.json
- overall_exit_code: <n>
- stdout_bytes: <n>, stderr_bytes: <n>

必要に応じて meta と stdout/stderr path を Read して判断してください。
次 step に進む場合は workflow を継続し、致命的失敗なら明示的に `exit 1` してください。
```

具体的な文面は `claude_loop_lib/deferred_commands.py::build_resume_prompt()` で生成。

---

## §3. 変更ファイル詳細

### 3-1. 新規: `scripts/claude_loop_lib/deferred_commands.py`

公開関数（案）:

| 関数 | 役割 |
|---|---|
| `scan_pending(deferred_dir: Path) -> list[DeferredRequest]` | `DEFERRED/*.md` を非再帰 glob（`done/` と `results/` は除外） |
| `validate_request(path: Path) -> DeferredRequest` | frontmatter + body パース、schema 検査（必須フィールド・cwd 存在・fenced code block 1 個） |
| `execute_request(req: DeferredRequest, *, deferred_dir: Path) -> DeferredResult` | subprocess.run で順次実行、meta.json/stdout.log/stderr.log 書き出し |
| `consume_request(req_path: Path, done_dir: Path) -> None` | request を `done/` へ move（失敗時も呼ぶ = orphan 防止） |
| `build_resume_prompt(results: list[DeferredResult]) -> str` | resume 用の追加 prompt 組み立て |

型は `dataclasses` を使わず素の `dict`/`TypedDict` または `namedtuple`（`.claude/rules/scripts.md` §1「dataclass 禁止」準拠）。frontmatter 読み取りは `frontmatter.py::parse_frontmatter` を再利用。

### 3-2. 変更: `scripts/claude_loop_lib/validation.py`

- `validate_deferred_request(path) -> list[str]`（errors）を追加
- startup 時には呼ばない（実行時検査）。`deferred_commands.validate_request` から呼ぶ
- 新設 effort / workflow 定数への追加は不要

### 3-3. 変更: `scripts/claude_loop.py`

1. `_execute_single_step()`（REFACTOR.md で抽出）の戻り値を `tuple[int, str | None]` → `tuple[int, str | None]` のまま保ち、deferred 検知は **step 完了後に `_run_steps` 側で `scan_pending` を呼ぶ**方式を採る（関数戻り値を拡張するより副作用が小さい）
2. `_run_steps` のループ最下部（feedback 消費と `previous_session_id` 更新の間）に:
    ```python
    pending = scan_pending(deferred_dir)
    if pending:
        results = [execute_request(req, deferred_dir=deferred_dir) for req in pending]
        for req in pending:
            consume_request(req.path, deferred_dir / "done")
        resume_prompt = build_resume_prompt(results)
        # Claude を -r session_id で再起動し、resume_prompt を追加入力で渡す
        resume_code = _execute_resume(session_id, resume_prompt, ...)
        if resume_code != 0:
            # 失敗切り分け: orphan は既に done/ 済み。workflow は止める
            stats.failed_step = step["name"] + " (deferred resume)"
            return resume_code, stats
    ```
3. `_execute_resume()` は `build_command` に `resume=True` を通して `claude -r <session_id> -p <resume_prompt>` を組み、`subprocess.run` / `TeeWriter` で実行（既存経路の流用）
4. `deferred_dir` は §0-5 決定後に確定（暫定は `Path.cwd() / "DEFERRED"`）
5. `--no-deferred` CLI フラグを追加し、問題切り分け用に deferred 検知を無効化できる（`parse_args` + `_run_steps` へ伝播、`.claude/rules/scripts.md` §3 準拠で argparse 追加）

### 3-4. 変更: `scripts/claude_loop_lib/logging_utils.py`

- `format_deferred_result(result: DeferredResult) -> str`（step footer 直後に挿入する 2〜4 行の要約）を追加
- 既存 `TeeWriter` / `format_duration` の interface 変更なし

### 3-5. 変更: `scripts/claude_loop_research.yaml`

- `write_current` step に `effort: high` を追加（ROUGH_PLAN §5）
- ほか 5 YAML（`claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` / `claude_loop_scout.yaml` / `claude_loop_question.yaml`）は **本版スコープ外**。ただし `.claude/rules/scripts.md` §3「6 ファイル間で同一内容を保つ」は `command` / `defaults` セクション限定のため、個別 step の effort 調整は sync 対象ではない（ROUGH_PLAN §5 で明示）

### 3-6. 新規: `scripts/tests/test_deferred_commands.py`

テスト対象（最小セット）:

1. `validate_request`: 正常・frontmatter 欠落・fenced code block 複数・cwd 不在でのエラー
2. `execute_request`: 正常（`echo ok` 的な fixture 1 コマンド）・失敗（`exit 1`）・複数コマンド（前段失敗で後段スキップ）
3. `consume_request`: `done/` へ move、既存 `done/<same name>` との衝突時のリネーム規則
4. `build_resume_prompt`: exit_code / stdout_bytes が prompt に含まれる・巨大 excerpt を渡さない

fixture は `tempfile.mkdtemp()` ベース（既存テストと揃える）。

### 3-7. 変更: `scripts/tests/test_claude_loop_integration.py`

- 既存の `TestRunStepsSessionTracking` に **deferred 経路の統合テスト**を 1 case 追加
- 流れ: fake YAML 1 step → mock subprocess.run で step 本体成功 + `DEFERRED/<uuid>.md` を tmp に事前配置 → `scan_pending` が拾う → `_execute_resume` も mock → resume が呼ばれたこと / request が `done/` へ移動したこと / `previous_session_id` が正しく伝搬したことを assert
- mock 対象は `subprocess.run` / `subprocess.Popen` / `uuid.uuid4`（既存と同様）

### 3-8. 変更: `scripts/README.md` / `scripts/USAGE.md`

- README: deferred execution 概要 1 段落 + `DEFERRED/` の配置（§0-5 確定後）
- USAGE: `--no-deferred` フラグ、request schema、result meta.json スキーマの要約、「巨大出力は meta + stdout.log に分離されるので prompt に全部貼らない」注意

### 3-9. 新規: `experiments/deferred-execution/`

- `{variant}/` サブディレクトリで方式比較を残す（§0-4）
- 各スクリプト先頭に「目的 / 削除条件」コメント必須（`experiments/README.md` §規約 3）
- 削除条件の目安: 「§2 完了条件を満たす方式が確定し、`scripts/claude_loop_lib/deferred_commands.py` に統合された時点で当該 variant は削除」

---

## §4. 実装手順

1. **REFACTOR** — REFACTOR.md の helper 抽出を先行コミット
2. **schema・file layout の仮実装** — `deferred_commands.py` の scan / validate / consume を先に作り、unit test で閉じる
3. **execute_request + meta.json 書き出し** — subprocess.run ベース、stdout を file へ、巨大出力の excerpt は `/experiment_test` 結果を待って決定（**実験判断待ち**）
4. **claude_loop.py への統合** — `_run_steps` に scan → execute → consume → resume の 1 ブロック挿入
5. **`_execute_resume()` の実装** — `build_command(resume=True, prompt=resume_prompt, ...)` + `subprocess.run` / `TeeWriter`
6. **research YAML の effort 調整**
7. **統合テスト追加**
8. **`experiments/deferred-execution/` 整備** — §0-4 で採用した方式を 1 variant として残し、落選方式は削除条件コメント付きで残す
9. **README / USAGE 追記**
10. **完了条件 5 項目のセルフチェック**

---

## §5. リスク・不確実性

### 5-1. Session resume の二重起動リスク

**リスク**: `claude -r <session-id>` を「deferred 完了後」に呼ぶ経路と、次の workflow step で `continue: true` のため `-r <session-id>` を呼ぶ経路が同 session ID に対して時間差で 2 回走ると、2 回目の `-r` が古い session を巻き戻すか・新規 branch を切るかが CLI 実装依存で不明。

**確認方法**: `/research_context` で (a) `claude --help` / 公式 docs の `-r` 挙動、(b) `scripts/USAGE.md` 既存記述、(c) `scripts/claude_loop.py` 現行 continue path の実コード、を確認。`/experiment_test` で (a) 同一 session ID に `claude -r ... -p "..."` を 2 回連続で呼び、2 回目が history を継承するかを実測（`experiments/deferred-execution/resume-twice/`）。

**fallback**: もし 2 回目の resume が安全でないと判明した場合、deferred 完了後の resume を「新規 session ID + 履歴を明示的に prompt に貼る」方式へ切り替える（その場合は session 継続性が失われるため、`research` workflow の中盤 step でのみ deferred を許容する制約を追加）。

### 5-2. orphan request の発生条件

**リスク**: `execute_request` 実行中に Python プロセスが SIGKILL された場合、`consume_request` が呼ばれず `DEFERRED/<id>.md` が残る。次の workflow 起動で再実行されると副作用あるコマンド（`git push`、DB migration 等）が 2 回走る恐れ。

**確認方法**: `/experiment_test` で、`execute_request` の try/finally と「開始マーカー file」方式（`DEFERRED/<id>.started` を事前書き出し、起動時に残存なら警告）を比較。

**fallback**: ver16.1 では「`DEFERRED/<id>.started` 残存時は実行をブロックし、ユーザー判断を求める ISSUE を自動起票」の最小機構のみ実装。本格的な冪等性保証（checkpoint / transaction）は ver16.2 以降。

### 5-3. 巨大 stdout による prompt 肥大化

**リスク**: excerpt 方式の上限が甘いと resume prompt が数万トークンになり、cost が跳ね上がる（PHASE8.0 §3 の計測がないため本版では気付きにくい）。

**確認方法**: `/experiment_test` で excerpt 行数を (A: head 50 + tail 50 / B: head 200 + tail 200 / C: head 20 + tail 20 + sizes のみ) の 3 案で比較し、実測サイズを `EXPERIMENT.md` に残す（**実験判断待ち**）。

**fallback**: 既定を C（最小）にし、Claude 側が「必要なら meta.json の path を Read せよ」と促す方針を採れば、prompt 肥大化の上限は予測可能。

### 5-4. YAML sync 契約への軽い逸脱

**リスク**: `scripts/claude_loop_research.yaml` のみ `write_current` step に `effort: high` を追加するのは、`.claude/rules/scripts.md` §3「6 ファイル間で同一内容」を表面的には破っているように見える。

**確認方法**: rule 本文の対象が `command` / `defaults` セクションであり、`steps` セクションは各 YAML 独自の構成が前提であることを再確認（本 ROUGH_PLAN §5 で既に整理済み）。

**fallback**: `/retrospective` 段で「sync 契約文面の曖昧さ」を改善候補として記録（ver16.2 以降で検討、PHASE8.0 §1 由来の継続論点）。

### 5-5. research workflow 自己適用時の観測バイアス

**リスク**: ver16.1 自身が `research` workflow で走るため、deferred 実装の不具合が `research` workflow の step（`/research_context` / `/experiment_test`）の健全性と切り分けづらい。

**確認方法**: deferred の最小試行は `experiments/deferred-execution/` で **本 run の外**に閉じる。本 run の `/research_context` / `/experiment_test` step 自体が deferred を発動することは禁じる（artifact 書き出しのみ）。

**fallback**: `MEMO.md` に「本 run で deferred が実際に発動したか」を明記し、retrospective で切り分ける。

---

## §6. 完了条件（§1 から再掲 + 検証手順）

| # | 完了条件 | 検証 |
|---|---|---|
| 1 | 登録 → 外部実行 → 結果保存 → request 削除 → session 再開の無人完走 | `test_claude_loop_integration.py` の新規 case が pass |
| 2 | 結果ファイル単体で「何が走ったか / 成功か / 出力サイズ」判定可能 | `test_deferred_commands.py::test_meta_json_schema` で assert |
| 3 | 90 秒見守りなしで heavy task を取り込める | `experiments/deferred-execution/{variant}/` の試行ログで実証（`EXPERIMENT.md` に記録） |
| 4 | 失敗時 orphan request ゼロ + resume 情報欠落なし | `test_deferred_commands.py::test_consume_on_failure` / `test_resume_prompt_contains_exit_code` |
| 5 | workflow 自己テスト方式の整理（常時組み込みはしない） | `experiments/deferred-execution/NOTES.md` に「有望 / 避けるべき」両リストを残し、standard YAML には組み込まない |

セルフチェックは `/wrap_up` 段で行う（本 IMPLEMENT.md をチェックリストとして開き、全 5 項目の根拠 path を記載）。

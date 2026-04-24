---
workflow: research
source: master_plan
---

# ver16.1 EXPERIMENT — PHASE8.0 §2 deferred execution 方式の実証

`/experiment_test` で RESEARCH.md「未解決点」§U1〜§U5 を検証した記録。本 run は `research` workflow の self-apply で、IMPLEMENT.md §5-5 に従い **nested `claude` CLI 起動を伴う仮説は `未検証` として deferred execution 機構実装後（ver16.2 以降）に繰越**している。参照日は全て **2026-04-24**。

---

## 検証した仮説

| # | 仮説 | 成功条件 | 結果 |
|---|---|---|---|
| §U1 | `~/.claude/projects/<slug>/<uuid>.jsonl` の retention 既定は 1 日以上あり、deferred→resume（分単位）には実害がない | 実機で現存する JSONL の最古 mtime が 1 日以上 | **PASS** (30.0 日) |
| §U2 | `claude -r <id> -p "<resume_prompt>" --bare` で resume できる | resume が成功し、応答品質に明確な劣化なし | **未検証**（§U2-note） |
| §U3 | 同一 session id への 2 回目 `-r` は、先行 `claude -r` プロセス終了後なら history を継承し分岐しない | 3 発話目で初回単語を再現 | **未検証**（§U2-note） |
| §U4 | C 案（head 20 + tail 20）が A/B より小さく、失敗判別に必要な signal を維持する | resume prompt 2KB 前後かつ `ERROR`/`exit status:1` 等が含まれる | **PASS**（C 案 2226 B、失敗 signal 維持） |
| §U5 | `.started` marker file 方式で SIGKILL 相当でも orphan を検知できる | 正常経路は marker 消去、kill 経路は marker 残存、scan が kill 分のみを拾う | **PASS** |

### §U2-note — §U2 / §U3 を `未検証` とした理由

本 step は `/experiment_test` 内で同期実行される Python プロセスであり、IMPLEMENT.md §5-5 により「本 run の `/research_context` / `/experiment_test` step 自体が deferred を発動することは禁じる」と明示されている。nested `claude -p` / `claude -r` 呼び出しは:

1. 親 workflow の session と衝突し得る（本 step 自身が `--session-id` 管理下で走っている）
2. `claude -p` 1 回 ≒ 数十秒〜、実測 3〜4 往復で同期 5 分制約の境界に達する
3. `research` workflow の観測バイアス（deferred 未完でも deferred のテストが走ってしまう）

`experiments/deferred-execution/resume-twice/README.md` に **ver16.2 以降で deferred 経路から実施する手順草稿**を残した。RESEARCH.md §A3 / §A6 / §E1 は「`-p --resume` 非対話継続」「`-p` 生成 session への `-r` 再開」「`--bare` による token 肥大回避」をいずれも一次資料（Anthropic 公式 docs / 公式 repo issue）で裏取り済のため、ver16.1 実装自体は **確定部分のみ**で進めて問題ない。

---

## 再現手順

前提: Python 3.10+（標準ライブラリのみ）、リポジトリ直下（`C:/CodeRoot/ANALOGY_MAKE`）。

### §U1 retention 実測

```bash
python experiments/deferred-execution/retention-check/check_retention.py
```

- 入力: `~/.claude/projects/*/*.jsonl`、`~/.claude/settings.json`
- 出力: `cleanupPeriodDays` 指定値（None=既定）、現存 jsonl の件数・最古/最新 mtime、判定

### §U4 excerpt サイズ比較

```bash
python experiments/deferred-execution/large-stdout/compare_excerpts.py
```

- 入力: なし（`fixture_stdout.log` をスクリプトが約 10MB で生成）
- 出力: A/B/C/sizes-only 4 ケースの resume prompt サイズと failure signal 保持有無

### §U5 orphan 検知

```bash
python experiments/deferred-execution/orphan-recovery/test_marker.py
```

- 入力: `tempfile.TemporaryDirectory()` で隔離（本番 queue に影響なし）
- 出力: 正常経路・kill 経路の exit code、残存 marker 一覧、判定

### §U2 / §U3（未検証）

`experiments/deferred-execution/resume-twice/README.md` の草稿手順を ver16.2 以降に実施。

---

## 結果

実行環境: Windows 11、Python 3.13（`C:\CodeRoot\ANALOGY_MAKE`）、claude CLI 2.1.117、実測 2026-04-24。

### §U1

```
$ python experiments/deferred-execution/retention-check/check_retention.py
settings.cleanupPeriodDays = None (None = default applied)
project_dirs count = 16
jsonl total    = 299
oldest jsonl   = 716c3402-693e-4979-b274-a86fc0aff279.jsonl (30.0 days ago)
newest jsonl   = 29a7278d-f6b8-443e-99b9-3258230dfbc9.jsonl (0.0 days ago)
verdict        = PASS (deferred→resume は分単位、1 日以上なら実害なし)
```

観察: 最古 JSONL がちょうど **30.0 日前** = RESEARCH.md §B1（Simon Willison「30 day default」）と整合。ユーザー側は `cleanupPeriodDays` 未設定で既定動作中。claude CLI `--help` には retention 関連フラグ無し（`--no-session-persistence` のみ存在 = 既定は永続化側）。

### §U2 / §U3

未検証。`experiments/deferred-execution/resume-twice/README.md` 参照。

### §U4

```
$ python experiments/deferred-execution/large-stdout/compare_excerpts.py
fixture size   = 10,700,083 bytes (10.20 MB)
fixture lines  = 216,202

sizes only                  prompt=   262B  failure_signal=False
A (head 50 + tail 50)       prompt=  5106B  excerpt=  4813B  failure_signal=True
B (head 200 + tail 200)     prompt= 19508B  excerpt= 19213B  failure_signal=True
C (head 20 + tail 20)       prompt=  2226B  excerpt=  1933B  failure_signal=True
```

観察:
- **sizes only**: prompt は 262B と最小だが、失敗 signal（`ERROR` / `exit status: 1`）が失われ「Claude 側が meta.json / stdout.log を明示的に Read しない限り判断不能」。
- **A 案**: 5KB、signal 維持。可。
- **B 案**: 19.5KB、cost が跳ねる（RESEARCH.md §5-3 のリスクに該当）。
- **C 案**: 2.2KB、signal 維持、prompt 肥大化なし。**採用候補**。

### §U5

```
$ python experiments/deferred-execution/orphan-recovery/test_marker.py
clean exit code = 0  (expected 0)
kill  exit code = 137  (expected 137 on posix / 137 on Windows via os._exit)
orphan markers  = ['req-B.started']
deferred_dir    = ['_helper.py', 'req-A.result', 'req-B.started']
verdict         = PASS
```

観察:
- 正常経路 (`try/finally` + `unlink(missing_ok=True)`): marker 消去。
- SIGKILL 相当 (`os._exit(137)`、finally 未実行): marker が残存。
- `scan_orphans()` (= `deferred_dir.glob("*.started")`) が kill 分の 1 件のみを拾えた。

---

## 判断

### §U1: **設計不変で確定**

deferred execution 機構は retention 既定 30 日を前提にして問題ない。`cleanupPeriodDays` を本版で明示設定する必要はない。ただし以下を IMPLEMENT.md / USAGE.md に残す:

- 「deferred → resume が 30 日超に跨るケースは本版のスコープ外。該当する場合は `cleanupPeriodDays` を明示する」という運用注記。ver16.2 以降の観測候補。

### §U2 / §U3: **未検証 — 本版では確定部分のみで進行**

RESEARCH.md §A1〜§A6（Anthropic 公式 docs / 公式 repo issue）で以下は一次資料確定:
- `-p "<prompt>" --resume <id>` が headless 継続の正典 pattern（§A3）
- `--fork-session` が既定オフ、つまり既定で同一 id 再利用し history 追記（§A2）
- `-p` 生成 session も `-r` で再開可能（§A6）

実機実測は ver16.2 以降の deferred 経路で実施する。本版 IMPLEMENT.md §2-1 / §3-3 `_execute_resume()` は `--bare` **なし**で着手し、token 肥大が観測された時点で ver16.2 以降で `--bare` に切り替える方針を採る（RESEARCH.md §Q4 結論と整合）。

### §U4: **C 案（head 20 + tail 20）確定**

IMPLEMENT.md §2-3 / §2-4 / §5-3 の「excerpt 行数」は **head 20 + tail 20** で確定。`build_resume_prompt()` 実装時は以下を採る:

- `head_excerpt` / `tail_excerpt` を meta.json に格納（各最大 20 行）
- resume prompt には meta.json の excerpt を埋め込み、詳細は `Read DEFERRED/results/<id>.stdout.log` を案内
- 10 MB 相当の stdout でも resume prompt 2.2 KB 前後に収まる

### §U5: **`.started` marker 方式を ver16.1 に組み込む**

IMPLEMENT.md §5-2 の fallback 案（「最小機構のみ」）を採用可。実装方針:

```python
# 疑似コード
marker = deferred_dir / f"{req.request_id}.started"
marker.write_text("running\n", encoding="utf-8")
try:
    result = _run_commands(req, ...)
finally:
    marker.unlink(missing_ok=True)

# 起動時
orphans = sorted(deferred_dir.glob("*.started"))
if orphans:
    # blocking error + ISSUE 自動起票 (ISSUES/util/high/ に need_human_action)
    ...
```

本版スコープ: marker の書き込み・削除・起動時検知まで。ISSUE 自動起票のテンプレートは `scripts/claude_loop_lib/deferred_commands.py` と `test_deferred_commands.py::test_orphan_detection` に含める。

---

## 次アクション

`/imple_plan` で IMPLEMENT.md に以下を反映:

1. §2-3 excerpt サイズを **head 20 + tail 20** で確定
2. §3-1 `deferred_commands.py` の公開関数に `scan_orphans(deferred_dir) -> list[Path]` を追加
3. §3-3 `_execute_resume()` は `--bare` **なし**で着手、理由を §5-5 に追記
4. §5-2 fallback を「本版で最小機構実装」に昇格、§U5 実験結果を参照
5. §0-1 の retention 論点は「§U1 で 30 日既定確認済、設計不変」として closed に書き換え

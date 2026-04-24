---
workflow: research
source: master_plan
---

# ver16.1 RESEARCH — PHASE8.0 §2 deferred execution 外部調査

`/research_context` で実施した外部調査の成果物。IMPLEMENT.md §0（未解決論点 5 件）と §5（リスク・不確実性）を入力とし、公式 docs / GitHub / Anthropic エンジニアリング blog / repo 内コードを突き合わせて「確定 / 部分的 / 未確定」の切り分けを行った。参照日は全て **2026-04-24**。

---

## 問い

IMPLEMENT.md §0・§5 から抽出した論点を、外部調査で解くべき問いに整理する。

1. **Q1 `-r` 挙動**: `claude -r <session-id>` は具体的に何をするか。`claude -p "<prompt>" -r <id>` を非対話で呼べるか。同一 session id に対し 2 回連続で `-r` を呼ぶと履歴は継承されるか、それとも分岐するか（IMPLEMENT §0-1 / §5-1）。
2. **Q2 `-r` と `--session-id` の関係**: 2 つのフラグは同じか別物か。どちらを新規 session 採番・どちらを既存 session 復帰に使うか（IMPLEMENT §0-1、repo の `build_command` との整合確認）。
3. **Q3 session 永続化**: Claude Code の session 履歴はどこに・いつ書かれるか。Python プロセスが終了しても次回 `claude -r` で復元できる保証はあるか（IMPLEMENT §0-1）。
4. **Q4 headless 起動の推奨形**: deferred 完了後に `claude_loop.py` 内部からさらに `claude` を subprocess として呼ぶ構造は公式推奨か。入れ子起動の既知の落とし穴はあるか（IMPLEMENT §3-3, §5-5）。
5. **Q5 Anthropic 長時間 task 指針**: 「context を一旦破棄し handoff artifact でつなぐ」設計は Anthropic 公式推奨パターンと整合するか（IMPLEMENT §0 の設計方針全体）。
6. **Q6 Python subprocess idiom**: 巨大 stdout を持つ一連コマンドを「前段失敗で後段スキップ・exit code 記録・meta.json + sidecar log に分離」する正典パターンは何か（IMPLEMENT §3-1 `execute_request`、§5-3）。
7. **Q7 request / result の file layout**: 既存 queue（`ISSUES/` / `QUESTIONS/` / `FEEDBACKS/`）の frontmatter + markdown 形式と統一すべきか、`.json` sidecar 併用がよいか（IMPLEMENT §0-2）。
8. **Q8 `experiments/` サブディレクトリ配置規約**: `experiments/deferred-execution/` 配下の切り方は既存 README 規約と整合する形が何か（IMPLEMENT §0-4）。
9. **Q9 本番 queue との隔離先**: deferred request / result を `DEFERRED/` / `data/deferred/` / `logs/deferred/` のどこに置くのが事故が少ないか（IMPLEMENT §0-5）。

---

## 収集した証拠

### A. Claude Code CLI 仕様（Q1–Q4 の一次資料）

| # | URL | 参照日 | 種別 | 要旨 |
|---|---|---|---|---|
| A1 | https://docs.claude.com/en/docs/claude-code/cli-reference | 2026-04-24 | PRIMARY | `--resume, -r` の定義: 「Resume a specific session by ID or name, or show an interactive picker」。`--session-id` の定義: 「Use a specific session ID for the conversation (must be a valid UUID)」。**両フラグは別物**として並列に定義されている。 |
| A2 | https://docs.claude.com/en/docs/claude-code/cli-reference | 2026-04-24 | PRIMARY | `--fork-session`: 「When resuming, create a new session ID instead of reusing the original (use with --resume or --continue)」。裏返すと、既定では **同一 id を再利用して履歴に追記**する。 |
| A3 | https://docs.claude.com/en/docs/claude-code/headless | 2026-04-24 | PRIMARY | 正典 pattern として掲載: `session_id=$(claude -p "Start a review" --output-format json \| jq -r '.session_id') ; claude -p "Continue that review" --resume "$session_id"`。**`-p "<prompt>" --resume <id>` の組み合わせが非対話継続の公式形**。 |
| A4 | https://docs.claude.com/en/docs/claude-code/headless | 2026-04-24 | PRIMARY | `--bare` 推奨: 「`--bare` is the recommended mode for scripted and SDK calls, and will become the default for `-p` in a future release」「Bare mode skips OAuth and keychain reads. Anthropic authentication must come from `ANTHROPIC_API_KEY` or an `apiKeyHelper`」。 |
| A5 | https://docs.claude.com/en/docs/claude-code/cli-reference | 2026-04-24 | PRIMARY | `--no-session-persistence`: 「Disable session persistence so sessions are not saved to disk and cannot be resumed (print mode only)」。このフラグの存在が **既定では disk 永続化されていること**の裏付け。 |
| A6 | https://github.com/anthropics/claude-code/issues/42311 | 2026-04-24 | PRIMARY | Anthropic リポ上の issue: 「The interactive `/resume` picker only lists interactive Claude Code sessions. Sessions created by `claude -p` or Agent SDK integrations do not appear in the picker. To continue those sessions, use the headless resume flow with `claude -p --continue` or `claude -p --resume <session-id>`」。**`-p` で作った session も `-r` で再開可能**。 |

### B. Session 永続化の実装レイヤ（Q3 の二次資料複数 + 一次示唆）

| # | URL | 参照日 | 種別 | 要旨 |
|---|---|---|---|---|
| B1 | https://simonwillison.net/2025/Oct/22/claude-code-logs/ | 2026-04-24 | SECONDARY | 「Claude Code stores full logs of your sessions as newline-delimited JSON in `~/.claude/projects/<encoded-directory>/<session-id>.jsonl`」。`cleanupPeriodDays: 99999` で 30 日自動削除を延期できると記述。 |
| B2 | https://milvus.io/blog/why-claude-code-feels-so-stable-a-developers-deep-dive-into-its-local-storage-design.md | 2026-04-24 | SECONDARY | 同じ path を記載。「special characters such as `/`, spaces, and `~` are replaced with `-`」と slug 化規則を具体化。 |
| B3 | https://codesignal.com/learn/courses/foundation-getting-started-with-claude-code/lessons/exploring-conversation-history | 2026-04-24 | SECONDARY | 「`~/.claude/projects/our-project/abc123.jsonl` and reads each line. […] This is why `/resume` seamlessly continues conversations even after days or weeks」。 |
| B4 | https://github.com/anthropics/claude-code/issues/22365 | 2026-04-24 | PRIMARY (issue on 公式 repo) | 「Over time, a session JSONL file in `~/.claude/projects/<encoded-path>/` grows to multiple gigabytes…」（path を公式 repo issue 本文でも言及）。 |

### C. Anthropic の長時間 task / context handoff 指針（Q5 の一次資料）

| # | URL | 参照日 | 種別 | 要旨 |
|---|---|---|---|---|
| C1 | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | 2026-04-24 | PRIMARY | 「The core challenge of long-running agents is that they must work in discrete sessions, and each new session begins with no memory of what came before. […] agents need a way to bridge the gap between coding sessions」。**initializer agent + per-session coding agent + artifact handoff** の 3 層を推奨。 |
| C2 | https://www.anthropic.com/engineering/harness-design-long-running-apps | 2026-04-24 | PRIMARY | 「Context resets—clearing the context window entirely and starting a fresh agent, combined with a structured handoff that carries the previous agent's state and the next steps—addresses both these issues [context rot and context anxiety]」。 |
| C3 | https://www.anthropic.com/engineering/managed-agents | 2026-04-24 | PRIMARY | 「A common thread across this work is that harnesses encode assumptions about what Claude can't do on its own」。deferred execution もこの思想に合致。 |
| C4 | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | 2026-04-24 | PRIMARY | compaction vs structured handoff のトレードオフを整理。長期タスクは **structured handoff 側**を推奨。 |

### D. Python subprocess idiom（Q6 の一次資料）

| # | URL | 参照日 | 種別 | 要旨 |
|---|---|---|---|---|
| D1 | https://docs.python.org/3/library/subprocess.html | 2026-04-24 | PRIMARY | `stdout=` / `stderr=` に file object を直接渡せる: 「*stdout*, *stderr*, and *stdin* may be `None`, `subprocess.PIPE`, `subprocess.DEVNULL`, an existing file descriptor (a positive integer), and an existing file object with a valid file descriptor」。 |
| D2 | 同上 | 2026-04-24 | PRIMARY | **PIPE buffer deadlock 警告**: 「This will deadlock when using `stdout=PIPE` or `stderr=PIPE` and the child process generates enough output to a pipe such that it blocks waiting for the OS pipe buffer to accept more data」。→ 巨大 stdout は PIPE 禁止、file object 必須。 |
| D3 | 同上 | 2026-04-24 | PRIMARY | `subprocess.run(..., check=True)` で非ゼロ時 `CalledProcessError` を raise、`CompletedProcess.returncode` で exit code を取得可能。`timeout=` で `TimeoutExpired` を raise。 |
| D4 | https://docs.python.org/3/library/json.html | 2026-04-24 | PRIMARY | `json.dump` / `json.load` が stdlib 同梱。meta.json は追加依存なしで実装可能。 |

### E. 入れ子 Claude Code 起動の落とし穴（Q4 の二次資料）

| # | URL | 参照日 | 種別 | 要旨 |
|---|---|---|---|---|
| E1 | https://dev.to/jungjaehoon/why-claude-code-subagents-waste-50k-tokens-per-turn-and-how-to-fix-it-41ma | 2026-04-24 | SECONDARY | 「When your wrapper spawns a `claude` CLI subprocess, each process starts fresh. That process inherits your entire global configuration: `~/CLAUDE.md`, `~/.claude/settings.json`. […] a single subprocess turn consumed ~50K tokens before doing any actual work」。**`--bare` でほぼ回避可能**（A4 で一次裏付け済）。 |
| E2 | https://venturebeat.com/orchestration/claude-codes-tasks-update-lets-agents-work-longer-and-coordinate-across/ | 2026-04-24 | SECONDARY | Claude Code v2.1.19 で「dangling processes where Claude Code would hang on terminal close」が修正済。subprocess lifecycle 設計で参考になる挙動情報。 |
| E3 | https://motlin.com/blog/claude-code-running-for-hours | 2026-04-24 | SECONDARY | file-based queue + subagent-loop で 2+ 時間の自律走行実績。本版の file-based deferred queue 方針の妥当性補強。 |

### F. repo 内コード / 既存 docs（Q2・Q7・Q8・Q9 の内部一次資料）

| # | path | 要旨 |
|---|---|---|
| F1 | `scripts/claude_loop_lib/commands.py:29-33` | `session_id is not None` で分岐。`resume=True` → `["-r", session_id]`、`resume=False` → `["--session-id", session_id]`。A1 の CLI spec とそのまま一致（**既に公式仕様どおりに実装済**）。 |
| F2 | `scripts/claude_loop.py:541-567` | `effective_continue` は `requested_continue and not continue_disabled and previous_session_id is not None` の合成条件。`previous_session_id is None` なら自動で `continue: true` を downgrade する。 |
| F3 | `scripts/claude_loop.py:617, 667` | `previous_session_id = session_id` は **in-process 変数**にしか書かない（disk には Claude CLI 側が `~/.claude/projects/…` に書く A5/B1–B4）。Python プロセスが終了したら `previous_session_id` は失われる。 |
| F4 | `scripts/claude_loop_lib/frontmatter.py:8-21` | `parse_frontmatter(text: str) -> tuple[dict \| None, str]`。malformed YAML は `yaml.YAMLError` を握りつぶして `(None, text)` を返す寛容仕様。 |
| F5 | `scripts/claude_loop_lib/feedbacks.py:28-46, 49-61` | `feedbacks_dir.glob("*.md")`（**非再帰**）。`done/` は構造的に除外。consume は **step 成功時のみ** `shutil.move` で `done/` へ。失敗時は据え置きで次回再処理 = 再試行機構。 |
| F6 | `scripts/claude_loop_lib/validation.py` | 起動時に全 YAML を一括検査 → `list[Violation]` → 1 つでも error なら `SystemExit(2)`。実行時 validation 用の API は未整備（deferred 用は新設が必要）。 |
| F7 | `ISSUES/README.md`, `QUESTIONS/README.md` | 両 queue とも `{category}/{priority}/*.md` + YAML frontmatter（`status` / `assigned` / `priority` / `reviewed_at`）+ 本文 markdown。**FEEDBACKS と合わせて「frontmatter+body」形式が既に確立された慣習**。 |
| F8 | `experiments/README.md` | 新規依存が必要なら `experiments/{slug}/` サブディレクトリで隔離。常設スクリプトは先頭に **目的 / 削除条件**コメント必須。throwaway スクリプトはコメント不要。 |
| F9 | `experiments/` root | 現状 5 file: `_shared.ts` / `01-basic-connection.ts` / `02-memory-management.ts` / `inspect-db.ts` / `README.md`。サブディレクトリは未作成（`experiments/deferred-execution/` が最初のサブディレクトリ採用例になる）。 |
| F10 | `CLAUDE.md` | `data/` は `.gitignore` 済で SQLite DB 置き場。`logs/workflow/` は workflow log。両者とも既に用途が固定済。 |

---

## 結論

各問いに対し「確定（3 ソース以上で裏取り） / 部分的（1–2 ソース or 一次 1 本のみ） / 未確定」で判定する。

### Q1 `-r` 挙動・`-p --resume` 非対話継続・二重起動時の履歴継承

**確定**。
- `-p "<prompt>" --resume <id>` は公式 headless docs の正典 pattern（A3）。
- 既定では同一 session id を再利用し履歴に**追記**、分岐させたい場合のみ `--fork-session` を明示（A2）。
- `-p` 起動 session も `-r` で再開可能（A6）。
- 重要：`-r` は「動作中のプロセスへの再アタッチ」ではなく「先行プロセス終了後に disk から JSONL を読み直して history を復元する」設計（A5 `--no-session-persistence` フラグの存在 + B1–B4 の JSONL append-as-you-go の 3 資料）。したがって **「前回 `-r` が完了してから次の `-r` を呼ぶ」限り、二重呼び出しは安全**。

### Q2 `-r` と `--session-id` の関係

**確定**。両者は別フラグ。`--session-id <uuid>` は新規 session を特定 UUID で採番、`--resume <id>` は既存 session の履歴を復元（A1）。repo 内 `build_command` は既にこの区別を `resume: bool` 引数で実装済（F1）。→ **追加の CLI 仕様調査は不要**。

### Q3 session 永続化 / プロセスをまたいだ復元保証

**部分的（PRIMARY 1 本 + SECONDARY 3 本）**。
- 確定部分：disk 永続化されていること自体（A5 の `--no-session-persistence` フラグの裏返し）、`~/.claude/projects/<slug>/<uuid>.jsonl` に保存されること（B1/B2/B3 + B4 が公式 repo issue で同 path を言及）は確定扱い。
- 未確定部分：**30 日自動削除のデフォルト値**は B1（Simon Willison）1 本のみで、公式 docs の裏付けなし。→ `EXPERIMENT.md` で `claude --help` 出力 or `~/.claude/settings.json` 既定値を実機確認する必要あり（未解決点 §U1）。
- ver16.1 の設計方針としては「**JSONL がすぐ消える前提は置かず、ただし 30 日デフォルトを想定した運用上限を意識する**」で十分。deferred 完了から resume までが分単位のため実害は無い。

### Q4 headless 起動の推奨形・入れ子起動の落とし穴

**確定**。
- scripted 起動は `claude --bare -p "<prompt>"` が Anthropic 推奨（A4、将来的に `-p` の既定になる予告あり）。
- 入れ子起動時の token 肥大（`~/CLAUDE.md` / `~/.claude/settings.json` の再注入）は **`--bare` でほぼ回避できる**（E1 の対処と A4 の bare mode 動作が整合、primary + secondary で裏取り可能）。
- ただし本 repo の `build_command`（F1）は現状 `--bare` を付けていない。deferred resume 経路で **`--bare` を採用するかは設計判断**（resume が CLAUDE.md 再注入を必要とするかで変わる。resume 時点で session JSONL に過去の CLAUDE.md 込み履歴が残っていれば `--bare` で問題なし）。→ 本版 IMPLEMENT §3-3 の `_execute_resume()` で `--bare` を試す価値あり。実験で確かめる（未解決点 §U2）。

### Q5 Anthropic 長時間 task 指針との整合性

**確定**。本版の設計（step 完了 → 一旦 workflow 終了 → 外部実行 → resume prompt で再開）は、Anthropic 公式の「context reset + structured handoff」パターンに完全一致（C1/C2/C3/C4 の 4 本）。

具体的な整合点:
- C1「agents need a way to bridge the gap between coding sessions」 → 本版の resume prompt が bridge に該当。
- C2「Context resets […] combined with a structured handoff that carries the previous agent's state and the next steps」 → 本版の `DEFERRED/results/<id>.meta.json` が structured handoff に該当。
- C3「harnesses encode assumptions about what Claude can't do on its own」 → deferred execution は「Claude が長時間待てない」という制約を harness 側で埋める典型。

設計レベルの追加確認は不要。

### Q6 Python subprocess idiom（巨大 stdout + 順次実行 + meta.json）

**確定**。stdlib のみで全要件を満たせる（D1–D4、すべて PRIMARY）。

採用すべき pattern:
```python
# 要点: stdout は PIPE を使わず file object に直接書き出す（deadlock 回避 D2）
with open(stdout_path, "wb") as out:
    proc = subprocess.run(
        cmd, stdout=out, stderr=subprocess.STDOUT,
        timeout=timeout_sec, check=False, cwd=cwd,
    )
# 順次実行で前段失敗時は break、exit_codes をリスト記録（D3）
# meta.json は json.dump で書き出し（D4）
```

- `check=False` を選ぶ（raise より明示的な exit code 記録が望ましい、IMPLEMENT §2-3 の `exit_codes` 配列と整合）。
- `stderr=subprocess.STDOUT` で merge するか別 file にするかは設計判断（IMPLEMENT §2-3 は別 file 案を採用済 → それで OK）。

### Q7 request / result の file layout（frontmatter+body vs json sidecar 併用）

**確定**。repo 内の既存慣習（F7）と Python 側読み取り基盤（F4）から、**request は frontmatter + body markdown / result は `.meta.json` + `.stdout.log` + `.stderr.log` sidecar**が最も自然。

根拠:
- Claude 側の書き出し: Claude は日常的に markdown + frontmatter を生成しているため、registered command も同形式にすれば学習コスト 0。
- Python 側の読み取り: `parse_frontmatter` が既に存在（F4）し、`feedbacks.py` の `load_feedbacks` が「非再帰 glob + `done/` 除外 + body 抽出」の正典パターンを提供済（F5）。この慣習を `deferred_commands.scan_pending` でコピーすれば事故が減る。
- result は構造化データ（exit_codes / timestamps / sizes）が主で人間可読性は副次的 → `meta.json` が妥当。巨大 stdout は sidecar log に分離（D2 と整合）。

結論として IMPLEMENT.md §2-2 / §2-3 の暫定案を**そのまま採用可**。

### Q8 `experiments/` サブディレクトリ配置

**確定**。`experiments/README.md`（F8）が「新依存が必要なら `{slug}/` サブディレクトリ」と規定しており、`experiments/deferred-execution/{variant}/` は規約に完全準拠。

採用する構造:
```
experiments/deferred-execution/
├── NOTES.md          # 方式比較の要約 / 有望・避けるべきリスト
├── fixture-basic/    # 最小 fixture 方式
├── resume-twice/     # 同一 session id の 2 回 resume 実測（§5-1 用）
├── large-stdout/     # head/tail excerpt 行数の実測（§5-3 用）
└── ...
```

各 `{variant}/` 直下のスクリプト先頭に「目的 / 削除条件」コメント必須。落選方式は削除条件コメント付きで残す（IMPLEMENT.md §3-9 と一致）。

### Q9 本番 queue との隔離先ディレクトリ

**部分的 → 推奨案を提示**。一次資料で選べる性質ではなく、repo 規約（F10）から判断。

候補評価:

| 候補 | 本番 queue と衝突 | diff 汚染 | 可視性 | 評価 |
|---|---|---|---|---|
| A. `DEFERRED/` (リポ直下) | なし | `.gitignore` 要追加 | 高 | ◯ |
| B. `data/deferred/` | なし（`data/` は DB 用途） | `.gitignore` 済（F10） | 中（`data/` は既に gitignore で普段見えない） | ◯◯ |
| C. `logs/deferred/` | なし | `.gitignore` 要確認 | 高 | △ |

**推奨: B (`data/deferred/`)**。理由:
- `data/` は既に `.gitignore` 済（F10）で追加設定不要。
- `data/` は SQLite DB 専用ではなく「ランタイム生成物置き場」として規定されているため、deferred queue を同居させても規約違反にならない（むしろ `data/` の用途拡張として自然）。
- `logs/workflow/` は workflow log 専用（`scripts/claude_loop.py` の `TeeWriter` 出力先）で、request/result の mix は可視性を落とす。
- リポ直下 `DEFERRED/` は視認性は高いが、`.gitignore` 編集が必要で、かつ root が肥大する。

`/imple_plan` 段で最終確定する際、`data/deferred/` を前提で `db-config.ts` と同じ「開発: `./data/deferred/` / 本番: `/home/data/deferred/`」の path 規約に揃えると運用が一貫する。

---

## 未解決点

`/experiment_test` (EXPERIMENT.md) で検証すべき仮説を列挙する。

### §U1. session JSONL の retention 仕様と deferred タイムラインの整合確認

- **仮説**: deferred 実行 → resume までは数秒〜数分で完了するため、30 日 retention デフォルトがあっても実害はない。
- **検証手順**: (a) `claude --help` の出力から retention 関連フラグ / 設定を列挙、(b) `~/.claude/settings.json` の既定値 or 空ファイル時の実動作を確認、(c) deferred 完了から resume までの典型遅延（想定 1 分以内）を記録。
- **判定基準**: retention 既定が 30 日以上なら design 不変、24h 未満なら mitigation 必要（`cleanupPeriodDays` 明示設定 or session 外部保存）。

### §U2. `--bare` を `_execute_resume` で採用すべきか

- **仮説**: `claude -r <id> -p "<resume_prompt>" --bare` で動作する。session JSONL に過去の CLAUDE.md 込み履歴が残っているため `--bare` でも context は復元できる。
- **検証手順**: `experiments/deferred-execution/resume-twice/` で `--bare` あり・なしの 2 パターンで同一 session resume を実施し、(a) 動作成否、(b) 応答内容の CLAUDE.md 参照有無、(c) 実行時間を比較。
- **判定基準**: `--bare` ありで正常に resume でき、応答品質に明確な劣化がなければ IMPLEMENT §3-3 `_execute_resume()` で `--bare` をデフォルト採用。劣化があれば既定 mode のまま運用し、`--bare` は将来課題として残す。

### §U3. 同一 session id への 2 回目 `-r` が「前回終了後」に安全なことの実測

- **仮説**: JSONL は append-as-you-go のため、先行 `claude -r` プロセスが完全終了してから後続 `claude -r` を呼ぶ限り、history は継承され分岐しない（A2 / A3 の docs 表現と一致）。
- **検証手順**: `experiments/deferred-execution/resume-twice/` で、(a) 初回 `claude -p "第 1 発話" --session-id <uuid>` を完走、(b) `claude -p "第 2 発話" -r <uuid>` を完走、(c) `claude -p "第 1 発話を覚えているか答えよ" -r <uuid>` の結果を記録。想定通り「覚えている」なら履歴継承が実測確定。
- **判定基準**: 履歴継承確定 → IMPLEMENT §2-1 のシーケンス図どおりに実装。継承されない（= 分岐する）場合、IMPLEMENT §5-1 fallback 案（新規 session id + 履歴貼付）に切替。

### §U4. 巨大 stdout の excerpt 行数（head_N + tail_N）の最適値

- **仮説**: C 案（head 20 + tail 20 + size のみ）が prompt token を最小化しつつ判断材料を提供できる。A 案（head 50 + tail 50）だと冗長、B 案（head 200 + tail 200）は resume prompt を数 KB に肥大化させる。
- **検証手順**: `experiments/deferred-execution/large-stdout/` で、10MB 相当の fixture stdout を生成し、A/B/C 3 案それぞれで `build_resume_prompt` を呼んで prompt 長を実測。Claude へ投げて判断品質（「成功したかどうか」「次 step へ進むべきか」）が識別可能かを確認。
- **判定基準**: C 案で判断品質が保てれば採用。保てない場合は A 案（head 50 + tail 50）を採用。B 案は cost 上の理由で棄却。

### §U5. orphan request の安全回収機構

- **仮説**: `DEFERRED/<id>.started` marker file を「execute 直前に書く / 正常終了時に削除」方式にすれば、次回 workflow 起動時に marker 残存をチェックすることで orphan を検知できる（IMPLEMENT §5-2）。
- **検証手順**: `experiments/deferred-execution/orphan-recovery/` で、(a) `execute_request` を途中 SIGKILL し marker と request が残ることを再現、(b) 次回起動時に marker 残存を検知して「blocking error + ISSUE 自動起票」経路を発動できるかを実装して確認。
- **判定基準**: 検知成功 → ver16.1 実装に含める。失敗する or 実装コスト過大 → ver16.2 以降に繰越（本版は try/finally での `consume_request` 保証のみに留める）。

---

## 参考: 本 RESEARCH で「調査不要」と判断した IMPLEMENT §0 項目

- **§0-2 file layout**: Q7 として結論「frontmatter + body markdown / meta.json sidecar」を確定済。実験不要で `/imple_plan` 段で確定可能。
- **§0-4 `experiments/` 配置**: Q8 として結論「`{variant}/` サブディレクトリ」を確定済。実験不要。
- **§0-5 隔離ディレクトリ**: Q9 として推奨「`data/deferred/`」を提示済。実験不要だが `/imple_plan` 段で最終合意が必要（reviewer 依存）。

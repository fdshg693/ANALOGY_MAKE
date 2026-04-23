# IMPLEMENT: util ver10.0 — workflow YAML step 単位 system prompt / model override

`ROUGH_PLAN.md` の主対象「PHASE7.0 §1: workflow YAML での step 単位 system prompt / model override」の実装方式を確定する。事前リファクタリングは不要（ROUGH_PLAN 末尾に明記）。

---

## 1. 設計確定事項

### 1-1. override 対象キー（限定列挙）

ver10.0 で受け入れる step / defaults override キーは以下の **4 種に限定**する。

| YAML キー | Claude CLI flag | 値の型 | 既存／新規 | 備考 |
|---|---|---|---|---|
| `model` | `--model` | non-empty string | 既存 | 変更なし |
| `effort` | `--effort` | non-empty string | 既存 | 変更なし。CLI が許容する値（`low`/`medium`/`high`/`xhigh`/`max`）の妥当性検証は §2 (ver10.1) に委譲 |
| `system_prompt` | `--system-prompt` | non-empty string | **新規** | デフォルト system prompt を完全置換 |
| `append_system_prompt` | `--append-system-prompt` | non-empty string | **新規** | デフォルト system prompt に追加 |

#### スコープ外（ver10.0 では受け付けない）

- **`temperature` / `max_tokens`**: Claude CLI に対応フラグが存在しない（`claude --help` 確認済み: `--temperature` / `--max-tokens` なし）。PHASE7.0 §1-1 文面では将来対象として例示されているが、CLI 経由で受け渡す手段が無いため、ver10.0 では **YAML に書かれてもエラーで落とす** 扱いとする（後方互換目的の silent ignore は採らない: ROUGH_PLAN 論点 6 と整合）
- **`fallback_model`**: CLI フラグは存在する（`--fallback-model`）が、本バージョンでは override 仕組み導入の最小集合にしぼり、追加要件があれば後続バージョンで拡張する
- 任意キーの透過 pass-through は行わない（PHASE7.0 §1-1 "任意キーの透過 pass-through は行わない" と整合）

### 1-2. 継承ルール（公式仕様）

3 段階の優先順位:

1. **step override**: `steps[i].<key>` にキーが存在し値が `None` でない場合、その値を使用
2. **defaults**: 上記が無く `defaults.<key>` にキーが存在し値が `None` でない場合、defaults の値を使用
3. **CLI 既定**: 上記いずれも無ければ該当 flag を CLI に渡さない（Claude CLI の標準挙動に委ねる）

`None` は「未指定」として扱う（既存 `model` / `effort` の挙動と同一）。空文字列は既存どおりエラー。
`append_system_prompt` の特例（既存 `--append-system-prompt` 構築処理との合成ルール）は §2-3 で詳述。

### 1-3. PHASE7.0 §1 完了条件への対応

| 完了条件 | ver10.0 充足状況 | ver10.0 での対応 |
|---|---|---|
| ① YAML だけで step 別 prompt / model 変更が表現できる | **充足** | `system_prompt` / `append_system_prompt` を新規 override キーとして追加（§2-2, §2-3） |
| ② 同一 workflow 内で複数 step が異なる model 設定を持っても継承順序が曖昧にならない | **充足** | §1-2 を `scripts/README.md` に「公式仕様」として明文化、3 段階優先を test で網羅（§3） |
| ③ 無効な model 名・未解決 prompt 参照・型不正な設定値が**実行前 validation で検出**される | **未充足**（ver10.1 で充足予定） | ver10.0 では YAML パース時の型検証（非空文字列）と未知キー拒否のみ実装。値の意味的検証（model 名が CLI で受け付けられるか等）は ver10.1 (§2 起動前 validation) で対応 |

**`/wrap_up` 引き継ぎ事項**: PHASE7.0.md 「実装進捗」表 §1 のステータスは「**部分完了**（条件①②充足、条件③は ver10.1 待ち）」として記録し、「実装済」とは記録しないこと。

### 1-4. MASTER_PLAN.md typo 修正

ROUGH_PLAN §「併せて整理する軽微な MASTER_PLAN 表記ズレ」に基づき以下を実施:

- `docs/util/MASTER_PLAN.md` 13 行目（`PHASE6.0.md` のサマリ）: ver9.0 で全節完了済のため「**実装済み**」に表記更新
- 14 行目（typo）: パスを `PHASE7.0.md` に修正、サマリを「**未実装**（骨子作成済、ver10.0 で §1 着手予定）」に変更
- 末尾改行を追加

ROUGH_PLAN 論点 7 に従い **PHASE7.0 §1 実装とは独立コミット** にする（§4 で `/imple_plan` 引き継ぎ指示として明記）。

---

## 2. 実装詳細

### 2-1. `scripts/claude_loop_lib/workflow.py` — override キーの正規化

#### 変更点 (a): `OVERRIDE_STRING_KEYS` 定数の導入

ファイル先頭に下記を追加し、`get_steps()` / `resolve_defaults()` で共有する:

```python
OVERRIDE_STRING_KEYS: tuple[str, ...] = (
    "model", "effort", "system_prompt", "append_system_prompt",
)
```

意図: 「YAML に書ける文字列型 override キー」の単一の真実源。テストもこの定数を import して整合性を担保する。

#### 変更点 (b): `get_steps()` の拡張

現状（lines 100-105）:

```python
for key in ("model", "effort"):
    if key in raw_step and raw_step[key] is not None:
        value = raw_step[key]
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"steps[{index}].{key} must be a non-empty string.")
        step_entry[key] = value
```

変更後: ループ対象を `OVERRIDE_STRING_KEYS` に置換するのみ（型検証ロジックは流用）。

```python
for key in OVERRIDE_STRING_KEYS:
    if key in raw_step and raw_step[key] is not None:
        value = raw_step[key]
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"steps[{index}].{key} must be a non-empty string.")
        step_entry[key] = value
```

#### 変更点 (c): `resolve_defaults()` の拡張

現状（lines 128-134）の `for key in ("model", "effort"):` も同様に `OVERRIDE_STRING_KEYS` ループへ置換する。返却型のシグネチャ `dict[str, str]` は維持。

#### 変更点 (d): 未知キーの拒否（任意キー pass-through 防止）

`get_steps()` 内の各 `raw_step` に対し、許容キー集合外の予期しないキーがある場合はエラーで落とす。

許容キー集合（既知）:
```
{"name", "prompt", "args", "continue"} | set(OVERRIDE_STRING_KEYS)
```

実装:

```python
ALLOWED_STEP_KEYS = frozenset({"name", "prompt", "args", "continue"} | set(OVERRIDE_STRING_KEYS))
# get_steps 内、prompt / name 検証後に:
unknown_keys = set(raw_step.keys()) - ALLOWED_STEP_KEYS
if unknown_keys:
    raise SystemExit(
        f"Step {index} has unknown keys: {sorted(unknown_keys)}. "
        f"Allowed keys: {sorted(ALLOWED_STEP_KEYS)}"
    )
```

`resolve_defaults()` 側も同様に `ALLOWED_DEFAULTS_KEYS = frozenset(OVERRIDE_STRING_KEYS)` を導入し、未知キー検出時に SystemExit。

これにより `temperature` / `max_tokens` などの想定外キーは確実に実行前で落ちる（PHASE7.0 §1-1 と整合）。

### 2-2. `scripts/claude_loop_lib/commands.py` — `--system-prompt` / `--append-system-prompt` 反映

#### 変更点 (a): `--system-prompt` フラグの追加

現状（lines 22-25）:

```python
for key, flag in (("model", "--model"), ("effort", "--effort")):
    value = step.get(key, defaults.get(key))
    if value is not None:
        cmd.extend([flag, value])
```

変更後: 単純フラグ置換キーに `system_prompt` を追加。

```python
for key, flag in (
    ("model", "--model"),
    ("effort", "--effort"),
    ("system_prompt", "--system-prompt"),
):
    value = step.get(key, defaults.get(key))
    if value is not None:
        cmd.extend([flag, value])
```

`--append-system-prompt` は既存 `system_prompts` リスト合成処理に統合する必要があるため、上記ループには含めない（次項参照）。

#### 変更点 (b): `--append-system-prompt` の合成処理拡張

現状（lines 31-43）の `system_prompts: list[str]` 構築処理に「step / defaults の `append_system_prompt`」を **末尾に追記** する。

```python
system_prompts: list[str] = []
if log_file_path:
    system_prompts.append(f"Current workflow log: {log_file_path}")
if auto_mode:
    system_prompts.append(
        "Workflow execution mode: AUTO (unattended). "
        "Do not use AskUserQuestion. Write requests to REQUESTS/AI/ instead."
    )
if feedbacks:
    feedback_section = "## User Feedback\n\n" + "\n\n---\n\n".join(feedbacks)
    system_prompts.append(feedback_section)
# --- 新規追加 ---
append_value = step.get("append_system_prompt", defaults.get("append_system_prompt"))
if append_value is not None:
    system_prompts.append(append_value)
# --- 既存 ---
if system_prompts:
    cmd.extend(["--append-system-prompt", "\n\n".join(system_prompts)])
```

合成順序の確定:
1. `log_file_path` 行
2. AUTO mode 注意文
3. User Feedback セクション
4. step / defaults の `append_system_prompt`

順序の根拠: 既存 3 種は `build_command()` の文脈情報（環境メタ・モード・人間入力）であり、step 固有 prompt 上書きは「最も後ろ」に置くことで、最後尾の指示が優先されやすい（LLM の指示優先順傾向）一貫性を持たせる。

#### 変更点 (c): YAML 内 `command.auto_args` の `--append-system-prompt` との重複問題

現状: 3 本の workflow YAML の `command.auto_args` には `--append-system-prompt "..."` がリテラルで含まれる。`build_command()` も別途 `--append-system-prompt` を追加するため、CLI には**同フラグが 2 回渡る**状態となっている（既存挙動）。

ver10.0 では:
- **本問題は ver10.0 のスコープ外として温存する**（既存挙動を変えない）。`auto_args` の整理は PHASE7.0 §3「legacy `--auto` 撤去」で扱われる予定（ver10.1 以降）
- 新規 `append_system_prompt` 追加は build_command 経由のため、既存の重複構造には新たな悪化を招かない（同フラグの 2 回渡しは Claude CLI が両方とも append として扱う既存動作のまま）
- IMPLEMENT.md / README には「YAML 側 `command.auto_args` の append-system-prompt と step 別 `append_system_prompt` は両立可能。両者は CLI に対する独立 `--append-system-prompt` 引数として別々に渡る」旨を明記

### 2-3. `scripts/claude_loop.py` — descriptor 行への影響

`_run_steps()` 内の descriptor 構築（lines 485-496）は `model` / `effort` のみ表示しており、`system_prompt` / `append_system_prompt` を表示する必要は無い（ログ肥大化を避けるため）。

ただし、PHASE7.0 §1-1 の「解決された有効設定が validation 時点で一意に決まる状態」への第一歩として、step descriptor に「`SystemPrompt: set` / `AppendSystemPrompt: set`」のような **存在ビット** を追加表示する。値そのものは表示しない。

実装方針:

```python
effective_system_prompt = step.get("system_prompt", effective_defaults.get("system_prompt"))
effective_append_sp = step.get("append_system_prompt", effective_defaults.get("append_system_prompt"))
if effective_system_prompt is not None:
    descriptor_parts.append("SystemPrompt: set")
if effective_append_sp is not None:
    descriptor_parts.append("AppendSystemPrompt: set")
```

注: descriptor の既存テスト（`test_claude_loop.py` の `TestRunStepsSessionTracking` 系）は本拡張の影響を受けない（既存ステップに新キーが無い限り descriptor 文字列に新パートは混入しない）。

### 2-4. workflow YAML 3 本（`claude_loop.yaml` / `_quick.yaml` / `_issue_plan.yaml`）の更新

#### 仕様面の追加

3 本ともファイル先頭の sync コメントを **新キー対応版に拡張**:

現状:
```
#       The `command` / `mode` / `defaults` sections must stay in sync with
#       claude_loop_quick.yaml and claude_loop_issue_plan.yaml.
```

変更後:
```
#       The `command` / `mode` / `defaults` sections must stay in sync with
#       claude_loop_quick.yaml and claude_loop_issue_plan.yaml.
#       Allowed `defaults`/`steps[]` override keys (string-typed):
#         model, effort, system_prompt, append_system_prompt
```

#### 実値の追加

ver10.0 では新キー（`system_prompt` / `append_system_prompt`）を **実用適用しない**（仕組みのみ導入）。理由:
- ROUGH_PLAN「スコープ外」「override を既存 SKILL に適用する本格運用」と整合
- どの step に何の system prompt を当てるかは PHASE7.0 §8 (`/retrospective` による prompt 評価、ver10.2 予定) で決定する設計

ただし、テスト fixture / 動作確認のためにも README に「サンプル」として **コメント例** を YAML 内に置くか、README 側のみで示すかは選択肢。本 IMPLEMENT では **README 側のみで示す方針**（YAML 本体に未使用 commented-out 例を残すのは保守負担）。

### 2-5. `scripts/README.md` — 公式仕様の記述更新

「YAML ワークフロー仕様」節（lines 128-176）を以下のように改訂する。

#### (a) override キー一覧表の追加（「セクションの意味」直後）

```markdown
### override 可能なキー（defaults / steps[] 共通）

string 型のみ。`None` は未指定扱い、空文字列はエラー。

| キー | CLI flag | 役割 |
|---|---|---|
| `model` | `--model` | 使用モデル（`opus` / `sonnet` 等） |
| `effort` | `--effort` | 推論努力レベル（`low` / `medium` / `high` / `xhigh` / `max`） |
| `system_prompt` | `--system-prompt` | デフォルト system prompt を完全置換 |
| `append_system_prompt` | `--append-system-prompt` | デフォルト system prompt に追加 |

未知キー（例: `temperature`, `max_tokens`）は YAML パース時にエラーで落とす（silent ignore はしない）。
```

#### (b) 継承ルールの明文化

```markdown
### 継承ルール

各 step の有効設定は次の 3 段階で解決される:

1. `steps[i].<key>` にキーが存在し値が non-`None` → step 値を採用
2. 上記が無く `defaults.<key>` にキーが存在し値が non-`None` → defaults 値を採用
3. 上記いずれも無ければ Claude CLI の既定挙動に従う（該当フラグを渡さない）
```

#### (c) `append_system_prompt` の合成順序の明記

```markdown
### `append_system_prompt` の合成順序

`build_command()` は `--append-system-prompt` 引数の本文を以下の順で連結する（区切りは空行 1 つ）:

1. `Current workflow log: {path}` 行（ログ有効時）
2. AUTO mode 注意文（auto モード時）
3. `## User Feedback` セクション（feedback 注入時）
4. step / defaults の `append_system_prompt` 値（指定時）

なお、YAML 側 `command.auto_args` の `--append-system-prompt` と、`build_command()` が組み立てる `--append-system-prompt` は CLI に **独立した 2 つの引数として渡る**（Claude CLI 側で両方とも append される既存挙動）。
```

#### (d) 拡張ガイド更新

「拡張ガイド」節 line 289 を新キー対応版に更新:

```markdown
- **新しい SKILL を追加する場合**: `claude_loop.yaml` または `claude_loop_quick.yaml` の `steps:` に
  `{ name, prompt, model?, effort?, system_prompt?, append_system_prompt?, args?, continue? }` を追記する
```

### 2-6. `docs/util/MASTER_PLAN.md` の typo 修正

ROUGH_PLAN §「併せて整理する軽微な MASTER_PLAN 表記ズレ」のとおり 13/14 行目 + 末尾改行修正。**§1 実装とは独立コミット**で行う（次節 §4 参照）。

---

## 3. テスト計画

### 3-1. 既存テストの維持

- `TestResolveDefaults` (5 cases) / `TestGetStepsModelEffort` (6 cases) / `TestBuildCommandWithModelEffort` (6 cases) / `TestYamlIntegration` 等は **既存ケース全件 pass を必須**とする
- 既存テストは `model` / `effort` のみ対象だが、内部実装変更（`OVERRIDE_STRING_KEYS` 定数化）後も挙動は同一
- 既存 YAML（3 本）が新仕様の許容キー集合に収まっていることをスモーク的に確認

### 3-2. 新規テストケース

`tests/test_claude_loop.py` に以下を追加。クラス分割案:

#### `TestResolveDefaultsOverrideKeys`（新キー）

| ケース | 内容 |
|---|---|
| `test_parses_system_prompt` | `defaults.system_prompt` が `dict["system_prompt"]` に格納される |
| `test_parses_append_system_prompt` | 同上 |
| `test_parses_all_four_keys_together` | 4 キー同時指定が全て格納される |
| `test_raises_on_unknown_key` | 未知キー（例: `temperature`）で SystemExit |
| `test_raises_on_empty_system_prompt` | `system_prompt: ""` で SystemExit |
| `test_raises_on_non_string_append` | `append_system_prompt: 5` で SystemExit |

#### `TestGetStepsOverrideKeys`（新キー）

| ケース | 内容 |
|---|---|
| `test_step_with_system_prompt` | step 単独指定が格納される |
| `test_step_with_append_system_prompt` | 同上 |
| `test_step_with_all_four_overrides` | 4 キー同時指定が格納される |
| `test_step_unknown_key_raises` | 未知キーで SystemExit、メッセージに `Allowed keys` を含む |
| `test_step_omits_keys_returns_no_keys` | 新キー無しの step に `system_prompt` キーが入らない |
| `test_step_none_value_treated_as_absent` | `system_prompt: null` / `append_system_prompt: null` がキー欠如と同等 |
| `test_step_empty_string_raises_for_each_key` | 4 キーそれぞれの空文字列で SystemExit（パラメタライズ） |

#### `TestBuildCommandWithSystemPrompt`（新フラグ）

| ケース | 内容 |
|---|---|
| `test_step_system_prompt_emits_flag` | `step.system_prompt` から `--system-prompt <val>` が生成される |
| `test_defaults_system_prompt_used_when_step_omits` | defaults からの継承 |
| `test_step_overrides_defaults_system_prompt` | step 値が defaults を上書き |
| `test_no_system_prompt_when_unset` | 双方未指定で `--system-prompt` flag が出ない |

#### `TestBuildCommandWithAppendSystemPrompt`（新フラグの合成）

| ケース | 内容 |
|---|---|
| `test_step_append_only` | step.append_system_prompt のみ指定で `--append-system-prompt` 末尾に値が入る |
| `test_appends_after_log_path` | `log_file_path` + step.append → 連結文字列内で log 行が前、append 値が後 |
| `test_appends_after_auto_mode` | auto_mode + step.append → AUTO 注意文が前、append 値が後 |
| `test_appends_after_feedbacks` | feedbacks + step.append → User Feedback セクションが前、append 値が後 |
| `test_full_combination_order` | log + auto + feedbacks + step.append の 4 種同時指定で順序が固定 |
| `test_defaults_append_used_when_step_omits` | defaults からの継承 |
| `test_step_overrides_defaults_append` | defaults=`"A"` / step=`"B"` のとき `--append-system-prompt` 連結結果に `"A"` が**含まれず** `"B"` のみが末尾に入ること（`step.get("append_system_prompt", defaults.get(...))` の Python dict-fallback 挙動による単純置換であり、defaults 値との合成は行わない）を assert する |

#### `TestOverrideInheritanceMatrix`（3 段階継承の網羅）

`OVERRIDE_STRING_KEYS` の各キーごとに以下マトリクスを `subTest` で検証:

| step 値 | defaults 値 | 期待 |
|---|---|---|
| 値あり | 値あり | step 値 |
| 値あり | 無し | step 値 |
| 無し | 値あり | defaults 値 |
| 無し | 無し | flag 渡さない |
| `None` | 値あり | defaults 値（None は未指定扱い） |

#### `TestYamlSyncOverrideKeys`（YAML 3 本同期確認）

3 本の YAML を `load_workflow` + `get_steps` でロードし、新仕様の許容キー集合内に収まっていることを確認（既存運用の破壊防止）。

### 3-3. テスト実行コマンド

```bash
pnpm exec vitest --run        # 既存テスト（フロントエンド）
python -m unittest tests.test_claude_loop -v   # 本変更の主対象
```

新規追加見込み: 約 25 ケース。既存 103 ケースと合算して 130 ケース弱（README line 300 の「現状 103 件」を更新する）。

---

## 4. コミット分割案（`/imple_plan` 引き継ぎ用）

ROUGH_PLAN 論点 7 に従い、独立コミット 2 本に分ける:

1. **`feat(util ver10.0): step 単位 system prompt / model override`**
   - `scripts/claude_loop_lib/workflow.py`
   - `scripts/claude_loop_lib/commands.py`
   - `scripts/claude_loop.py`（descriptor 拡張）
   - `scripts/claude_loop.yaml` / `_quick.yaml` / `_issue_plan.yaml`（コメント拡張のみ）
   - `scripts/README.md`
   - `tests/test_claude_loop.py`

2. **`docs(util ver10.0): MASTER_PLAN.md PHASE6.0/7.0 表記ズレ修正`**
   - `docs/util/MASTER_PLAN.md`

PHASE7.0.md の「実装進捗」表 (§1 → 「実装済」) の更新は `/wrap_up` の責務として持ち越し（ROUGH_PLAN 論点 8 と整合）。

---

## 5. リスク・不確実性

### 5-1. CLI フラグ仕様の前提

- 本実装は `claude --help` で確認した CLI flag 仕様（`--system-prompt` / `--append-system-prompt` / `--model` / `--effort` の存在）に依拠する
- Claude CLI のバージョンが想定と異なる環境（例: 古い CLI）では `--system-prompt` 等が unknown option として落ちる可能性がある
- **対策**: ver10.0 では新キーを既存 YAML 3 本に **実値として書かない** ため、本リスクは「ユーザが新キーを能動的に書いた場合のみ顕在化」する。README で「Claude CLI が当該フラグをサポートする必要あり」と注意書きする

### 5-2. `--append-system-prompt` の二重引数化（既存挙動）

- 現状 `command.auto_args` 内 `--append-system-prompt "..."` と `build_command()` 組立の `--append-system-prompt` が CLI に重複して渡る
- Claude CLI が複数 `--append-system-prompt` をどう扱うか（後勝ち / 連結 / どちらか無視）は CLI 仕様に明示が無い
- **本バージョンでは挙動を変更しない**（PHASE7.0 §3 で auto_args 整理時に解消する設計）。本実装の新キー追加は `build_command()` 経由のため、既存重複に**追加の重複は生じない**
- **対策**: README の §2-5(c) に「2 引数渡し」の明示と、PHASE7.0 §3 で扱う旨を 1 行で言及

### 5-3. 未知キー拒否の破壊的変更性

- §2-1(d) の「未知キー rejection」は、既存 YAML が想定外のキー（例: コメント代わりの `note:` 等）を含んでいた場合に新仕様で落ちる可能性
- **確認結果**: 現状 3 本の YAML は許容キー集合内に完全に収まっている（`name` / `prompt` / `model` / `effort` / `continue` / `args` のみ）。新規 reject による既存環境破壊は **無い**
- **対策**: それでも、エラーメッセージに `Allowed keys: [...]` を必ず含めて移行先の見当をつけやすくする

### 5-4. `system_prompt` (非 append) 利用時の影響

- `--system-prompt` はデフォルト system prompt を完全置換するため、Claude Code の本来挙動（CLAUDE.md の自動読込み等）が失われる可能性が高い
- ver10.0 では実値投入をしないため未顕在化。利用前に動作確認が必須
- **対策**: README に「`system_prompt` は強い置換であり、CLAUDE.md 自動読込等の Claude Code 既定挙動を失う可能性あり。通常は `append_system_prompt` を使うこと」と注意書き

### 5-5. テスト追加によるテスト数増加

- README line 300 の「現状 103 件」を更新する必要あり（実装後の最終件数で更新）
- 本実装スコープ内、`/wrap_up` 段階で確定値に書き換える

### 5-6. `claude_loop.py` descriptor 行のフォーマット変更

- §2-3 で descriptor に `SystemPrompt: set` / `AppendSystemPrompt: set` を追加する変更は、ログを正規表現で grep している外部ツールがあれば破壊する
- **確認結果**: リポジトリ内 `descriptor_line` / descriptor フォーマット文字列（`Model:` / `Effort:` / `Continue:` / `Session:`）の grep は `scripts/claude_loop.py`（生成元）と `scripts/README.md`（仕様記述）の 2 ファイルのみにヒット。外部 parser は存在せず、descriptor 拡張に依存するテストも無し（grep 確認済）
- **対策**: README §「ログフォーマット」の `descriptor 行（Model / Effort / Continue / Session）の表示ルール:` に新パートを追記

---

## 6. 実装順序（推奨）

1. `scripts/claude_loop_lib/workflow.py`: `OVERRIDE_STRING_KEYS` / `ALLOWED_STEP_KEYS` / `ALLOWED_DEFAULTS_KEYS` の導入と `get_steps` / `resolve_defaults` 拡張
2. `tests/test_claude_loop.py`: 上記に対応する `TestResolveDefaultsOverrideKeys` / `TestGetStepsOverrideKeys` を先に追加し pass 確認（TDD）
3. `scripts/claude_loop_lib/commands.py`: `--system-prompt` 単純フラグ追加 + `--append-system-prompt` 合成拡張
4. `tests/test_claude_loop.py`: `TestBuildCommandWithSystemPrompt` / `TestBuildCommandWithAppendSystemPrompt` / `TestOverrideInheritanceMatrix` 追加
5. `scripts/claude_loop.py`: descriptor 行拡張
6. `scripts/claude_loop.yaml` / `_quick.yaml` / `_issue_plan.yaml`: 先頭 sync コメント拡張のみ（実値投入なし）
7. `tests/test_claude_loop.py`: `TestYamlSyncOverrideKeys` 追加
8. `scripts/README.md`: §2-5(a)〜(d) を反映
9. 全テスト pass 確認 → コミット 1
10. `docs/util/MASTER_PLAN.md`: typo 修正 → 独立コミット 2

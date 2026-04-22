# ver4.0 IMPLEMENT

## 前提と全体方針

- ROUGH_PLAN.md で定義したスコープ（ステップごとの `--model` / `--effort` 指定、セッション継続は対象外）に従う
- 変更対象:
  1. `scripts/claude_loop.py` — YAML パーサとコマンド構築ロジックを拡張
  2. `scripts/claude_loop.yaml` — `defaults:` セクション追加 + 各 step に必要な上書きを付与
  3. `scripts/claude_loop_quick.yaml` — 同上
  4. `tests/test_claude_loop.py` — `defaults` / step 上書き / 未指定時の挙動を検証するテスト追加
  5. `.claude/SKILLS/meta_judge/WORKFLOW.md` — 「ステップごとのモデル/effort 指定が可能」の一文を追記
- 既存の挙動を壊さないこと（後方互換）が最重要。既存 YAML は `defaults` / `model` / `effort` を一切持たないため、これらが全て未指定の場合は `--model` / `--effort` 引数が CLI に渡されないことが正しい挙動

## 1. `scripts/claude_loop.py` の変更

### 1-1. `resolve_defaults(config)` を新規追加

`resolve_command_config` の近く（定義順序的には同セクション）に配置する:

```python
def resolve_defaults(config: dict[str, Any]) -> dict[str, str]:
    """Extract defaults.model / defaults.effort from config.

    Returns dict with only the keys that were explicitly set. Absent keys are
    left out (rather than stored as None) so that dict.get() / 'in' checks can
    be used uniformly with step-level overrides.
    """
    defaults_config = config.get("defaults") or {}
    if not isinstance(defaults_config, dict):
        raise SystemExit("'defaults' must be a mapping when provided.")

    result: dict[str, str] = {}
    for key in ("model", "effort"):
        value = defaults_config.get(key)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"'defaults.{key}' must be a non-empty string.")
        result[key] = value
    return result
```

- `defaults` セクション自体が YAML に無い場合 `{}` を返す（全ステップが CLI デフォルトで動く）
- `defaults.model` / `defaults.effort` のうち **設定されたキーだけ** を dict に入れる。`None` / 空文字列はエラー（`model: null` のような「defaults 無効化」は ROUGH_PLAN の非対象方針通りサポートしない）
- `defaults` が dict でない場合は SystemExit

### 1-2. `get_steps()` の拡張

既存の `get_steps` 内のステップ組み立て部分で、`model` / `effort` のキー取り出しを追加する:

```python
step_entry: dict[str, Any] = {
    "name": name,
    "prompt": prompt,
    "args": normalize_cli_args(raw_step.get("args"), f"steps[{index}].args"),
}
for key in ("model", "effort"):
    if key in raw_step and raw_step[key] is not None:
        value = raw_step[key]
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"steps[{index}].{key} must be a non-empty string.")
        step_entry[key] = value
steps.append(step_entry)
```

- `model` / `effort` キー自体がない、または `None` の場合はステップ dict に入れない → 後続で `defaults` が採用される
- 非文字列や空文字列はバリデーションエラー

### 1-3. `build_command()` の拡張

既存シグネチャに `defaults: dict[str, str] | None = None` を追加する。シグネチャ変更は後方互換のためデフォルト値 `None` を付与:

```python
def build_command(
    executable: str,
    prompt_flag: str,
    common_args: list[str],
    step: dict[str, Any],
    log_file_path: str | None = None,
    auto_mode: bool = False,
    feedbacks: list[str] | None = None,
    defaults: dict[str, str] | None = None,
) -> list[str]:
    cmd = [executable, prompt_flag, step["prompt"], *common_args, *step["args"]]
    defaults = defaults or {}
    for key, flag in (("model", "--model"), ("effort", "--effort")):
        value = step.get(key, defaults.get(key))
        if value is not None:
            cmd.extend([flag, value])
    # ... 既存の system_prompts 組み立てに続く
```

- `step.get(key, defaults.get(key))` の 2 番目の引数により「step dict に該当キーが存在しない場合に限り defaults を参照する」という **キー存在ベース** の上書き判定が成立する
- 付与判定は `if value is not None:`（`if value:` のような falsy 判定ではなく明示的な None チェック）。これにより「コメントと実装の意図が食い違わない」「将来読者の混乱を防ぐ」
- 1-2 のバリデーションで step 側 / defaults 側ともに空文字列はエラーになっているため、`None` チェックで十分に安全
- 追加位置: 既存の `system_prompts` 組み立ての **前**（位置は意味的には問わないが、後述のログで `$ claude -p ...` に `--model`/`--effort` が含まれている方が追跡しやすい）

### 1-4. `main()` の改修

`resolve_command_config` の次で `resolve_defaults` を呼び出して dict を取得し、以降のルートに引き渡す:

```python
executable, prompt_flag, common_args, auto_args = resolve_command_config(config)
defaults = resolve_defaults(config)
```

以降の `_run_steps` 呼び出し 2 箇所（log 有効/無効）に `defaults` を追加して渡す。`_run_steps` のシグネチャにも `defaults: dict[str, str]` を追加。

### 1-5. `_run_steps()` の改修

ループ内で `build_command` を呼ぶ箇所に `defaults=defaults` を追加。

ステップヘッダのログ出力に「Model / Effort」の表示を追加する。ヘッダは現在以下の形:

```
[1/5] split_plan
Started: 2026-04-22 10:00:00
$ {command_str}
```

ここに `Started` の直後、`$` の前に 1 行追加する:

```
Model: opus, Effort: high
```

- いずれも未指定の場合は **行ごと出力しない**（冗長を避ける）
- 片方だけ指定の場合はその側だけ表示: `Model: opus`
- tee 無し（`print_step_header`）側も同様の行を出力するよう `_out` 経由で対応

実装イメージ:

```python
effective_model = step.get("model", defaults.get("model"))
effective_effort = step.get("effort", defaults.get("effort"))
descriptor_parts: list[str] = []
if effective_model is not None:
    descriptor_parts.append(f"Model: {effective_model}")
if effective_effort is not None:
    descriptor_parts.append(f"Effort: {effective_effort}")
if descriptor_parts:
    _out(", ".join(descriptor_parts))
```

tee の有無にかかわらず `_out(...)` で統一する（`_out` は tee が `None` のとき `print` にフォールバックする既存設計 L527-531）。ログ有り分岐と無し分岐で別々に `print` を書き分けないこと。挿入位置はどちらのルートでも「ステップヘッダ / Started 行」の直後・「`$ {command_str}`」の直前。

### 1-6. 既存テストへの影響

`build_command` のシグネチャに `defaults` 引数を追加するため、既存テストはキーワード引数（`defaults=` を省略）で呼び出している限り壊れない。既存テストの呼び出しは位置引数で `log_file_path` / `auto_mode` / `feedbacks` を渡しているため、引数順序が変わらないよう `defaults` は **末尾** に追加すること。

## 2. YAML ファイルの更新

### 2-1. 方針

- `defaults` セクションを新設して全ステップの共通設定を置く
- 各ステップの「定常とは違う重さ」を上書きで表現する（差分が見えやすくなる）
- デフォルト値は「多くのステップにとって無難な中間」を選ぶ。`sonnet` + `medium` を採用

### 2-2. `scripts/claude_loop.yaml`（フルワークフロー）

追加・変更箇所:

```yaml
defaults:
  model: sonnet
  effort: medium

steps:
  - name: split_plan
    prompt: /split_plan
    model: opus        # 計画策定は重いため opus
    effort: high

  - name: imple_plan
    prompt: /imple_plan
    model: opus        # 実装計画も重い
    effort: high

  - name: wrap_up
    prompt: /wrap_up
    # defaults (sonnet, medium)

  - name: write_current
    prompt: /write_current
    effort: low        # ドキュメント整形中心のため effort を下げる

  - name: retrospective
    prompt: /retrospective
    # defaults (sonnet, medium)
```

- 既存の `mode:` / `command:` セクションは変更しない

### 2-3. `scripts/claude_loop_quick.yaml`

```yaml
defaults:
  model: sonnet
  effort: medium

steps:
  - name: quick_plan
    prompt: /quick_plan
    # defaults (sonnet, medium)

  - name: quick_impl
    prompt: /quick_impl
    effort: high       # 実装本体のため effort を上げる

  - name: quick_doc
    prompt: /quick_doc
    effort: low        # ドキュメント生成中心
```

## 3. `tests/test_claude_loop.py` へのテスト追加

末尾に新規テストクラスを 4 つ追加する。既存の `resolve_command_config` や `build_command` のテストと同じスタイル（`unittest.TestCase`・assert）で記述。

### 3-1. `TestResolveDefaults`

対象: `resolve_defaults()`

| メソッド名 | 内容 |
|---|---|
| `test_returns_empty_when_key_absent` | config に `defaults` キー無し → `{}` |
| `test_parses_model_and_effort` | `{"defaults": {"model": "opus", "effort": "high"}}` → `{"model": "opus", "effort": "high"}` |
| `test_omits_absent_keys` | `{"defaults": {"model": "opus"}}` → `{"model": "opus"}` のみ（`effort` キー無し） |
| `test_raises_on_non_mapping` | `{"defaults": "opus"}` → `SystemExit` |
| `test_raises_on_empty_string` | `{"defaults": {"model": ""}}` → `SystemExit` |

`resolve_defaults` を `claude_loop` import に追加する必要がある（`from claude_loop import ..., resolve_defaults`）。

### 3-2. `TestBuildCommandWithModelEffort`

対象: `build_command(..., defaults=...)`

| メソッド名 | 内容 |
|---|---|
| `test_no_model_no_effort_when_unset` | `defaults={}` かつ step に model/effort 無 → `--model`/`--effort` が cmd に含まれない |
| `test_uses_defaults_when_step_omits` | `defaults={"model": "sonnet", "effort": "medium"}`、step 側は無 → cmd に `--model sonnet --effort medium` が含まれる |
| `test_step_overrides_defaults` | `defaults={"model": "sonnet"}`、step に `model="opus"` → cmd に `--model opus`（sonnet ではない） |
| `test_step_sets_when_no_defaults` | `defaults={}`、step に `effort="high"` → cmd に `--effort high`、`--model` は無し |
| `test_model_effort_order` | 構築された cmd リスト内で `--model` と `--effort` のインデックスがいずれも `--append-system-prompt` のインデックスより小さい（`--append-system-prompt` より前に配置されている）ことを確認する。ステップヘッダログにも設定値が見えやすくするための配置を守るテスト |

### 3-3. `TestGetStepsModelEffort`

対象: `get_steps()` の model/effort 受け取り

| メソッド名 | 内容 |
|---|---|
| `test_step_without_model_effort_omits_keys` | 既存 YAML 相当の step → 返り値 dict に `model`/`effort` キーが無い |
| `test_step_with_model_and_effort` | YAML で `model: opus, effort: high` を指定 → dict に両方含まれる |
| `test_step_with_only_effort` | `effort: low` のみ → dict に `effort` のみ、`model` 無し |
| `test_raises_on_empty_model` | `model: ""` → `SystemExit` |
| `test_raises_on_non_string_effort` | `effort: 5` → `SystemExit` |

`get_steps` は既存で import 済み (`resolve_command_config` と同様）だが、現在の import 文には含まれていないので追加が必要。

### 3-4. `TestResolveMainIntegration`（軽量統合テスト、任意）

`main` 全体を動かすテストは既存にないため無理に追加しない。代わりに「ロード → `get_steps` + `resolve_defaults` → `build_command` に食わせる」という連携だけを 1 メソッドで検証する統合テストを 1 本だけ追加する（`TestYamlIntegration` として新規クラス）:

| メソッド名 | 内容 |
|---|---|
| `test_full_yaml_flow` | 一時 YAML を作成し、`load_workflow` → `get_steps` + `resolve_defaults` → `build_command` を通して、defaults 継承とステップ上書きが期待通り反映されたコマンドになることを確認 |

## 4. `.claude/SKILLS/meta_judge/WORKFLOW.md` への追記

「保守上の注意」節の前（または末尾）に以下を追記する:

```markdown
### モデル・エフォートの指定

`claude_loop.yaml` / `claude_loop_quick.yaml` には各ステップのモデル（`model`）と推論エフォート（`effort`）を指定できる。トップレベルの `defaults:` で全ステップ共通値を定義し、各ステップで必要に応じて上書きする。省略時は CLI デフォルトが使用される（従来挙動）。
```

分量は 2〜3 行に抑える。実装解説は YAML 本体のコメントと README（ver4.1 以降）に任せる。

## 5. 動作確認手順

1. `python scripts/claude_loop.py --dry-run` を実行し、各ステップのコマンドが `--model` / `--effort` 付きで表示されることを確認
2. `python scripts/claude_loop.py -w scripts/claude_loop_quick.yaml --dry-run` でも同様に確認
3. `defaults` と step 上書きを一時的に外した YAML で `--dry-run` を行い、`--model` / `--effort` が含まれないことを確認（後方互換の実地確認）
4. `pytest tests/test_claude_loop.py -q` を実行して全テストがグリーンになることを確認
5. Claude CLI が実際に `--model sonnet` や `--effort medium` を受理するかは実装時に 1 ステップだけ手で `--dry-run` 相当を外して検証する（ただしフルワークフロー全体を実走させる必要はない）

## 6. コミット計画

- 今回 `split_plan` ステップの成果物として、このディレクトリ配下 3 ファイル（`ROUGH_PLAN.md` / `IMPLEMENT.md` / （REFACTOR 不要のため作成せず））を 1 コミットで投入する
- コミットメッセージ: `docs(ver4.0): split_plan完了`

## 7. リスク・不確実性

### 7-1. `--effort` フラグが CLI で受理されるか

`--effort` は Claude CLI のバージョンによっては未実装の可能性がある（`claude --help` で要確認）。受理されない場合の挙動:

- **受理されるが無視される**: 問題なし
- **エラーで終了する**: 全ステップが起動できなくなる致命的障害

対応案:
- 実装完了時点で `claude --help | grep -- --effort` を確認する手順を `main()` ではなく「5. 動作確認手順」に含める
- 受理されない場合は、`effort` 指定機能のみを暫定無効化（`build_command` から `--effort` 付与部分をコメントアウト）し、`model` のみでリリースする。YAML からは `effort` を落とさず温存して、後から CLI が対応したら再有効化する
- この条件分岐はコード側で動的チェックしない（実装が肥大化するため）

### 7-2. 推奨値（`opus` / `high` 等）の適切性

PHASE4.0.md に提示された推奨値をベースに、ver4.0 では次の簡略版を採用する（詳細は 2-2 / 2-3 参照）:

| 見直しポイント | 本実装の判断 |
|---|---|
| PHASE4.0 原案は `split_plan: opus/high`・`imple_plan: opus/high` | **採用**（両ステップとも計画立案で負荷が高い） |
| 原案は `retrospective: sonnet/medium` | **採用**（defaults と一致） |
| 原案は `write_current: sonnet/low` | **部分採用**: `effort: low` のみ設定。`model` は defaults（sonnet）に寄せる |
| 原案は `quick_plan: sonnet/medium`・`quick_impl: sonnet/high`・`quick_doc: sonnet/low` | **採用**（defaults 継承 + 必要な上書きのみ） |

運用後 1〜2 回の実走で不満が出た場合はマイナーバージョン（ver4.1 等）で調整する。

### 7-3. 後方互換性

- 全 SKILL 呼び出しにおいて、既存 YAML（defaults 無・step level 無）でも `--model` / `--effort` がコマンドに含まれないことをテスト（3-2 / 3-3）で明示的に検証する
- `build_command` の引数順序は `defaults` を **末尾** に追加することで既存テストを壊さない

## 8. 実装順序

1. `scripts/claude_loop.py` の `resolve_defaults` / `get_steps` 拡張 / `build_command` 拡張を先に完成させる
2. `tests/test_claude_loop.py` にテストを追加し、`pytest` がグリーンになることを確認
3. YAML 2 ファイルに `defaults` と step 上書きを追加
4. `--dry-run` で実地確認
5. `.claude/SKILLS/meta_judge/WORKFLOW.md` を追記
6. `CURRENT.md` 等は `write_current` ステップで後述

この順で進めると、コード・テストが先に固まるため、YAML を触る時点ですでにバリデーションが効いた状態になる。

---
workflow: full
source: master_plan
---

# ver16.0 IMPLEMENT — `research` workflow の新設

## 0. 前提 / 命名 / 責務境界の確定

### Artifact 命名（確定）

handoff §5「artifact 命名」で仮称だった名前を以下で確定する。全て UPPER_SNAKE_CASE、接尾辞なし、既存 `ROUGH_PLAN.md` / `IMPLEMENT.md` / `MEMO.md` と揃える。

- **`RESEARCH.md`** — `/research_context` の成果物。`docs/{cat}/ver{X.Y}/RESEARCH.md` に配置
- **`EXPERIMENT.md`** — `/experiment_test` の成果物。`docs/{cat}/ver{X.Y}/EXPERIMENT.md` に配置

### `question` / `research` の責務境界（確定）

handoff §5 で「docs / SKILL / README で明示する必要あり」とされた 3 観点に対する確定方針:

| 観点 | `question` (`QUESTIONS/`) | `research` (`docs/{cat}/ver{X.Y}/RESEARCH.md`) |
|---|---|---|
| (a) 最終成果物 | 報告書のみ（`docs/{cat}/questions/{slug}.md`） | **コード変更**（`RESEARCH.md` は中間成果物） |
| (b) 入力キュー | `QUESTIONS/{cat}/{priority}/` | `ISSUES/{cat}/{priority}/` または MASTER_PLAN |
| (c) workflow | 調査→報告書で終了（実装に進まない） | 調査→実験→実装→retrospective まで 8 step 完走 |

このテーブルを `.claude/skills/research_context/SKILL.md` 冒頭と `scripts/README.md` / `scripts/USAGE.md` にも転記する。

### 8 step 固定の方針（確定）

handoff §2 の「省略可能な variant を設けるべきか」に対する判断:

- **2 step 固定で進める**。`/research_context` 単独 / `/experiment_test` 単独の workflow variant は作らない
- 理由: ① 利用実績がなく省略条件を定義できない、② YAML ファイル増加は運用負担（sync 対象拡大、validation 対象拡大）、③ 使わない step は成果物空白で済み致命的ではない
- 再評価タイミング: ver16.1 以降で `research` 利用実績が 3 件以上蓄積してから

### auto 選定条件の粒度（確定）

handoff §3 で「いずれか 1 つ」vs「複数条件同時」の論点に対する確定方針:

- **「いずれか 1 つを満たす」**ルール。PHASE8.0 §1-1 の 4 条件（外部仕様確認 / 実装方式実験絞込 / 長時間検証 / 隔離環境試行）のうち 1 つ以上を含めば `research`
- リスク「full で十分な課題まで research に流れる」への緩和: 条件のうち「長時間検証」は「1 step で 5 分以上を要する実測系」のように具体化し、曖昧判定を防ぐ
- 判断に迷う場合は **`full` 優先**（既存の「迷ったら full」原則を継承）

### `RESEARCH.md` / `EXPERIMENT.md` の最低要求節（確定）

handoff §5 で「SKILL に強制するか空テンプレか」に対する確定方針:

- **SKILL 側で最低節を強制する**（空テンプレではなく節見出しを埋めることを要求）
- `RESEARCH.md`: `## 問い` / `## 収集した証拠` / `## 結論` / `## 未解決点` の 4 節
- `EXPERIMENT.md`: `## 検証した仮説` / `## 再現手順` / `## 結果` / `## 判断` の 4 節
- 理由: 後続 `/imple_plan` が `RESEARCH.md` / `EXPERIMENT.md` を入力として読む際、節が揃っていないと抜粋ロジックを SKILL ごとに書き分ける必要が出る

### テスト方針（確定）

handoff §5 の「mock か実 CLI か」:

- **既存方式（実 claude CLI 呼び出し）踏襲**。`test_claude_loop_integration.py` は既存 quick/full integration と同一方針で research 経路も走らせる
- 8 step 完走テストは **mock あり版を別途追加しない**（既存方針維持）
- 新規追加は `test_claude_loop_cli.py` 側の unit-level テストに集中（`--workflow research` 引数パース / frontmatter 解釈 / auto phase2 での research 分岐）

## 1. リスク・不確実性

### 1.1 新規ライブラリ / 未使用 API

- **該当なし**。本版は標準ライブラリ + PyYAML + 既存 SKILL 構文の範疇に収まる

### 1.2 型定義の不備 / ドキュメント不足の可能性

- **`_read_workflow_kind` の戻り値型変更**: `Literal["full", "quick"]` → `Literal["full", "quick", "research"]` 相当への拡張。既存の type hint は `str` 表現のため実害なし。呼び出し元（`_run_auto` 内の `phase2_kind == "quick"` 比較）の完全性をレビューで確認する必要あり
- **`--workflow auto` の dry-run 時の新ログ出力**: `_run_auto` の `f"--- auto: phase2 = {phase2_kind} ({phase2_yaml.name}) ---"` は `phase2_kind` が "research" でも文字列として成立する。追加の format 修正は不要

### 1.3 実行時挙動の不確実性

- **8 step での `continue: true` 境界**: 現行 `full` では `wrap_up` のみ `continue: true`。research でも同一方針とし、`/research_context` / `/experiment_test` は `continue: false`（session 分離）とする。根拠: 新 SKILL は外部 API 叩く tool 呼び出しが主で session 継続に依存しない
- **`RESEARCH.md` / `EXPERIMENT.md` 不在時の `/imple_plan` 挙動**: research 以外の workflow（full / quick）では `RESEARCH.md` / `EXPERIMENT.md` は存在しないが、`/imple_plan` 側で「存在すれば読む / なければ無視」の条件分岐になるよう SKILL 本文を書く（エラーにしない）
- **`experiments/` 配下の既存スクリプト**: 既に 4 本の `.ts` ファイルが存在。本版でこれらに破壊的変更は加えない（`experiments/README.md` の新設のみ）

## 2. 新規作成ファイル

### 2.1 `scripts/claude_loop_research.yaml`（新規）

以下を作成する。`claude_loop.yaml` の 6 step 構成に `/research_context` / `/experiment_test` を `/split_plan` と `/imple_plan` の間に挿入した形。

```yaml
# NOTE: --workflow research で起動する 8 step workflow（実装前に調査・実験を正式 step として挟む）。
#       --workflow auto で選択される条件: ROUGH_PLAN.md frontmatter が workflow: research の場合。
#       The `command` / `defaults` sections must stay in sync with claude_loop.yaml,
#       claude_loop_quick.yaml, claude_loop_issue_plan.yaml, claude_loop_scout.yaml,
#       and claude_loop_question.yaml.
#       Allowed `defaults`/`steps[]` override keys (string-typed):
#         model, effort, system_prompt, append_system_prompt

command:
  executable: claude
  prompt_flag: -p
  args:
    - --dangerously-skip-permissions
    - --disallowedTools "AskUserQuestion"

defaults:
  model: sonnet
  effort: medium

steps:
  - name: issue_plan
    prompt: /issue_plan
    model: opus
    effort: high

  - name: split_plan
    prompt: /split_plan
    model: opus
    effort: high

  - name: research_context
    prompt: /research_context
    model: opus
    effort: high

  - name: experiment_test
    prompt: /experiment_test
    model: opus
    effort: high

  - name: imple_plan
    prompt: /imple_plan
    model: opus
    effort: high

  - name: wrap_up
    prompt: /wrap_up
    continue: true

  - name: write_current
    prompt: /write_current

  - name: retrospective
    prompt: /retrospective
    model: opus
```

**sync 契約**: 既存 5 YAML の NOTE コメントも全て `claude_loop_research.yaml` を含む 6 ファイル列挙に更新する（抜け防止のため全 YAML 同時編集をコミットに含める）。

### 2.2 `.claude/skills/research_context/SKILL.md`（新規）

テンプレートとして `question_research/SKILL.md` の見出し構造を模倣。以下の節構成で作成:

```markdown
---
name: research_context
description: research workflow の実装前調査 step。RESEARCH.md を生成（--workflow research でのみ起動）
disable-model-invocation: true
user-invocable: true
---

## コンテキスト

- カテゴリ: !`cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app`
- 最新バージョン番号: !`bash .claude/scripts/get_latest_version.sh`
- 今日の日付: !`date +%Y-%m-%d`

## 役割

`research` workflow の 3 step 目。`/split_plan` が作成した `REFACTOR.md` / `IMPLEMENT.md` と `PLAN_HANDOFF.md` を読み、**実装に進む前に必要な外部調査**（公式 docs 確認 / 仕様の裏取り / 類似事例調査）を行い、成果を `docs/{cat}/ver{X.Y}/RESEARCH.md` に残す。

### `question_research` との責務境界

（§0 で確定した 3 観点テーブルを転記）

### やらないこと

- コード変更 / テスト追加 / 実装
- `experiments/` 配下でのスクリプト実行（それは `/experiment_test` の責務）
- 新規 ISSUE 起票（必要なら `IMPLEMENT.md` に追記するにとどめる）

## 手順（3 段階）

### 1. 入力読み込み
- `ROUGH_PLAN.md` / `PLAN_HANDOFF.md` / `REFACTOR.md`（あれば）/ `IMPLEMENT.md` / `IMPLEMENT.md` 中の「## リスク・不確実性」節

### 2. 外部調査（`use-tavily` SKILL 前提）
- 公式 docs / GitHub README / API リファレンスに当たる
- 複数ソース（3 箇所以上）で裏取りした事実のみ「確定」、それ以外は「未確定」として残す
- 証拠は **URL + 参照日** の形で記録

### 3. `RESEARCH.md` 出力

出力先: `docs/{cat}/ver{X.Y}/RESEARCH.md`

以下 4 節を必ず含める（節見出しは固定）:
- `## 問い` — `IMPLEMENT.md` の論点から抽出、箇条書き
- `## 収集した証拠` — URL + 参照日 + 要約の 3 点セット
- `## 結論` — 各問いに対する「確定 / 部分的 / 未確定」
- `## 未解決点` — 実験（`/experiment_test`）で確かめる必要がある項目

## Git コミット

- `git add docs/{cat}/ver{X.Y}/RESEARCH.md`
- コミットメッセージ: `docs(ver{X.Y}): research_context 完了`
- **プッシュはしない**（後続 step でまとめて push）
```

### 2.3 `.claude/skills/experiment_test/SKILL.md`（新規）

`research_context` と対をなす 4 step 目。

```markdown
---
name: experiment_test
description: research workflow の実装前検証 step。experiments/ 配下で再現・性能・CLI 試行を行い EXPERIMENT.md を生成
disable-model-invocation: true
user-invocable: true
---

## コンテキスト
（research_context と同構造）

## 役割

`research` workflow の 4 step 目。`RESEARCH.md` の未解決点（特に「実装方式を実験で絞り込む」「長時間検証」「隔離環境での試行」）を実際に `experiments/` 配下でスクリプトを書いて検証し、結果を `docs/{cat}/ver{X.Y}/EXPERIMENT.md` に残す。

### `experiments/` ディレクトリ運用ルール（本版新設）

- 既存依存で足りるなら既存 `package.json` / `.venv` をそのまま使う
- 新しい依存が必要な場合は `experiments/{slug}/` 配下に閉じる（プロジェクトルートの依存を増やさない）
- 残すスクリプトは先頭コメントに以下 2 点を必ず書く:
  - `// 何を確かめるためか: ...`
  - `// いつ削除してよいか: ...`

### やらないこと

- production コード（`app/` / `server/` / `scripts/`）への変更
- 長時間コマンドの本 step 内での同期実行は許容するが、**deferred execution（§2 ver16.1）の代替手段としての使い方はしない**（本 step 完了を待って次に進む前提）

## 手順

### 1. 仮説整理
- `RESEARCH.md` の「未解決点」から検証仮説を 1〜N 個抽出
- 各仮説に「再現手順」と「成功条件」を割り当てる

### 2. 実験スクリプト作成・実行
- `experiments/` 配下に追加（既存ファイルを壊さない）
- 実行ログは `EXPERIMENT.md` に貼る（コマンドと出力の前後 10 行程度）

### 3. `EXPERIMENT.md` 出力

出力先: `docs/{cat}/ver{X.Y}/EXPERIMENT.md`

必須 4 節:
- `## 検証した仮説` — 箇条書き
- `## 再現手順` — コマンド / 前提条件
- `## 結果` — 出力 / 性能値
- `## 判断` — 実装方式の確定 / 却下 / 未確定

## 長時間コマンドの扱い（ver16.1 以降の拡張ポイント）

本 step 内では **同期実行に限定**。5 分を超える長時間コマンドを本 step で扱う必要が出た場合、ver16.1 の deferred execution 機構に委譲することを前提とし、本版では該当仮説は `未検証` として `EXPERIMENT.md` の「判断」に明記する。

## Git コミット
- `git add docs/{cat}/ver{X.Y}/EXPERIMENT.md experiments/`
- コミットメッセージ: `docs(ver{X.Y}): experiment_test 完了`
- **プッシュはしない**
```

### 2.4 `experiments/README.md`（新規）

現状、experiments/ には `_shared.ts` / `01-basic-connection.ts` / `02-memory-management.ts` / `inspect-db.ts` の 4 本が存在する。既存ファイルには触らず、ルールのみ明記する。

```markdown
# experiments/

**目的**: 実装前の仮説検証・隔離試行・長時間コマンドの検討。`scripts/` がプロダクション自動化に対して、ここは一時的・使い捨ての実験置き場。

## 規約

1. **既存依存で足りる場合**: プロジェクトルートの `package.json` / `pnpm-lock.yaml` / `.venv` をそのまま使う
2. **新しい依存が必要な場合**: `experiments/{slug}/` のサブディレクトリを切り、そこに閉じる（ルートの依存を増やさない）
3. **残すスクリプト**: 先頭コメントに以下 2 点を必須:
   - 何を確かめるためか（目的）
   - いつ削除してよいか（削除条件: 「実装統合されたら削除」「ver16.2 以降不要」等）
4. **使い捨てスクリプト**: 本人が本ループ内で消すのであれば規約 3 は免除

## 既存ファイル

（一覧記載。各ファイルの目的をコメントから抜粋）

## `scripts/` との棲み分け

- `scripts/` = CI / 自動化の一部として他 SKILL が呼ぶ production コード
- `experiments/` = 試行錯誤・検証・再現スクリプト。他 SKILL が参照しない
```

## 3. 変更ファイル

### 3.1 `scripts/claude_loop.py`

#### 3.1.1 `_read_workflow_kind` の許容値拡張（`scripts/claude_loop.py:207-228`）

```python
# 変更前
if value not in ("quick", "full"):

# 変更後
if value not in ("quick", "full", "research"):
```

戻り値の doc も `"full" / "quick" / "research"` 3 値に更新。

#### 3.1.2 `_run_auto` の phase2 YAML 選択（`scripts/claude_loop.py:360-364`）

現状:

```python
phase2_yaml = yaml_dir / (
    QUICK_YAML_FILENAME if phase2_kind == "quick" else FULL_YAML_FILENAME
)
```

変更後（REFACTOR の `WORKFLOW_YAML_FILES` を利用）:

```python
from claude_loop_lib.workflow import WORKFLOW_YAML_FILES

# phase2_kind は _read_workflow_kind により "quick" / "full" / "research" のいずれか
phase2_yaml = yaml_dir / WORKFLOW_YAML_FILES[phase2_kind]
```

`WORKFLOW_YAML_FILES` は REFACTOR で追加された dict（`research` キーも含む）。これにより将来 workflow 値が増えても `_run_auto` の分岐追加は不要。

#### 3.1.3 `--workflow` の help 文言更新（`scripts/claude_loop.py:93`）

```python
# 変更前
help="Workflow selector: 'auto' (default) | 'full' | 'quick' | path to a YAML file",

# 変更後
help=(
    "Workflow selector: 'auto' (default) | 'full' | 'quick' | 'research' | "
    "'scout' | 'question' | path to a YAML file"
),
```

（`scout` / `question` も現状から漏れていたため併せて追記）

### 3.2 `scripts/claude_loop_lib/workflow.py`

REFACTOR.md の Step 1 で導入した `WORKFLOW_YAML_FILES` dict に `research` キーを追加する:

```python
RESEARCH_YAML_FILENAME = "claude_loop_research.yaml"

WORKFLOW_YAML_FILES: dict[str, str] = {
    "full": FULL_YAML_FILENAME,
    "quick": QUICK_YAML_FILENAME,
    "research": RESEARCH_YAML_FILENAME,  # NEW
    "scout": SCOUT_YAML_FILENAME,
    "question": QUESTION_YAML_FILENAME,
}
```

REFACTOR Step 2 の `AUTO_TARGET_YAMLS` にも追加:

```python
AUTO_TARGET_YAMLS: tuple[str, ...] = (
    ISSUE_PLAN_YAML_FILENAME,
    FULL_YAML_FILENAME,
    QUICK_YAML_FILENAME,
    RESEARCH_YAML_FILENAME,  # NEW（auto phase2 の候補 YAML）
)
```

### 3.3 `scripts/claude_loop_lib/validation.py`

- `_resolve_target_yamls` は REFACTOR で既に `AUTO_TARGET_YAMLS` 駆動に置き換わっているため追加変更不要
- `RESEARCH_YAML_FILENAME` を import に追加（起動時検証の対象として明示される副作用あり）

### 3.4 `.claude/skills/issue_plan/SKILL.md`

**`workflow: auto` 選択ロジックの拡張**（現状: `quick | full` 2 値）:

```markdown
## ワークフロー選択（`workflow: quick | full | research`）

選定 ISSUE・タスクの性質に応じて以下ルールで決定する:

- 選定 ISSUE に `status: review` が 1 件でも含まれる場合 → **必ず `full`**
- MASTER_PLAN 新項目 / アーキテクチャ変更 / 新規ライブラリ導入を含み、かつ **以下 4 条件のいずれか 1 つを満たす** 場合 → **`research`**
  - 外部仕様・公式 docs の確認が主要成果に影響する
  - 実装方式を実験で絞り込む必要がある
  - 1 step で 5 分以上を要する実測系の長時間検証が事前に必要
  - 軽い隔離環境（`experiments/` 配下）での試行が前提
- MASTER_PLAN 新項目 / アーキテクチャ変更 / 新規ライブラリ導入を含むが、上記 4 条件のいずれも該当しない場合 → **`full`**
- 全 `ready` で、変更対象が 3 ファイル以下かつ 100 行以下の見込みなら → `quick`
- 判断に迷う場合 → 安全側で **`full`**
```

**`ROUGH_PLAN.md` frontmatter 許容値の更新**:

```markdown
---
workflow: full | quick | research
source: issues | master_plan
---
```

### 3.5 `.claude/skills/split_plan/SKILL.md`

`/research_context` / `/experiment_test` への handoff 節を追加:

- 「## research workflow 時の追加注意」という節を末尾に追加
- 内容: (a) `IMPLEMENT.md` の「## リスク・不確実性」節は `/research_context` が直接参照する ため具体化を徹底する、(b) 実験方式が分岐する場合は `EXPERIMENT.md` が判断する前提で `IMPLEMENT.md` に「実験判断待ち」マーカーを残してよい

### 3.6 `.claude/skills/imple_plan/SKILL.md`

`RESEARCH.md` / `EXPERIMENT.md` を入力として読む手順を追加:

- 「## 入力読み込み」節に以下を追記:
  - `docs/{cat}/ver{X.Y}/RESEARCH.md` が存在すれば読み込み、「確定」事実は IMPLEMENT.md 実行計画に反映
  - `docs/{cat}/ver{X.Y}/EXPERIMENT.md` が存在すれば読み込み、「判断」節の確定事項を実装方式選定に反映
  - 両ファイルとも **存在しなくてもエラーにしない**（full / quick workflow では存在しない）

### 3.7 `.claude/SKILLS/meta_judge/WORKFLOW.md`

3 系統（quick / full / research）として再定義。新規 §3 を追加:

```markdown
## §3 調査・実験ワークフロー（research）

8 step: `/issue_plan → /split_plan → /research_context → /experiment_test → /imple_plan → /wrap_up → /write_current → /retrospective`

### 選択条件

（§3.4 と同一の 4 条件を転記）

### 成果物

- `RESEARCH.md` — 外部調査結果（`/research_context` が生成）
- `EXPERIMENT.md` — 実験結果（`/experiment_test` が生成）
- `IMPLEMENT.md` — `RESEARCH.md` / `EXPERIMENT.md` を入力に確定された実装計画

### `question` workflow との違い

（§0 で確定した 3 観点テーブルを転記）
```

### 3.8 `.claude/rules/scripts.md`

§3 行 24 の YAML sync 契約を 5 → 6 ファイルに更新:

```markdown
- `claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_research.yaml` / `claude_loop_issue_plan.yaml` / `claude_loop_scout.yaml` / `claude_loop_question.yaml` の `command` / `defaults` セクションは 6 ファイル間で同一内容を保つ
```

### 3.9 `scripts/README.md` / `scripts/USAGE.md`

- workflow table に `research` 行を追加
- `--workflow research` の CLI 例を追加
- `experiments/` 運用ルールへの参照（`experiments/README.md` リンク）
- `question` と `research` の責務境界テーブル（§0 のものを転記）

## 4. テスト追加

### 4.1 `scripts/tests/test_claude_loop_cli.py`

以下のテストを追加:

```python
class TestResolveWorkflowValue(unittest.TestCase):
    def test_research_resolves_to_yaml(self):
        yaml_dir = Path("/tmp/yaml")
        result = resolve_workflow_value("research", yaml_dir)
        assert result == yaml_dir / "claude_loop_research.yaml"

    def test_all_registered_values_resolve_to_yaml(self):
        # WORKFLOW_YAML_FILES の全キーが yaml_dir / filename を返すことを確認
        ...

class TestReadWorkflowKind(unittest.TestCase):
    def test_research_in_frontmatter(self):
        p = self._write(Path(td), "---\nworkflow: research\n---\nbody\n")
        assert _read_workflow_kind(p) == "research"
```

既存 `test_missing_workflow_key_falls_back_to_full` / `test_invalid_workflow_value_falls_back_to_full` は `research` を有効値に追加した後も fallback 動作が壊れていないことを確認（`full` に落ちる動作は維持）。

`/issue_plan` の auto 選定ロジックの unit test（`test_issues_only_defaults_to_full` の拡張）には新規 `test_research_conditions_trigger_research_workflow` を追加し、4 条件のいずれか 1 つを含む場合に `result.workflow == "research"` となることを確認。

### 4.2 `scripts/tests/test_claude_loop_integration.py`

既存 integration test の workflow dispatch 部分に `--workflow research` 経路を追加。具体的には:

- `--workflow research` 指定時に `claude_loop_research.yaml` がロードされ 8 step が dry-run で走ることを確認
- `--workflow auto` + 事前に `workflow: research` frontmatter の `ROUGH_PLAN.md` を配置した状態で phase2 が `claude_loop_research.yaml` を選択することを確認

mock は使わず既存方式踏襲（`--dry-run` で claude CLI 実行はスキップされるため、テスト自体は CI で成立）。

## 5. MASTER_PLAN / CURRENT.md 更新

### 5.1 `docs/util/MASTER_PLAN/PHASE8.0.md`

- §1 冒頭に「**ver16.0 で実装済み（2026-04-24）**」を追記
- §1-2 完了条件 5 項目に各 ✅ を付ける（本版で達成した項目）
- ver16.1 以降に持ち越す項目があれば明示

### 5.2 `docs/util/MASTER_PLAN.md`

- PHASE8.0 §1 実装済みの注記

### 5.3 `docs/util/ver16.0/CURRENT.md`（メジャー版のため新規作成）

- カテゴリの現況完全版
- 以下を網羅: workflow 一覧（6 YAML）、SKILL 一覧（12 SKILL）、artifact 一覧、sync 契約、test 構造
- CLAUDE.md と重複する内容は書かない（本版で追加された `research` 関連のみ詳述）

## 6. PHASE8.0 §1-2 完了条件チェックリスト

handoff の指示（`/wrap_up` で 1 項目ずつ達成判定できるよう）に従い、IMPLEMENT.md 末尾に PHASE8.0 §1-2 の 5 完了条件を転記する（PHASE8.0.md 確定後に埋める）:

- [x] 条件1: `--workflow research` 明示起動が動作する
- [x] 条件2: `--workflow auto` で ROUGH_PLAN frontmatter `workflow: research` が選ばれた時に `claude_loop_research.yaml` が実行される
- [x] 条件3: `question` / `research` の責務境界が docs / SKILL / README で明示されている
- [x] 条件4: `RESEARCH.md` / `EXPERIMENT.md` が後続 `/imple_plan` から入力として利用可能
- [x] 条件5: `experiments/` 運用ルール（`experiments/README.md`）が存在する

※ 条件文は PHASE8.0.md §1-2 の実文から転記する必要あり。`/wrap_up` で確認すること。

## 7. 実装順序（推奨）

1. **REFACTOR（Step 1〜Step 2）** — 既存テスト全 green 確認
   - `scripts/claude_loop_lib/workflow.py` に `WORKFLOW_YAML_FILES` / `AUTO_TARGET_YAMLS` 導入
   - `scripts/claude_loop_lib/validation.py` の `_resolve_target_yamls` を dict 駆動へ
   - コミット: `refactor(ver16.0): workflow 値レジストリ化（research 追加の前段）`

2. **YAML / レジストリに `research` を追加**
   - `claude_loop_research.yaml` 新規
   - `WORKFLOW_YAML_FILES` / `AUTO_TARGET_YAMLS` に 1 行ずつ追加
   - `_read_workflow_kind` 許容値拡張
   - `_run_auto` の phase2 YAML 選択を dict 駆動へ
   - 既存 5 YAML の NOTE コメント更新（6 ファイル sync 契約）
   - `.claude/rules/scripts.md` 5 → 6 更新
   - コミット: `feat(ver16.0): research workflow YAML とレジストリ統合`

3. **新 SKILL 2 件**
   - `.claude_sync/` 経由で `research_context` / `experiment_test` を追加
   - `claude_sync.py import` で `.claude/` に反映
   - コミット: `feat(ver16.0): /research_context と /experiment_test SKILL 新設`

4. **既存 SKILL 更新**
   - `issue_plan` / `split_plan` / `imple_plan` / `meta_judge/WORKFLOW.md`
   - `.claude_sync/` 経由
   - コミット: `docs(ver16.0): 既存 SKILL に research workflow 対応追記`

5. **`experiments/README.md` 新設 + `scripts/README.md` / `USAGE.md` 更新**
   - コミット: `docs(ver16.0): experiments 運用ルールと scripts/ docs 更新`

6. **テスト追加**
   - `test_claude_loop_cli.py` / `test_claude_loop_integration.py` 更新
   - CI 想定の green 確認
   - コミット: `test(ver16.0): research workflow の cli / integration test 追加`

7. **MASTER_PLAN / CURRENT.md 更新**
   - `/wrap_up` / `/write_current` / `/retrospective` の各 step で担当（本 IMPLEMENT.md の範囲は 7 まで含まない、参考のみ）

コミット分割はレビュー容易性を優先。手順 2 以降は論理単位で push 可能だが、本 SKILL は push しない（後続でまとめ push）。

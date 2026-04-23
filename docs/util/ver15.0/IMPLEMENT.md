# ver15.0 IMPLEMENT — `issue_scout` workflow 新設

`ROUGH_PLAN.md`（workflow: full / source: master_plan）で固定された PHASE7.1 §1 の実装計画。新規 SKILL / 新規 workflow YAML / `claude_loop.py` 拡張 / 関連 docs 追記を、既存構造を壊さず add-only で積む。

## ゴール（完了条件の再掲）

- `python scripts/claude_loop.py --workflow scout --category util` 相当で起動可能
- 1 run で `ISSUES/util/{priority}/*.md` に 1〜3 件の新規 ISSUE（原則 `raw / ai`）を起票してサマリを出して終了する
- `auto` / `full` / `quick` の既存挙動と自動選択ロジックには一切触れない
- 起票された ISSUE は既存 `issue_review` / `issue_plan` フローへフロントマター互換で接続できる

## 成果物一覧（PHASE7.1.md §「ファイル変更一覧」§1 分と同期）

| # | パス | 操作 | 概要 |
|---|---|---|---|
| 1 | `scripts/claude_loop_lib/workflow.py` | 変更 | 定数 `SCOUT_YAML_FILENAME` 追加 / `RESERVED_WORKFLOW_VALUES` に `"scout"` 追加 / `resolve_workflow_value()` に分岐追加 |
| 2 | `scripts/claude_loop_lib/validation.py` | 変更なし（検証経路は既存 `_resolve_target_yamls` の `else` パスで吸収されるため） |
| 3 | `scripts/claude_loop.py` | 変更なし（`--workflow` は文字列値をそのまま `resolve_workflow_value()` に渡すため追加実装不要。`_run_auto()` には触れない） |
| 4 | `scripts/claude_loop_scout.yaml` | 新規 | 1 ステップ `/issue_scout` のみを持つ workflow 定義 |
| 5 | `.claude/SKILLS/issue_scout/SKILL.md` | 新規 | 潜在課題の探索手順と起票規約（`claude_sync.py` 経由で配置） |
| 6 | `scripts/README.md` | 変更 | 「フル/quick の使い分け」節の直後に「scout（能動探索）」節を追加 |
| 7 | `scripts/USAGE.md` | 変更 | 「YAML ワークフロー仕様」節末尾に scout YAML の最小サンプルを追記 |
| 8 | `ISSUES/README.md` | 変更 | 「AI が起票するパス」節に `issue_scout` 起票時の frontmatter 既定値（`raw / ai` 原則、`ready / ai` 昇格条件）を追記 |
| 9 | `scripts/claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` | 変更 | 先頭 NOTE コメントの sync 対象リストに `claude_loop_scout.yaml` を追加（4-way sync に更新） |
| 10 | `scripts/tests/test_workflow.py` | 変更 | 下記 §テスト方針に従い 3 箇所にケース追加 |
| 11 | `scripts/tests/test_validation.py` | 変更 | `TestValidateStartupExistingYamls` クラスに `test_scout_yaml_passes` を追加 |
| 12 | `docs/util/MASTER_PLAN.md` / `docs/util/MASTER_PLAN/PHASE7.1.md` | 変更 | §1 の進捗を「実装済み（ver15.0）」に更新 |

ROUGH_PLAN.md で「新規 CLI オプション（`--scout`）の追加が真に必要かは IMPLEMENT.md の判断」と記載された点については、**`--workflow scout` 一本で十分**と判断する。`--scout` のような別フラグは引数パース経路を二系統化してしまい scripts.md rule § 3（argparse 単一化）と整合しない。

## 設計の要点

### 1. workflow 入口の実装方針

`resolve_workflow_value()` の拡張のみで成立させる。パターンは既存 `full` / `quick` と完全対称:

```python
FULL_YAML_FILENAME = "claude_loop.yaml"
QUICK_YAML_FILENAME = "claude_loop_quick.yaml"
ISSUE_PLAN_YAML_FILENAME = "claude_loop_issue_plan.yaml"
SCOUT_YAML_FILENAME = "claude_loop_scout.yaml"   # ← 追加

RESERVED_WORKFLOW_VALUES = ("auto", "full", "quick", "scout")   # ← "scout" 追加

def resolve_workflow_value(value: str, yaml_dir: Path) -> str | Path:
    if value == "auto":
        return "auto"
    if value == "full":
        return yaml_dir / FULL_YAML_FILENAME
    if value == "quick":
        return yaml_dir / QUICK_YAML_FILENAME
    if value == "scout":                           # ← 追加
        return yaml_dir / SCOUT_YAML_FILENAME
    return Path(value).expanduser()
```

`validation.py` 側は `_resolve_target_yamls()`（validation.py:65-76）が `resolved` が `Path` の場合にそれを単独で検証する既存経路を通るため、auto 分岐に `scout` を追加する必要はない（= auto に自動混入しない保証）。`validate_single_yaml` は YAML 構造を汎用的に検査するため scout YAML もそのまま通る。

**`_run_auto()`（claude_loop.py:268-333）には触れない。** これが「`auto` / `full` / `quick` の挙動を変えない」完了条件の技術的裏付け。

### 2. `scripts/claude_loop_scout.yaml` の骨格

1 ステップのみ。`command` / `defaults` は既存 3 YAML と**完全一致**（scripts.md rule § 3 の同期契約）。

```yaml
# NOTE: --workflow scout で起動する opt-in 能動探索 workflow。
#       --workflow auto には自動混入しない（validation.py / claude_loop.py の auto 経路で選ばれない）。
#       The `command` / `defaults` sections must stay in sync with claude_loop.yaml,
#       claude_loop_quick.yaml, and claude_loop_issue_plan.yaml.

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
  - name: issue_scout
    prompt: /issue_scout
    model: opus
    effort: high
```

モデル選択根拠: 探索は品質 > スピード（1〜3 件の高価値抽出が目的）のため `opus` / `high`。`issue_plan` / `split_plan` / `imple_plan` の既存大型ステップと揃える。

### 3. `.claude/SKILLS/issue_scout/SKILL.md` の責務

frontmatter は既存 SKILL と同パターン:

```markdown
---
name: issue_scout
disable-model-invocation: true
user-invocable: true
---
```

本文の骨子（実装対象節）:

1. **コンテキスト** — 現カテゴリ / 最新バージョン / 既存 `ISSUES/{cat}` 分布（`python scripts/issue_status.py <cat>` 埋め込み）/ 直近 `RETROSPECTIVE.md` / `MASTER_PLAN.md` 進捗 をシェル補間で注入
2. **役割** — 能動探索専用であり ISSUE 起票のみを行う。コード実装・テスト修正・ドキュメント更新・バージョンディレクトリ作成をしないことを明記
3. **探索手順（3 段階）**
   - 3.1 **既存資産の棚卸し**: `ISSUES/{cat}/**/*.md`（`done/` 配下も含む）/ 直近 3 バージョンの `RETROSPECTIVE.md` / `MASTER_PLAN/PHASE*.md` の「実装進捗」表 / `CURRENT*.md` を Read
   - 3.2 **潜在課題の抽出**: コード・tests・docs・設定を走査し、以下の観点で候補化する（価値 > 件数）
     - 壊れ兆候（例外握りつぶし / 未使用分岐 / dead code / TODO コメント長期滞留）
     - ドキュメント × 実装の乖離（rule と実コードの食い違い / README 記載と挙動の差）
     - `RETROSPECTIVE.md` で「次ループ観察」扱いだが未 ISSUE 化の事項
   - 3.3 **重複排除 / 除外チェック**（起票前ゲート）
     - タイトル類似（正規化文字列の完全一致）
     - 本文冒頭 50 文字の語彙重複率 > 50%
     - 重複した既存 ISSUE がある場合、該当パスを出力し起票をスキップ
4. **起票ルール**
   - 件数上限: 1 run あたり最大 3 件（下限 0。価値ある候補が無ければ起票ゼロで終了）
   - frontmatter 既定: `status: raw` / `assigned: ai` / `priority: {high|medium|low}` / `reviewed_at: "{YYYY-MM-DD}"`（文字列クオート必須）
     - **`priority` は必須扱い**（`ISSUES/README.md` 本体では任意だが、scout 起票では配置先ディレクトリ `ISSUES/{cat}/{priority}/` と frontmatter を必ず一致させる運用を強制。SKILL 本文でこの要件を明記する）
   - `ready / ai` への昇格条件（すべて満たす場合のみ許可）:
     - 症状の再現条件がファイルパス + 具体操作で書ける
     - 影響範囲が 3 ファイル / 100 行以内で見積もれる
     - 修正方向が IMPLEMENT.md なしで 1 段落で書ける
   - ファイル命名: `ISSUES/{cat}/{priority}/{kebab-case-summary}.md`（既存 ISSUE と同規約）
   - 本文テンプレ: `## 症状` / `## 影響` / `## なぜ今見る価値があるか` / `## 想定修正方向（任意）`
5. **サマリ報告** — run 終了時に「起票件数」「起票パス一覧」「重複でスキップした候補があればその件数」を stdout に出す
6. **やらないこと** — コード修正 / テスト実行 / ドキュメント更新 / `.claude/` 編集 / `docs/{cat}/ver*/` 作成 / 既存 ISSUE の書き換え
7. **Git コミット** — 新規 ISSUE 起票のみをコミット（メッセージ例: `issues(util): issue_scout による能動起票 (3件)`）。プッシュしない

**配置手順**: `.claude/` 配下は CLI `-p` モードで直接編集不可（`.claude/rules/claude_edit.md`）のため、`python scripts/claude_sync.py export` → `.claude_sync/SKILLS/issue_scout/SKILL.md` 作成 → `python scripts/claude_sync.py import` の 3 段で配置する。

### 4. docs 追記の要点

- **`scripts/README.md`** 「フル/quick の使い分け」節（lines 87-96）の直後に節を挿入:
  - 見出し: `## scout（能動探索）` 程度
  - 内容: 起動方法（`python scripts/claude_loop.py --workflow scout --category <cat>`）/ `auto` に自動混入しないこと / 出力は ISSUE 起票のみであること / 推奨頻度（定期監査・節目のみ）
- **`scripts/USAGE.md`** 「YAML ワークフロー仕様」節末尾に scout YAML 例を 10-15 行で転記
- **`ISSUES/README.md`** 「AI が起票するパス」節（lines 79-87）の表の下に段落追加:
  - `issue_scout` による起票は **原則 `raw / ai`** とし、昇格条件（症状・影響・修正方向の 3 点が自力で固まった小粒に限る）を満たす場合のみ `ready / ai` を許可する旨
- **`docs/util/MASTER_PLAN.md`** / **`PHASE7.1.md`** の進捗表で §1 を「実装済み（ver15.0）」に更新

### 5. 重複検出の実装方針（ROUGH_PLAN §リスク引き継ぎ 2 の深掘り）

SKILL 内で純粋に Read ベースのヒューリスティックとして実施する。**スクリプト化・埋め込み関数追加は行わない**（Python 側に寄せると scripts.md rule § 4 の「ISSUE frontmatter は `issues.py` の定数を参照」と組み合わせて新規依存が発生する割に、1 run 1〜3 件の目視精度で十分）。

採用ロジック:
1. タイトル正規化: 先頭 `#` 以降を lower + 非英数字除去 + NFKC
2. 正規化後タイトルが完全一致 → 重複扱い
3. 本文冒頭 50 文字を形態素分割せず空白区切り単語集合化 → Jaccard ≥ 0.5 → 重複扱い
4. 重複ヒット時は該当パスをサマリ出力で報告してスキップ

却下した案:
- 埋め込みベクトル類似度 → PyYAML のみ許容の依存縛り（scripts.md § 1）に反する
- タイトル substring 検索 → 過検出リスク高（`testing` / `request` 等の汎用語で誤爆）

### 6. 探索対象スコープの既定値（ROUGH_PLAN §リスク引き継ぎ 3 の深掘り）

**カテゴリ単位で閉じる**を既定とする。`--category <cat>`（= `.claude/CURRENT_CATEGORY`）で渡されたカテゴリに対応する:

- コード: そのカテゴリが主に触るソースツリー（util なら `scripts/`・`.claude/` / app なら `app/`・`server/`）
- ISSUES: `ISSUES/{cat}/**/*.md`
- docs: `docs/{cat}/**/*.md`（最新 3 バージョン優先）

理由: (a) `MASTER_PLAN` がカテゴリ単位で組まれている / (b) リポジトリ全体走査は 1 run の読み込み量が発散しシグナル/ノイズ比が悪化 / (c) カテゴリ横断の課題が見つかった場合は複数カテゴリに「同一観点」の ISSUE を個別起票すれば重複検出で自然に抑制される。

### 7. `issue_review` / `issue_plan` 接続性の担保（ROUGH_PLAN §リスク引き継ぎ 4）

scout 起票の frontmatter は `status: raw` / `assigned: ai` を既定とするため、既存 `issue_plan` の「選定対象は `ready / ai` のみ / `raw` は対象外」ポリシー（`issue_plan/SKILL.md:88`）と**即整合する**。`issue_review` は `review / ai` しか走査しないため scout 起票物（`raw / ai`）に触らず、既存フローを乱さない。

`ready / ai` で起票した場合のみ次回 `/issue_plan` の選定候補に入る。`reviewed_at` は scout 実行日（YYYY-MM-DD 文字列クオート）を付与する — これにより `issue_status.py` の date 変換警告を回避し、`ISSUES/README.md` の推奨に揃う。

## 実装ステップ（順序固定）

**Step 0（事前確認、コード変更なし）** — 実装着手前に以下を Grep / Read で確認し、設計前提が崩れていないことを担保:
- `RESERVED_WORKFLOW_VALUES` の他参照箇所を Grep で列挙（`claude_loop.py` / 他モジュール / テスト）。`claude_loop.py:119-124` 付近の `validate_auto_args` 等で間接参照があれば影響範囲を確認
- `scripts/issue_worklist.py` の status フィルタ実装を Read し、`raw / ai` が選定結果に含まれないこと（= scout の `raw / ai` 起票が `issue_plan` のコンテキストを肥大化させないこと）を確認。含まれる場合は `issue_worklist.py` 側の扱いを MEMO.md に追記して次バージョン検討対象にする
- `validation.py:258,279` の SKILL 存在チェックがパス `.claude/skills/{name}/SKILL.md`（小文字）で行われていることを確認。Windows 上は case-insensitive なので `.claude/SKILLS/` と実質一致するが、Linux 実行時の互換は本バージョンのスコープ外（既存パス表記を変更しない）

1. **`scripts/claude_loop_lib/workflow.py` 拡張** — 定数 `SCOUT_YAML_FILENAME` 追加 / `RESERVED_WORKFLOW_VALUES` タプル拡張 / `resolve_workflow_value()` 分岐追加
2. **`scripts/claude_loop_scout.yaml` 新規作成** — 上記骨格。`command` / `defaults` は既存 3 YAML からコピー
3. **既存 3 YAML の先頭 NOTE コメント更新** — sync 同期対象リストに `claude_loop_scout.yaml` を追加し 4-way sync に更新。`scripts/claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` 全てに同じ更新を適用
4. **`scripts/tests/test_workflow.py` 拡張** — 下記 §テスト方針 参照
5. **`.claude_sync/SKILLS/issue_scout/SKILL.md` 作成** — `python scripts/claude_sync.py export` → `.claude_sync/SKILLS/issue_scout/SKILL.md` を新規作成 → `python scripts/claude_sync.py import`（※`claude_edit.md` rule 準拠）。import 後に `ls .claude/SKILLS/issue_scout/SKILL.md` で物理配置を確認
6. **`scripts/tests/test_validation.py` 拡張** — `TestValidateStartupExistingYamls` クラスに `test_scout_yaml_passes` を追加（SKILL 配置後でないと SKILL 存在チェックに失敗するため Step 5 の後に実行）
7. **`python -m pytest scripts/tests/test_workflow.py scripts/tests/test_validation.py` 実行** — 新テストすべてグリーンを確認
8. **`python scripts/claude_loop.py --workflow scout --dry-run`** で validation + resolve 完走を確認（この時点で SKILL は配置済のため `/issue_scout` の存在チェックが通る）
9. **`scripts/README.md` / `scripts/USAGE.md` / `ISSUES/README.md` 追記**
10. **`docs/util/MASTER_PLAN.md` / `docs/util/MASTER_PLAN/PHASE7.1.md` 進捗更新**
11. **統合 smoke test** — `/wrap_up` SKILL 手順の中で、実環境 `python scripts/claude_loop.py --workflow scout --category util --max-loops 1` を 1 回実行し、起票 0〜3 件とサマリ出力を目視確認。本 smoke test の責務は `/wrap_up` に委ね、IMPLEMENT 段階では着手しない

## リスク・不確実性

| # | リスク | 影響 | 抑制策 | MEMO.md で確認する項目 |
|---|---|---|---|---|
| R1 | `issue_scout` の判定粒度が粗いと `raw / ai` が増えて `ISSUES/` がノイズ化（PHASE7.1 リスク 1） | `issue_plan` の初期レビュー負荷増・`issue_status.py` 分布のシグナル劣化 | 起票件数上限 3 / 事前重複検出 / 価値観点 3 軸に明示的に絞る | 初回 smoke test の起票件数・内容の目視結果 |
| R2 | 重複検出ヒューリスティックの閾値不明（Jaccard 0.5 / タイトル正規化一致） | 過検出 or 取りこぼし | 初回 run 結果の既存 ISSUE との重複状況を MEMO.md §リスク検証でクローズ | 実起票と `ISSUES/{cat}/done/` の見た目 diff |
| R3 | `claude_sync.py` の export/import サイクルで新規 SKILL が「既存 `.claude/`」側にない状態から始まるため import が期待通りに追加するか未確認 | SKILL が配置されず `/issue_scout` が「skill not found」で validation エラー | 実装ステップ 7 の後に `ls .claude/SKILLS/issue_scout/SKILL.md` で存在確認 / validation.py の skill 存在チェック（validation.py:272-281）を活用 | import 後の実ファイル有無 |
| R4 | scout YAML が既存 3 YAML と `command` / `defaults` がドリフトする（rule § 3 の同期契約破り） | 実行時挙動の差 | 実装ステップ 2 で既存 YAML からコピー / テスト追加 | `diff` で 3 ファイルとの `command`/`defaults` セクション差分ゼロ |
| R5 | `RESERVED_WORKFLOW_VALUES` に追加した `"scout"` がどこか別の箇所でも参照されている可能性（Grep 漏れ） | 想定外のメッセージ・自動選択への混入 | 実装開始時に `Grep "RESERVED_WORKFLOW_VALUES\|claude_loop_scout\|\"scout\""` で現状参照ゼロを確認 | 追加前後の Grep 結果比較 |
| R6 | SKILL.md のシェル補間（`!`…``）で `issue_status.py` を呼ぶがカテゴリ引数未指定時のフォールバックが想定と異なる可能性 | SKILL コンテキスト生成時にエラー or 別カテゴリ情報が混入 | `python scripts/issue_status.py util` 等、カテゴリ明示呼び出しを SKILL 側で使う / フォールバックは `cat .claude/CURRENT_CATEGORY` 経由で既存パターンを踏襲 | SKILL ドライランでのコンテキスト出力 |
| R7 | `issue_scout` から `raw / ai` を多量起票した場合、`issue_worklist.py --format json` の出力が増えて `issue_plan` コンテキストが肥大化 | `/issue_plan` のトークン消費増・拾い上げ精度低下 | 上限 3 件制約 / `issue_worklist.py` は `ready / review` のみ返す既存実装に依存（`raw / ai` は含まれない想定）のため基本無害。実装前に `issue_worklist.py` 実装を確認 | `issue_worklist.py` の status フィルタ実装 |
| R8 | scout YAML に `continue: true` を入れなかった場合でも単一ステップなので session 引き継ぎ不要なはずだが、ログ出力・notify で通常 workflow と差が出る可能性 | サマリ通知の体裁が崩れる | 既存 1 ステップ YAML（`claude_loop_issue_plan.yaml`）の挙動を参考に整合を取る | dry-run ログの体裁確認 |

## テスト方針

### ユニットテスト追加（具体的なファイル・クラス・メソッド単位）

**`scripts/tests/test_workflow.py`**（3 箇所）:
1. 既存 import 行（現在 `FULL_YAML_FILENAME, QUICK_YAML_FILENAME, ISSUE_PLAN_YAML_FILENAME` を import）に `SCOUT_YAML_FILENAME` を追加
2. `TestResolveWorkflowValue` クラスに `test_resolve_scout_returns_scout_yaml_path` を追加（`result == self.yaml_dir / SCOUT_YAML_FILENAME`）
3. `TestYamlSyncOverrideKeys`（または既存の YAML allowed-keys 検査クラス）に `test_scout_yaml_uses_only_allowed_keys` を追加。`load_workflow(self._yaml_path(SCOUT_YAML_FILENAME))` を呼び、step / defaults キーが `ALLOWED_STEP_KEYS` / `ALLOWED_DEFAULTS_KEYS` に収まることを assert

**`scripts/tests/test_validation.py`**（1 箇所）:
1. `TestValidateStartupExistingYamls` クラスに `test_scout_yaml_passes` を追加。`_make_args(workflow="scout")` パターンで `validate_startup(YAML_DIR / SCOUT_YAML_FILENAME, args, YAML_DIR, PROJECT_ROOT)` が例外なく完走することを assert。`workflow.py` から `SCOUT_YAML_FILENAME` を直接 import する（`validation.py` 経由ではない）

### 手動確認
- Step 8 の `--dry-run` で scout YAML の resolve + validate がエラーなく通ること
- Step 11 の smoke run（`/wrap_up` 段階）で 0〜3 件の起票と停止が期待通りであること

### 回帰確認
- `python -m pytest scripts/tests/` 全体でグリーンを保つこと
- 特に `test_claude_loop_integration.py` 既存テストが scout 追加で影響を受けないこと（auto 経路のテストが 3 YAML のみ参照のままであること）

## スコープ外（念のための明示）

- PHASE7.1 §2〜§4（QUESTIONS / PLAN_HANDOFF 分離 / run 単位通知）
- `issue_scout` を `--workflow auto` に自動混入させる仕組み
- app / infra への初回適用（util インフラ整備のみ）
- 独自フラグ（`--scout`）の追加
- 既存 ISSUE の一括再整理（scout は起票専用）
- 埋め込みベクトル等による高精度重複検出

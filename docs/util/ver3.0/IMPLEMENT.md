# IMPLEMENT: util ver3.0

## 事前リファクタリング不要

`claude_loop.py` には `-w` / `--workflow` フラグが既に実装済み（L40-46）。PHASE3.0 で想定されていた「`-w` フラグの追加」は不要。Python コードの変更は一切なし。

## 既存コードの確認結果

| ファイル | 確認結果 |
|---|---|
| `scripts/claude_loop.py` | `-w` フラグ実装済み（L40-46）。`create_log_path` はワークフロー名をログファイル名に含める（L257）ため、quick YAML は自動で `*_claude_loop_quick.log` と区別される |
| `scripts/claude_loop.yaml` | full ワークフロー定義。`mode`, `command`, `steps` の 3 セクション構成。`auto_args` に `.claude/` 編集の注意事項を含む |
| `.claude/SKILLS/` | `split_plan`, `imple_plan`, `wrap_up`, `write_current`, `retrospective`, `meta_judge` の 6 ディレクトリ。SKILL.md でスキル定義 |
| `.claude/SKILLS/meta_judge/WORKFLOW.md` | フルワークフローの 5 ステップのみ記載 |

## 変更一覧

| # | ファイル | 操作 | 内容 |
|---|---|---|---|
| 1 | `scripts/claude_loop_quick.yaml` | 新規作成 | 軽量ワークフロー YAML 定義 |
| 2 | `.claude/SKILLS/quick_plan/SKILL.md` | 新規作成 | 軽量版計画ステップ |
| 3 | `.claude/SKILLS/quick_impl/SKILL.md` | 新規作成 | 軽量版実装ステップ |
| 4 | `.claude/SKILLS/quick_doc/SKILL.md` | 新規作成 | 軽量版ドキュメントステップ |
| 5 | `.claude/SKILLS/meta_judge/WORKFLOW.md` | 変更 | quick ワークフローの説明を追記 |

---

## 1. `scripts/claude_loop_quick.yaml`

既存の `claude_loop.yaml` と同じ構造（`mode`, `command`, `steps`）。`command` セクションは full と同一（`--dangerously-skip-permissions`、`auto_args` の `.claude/` 編集注意等）。`steps` のみ 3 ステップに変更。

```yaml
mode:
  auto: false

command:
  executable: claude
  prompt_flag: -p
  args:
    - --dangerously-skip-permissions
  auto_args:
    - --disallowedTools "AskUserQuestion"
    - >-
      --append-system-prompt "you cannot ask questions to the user. so,
      whenever you think you should get human feedback, just write a file under
      `REQUESTS/AI` folder. Human will see this after you finish this step.
      (**So you cannot directly ask nor get human feedback in this session.**)

      ## Editing files under .claude/

      Files under `.claude/` cannot be directly edited in CLI `-p` mode (security restriction).
      To edit files in `.claude/`, use `scripts/claude_sync.py` with the following steps:

      1. `python scripts/claude_sync.py export` — Copy `.claude/` to `.claude_sync/`
      2. Edit the corresponding files in `.claude_sync/` (this directory is writable)
      3. `python scripts/claude_sync.py import` — Write back `.claude_sync/` contents to `.claude/`

      **Note**: Run export/import via the Bash tool with `python scripts/claude_sync.py <command>`."

steps:
  - name: quick_plan
    prompt: /quick_plan

  - name: quick_impl
    prompt: /quick_impl

  - name: quick_doc
    prompt: /quick_doc
```

**設計判断**: `command` セクションを full と完全に同一にする。auto_args の `.claude/` 編集制限は quick でも必要であり、差分を作ると将来の保守が二重になる。

---

## 2. `.claude/SKILLS/quick_plan/SKILL.md`

フルワークフローの `split_plan` の簡略版。以下の点を簡略化:
- `IMPLEMENT.md` / `REFACTOR.md` の作成を省略
- `plan_review_agent` による承認を省略
- メジャーバージョンが必要と判断した場合はユーザーに報告してフルワークフローへの切り替えを推奨

### 構造

```markdown
## コンテキスト
（split_plan と同じテンプレート変数: カテゴリ、最新バージョン番号、次のマイナーバージョン番号）

## 準備
- 最新バージョンの CURRENT.md または CHANGES.md を参照
- ISSUES/{カテゴリ} の high/medium 課題を確認
- 直前バージョンの RETROSPECTIVE.md の未実施改善を確認

## 計画
- マイナーバージョンのみ（メジャーが必要なら報告して full への切り替えを推奨）
- docs/{カテゴリ}/ver{次のマイナーバージョン番号}/ フォルダを作成
- ROUGH_PLAN.md を作成:
  - 対応する ISSUE（1〜2 件）
  - 変更対象ファイル（3 つ以下の見込み）
  - 変更方針（5〜10 行程度の簡潔な記述）
  - 実装方針も簡潔に含める（IMPLEMENT.md を作成しないため）
- plan_review_agent は起動しない

## Git にコミットする
- コミットメッセージ: `docs(ver{バージョン番号}): quick_plan完了`
```

### split_plan との主な差分

| 項目 | split_plan | quick_plan |
|---|---|---|
| バージョン種別 | メジャー/マイナー両方 | マイナーのみ |
| 出力ドキュメント | ROUGH_PLAN + REFACTOR + IMPLEMENT | ROUGH_PLAN のみ |
| plan_review_agent | 2 回起動（概要+実装） | 起動しない |
| 小規模タスク判定 | あり（省略判定ロジック） | 不要（常に簡潔） |

---

## 3. `.claude/SKILLS/quick_impl/SKILL.md`

フルワークフローの `imple_plan` + `wrap_up` を統合した簡略版。

### 構造

```markdown
## コンテキスト
（カテゴリ、最新バージョン番号）

## 実装
- ROUGH_PLAN.md の変更方針に基づいて実装
- サブエージェントの利用は任意（小規模なので直接実装が効率的な場合が多い）

## 品質確認
- `npx nuxi typecheck` を最低 1 回実施
- `pnpm test` を実施（テストが存在する場合）
- ROUGH_PLAN で指定されたテストがあれば作成・実行

## MEMO
- MEMO.md に実装メモを記載（ある場合のみ）
- MEMO 項目がある場合はその場で対応（wrap_up 相当）
- 対応不可能な項目は ISSUES/{カテゴリ} に記載

## Git にコミットする
- 実装変更をコミット
- コミットメッセージ: 変更内容に応じた適切なメッセージ（例: `fix(util): ログ出力エラーを修正`）
```

### imple_plan + wrap_up との主な差分

| 項目 | imple_plan + wrap_up | quick_impl |
|---|---|---|
| 計画参照 | IMPLEMENT.md + REFACTOR.md | ROUGH_PLAN.md のみ |
| typecheck | 最低 2 回 | 最低 1 回 |
| MEMO 対応 | wrap_up で別ステップ | その場で統合対応 |
| ユーザー確認 | ビルド・ブラウザ確認を提案 | 省略 |

---

## 4. `.claude/SKILLS/quick_doc/SKILL.md`

フルワークフローの `write_current` の簡略版。CHANGES.md のみ作成（CURRENT.md はメジャーバージョン専用のため不要）。

### 構造

```markdown
## コンテキスト
（カテゴリ、最新バージョン番号）

## ドキュメント作成
- CHANGES.md を作成
  - git diff --name-status で変更ファイルを確認
  - 変更内容・技術的判断を簡潔に記載
  - git diff との照合で記載漏れを検証

## 更新確認
- CLAUDE.md の更新が必要か確認（必要な場合のみ更新提案）
- MASTER_PLAN.md の該当項目ステータス更新（該当する場合）
- 解決した ISSUES ファイルを削除

## Git にコミットする
- コミットメッセージ: `docs(ver{バージョン番号}): quick_doc完了`
```

### write_current との主な差分

| 項目 | write_current | quick_doc |
|---|---|---|
| 出力 | CURRENT.md (メジャー) or CHANGES.md (マイナー) | CHANGES.md のみ |
| git diff 検証 | あり | あり（同一） |
| ISSUES 整理 | なし（wrap_up で実施） | あり（wrap_up が存在しないため統合） |

---

## 5. `.claude/SKILLS/meta_judge/WORKFLOW.md` の更新

既存のフルワークフロー説明の後に、quick ワークフローのセクションを追加する。

### 追加内容

```markdown
## 2. 軽量ワークフロー（quick）

小規模タスク向けの 3 ステップワークフロー。`claude_loop_quick.yaml` で定義。

1. `/quick_plan` — ISSUE 選定 + 簡潔な計画（ROUGH_PLAN.md のみ）
2. `/quick_impl` — 実装 + MEMO対応 + typecheck + コミット
3. `/quick_doc` — CHANGES.md 作成 + CLAUDE.md 更新確認 + ISSUES 整理 + コミット

### ワークフロー選択ガイドライン

| 条件 | 推奨 |
|---|---|
| MASTER_PLAN の新項目着手 | full |
| アーキテクチャ変更・新規ライブラリ導入 | full |
| 変更ファイル 4 つ以上 | full |
| ISSUES/high の対応（複雑） | full |
| ISSUES の 1 件対応（単純） | quick |
| バグ修正（原因特定済み） | quick |
| 既存機能の微調整 | quick |
| ドキュメント・テスト追加 | quick |
| 変更ファイル 3 つ以下 | quick |
```

---

## リスク・不確実性

### 低リスク

- **SKILL 定義の不備**: 新 SKILL は既存 SKILL のパターンに従うため、構造上の問題は考えにくい。ただし、quick_impl で `wrap_up` 相当の MEMO 対応を統合するため、MEMO 項目が予想外に多い場合のフォールバック手順が曖昧。→ SKILL 内に「対応不可能な項目は ISSUES に記載」の手順を明記して対処
- **YAML の `command` セクション同期**: full と quick で `command` セクションを完全同一にするが、将来 full 側を変更した際に quick 側の更新を忘れるリスク。→ 現時点では重複を受け入れる（YAML 共通化は PHASE3.0 スコープ外）

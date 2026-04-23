# CURRENT_skills: util ver14.0 — SKILL ファイル・rules ファイル・サブエージェント

ver14.0 で `retrospective` / `issue_plan` の 2 SKILL を更新し、`meta_judge/WORKFLOW.md` の誤記を修正。`.claude/rules/scripts.md` を新規追加。その他の SKILL は ver13.0 と同一。

## rules ファイル

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/rules/claude_edit.md` | 12 | `.claude/**/*` 編集時の `claude_sync.py` 手順を定義。`paths:` frontmatter で適用対象を限定 |
| `.claude/rules/scripts.md` | 39 | `scripts/**/*` を対象にした stable 規約（Python 前提・パス操作・CLI 引数・frontmatter/YAML 更新作法・ログ出力）。ver14.0 で新規追加 |

### `.claude/rules/scripts.md` の構成（ver14.0 新規）

`paths: scripts/**/*` frontmatter で適用対象を限定。5 節構成:

1. **Python 前提** — Python 3.10+ / PEP 604 型ヒント / 依存は標準ライブラリ + PyYAML のみ
2. **パス操作** — `pathlib.Path` を使い `os.path.join` は使わない / `Path(__file__).resolve().parent` 起点
3. **CLI 引数処理** — `argparse` 使用 / 廃止オプションを黙って無視しない / YAML 3 ファイルの `command/defaults` セクション同期義務
4. **frontmatter / YAML 更新時の作法** — `frontmatter.parse_frontmatter` 共通基盤 / `issues.py` 定数参照 / override キー拡張は `workflow.py` → `validation.py` 経路必須
5. **ログ出力** — `logging_utils.py` の `TeeWriter` / `print_step_header` / `format_duration` 使用 / ログファイル名規約維持

末尾に「詳細仕様・背景は `scripts/README.md` / `scripts/USAGE.md` を一次資料とする。rule と食い違いがあった場合は docs 側が優先」を明記。

`paths:` frontmatter を agents がどう解釈するかは本バージョン時点で未検証（`ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md` に記録済）。

## フルワークフロー（6 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `issue_plan/SKILL.md` | 102 | ステップ 1: 現状把握・ISSUE レビュー・ISSUE/MASTER_PLAN 選定・ROUGH_PLAN.md 作成・workflow 判定。`issue_worklist.py --limit 20` で ISSUE 一覧を取得。ver14.0 で FEEDBACK handoff 受信指示を追加 |
| `split_plan/SKILL.md` | 38 | ステップ 2: REFACTOR/IMPLEMENT 作成 + plan_review_agent での review のみ |
| `imple_plan/SKILL.md` | 81 | ステップ 3: 実装。CURRENT.md + 計画ドキュメントに基づきコード実装。MEMO.md を出力。検証先送りリスクは `ISSUES/` に独立ファイルを作成 |
| `wrap_up/SKILL.md` | 46 | ステップ 4: 残課題対応。MEMO.md の項目を ✅完了 / ⏭️不要 / 📋先送り に分類し、ISSUES 整理 |
| `write_current/SKILL.md` | 83 | ステップ 5: ドキュメント更新。メジャー版は CURRENT.md、マイナー版は CHANGES.md を作成。150 行超の場合は `CURRENT_{トピック名}.md` に分割 |
| `retrospective/SKILL.md` | 182 | ステップ 6: 振り返り。ver14.0 で §3.5（workflow prompt/model 評価）と §4.5（FEEDBACK handoff）を追加 |

## 軽量ワークフロー quick（3 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `issue_plan/SKILL.md` | 102 | ステップ 1: quick でも同じ前半ステップを使用 |
| `quick_impl/SKILL.md` | 43 | ステップ 2: 実装 + MEMO 対応を統合 |
| `quick_doc/SKILL.md` | 55 | ステップ 3: CHANGES.md 作成 + CLAUDE.md 更新確認 + ISSUES 整理 + コミット＆プッシュ |

## ISSUE レビュー仕様書

| ファイル | 行数 | 役割 |
|---|---|---|
| `issue_review/SKILL.md` | 99 | ISSUE レビューフェーズの一次資料。`/issue_plan` が参照し、スキャン → 個別レビュー → 書き換えガード → サマリ報告 の手順を定義。**直接起動しない** |

## メタ評価・ワークフロー文書

| ファイル | 行数 | 役割 |
|---|---|---|
| `meta_judge/SKILL.md` | 18 | メタ評価。ワークフロー全体の有効性を評価する手動実行専用 SKILL |
| `meta_judge/WORKFLOW.md` | 49 | 保守上の注意（3 ファイル同期義務・`--workflow auto` 実装済み）を定義。ver14.0 で `command / defaults`（`mode` 誤記修正）と §6 handoff 言及を追記 |

## サブエージェント

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/agents/plan_review_agent.md` | 17 | 計画レビュー専用エージェント。Sonnet モデル、Read/Glob/Grep のみ使用。`/split_plan` で利用（quick ワークフローでは使用しない） |

## ver14.0 での変更詳細

### `retrospective/SKILL.md`（84行 → 182行）

**§3.5 workflow prompt / model 評価**（§3「次バージョンの種別推奨」の直後に挿入）:
- 評価対象: 直前バージョンで実行された YAML の各 step（`system_prompt`・`model`・`effort`・`continue` 選択の妥当性）
- 3 分類: 維持 / 調整 / 削除候補。分類理由と「次ループでの具体的な修正案」を記録
- 評価結果は `RETROSPECTIVE.md` §8 節に全文残し、「次 1 ループ以内に試す調整」のみ §4.5 handoff に転記
- **省略条件明記**: 評価材料がない場合（差分なし・モデル変更なし）は省略可（形骸的評価を毎ループに強制しない）
- テンプレート例（step × model / effort / 分類 / 理由）を SKILL 本文内に掲載

**§4.5 次ループへの FEEDBACK handoff**（§4「振り返り結果の記録」の直後に挿入）:
- 書き出し対象: 次に着手すべき ISSUE 候補・保留判断継続事項・workflow 設定見直しメモ・次 `/issue_plan` への注意点
- **書き出さないケース明記**: 引き継ぐ内容がない場合は省略（空 handoff / 感想のみ FEEDBACK 禁止）
- ファイル名規約: `FEEDBACKS/handoff_ver{現行バージョン}_to_next.md`
- frontmatter: `step: issue_plan`（次ループの `/issue_plan` にのみ注入）
- 本文推奨構成: 「## 背景」「## 次ループで試すこと」「## 保留事項」の 3 節

### `issue_plan/SKILL.md`（101行 → 102行）

「## 準備」節の retrospective.md 確認指示の直後に FEEDBACK handoff 受信指示を追記:
- `FEEDBACKS/handoff_ver*_to_next.md` が存在する場合、`--append-system-prompt` 経由で自動注入される
- ROUGH_PLAN の判断材料として優先度高で参照する（感想ではなく次ステップに効く入力として扱う）

### `meta_judge/WORKFLOW.md`（47行 → 49行）

- L45 の `command / mode / defaults` 記述を `command / defaults` に修正（`mode` は ver13.0 で撤去済）
- §6 handoff の WORKFLOW 記述を末尾に 1 行追記

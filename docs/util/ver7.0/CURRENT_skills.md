# CURRENT_skills: util ver7.0 — SKILL ファイル・サブエージェント

`.claude/skills/` 配下の SKILL ファイルと、サブエージェントの構成。ver6.0 で `issue_review` SKILL を新設し、ver7.0 で `retrospective/SKILL.md` §3 に `issue_worklist.py` 呼び出しを追加した。

## フルワークフロー（5 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `split_plan/SKILL.md` | 88 | ステップ 1: 計画策定。冒頭の ISSUE レビューフェーズで `review/ai` を振り分け後、`ready/ai` ISSUE を優先度順（high → medium → low）で拾い上げ。`ready/ai` が無い場合のみ MASTER_PLAN の次項目に進む。ROUGH_PLAN / REFACTOR / IMPLEMENT を作成 |
| `imple_plan/SKILL.md` | 81 | ステップ 2: 実装。CURRENT.md + 計画ドキュメントに基づきコード実装。MEMO.md を出力。検証先送りリスクは `ISSUES/` に独立ファイルを作成 |
| `wrap_up/SKILL.md` | 46 | ステップ 3: 残課題対応。MEMO.md の項目を ✅完了 / ⏭️不要 / 📋先送り に分類し、ISSUES 整理 |
| `write_current/SKILL.md` | 83 | ステップ 4: ドキュメント更新。メジャー版は CURRENT.md、マイナー版は CHANGES.md を作成。150 行超の場合は `CURRENT_{topic}.md` に分割 |
| `retrospective/SKILL.md` | 76 | ステップ 5: 振り返り。**ver7.0 で §3 冒頭に `issue_worklist.py` 呼び出し 2 行を追加**（次バージョン推奨の前に AI 担当 ISSUE を把握） |

## 軽量ワークフロー quick（3 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `quick_plan/SKILL.md` | 51 | ステップ 1: ISSUE レビューフェーズ（split_plan と同等）+ 簡潔な計画（ROUGH_PLAN.md のみ、plan_review_agent 省略） |
| `quick_impl/SKILL.md` | 43 | ステップ 2: 実装 + MEMO 対応を統合 |
| `quick_doc/SKILL.md` | 55 | ステップ 3: CHANGES.md 作成 + CLAUDE.md 更新確認 + ISSUES 整理 + コミット＆プッシュ |

## ISSUE レビュー仕様書

| ファイル | 行数 | 役割 |
|---|---|---|
| `issue_review/SKILL.md` | 100 | `split_plan` / `quick_plan` の ISSUE レビューフェーズの**一次資料**。スキャン → 個別レビュー → 書き換えガード → サマリ報告 の手順を定義。仕様変更時は両 SKILL に同期が必要 |

### issue_review の処理フロー

1. **スキャン**: `ISSUES/{カテゴリ}/{high,medium,low}/*.md` を走査し frontmatter を読む
2. **レビュー対象抽出**: `status: review` かつ `assigned: ai` のファイルを選出
3. **個別レビュー**: 各ファイルを Read → 判定 → Edit（frontmatter ブロック丸ごと置換）
   - 記述が具体的（再現手順/期待動作/影響範囲の 2 点以上）→ `ready / ai`
   - 人間対応必要 / 記述が粗すぎる → `need_human_action / human` + `## AI からの依頼` 追記
4. **サマリ報告**: `## ISSUE レビュー結果` / `## ISSUE 状態サマリ` を ROUGH_PLAN 冒頭に残す

- `issue_review/SKILL.md` は仕様書として位置づけ、**直接起動しない**（インライン展開方式を採用）
- `split_plan/SKILL.md` / `quick_plan/SKILL.md` に同等の手順が記述されているため、仕様変更時は 3 箇所を同期修正する

## retrospective §3 の現在の構成（ver7.0 追加分）

```markdown
## 3. 次バージョンの種別推奨

次バージョンの方針を決める前に、AI が着手可能・レビュー待ちの ISSUE を把握する:

- 現在カテゴリの着手候補: !`python scripts/issue_worklist.py`
- 機械可読形式: !`python scripts/issue_worklist.py --format json`

次に予定されるタスク（MASTER_PLAN の次項目、未解決 ISSUES）を踏まえて、
次バージョンがメジャー・マイナーのどちらが適切かを推奨する。

- 次のマイナーバージョン候補: !`bash .claude/scripts/get_latest_version.sh next-minor`
- 次のメジャーバージョン候補: !`bash .claude/scripts/get_latest_version.sh next-major`
```

## メタ評価・ワークフロー文書

| ファイル | 行数 | 役割 |
|---|---|---|
| `meta_judge/SKILL.md` | 18 | メタ評価。ワークフロー全体の有効性を評価する手動実行専用 SKILL |
| `meta_judge/WORKFLOW.md` | 44 | ワークフロー概要ドキュメント。フルワークフロー・軽量ワークフローの説明、選択ガイドライン、モデル/エフォート指定節 |

## サブエージェント

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/agents/plan_review_agent.md` | 17 | 計画レビュー専用エージェント。Sonnet モデル、Read/Glob/Grep のみ使用。split_plan と wrap_up で利用（quick ワークフローでは使用しない） |

## 各 SKILL ファイルで保持すべき主要な振る舞い

- **全ステップ共通**: `.claude/CURRENT_CATEGORY` を参照して現在のカテゴリに対応するパスを取得
- **計画系ステップ（split_plan / quick_plan）**: 冒頭で `review/ai` ISSUE を走査・振り分け後、`ready/ai` ISSUE を優先度順で拾い上げ。`ready/ai` が無い場合のみ MASTER_PLAN の次項目に進む
- **imple_plan**: 検証先送りリスクは MEMO 内注記に加え `ISSUES/` に独立ファイルを作成して追跡
- **write_current**: CURRENT.md 分割基準（150 行超）、命名規則（`CURRENT_{トピック名}.md`）を遵守
- **retrospective**: SKILL 自体の改善を即時適用する自己改善ループを含む。§3 で `issue_worklist.py` を呼んで次バージョン推奨の材料を収集する

# CURRENT_skills: util ver5.0 — SKILL ファイル・サブエージェント

`.claude/SKILLS/` 配下の SKILL ファイルと、サブエージェントの構成。

## フルワークフロー（5 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `split_plan/SKILL.md` | 87 | ステップ 1: 計画策定。MASTER_PLAN・ISSUES・前回 RETROSPECTIVE から今回バージョンの計画ドキュメント（ROUGH_PLAN / REFACTOR / IMPLEMENT）を作成。分割 CURRENT.md の選択的読み込みに対応 |
| `imple_plan/SKILL.md` | 76 | ステップ 2: 実装。CURRENT.md + 計画ドキュメントに基づきコード実装。MEMO.md を出力。**検証先送りリスクは `ISSUES/{カテゴリ}/{優先度}/` に独立ファイルを作成**し MEMO に参照を残す（ver5.0 で追加） |
| `wrap_up/SKILL.md` | 45 | ステップ 3: 残課題対応。MEMO.md の項目を ✅完了 / ⏭️不要 / 📋先送り に分類し、ISSUES 整理 |
| `write_current/SKILL.md` | 83 | ステップ 4: ドキュメント更新。メジャー版は CURRENT.md、マイナー版は CHANGES.md を作成。CURRENT.md が 150 行超の場合はトピック単位で `CURRENT_{topic}.md` に分割。CLAUDE.md・MASTER_PLAN も更新 |
| `retrospective/SKILL.md` | 64 | ステップ 5: 振り返り。git diff ベースでバージョン作業を振り返り、SKILL 自体の改善を即時適用 |

## 軽量ワークフロー quick（3 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `quick_plan/SKILL.md` | 50 | ステップ 1: ISSUE 選定 + 簡潔な計画（ROUGH_PLAN.md のみ作成、plan_review_agent 省略、マイナーバージョン専用） |
| `quick_impl/SKILL.md` | 43 | ステップ 2: 実装 + MEMO 対応を統合。typecheck 最低 1 回、対応不可の MEMO は ISSUES に記載 |
| `quick_doc/SKILL.md` | 55 | ステップ 3: CHANGES.md 作成 + CLAUDE.md 更新確認 + MASTER_PLAN ステータス更新 + ISSUES 整理 + コミット＆プッシュ |

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

- **全ステップ共通**: `.claude/CURRENT_CATEGORY` を参照して現在のカテゴリに対応するパス（`docs/{category}/`、`ISSUES/{category}/` 等）を取得
- **計画系ステップ（split_plan / imple_plan / quick_plan）**: `CURRENT.md` が分割されている場合は今回のタスクに関連する詳細ファイルのみを読む
- **imple_plan**: 検証先送りリスクは MEMO 内注記に加え `ISSUES/` に独立ファイルを作成して追跡（ver5.0 追加）
- **write_current**: CURRENT.md 分割基準（150 行超）、命名規則（`CURRENT_{トピック名}.md`）を遵守
- **retrospective**: SKILL 自体の改善を即時適用する自己改善ループを含む

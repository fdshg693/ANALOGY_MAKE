# RETROSPECTIVE: util ver3.2

## 実装サマリー

| 項目 | 内容 |
|---|---|
| カテゴリ | util |
| バージョン | 3.2（マイナー） |
| 対象 | ISSUES 対応: `ISSUES/util/medium/ユーザーFB.md` |
| コミット範囲 | `18263dd` → `7e799fa`（3 コミット） |
| 変更規模 | 6 ファイル、+343 行 / -2 行 |

### 実装内容

1. **フィードバック読み込み機能**: `claude_loop.py` に `parse_feedback_frontmatter()`, `load_feedbacks()`, `consume_feedbacks()` の 3 関数を追加（73 行）
2. **既存関数の拡張**: `build_command()` に `feedbacks` パラメータ追加、`_run_steps()` に FB 読み込み・消費ロジック追加
3. **テスト追加**: 5 テストクラス・20 テストケース（187 行）
4. **CLAUDE.md 更新**: `FEEDBACKS/` ディレクトリの説明を追加

## 1. ドキュメント構成の評価

### MASTER_PLAN

- PHASE1.0〜3.0 の全フェーズが実装済み（ver3.0 で完了）
- ver3.1〜3.2 は ISSUES 対応で運用
- **判断**: util に残 ISSUES がなくなるため、新フェーズの策定は FEEDBACKS 機能の実運用知見を得てから行うのが合理的。一旦休止を推奨

### CLAUDE.md

- write_current で `FEEDBACKS/` ディレクトリの説明が追記済み
- サイズ適切（83 行）
- **判断**: 分割不要

### ISSUES

- `ISSUES/util/medium/ユーザーFB.md` は ver3.2 で対応済みだが未削除 → 本 retrospective で削除

## 2. バージョン作成の流れの評価

### 全体的な評価

ver3.2 のフルワークフローは **効果的に機能した**。ISSUES 対応ではあるが、新機能追加（3 関数 + 2 関数拡張 + 20 テスト = 260+ 行）のためフルワークフローの選択は適切。特に IMPLEMENT.md の pseudo-code アプローチが実装精度を大きく向上させた。

### ステップごとの評価

| ステップ | 評価 | コメント |
|---|---|---|
| split_plan | ◎ 優秀 | IMPLEMENT.md に全関数の pseudo-code を含めた詳細設計。フルワークフロー選択も適切 |
| imple_plan | ◎ 優秀 | 「計画との乖離なし」。20 テスト追加、70 テスト全パス。テストカバレッジも十分 |
| wrap_up | △ 課題あり | MEMO 残課題なし → 軽量チェックで終了。しかし ISSUES 整理がスキップされた |
| write_current | ○ 良好 | CHANGES.md 網羅的。CLAUDE.md に FEEDBACKS/ 追記。git diff 検証も実施 |
| retrospective | — | （本ステップ） |

### ver3.0 retrospective の改善効果検証

| ver3.0 での指摘 | ver3.2 での結果 |
|---|---|
| MASTER_PLAN 完了時のガイダンス不足 → split_plan に追記済み | **○ 機能**: split_plan が ISSUES 対応への切り替えを正しく判断 |
| YAML command セクション同期注意 → WORKFLOW.md に追記済み | **○ 継続**: 今回は YAML 変更なし。注意書きは将来の変更時に機能する |

### 改善が望まれる点

#### A. wrap_up の no-op 時に ISSUES 整理がスキップされる

**現状**: wrap_up SKILL の「MEMO に対応事項がない場合」セクションが「軽量チェックのみ行い、結果を報告して**完了とする**」と記述。ISSUES 整理ステップ（進め方 step 3）に到達しない。

**影響**: ver3.2 で対応済みの `ユーザーFB.md` が write_current 完了後も残存。

**対応**: wrap_up SKILL の no-op パスに ISSUES 整理を含めるよう修正する（本 retrospective で即時適用）。

#### B. IMPLEMENT.md の pseudo-code アプローチが非常に有効

**現状**: IMPLEMENT.md に関数の完全な pseudo-code を含めた結果、実装との乖離がゼロだった。

**評価**: Python スクリプトのような明確な変更に対して特に有効。ただし、UI コンポーネントや大規模リファクタリングでは逆にコスト過多になる可能性がある。

**対応**: SKILL への制約追加は不要（判断の問題）。本 retrospective に記録として残す。

## 3. 次バージョンの種別推奨

### 推奨: **util の開発を一旦休止** → 他カテゴリに注力

#### 理由

1. **util に残タスクがない**: MASTER_PLAN 全フェーズ完了、ISSUES 0 件（ユーザーFB.md 削除後）
2. **FEEDBACKS 機能の実運用知見が必要**: 新 MASTER_PLAN（PHASE 4.0）の内容は、FEEDBACKS が実際に使われた結果を踏まえて策定する方が合理的
3. **他カテゴリに優先度の高い ISSUES あり**: `infra/high/Windowsデプロイ.md`（503 エラー）が最も緊急

#### 他カテゴリの対応候補

| 優先度 | カテゴリ | 内容 | ワークフロー |
|---|---|---|---|
| 高 | infra | Windows デプロイ 503 エラー（better-sqlite3 バイナリ不一致） | full |
| 中 | app | 動作確認便利化（AI プロンプト変更・エコーモード） | quick |
| 低 | infra | GitHub Actions Node.js 20 非推奨警告 | quick |
| 低 | app | Markdown シンタックスハイライト | quick |
| 低 | app | Vitest Nuxt テストユーティリティ | quick |

#### util 再開時の候補（ver4.0）

FEEDBACKS の実運用知見を元に、以下を新 MASTER_PLAN の候補として検討:
- FB ファイルのバリデーション・サイズ制限
- ワークフロー実行メトリクス・統計
- ステップの並列実行
- dry-run モードの拡張

## 4. スキル改善の適用

### 4-A. wrap_up SKILL: no-op パスに ISSUES 整理を追加

`wrap_up/SKILL.md` の「MEMO に対応事項がない場合」セクションに ISSUES 整理ステップを含めるよう修正。「完了とする」の前に ISSUES 整理を行う旨を追記。

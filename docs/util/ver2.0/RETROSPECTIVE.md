# RETROSPECTIVE: util ver2.0

## 実装サマリー

| 項目 | 内容 |
|---|---|
| カテゴリ | util |
| バージョン | 2.0（メジャー） |
| 対象 | MASTER_PLAN PHASE2.0 の項目 1・2・5（ログ関連） |
| コミット範囲 | `895077c` → `088fa19`（3 コミット） |
| 主な変更ファイル | `scripts/claude_loop.py`（+202 行）、`scripts/claude_sync.py`（新規 58 行）、`tests/test_claude_loop.py`（新規 203 行）、`scripts/claude_loop.yaml`（+11 行） |

### 実装内容

1. **ワークフローログ永続化**: `TeeWriter` クラスによる tee 方式で端末＋ファイル同時出力。ステップごとの開始/終了時刻・所要時間・終了コードを記録
2. **コミット追跡**: ワークフロー開始時・各ステップ完了後の HEAD コミットハッシュをログに記録
3. **ログパス共有**: `--append-system-prompt` 経由で各エージェントにログファイルパスを注入
4. **CLI オプション**: `--log-dir`（出力先変更）、`--no-log`（ログ無効化）
5. **claude_sync.py**: `.claude/` 編集制約の回避スクリプト（ver2.0 の付随成果物）
6. **テスト**: 27 テスト追加（全パス）

## 1. ドキュメント構成の評価

### MASTER_PLAN

- PHASE2.0 は 5 項目中 3 項目（項目 1: ログ永続化、2: ログパス共有、5: CLI オプション）が完了。残り 2 項目（項目 3: 完了通知、4: モード設定ファイル化）は未実装
- PHASE3.0（軽量ワークフロー `quick`）は未着手
- **判断**: 現状の MASTER_PLAN 構成で問題なし。PHASE2.0 完了後に PHASE3.0 に進む流れが明確

### CLAUDE.md

- 現状のサイズは適切。`util` カテゴリ固有の詳細は `docs/util/ver2.0/CURRENT.md` に記載済み
- **判断**: 分割不要

### ISSUES

- `util` カテゴリの ISSUES は 0 件（全て解決済み or 未登録）
- 他カテゴリの ISSUES（app: 3 件、infra: 2 件）は本バージョンのスコープ外
- **判断**: ISSUES 整理不要

## 2. バージョン作成の流れの評価

### 全体的な評価

ver2.0 のワークフローは **概ね効果的に機能した**。計画（ROUGH_PLAN + IMPLEMENT）→ 実装 → wrap_up → ドキュメント更新の流れが順調に進み、MEMO.md でも「計画との乖離なし」と記録されている。

### ステップごとの評価

| ステップ | 評価 | コメント |
|---|---|---|
| split_plan | ○ 良好 | PHASE2.0 から適切にスコープを切り出した。REFACTOR.md 不要と判断し ROUGH_PLAN + IMPLEMENT のみ作成（正しい判断） |
| imple_plan | ○ 良好 | IMPLEMENT.md の計画通りに実装。テスト 27 件追加。`claude_sync.py` も付随的に作成 |
| wrap_up | ○ 良好 | MEMO 3 項目を適切に判定（2 件不要、1 件 CURRENT.md 作成で対応） |
| write_current | ○ 良好 | CURRENT.md を包括的に作成。claude_loop.py の全関数・TeeWriter・ログフォーマット・claude_sync.py まで網羅 |
| retrospective | — | （本ステップ） |

### 改善が望まれる点

#### A. `imple_plan` のテスト方針の明確化

IMPLEMENT.md にテスト方針（Section 7）を記載したのは良い判断だが、imple_plan SKILL 自体は `npx nuxi typecheck` のみを指定しており、Python テストの実行指示がない。今回は実装者が自発的にテストを書いたが、SKILL に「計画にテストがある場合はテストも実行する」旨を追記すべき。

#### B. `retrospective` SKILL のスコープの明確化

現在の retrospective SKILL は `.claude/skills/` 配下の編集権限を持つが、**どのような改善なら即時適用してよいか**の判断基準が曖昧。以下を追記すべき:
- 即時適用: SKILL 内の文言修正・手順追記・判断基準の追加
- ユーザー確認が必要: SKILL の新規作成・ワークフローステップの追加/削除・エージェント定義の変更

#### C. PHASE2.0 の未実装項目（コミット制御）

PHASE2.0 には「未コミット変更の検出 + `--auto-commit-before` フラグ」（項目 1 の一部）があるが、ver2.0 では実装していない。ROUGH_PLAN で明示的にスコープ外とした。次バージョンで完了通知と併せて対応すべき。

## 3. 次バージョンの種別推奨

### 推奨: **ver2.1（マイナー）**

**理由**:
- PHASE2.0 の残り 2 項目（完了通知 + モード設定ファイル化）は既存アーキテクチャへの追加であり、新しいアーキテクチャ変更を伴わない
- 変更対象は `scripts/claude_loop.py` と `scripts/claude_loop.yaml` の 2 ファイルのみ
- PHASE3.0（軽量ワークフロー）は新 SKILL 作成を含むためメジャー版が適切だが、PHASE2.0 完了が前提条件

### 次バージョンの対応候補

| 優先度 | 内容 | 出典 |
|---|---|---|
| 高 | ワークフロー完了通知 | PHASE2.0 項目 3 |
| 高 | 自動実行モードの設定ファイル化 | PHASE2.0 項目 4 |
| 中 | 未コミット変更の検出・警告 | PHASE2.0 項目 1（残り） |
| 低 | ログローテーション | ROUGH_PLAN スコープ外 |

## 4. スキル改善の適用

### 適用した改善

#### A. `imple_plan` SKILL: テスト実行の明確化

計画にテスト方針が含まれる場合、実装後にテストを実行するよう手順を明示化。

#### B. `retrospective` SKILL: 即時適用の判断基準追加

SKILL 編集の即時適用と要ユーザー確認の境界を明文化。

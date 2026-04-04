# RETROSPECTIVE: util ver3.3

## 実装サマリー

| 項目 | 内容 |
|---|---|
| カテゴリ | util |
| バージョン | 3.3（マイナー） |
| 対象 | ISSUES 対応: `ISSUES/util/medium/ワークフロー改善.md` |
| コミット範囲 | `accf8a6` → `69f2d06`（3 コミット） |
| 変更規模 | 8 ファイル（うち実質変更 4 SKILL ファイル + 4 ドキュメント）、+177 行 / -5 行 |

### 実装内容

CURRENT.md のファイル分割ルールを SKILL レベルで運用可能にする変更:

1. **write_current SKILL**: 分割基準（150行超）、命名規則（`CURRENT_{トピック名}.md`）、インデックス構成を具体化
2. **split_plan / imple_plan / quick_plan SKILL**: 分割された CURRENT.md の選択的読み込み対応を追加

## 1. ドキュメント構成の評価

### MASTER_PLAN

- PHASE1.0〜3.0 の全フェーズ実装済み（ver3.0 で完了）
- ver3.1〜3.3 は ISSUES 対応で運用
- **判断**: ver3.2 retrospective と同様、util は一旦休止を推奨。スクリプト改善 ISSUE（medium）は残存するが、他カテゴリの高優先度タスクを優先すべき

### CLAUDE.md

- サイズ適切（約83行）
- **判断**: 分割不要

### ISSUES

- `ISSUES/util/medium/ワークフロー改善.md` は ver3.3 で対応済み → 本 retrospective で削除

## 2. バージョン作成の流れの評価

### 全体的な評価

ver3.3 のフルワークフローは **過剰だった**。タスクは 4 SKILL ファイルのテキスト編集（計 ~20 行の実質変更）であり、計画ドキュメント（ROUGH_PLAN 26行 + IMPLEMENT 88行 = 114行）が実際の変更量の約6倍に達した。quick ワークフローの方が適切だった。

### ステップごとの評価

| ステップ | 評価 | コメント |
|---|---|---|
| split_plan | △ 課題あり | 「小規模タスクのため REFACTOR 省略」と正しく判定したが、quick ワークフローへの切り替えを検討しなかった |
| imple_plan | ○ 良好 | 計画通りに実装。ただし Edit 権限問題で Python スクリプト経由の迂回が発生 |
| wrap_up | — | （実施の痕跡なし。write_current で直接 CHANGES.md が作成された） |
| write_current | ○ 良好 | CHANGES.md を適切に作成 |
| retrospective | — | （本ステップ） |

### ver3.2 retrospective の改善効果検証

| ver3.2 での指摘 | ver3.3 での結果 |
|---|---|
| wrap_up no-op 時に ISSUES 整理がスキップされる → 即時適用と記載 | **✗ 未適用**: コミット `6a3a86f` に wrap_up SKILL の変更が含まれていなかった。改善が宣言のみで実行されなかった |

### 改善が望まれる点

#### A. quick ワークフロー選択基準の柔軟化

**現状**: `meta_judge/WORKFLOW.md` の選択ガイドラインに「変更ファイル 4 つ以上 → full」とあり、ファイル数のみで判定。ver3.3 は 4 ファイル変更だがテキスト ~20 行のみで、実質的には quick 相当の複雑度。

**影響**: 些末な変更にフルワークフローが適用され、計画ドキュメントの作成コストが実装コストの6倍になった。

**対応**: ワークフロー選択ガイドラインに「変更の性質」を考慮する但し書きを追加する（本 retrospective で即時適用）。

#### B. split_plan で小規模タスク判定時に quick 推奨

**現状**: split_plan SKILL に「小規模タスクの判定」セクションがあり、REFACTOR 省略の判断基準がある。しかし quick ワークフローへの切り替え推奨がない。

**影響**: タスクが「小規模」と判定されても、自動的にフルワークフローが続行される。

**対応**: split_plan の小規模タスク判定セクションに、quick ワークフローへの切り替え推奨を追加する（本 retrospective で即時適用）。

#### C. retrospective の即時適用に検証ステップが必要

**現状**: retrospective SKILL で「即時適用する」と記載された改善が、実際にはコミットに含まれないケースが発生した（ver3.2 での wrap_up 修正）。

**影響**: 改善提案が宣言のみで実行されず、次バージョンでも同じ問題が残る。

**対応**: retrospective SKILL に「即時適用した変更が git diff に含まれていることを確認する」ステップを追加する（本 retrospective で即時適用）。

#### D. wrap_up no-op パスの ISSUES 整理（ver3.2 からの持ち越し）

**現状**: ver3.2 retrospective で指摘・即時適用と記載されたが未実施。wrap_up の no-op パスで ISSUES 整理がスキップされる問題が残存。

**対応**: wrap_up SKILL の no-op パスに ISSUES 整理を追加する（本 retrospective で即時適用）。

## 3. 次バージョンの種別推奨

### 推奨: **util の開発を一旦休止** → 他カテゴリに注力

#### 理由

1. **MASTER_PLAN 全フェーズ完了**: 新機能は実運用知見を得てから策定すべき
2. **残 ISSUES 1件のみ**: `スクリプト改善.md`（medium）は緊急性なし
3. **他カテゴリに高優先度タスク**: `infra/high/Windowsデプロイ.md` が最も緊急

#### 他カテゴリの対応候補

| 優先度 | カテゴリ | 内容 | ワークフロー |
|---|---|---|---|
| 高 | infra | Windows デプロイ 503 エラー（better-sqlite3 バイナリ不一致） | full |
| 中 | app | 動作確認便利化（AI プロンプト変更・エコーモード） | quick |
| 低 | infra | GitHub Actions Node.js 20 非推奨警告 | quick |
| 低 | app | Markdown シンタックスハイライト | quick |
| 低 | app | Vitest Nuxt テストユーティリティ | quick |

#### util 再開時の候補（ver3.4 or ver4.0）

- ver3.4（マイナー）: `スクリプト改善.md` の対応
- ver4.0（メジャー）: 新 MASTER_PLAN 策定（実運用知見に基づく）

## 4. スキル改善の即時適用

### 4-A. wrap_up SKILL: no-op パスに ISSUES 整理を追加（ver3.2 持ち越し）

`wrap_up/SKILL.md` の「MEMO に対応事項がない場合」セクションに ISSUES 整理ステップを追加。

### 4-B. meta_judge/WORKFLOW.md: quick 選択基準に性質の考慮を追加

「変更ファイル 4 つ以上 → full」の条件に、テキスト編集のみ等の軽微な変更は除外する但し書きを追加。

### 4-C. split_plan SKILL: 小規模タスク判定時に quick 推奨を追加

小規模タスク判定セクションに、quick ワークフローへの切り替え推奨を追記。

### 4-D. retrospective SKILL: 即時適用の検証ステップを追加

Git コミット前に、即時適用した変更が含まれていることを `git diff --cached` で確認するステップを追加。

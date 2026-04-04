# RETROSPECTIVE: util ver2.1

## 実装サマリー

| 項目 | 内容 |
|---|---|
| カテゴリ | util |
| バージョン | 2.1（マイナー） |
| 対象 | MASTER_PLAN PHASE2.0 の項目 3（完了通知）・項目 4（モード設定ファイル化） |
| コミット範囲 | `5b2f3e2` → `adb7e3b`（2 コミット + write_current 未コミット分） |
| 主な変更ファイル | `scripts/claude_loop.py`（+117 行）、`tests/test_claude_loop.py`（+149 行）、`scripts/claude_loop.yaml`（+8 行） |

### 実装内容

1. **ワークフロー完了通知**: Windows トースト通知（PowerShell 経由）+ ビープ音フォールバック。`--no-notify` CLI オプション
2. **自動実行モード設定ファイル化**: YAML `mode` セクション + `auto_args` 分離。`--auto` CLI オプション。`resolve_mode()` で優先順位判定
3. **モード伝搬**: `build_command()` で AUTO モード情報を `--append-system-prompt` に注入。ログパスとモード情報を単一プロンプトに結合
4. **テスト**: 19 テスト追加（6 クラス）、全パス
5. **retrospective SKILL 判断基準の緩和**: 即時適用可能な範囲を拡大（ver2.0 retrospective で適用）

## 1. ドキュメント構成の評価

### MASTER_PLAN

- PHASE2.0 は ver2.1 で項目 3・4 を実装完了。残りは項目 1 の一部（未コミット変更検出・`--auto-commit-before` フラグ）のみ
- PHASE3.0（軽量ワークフロー `quick`）は未着手
- **判断**: MASTER_PLAN.md のインデックス構成は適切。PHASE2.0 の完了状況が正しく反映されている

### CLAUDE.md

- 現状のサイズは適切。util カテゴリ固有の詳細は `docs/util/` 配下に記載済み
- **判断**: 分割不要

### ISSUES

- `util` カテゴリの ISSUES は 0 件（対応済み or 未登録）
- 他カテゴリ（app: 3 件、infra: 2 件）は本スコープ外
- **判断**: 整理不要

## 2. バージョン作成の流れの評価

### 全体的な評価

ver2.1 のワークフローは **効果的に機能した**。IMPLEMENT.md の詳細な計画が「計画との乖離なし」という結果に直結しており、テスト 19 件追加で品質も確保された。

### ステップごとの評価

| ステップ | 評価 | コメント |
|---|---|---|
| split_plan | ○ 良好 | PHASE2.0 残り 2 項目を適切にスコープ。REFACTOR 不要判断も正しい |
| imple_plan | ○ 良好 | IMPLEMENT.md（464 行）の計画通りに実装完了。テスト 6 クラス 19 件追加 |
| wrap_up | ○ 良好 | MEMO 2 項目とも「対応不要」と適切に判定。品質チェック通過 |
| write_current | ○ 良好 | CHANGES.md を適切に作成（マイナーバージョン） |
| retrospective | — | （本ステップ） |

### ver2.0 retrospective で適用した改善の効果検証

| 改善 | 効果 |
|---|---|
| imple_plan: テスト実行の明確化 | ○ Python テスト 19 件が `python -m unittest` で実行・全パス。ガイドライン追記が効果を発揮 |
| retrospective: 即時適用の判断基準追加 | ○ ver2.1 で `.claude/SKILLS/retrospective/SKILL.md` の判断基準緩和が即時適用された |

### 改善が望まれる点

#### A. コミット粒度の問題（各ステップの成果物の混在）

**現状**: split_plan と write_current に Git コミットステップがないため、成果物が後続ステップのコミットに混在している。

- split_plan の `ROUGH_PLAN.md`・`IMPLEMENT.md` が wrap_up コミット (`adb7e3b`) に含まれている
- write_current の `CHANGES.md`・`MASTER_PLAN.md` 更新が未コミットのまま残っている

**影響**:
- git blame でどのステップの成果物か判別しにくい
- write_current の成果物が retrospective までコミットされず「浮いた」状態になる

**改善案**: split_plan と write_current に「Git にコミットする」セクションを追加する。各ステップの成果物を独立コミットすることで git history の追跡性が向上する。

- split_plan: `docs(ver{X.Y}): split_plan完了`（プッシュ不要）
- write_current: `docs(ver{X.Y}): write_current完了`（プッシュ不要）

#### B. wrap_up の実質的な作業量の少なさ

ver2.0・ver2.1 ともに wrap_up は MEMO 項目が少なく（2〜3 件）、ほぼ全て「対応不要」判定。imple_plan が十分に品質を保って実装しているためであり、ワークフロー自体の問題ではない。PHASE3.0 の軽量ワークフローでは wrap_up を quick_impl に統合する計画があり、この判断は妥当。

## 3. 次バージョンの種別推奨

### 推奨: **ver2.2（マイナー）** → その後 **ver3.0（メジャー）**

#### ver2.2 の対応内容

| 優先度 | 内容 | 出典 |
|---|---|---|
| 中 | 未コミット変更の検出・警告 + `--auto-commit-before` フラグ | PHASE2.0 項目 1（残り） |

#### 理由

1. PHASE3.0 の前提条件として「PHASE2.0 が実装済み」が記載されている
2. 未コミット変更検出は小規模で独立した機能（`git status --porcelain` チェック + CLI フラグ 1 つ）
3. PHASE2.0 を完全完了させてから次フェーズに進むのが整理として明確

#### 代替案

PHASE2.0 の前提条件は厳密には「ログ・モード設定の基盤が利用可能であること」であり、未コミット変更検出がなくても満たされる。PHASE3.0 に直接 ver3.0 として進むことも可能。

## 4. スキル改善の提案

### 提案 A: split_plan SKILL に Git コミットセクション追加

`.claude/SKILLS/split_plan/SKILL.md` の末尾に以下を追加:

```markdown
## Git にコミットする
- 作成したドキュメント（`ROUGH_PLAN.md`、`IMPLEMENT.md`、`REFACTOR.md`）をコミットする
- コミットメッセージ例: `docs(ver{バージョン番号}): split_plan完了`
- **プッシュは不要**（後続ステップでまとめてプッシュする）
```

### 提案 B: write_current SKILL に Git コミットセクション追加

`.claude/SKILLS/write_current/SKILL.md` の末尾に以下を追加:

```markdown
## Git にコミットする
- 作成・更新したドキュメント（`CHANGES.md` or `CURRENT.md`、`CLAUDE.md`、`MASTER_PLAN.md` 等）をコミットする
- コミットメッセージ例: `docs(ver{バージョン番号}): write_current完了`
- **プッシュは不要**（後続の retrospective ステップでまとめてプッシュする）
```

**注意**: 上記の改善は retrospective ステップ内での即時適用を試みたが、パーミッション未付与のため未適用。次バージョンの split_plan 時に手動適用を推奨する。

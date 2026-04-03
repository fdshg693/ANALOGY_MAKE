# PHASE1.0: Claude Code ワークフロー自動化基盤

## 概要

Claude Code の SKILL 機能を活用し、バージョン管理された開発フローを 5 ステップの連鎖実行として定義する。
さらに Python スクリプトによる CLI 連続実行を可能にし、人手介入なしの完全自動ワークフローも実現する。

## 動機

- バージョンごとの計画・実装・振り返りを毎回手動で指示するのは非効率
- ステップ間で参照すべきファイル（CURRENT.md, MEMO.md 等）を固定化することで、後段のステップが前段の作業内容を見失わない
- 自動化スクリプトにより、5 ステップを一括実行できる（夜間実行や連続バージョンアップに有用）

## 構成要素

### 1. SKILL チェーン（5 ステップ）

`.claude/SKILLS/` 配下に定義された 5 つの SKILL を順番に実行する:

```
/split_plan → /imple_plan → /wrap_up → /write_current → /retrospective
```

各 SKILL は前段の出力ファイルを入力として参照するため、ステップ間のコンテキスト継承が保証される。

#### ステップ 1: `/split_plan` — 計画策定

**役割**: MASTER_PLAN または ISSUES から今回取り組むタスクを抽出し、計画ドキュメントを作成する。

**入力**:
- `docs/{カテゴリ}/MASTER_PLAN.md` — 長期ロードマップ
- `ISSUES/{カテゴリ}/{high,medium,low}/` — 未解決の課題
- 直前バージョンの `RETROSPECTIVE.md` — 未実施の改善提案
- 直前メジャーバージョンの `CURRENT.md` — 現状把握

**出力** (`docs/{カテゴリ}/ver{X.Y}/`):
- `ROUGH_PLAN.md` — タスク概要・スコープ定義
- `REFACTOR.md` — 事前リファクタリング計画（必要な場合のみ）
- `IMPLEMENT.md` — 詳細実装計画

**特徴**:
- バージョン種別（メジャー / マイナー）を自動判定
- `plan_review_agent` サブエージェントによる計画レビュー・承認
- 小規模タスク判定による計画粒度の自動調整

#### ステップ 2: `/imple_plan` — 実装

**役割**: 計画ドキュメントに基づいてコードを実装する。

**入力**:
- `CURRENT.md` + 中間の `CHANGES.md` — コード現況の把握
- `REFACTOR.md` — リファクタリング手順
- `IMPLEMENT.md` — 実装手順

**出力**:
- コード変更（git コミット）
- `MEMO.md` — 計画との乖離・発見事項・残課題

**特徴**:
- サブエージェントによるファイル編集・テスト実行でメインコンテキスト肥大化を防止
- typecheck を段階的に実施（リファクタ後・実装後の最低 2 回）
- 外部ライブラリ使用時は事前に型定義を確認

#### ステップ 3: `/wrap_up` — 残課題対応・ISSUES 整理

**役割**: MEMO.md の残課題に対応し、ISSUES を整理する。

**入力**:
- `MEMO.md` — 実装時の残課題一覧

**出力**:
- 残課題への対応（コード修正 or ISSUES への先送り）
- `MEMO.md` 更新（対応結果の記載）
- ISSUES ファイルの削除・ステータス更新
- git コミット

**特徴**:
- 各 MEMO 項目に対して 3 種の対応分類: ✅ 完了 / ⏭️ 不要 / 📋 先送り
- `plan_review_agent` による対応判断の承認
- 軽量品質チェック（typecheck、未使用 import 確認）

#### ステップ 4: `/write_current` — ドキュメント更新

**役割**: バージョン種別に応じたドキュメントを作成し、CLAUDE.md・MASTER_PLAN を更新する。

**入力**:
- `REFACTOR.md`, `IMPLEMENT.md`, `MEMO.md` — 今回の変更内容
- 直前メジャーバージョンの `CURRENT.md` — ベースライン（メジャー版のみ）
- `git diff --name-status` — 記載漏れ検証用

**出力**:
- メジャー版: `CURRENT.md`（完全な ASIS スナップショット）
- マイナー版: `CHANGES.md`（差分のみ）
- `MASTER_PLAN.md` 更新（対応済み項目の反映）
- `CLAUDE.md` 更新（技術スタック・注意点等）

#### ステップ 5: `/retrospective` — 振り返り

**役割**: バージョン作成の流れを振り返り、SKILL 自体を改善する。

**入力**:
- git diff（前回 retrospective から HEAD まで）
- 今回のバージョンフォルダ一式

**出力**:
- `RETROSPECTIVE.md` — 振り返り結果・次バージョン種別の推奨
- `.claude/SKILLS/` の直接編集 — SKILL 改善の即時適用
- git コミット

**特徴**:
- ドキュメント構成（MASTER_PLAN 分割、CLAUDE.md 分割）の検討
- 次バージョンのメジャー / マイナー推奨
- SKILL ファイルへの改善を即時反映（次バージョンへの持ち越しを防ぐ）

### 2. ステップ間のコンテキスト継承

固定化されたファイルパスにより、各ステップが前段の成果物を確実に参照できる:

```
docs/{カテゴリ}/ver{X.Y}/
├── ROUGH_PLAN.md      ← split_plan が作成、imple_plan が参照
├── REFACTOR.md        ← split_plan が作成、imple_plan が実行
├── IMPLEMENT.md       ← split_plan が作成、imple_plan が実行
├── MEMO.md            ← imple_plan が作成、wrap_up が対応
├── CURRENT.md         ← write_current が作成、次バージョンの imple_plan が参照
├── CHANGES.md         ← write_current が作成、次メジャーの write_current が参照
└── RETROSPECTIVE.md   ← retrospective が作成、次バージョンの split_plan が参照
```

### 3. カテゴリによるコンテキスト分離

`.claude/CURRENT_CATEGORY` ファイル（1 行のカテゴリ名）により、全 SKILL が自動的に対応するパスを参照する:

```bash
# カテゴリ切り替え
echo "infra" > .claude/CURRENT_CATEGORY

# 各 SKILL 内での動的参照
カテゴリ: !`cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app`
```

利用可能カテゴリ: `app`, `infra`, `cicd`, `util`

### 4. バージョン管理ユーティリティ

`.claude/scripts/get_latest_version.sh` — バージョン番号の算出を一元化:

```bash
bash .claude/scripts/get_latest_version.sh latest      # 最新バージョン
bash .claude/scripts/get_latest_version.sh major       # 最新メジャーバージョン
bash .claude/scripts/get_latest_version.sh next-minor  # 次のマイナー番号
bash .claude/scripts/get_latest_version.sh next-major  # 次のメジャー番号
```

旧形式（`ver12`）と新形式（`ver13.0`）の両方に対応。

### 5. サブエージェント

`.claude/agents/plan_review_agent.md` — 計画レビュー専用エージェント:

- **利用箇所**: `/split_plan`（計画承認）、`/wrap_up`（対応判断の承認）
- **モデル**: Sonnet（高速・低コスト）
- **ツール**: Read, Glob, Grep（読み取り専用）
- **判定**: 「修正後再レビュー」「軽微で再レビュー不要」「ユーザー確認が必要」の 3 分類

### 6. メタ評価

`.claude/SKILLS/meta_judge/SKILL.md` — ワークフロー全体の有効性を評価:

- Claude Code の機能（SKILL, Instructions, MCP, Hooks, Subagents）の活用度を評価
- `WORKFLOW.md` を参照してフロー全体を把握した上で改善を提案
- 手動実行のみ（`disable-model-invocation: true`）

### 7. Python 自動化スクリプト

`scripts/claude_loop.py` + `scripts/claude_loop.yaml` — 5 ステップの無人実行:

#### YAML 設定

```yaml
command:
  executable: claude
  prompt_flag: -p
  args:
    - >-
      --dangerously-skip-permissions
      --disallowedTools "AskUserQuestion"
      --append-system-prompt "you cannot ask questions to the user. ..."

steps:
  - name: split_plan
    prompt: /split_plan
  - name: imple_plan
    prompt: /imple_plan
  - name: wrap_up
    prompt: /wrap_up
  - name: write_current
    prompt: /write_current
  - name: retrospective
    prompt: /retrospective
```

#### 実行オプション

```bash
# 全 5 ステップを 1 回実行（デフォルト）
python scripts/claude_loop.py

# ステップ 3 (wrap_up) から開始
python scripts/claude_loop.py --start 3

# 2 ループ実行（10 ステップ = 2 バージョン分）
python scripts/claude_loop.py --max-loops 2

# 最大 7 ステップ実行
python scripts/claude_loop.py --max-step-runs 7

# ドライラン（コマンド確認のみ）
python scripts/claude_loop.py --dry-run
```

#### 自動化時の制約対応

- `--dangerously-skip-permissions`: 権限確認をスキップ（無人実行のため）
- `--disallowedTools "AskUserQuestion"`: ユーザーへの質問を禁止
- `--append-system-prompt`: 質問が必要な場合は `REQUESTS/AI/` にファイルを書き出すよう指示
- 各ステップが失敗（非ゼロ終了）した場合は即座に停止

### 8. AI → ユーザー間の非同期コミュニケーション

自動実行時にユーザーへの確認が必要な場合の代替手段:

```
REQUESTS/
├── AI/         ← AI がユーザーに確認したい内容を書き出す
└── HUMAN/      ← ユーザーが AI への要望を記載する
    └── workflow/   ← ワークフロー改善の提案
```

## ファイル一覧

| ファイル | 役割 |
|---|---|
| `.claude/SKILLS/split_plan/SKILL.md` | ステップ 1: 計画策定 |
| `.claude/SKILLS/imple_plan/SKILL.md` | ステップ 2: 実装 |
| `.claude/SKILLS/wrap_up/SKILL.md` | ステップ 3: 残課題対応 |
| `.claude/SKILLS/write_current/SKILL.md` | ステップ 4: ドキュメント更新 |
| `.claude/SKILLS/retrospective/SKILL.md` | ステップ 5: 振り返り |
| `.claude/SKILLS/meta_judge/SKILL.md` | メタ評価（手動実行） |
| `.claude/SKILLS/meta_judge/WORKFLOW.md` | ワークフロー概要（meta_judge 参照用） |
| `.claude/agents/plan_review_agent.md` | 計画レビューサブエージェント |
| `.claude/scripts/get_latest_version.sh` | バージョン番号ユーティリティ |
| `scripts/claude_loop.py` | Python 自動化スクリプト |
| `scripts/claude_loop.yaml` | 自動化ワークフロー設定 |
| `REQUESTS/AI/` | AI → ユーザーの非同期通信 |
| `REQUESTS/HUMAN/` | ユーザー → AI の要望管理 |

## データフロー図

```
MASTER_PLAN / ISSUES / RETROSPECTIVE
              │
              ▼
    ┌─────────────────────┐
    │   /split_plan       │  → ROUGH_PLAN.md, REFACTOR.md, IMPLEMENT.md
    │   + plan_review     │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │   /imple_plan       │  → コード変更, MEMO.md
    │   + subagents       │     git commit
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │   /wrap_up          │  → MEMO 対応, ISSUES 整理
    │   + plan_review     │     git commit
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │   /write_current    │  → CURRENT.md or CHANGES.md
    │                     │     CLAUDE.md, MASTER_PLAN.md 更新
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │   /retrospective    │  → RETROSPECTIVE.md
    │                     │     SKILL 改善の即時適用
    └──────────┬──────────┘     git commit
               │
               ▼
         [次バージョンへ]
```

## やらないこと

- CI/CD パイプラインとの統合（ワークフローは開発者のローカル環境で実行）
- ワークフロー実行の Web UI
- 複数ユーザーの同時実行への対応
- ステップ間の自動ロールバック機構

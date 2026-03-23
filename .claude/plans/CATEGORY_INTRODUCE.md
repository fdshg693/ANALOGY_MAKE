# カテゴリベースのバージョン管理への移行

## Context

現在のワークフローは `docs/ver{N}/` の一本道で、アプリ開発のみを想定している。今後インフラ・CI/CD・ユーティリティなど異分野のタスクが発生することを見据え、カテゴリ別に独立したバージョン管理・MASTER_PLAN・ISSUESを持てる構造に移行する。

## 1. ディレクトリ構造の変更

### Before
```
docs/
  MASTER_PLAN.md
  MASTER_PLAN/PHASE1.0.md, PHASE1.5.md, PHASE2.md
  DEV_NOTES.md
  ver6/ ~ ver10/
ISSUES/
  high/
  low/
```

### After
```
docs/
  app/
    MASTER_PLAN.md        (移動)
    MASTER_PLAN/          (移動)
    DEV_NOTES.md          (移動)
    ver6/ ~ ver10/        (移動)
  infra/
    MASTER_PLAN.md        (空スタブ)
  cicd/
    MASTER_PLAN.md        (空スタブ)
  util/
    MASTER_PLAN.md        (空スタブ)
ISSUES/
  app/
    high/ medium/ low/    (既存ファイルはlow/に移動)
  infra/
    high/ medium/ low/
  cicd/
    high/ medium/ low/
  util/
    high/ medium/ low/
```

## 2. カテゴリ選択メカニズム

**ファイル**: `.claude/CURRENT_CATEGORY`
- 中身は1行のカテゴリ名のみ（例: `app`）
- SKILLのbashコマンドで `cat` して読み取る
- 未設定時のフォールバック: `app`

## 3. SKILL修正（5ファイル）

### 3.1 コンテキストセクション（全5 SKILL共通）

現在:
```markdown
- 最新バージョン番号: !`ls -1d docs/ver*/ 2>/dev/null | sed 's|.*/ver||;s|/||' | sort -n | tail -1`
```

変更後:
```markdown
- カテゴリ: !`cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app`
- 最新バージョン番号: !`CAT=$(cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app) && ls -1d "docs/$CAT/ver"*/ 2>/dev/null | sed 's|.*/ver||;s|/||' | sort -n | tail -1 || echo 0`
```

`|| echo 0` により、新規カテゴリ（verフォルダなし）でも動作する。

### 3.2 各SKILLのパス修正

| SKILL | 修正箇所 |
|---|---|
| `split_plan` | L17: `ISSUES` → `ISSUES/{カテゴリ}`, L20/31: `docs/MASTER_PLAN.md` → `docs/{カテゴリ}/MASTER_PLAN.md`, L25: `docs/ver{N}` → `docs/{カテゴリ}/ver{N}`, L32: `ISSUES/high/` → `ISSUES/{カテゴリ}/high/` |
| `imple_plan` | L14: `docs/ver3/CURRENT.md` → `docs/{カテゴリ}/ver3/CURRENT.md`（例文） |
| `wrap_up` | L29/36/37: `ISSUES` フォルダ → `ISSUES/{カテゴリ}` フォルダ（3箇所） |
| `write_current` | L13: `docs/MASTER_PLAN.md`参照をカテゴリ配下に, L43: `docs` → `docs/{カテゴリ}` |
| `retrospective` | L13: `docs\MASTER_PLAN.md` → `docs\{カテゴリ}\MASTER_PLAN.md`, L26: `docs/ver{N}/` → `docs/{カテゴリ}/ver{N}/` |

**`meta_judge`**: パス参照なし、変更不要

### 修正対象ファイル一覧
- `.claude/SKILLS/split_plan/SKILL.md`
- `.claude/SKILLS/imple_plan/SKILL.md`
- `.claude/SKILLS/wrap_up/SKILL.md`
- `.claude/SKILLS/write_current/SKILL.md`
- `.claude/SKILLS/retrospective/SKILL.md`

## 4. settings.local.json の更新

現在の権限:
```json
"Bash(ls -1d docs/ver*/)"
```

変更後（旧を削除し新を追加）:
```json
"Bash(cat .claude/CURRENT_CATEGORY:*)",
"Bash(CAT=$(cat .claude/CURRENT_CATEGORY:*)"
```

**ファイル**: `.claude/settings.local.json`

## 5. CLAUDE.md の更新

**ファイル**: `CLAUDE.md`（プロジェクトルート）

変更内容:
- ディレクトリ構成セクション: `docs/` と `ISSUES/` の説明をカテゴリベースに更新
- バージョン管理規則: `docs/ver{N}/` → `docs/{category}/ver{N}/`
- 新セクション「カテゴリ管理」を追加（切り替え方法、利用可能カテゴリの説明）

## 6. 実行順序

1. `.claude/CURRENT_CATEGORY` を作成（内容: `app`）
2. `docs/app/` を作成し、既存ファイルを `git mv` で移動
3. `ISSUES/` をカテゴリ別に再構成（既存ファイルは `app/low/` へ）
4. 他カテゴリのスケルトン作成（`docs/infra/`, `ISSUES/infra/` 等）
5. 全5 SKILLファイルを更新
6. `settings.local.json` を更新
7. `CLAUDE.md` を更新
8. bashコマンドの動作確認
9. git commit

## 7. 検証

```bash
# カテゴリ読み取り
cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app
# → app

# バージョン番号取得
CAT=$(cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app) && ls -1d "docs/$CAT/ver"*/ 2>/dev/null | sed 's|.*/ver||;s|/||' | sort -n | tail -1 || echo 0
# → 10

# 新規カテゴリ（verなし）のテスト
echo "infra" > .claude/CURRENT_CATEGORY
CAT=$(cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app) && ls -1d "docs/$CAT/ver"*/ 2>/dev/null | sed 's|.*/ver||;s|/||' | sort -n | tail -1 || echo 0
# → 0

# 元に戻す
echo "app" > .claude/CURRENT_CATEGORY
```

## 8. スコープ外（今回やらないこと）

- カテゴリ固有の `CLAUDE.md`（`docs/{category}/CLAUDE.md`）の作成 → 必要性が出てから対応
- カテゴリ横断の依存関係管理
- `REQUESTS/` フォルダのカテゴリ分け

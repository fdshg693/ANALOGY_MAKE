# バージョン管理のメジャー.マイナー形式への移行

## Context

現在のバージョン管理は `ver1 → ver2 → ver3` のフラット形式。`CURRENT.md` は毎バージョンで完全なASISスナップショットを記述するため、依存パッケージ表・ファイル別詳細・API契約など大部分が前バージョンのコピーになっている。

メジャー.マイナー形式 (`ver1.0 → ver1.1 → ver2.0`) に移行し、**メジャーバージョン (X.0) のみフルスナップショット**、**マイナーバージョン (X.Y) は変更差分のみ**記載とすることで重複を解消する。

### 決定事項: 旧バージョンの扱い

- **A. 連番継続**: 既存 ver9〜ver12 はそのまま残し、`ver13.0` から新形式開始（git historyとの整合性を維持）

## 1. `get_latest_version.sh` の改修（基盤）

**ファイル**: `.claude/scripts/get_latest_version.sh`

### Before
```bash
#!/bin/bash
CAT=$(cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app)
VER=$(ls -1d "docs/$CAT/ver"*/ 2>/dev/null | sed 's|.*/ver||;s|/||' | sort -n | tail -1)
echo "${VER:-0}"
```

### After
```bash
#!/bin/bash
CAT=$(cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app)
MODE="${1:-latest}"  # latest | major | next-minor | next-major

# 全バージョンを取得（旧形式 ver12 と新形式 ver13.0 の両方に対応）
ALL=$(ls -1d "docs/$CAT/ver"*/ 2>/dev/null | sed 's|.*/ver||;s|/||' | sort -t. -k1,1n -k2,2n)

case "$MODE" in
  latest)
    # 最新バージョン（形式問わず）
    echo "${ALL}" | tail -1 | tr -d '[:space:]'
    ;;
  major)
    # 最新のメジャーバージョン（X.0 または旧形式の整数）
    echo "${ALL}" | grep -E '^[0-9]+$|\.0$' | tail -1 | tr -d '[:space:]'
    ;;
  next-minor)
    # 次のマイナーバージョン番号を提案
    LATEST=$(echo "${ALL}" | tail -1 | tr -d '[:space:]')
    if echo "$LATEST" | grep -q '\.'; then
      MAJOR=$(echo "$LATEST" | cut -d. -f1)
      MINOR=$(echo "$LATEST" | cut -d. -f2)
      echo "${MAJOR}.$((MINOR + 1))"
    else
      # 旧形式からの移行: 次のメジャー番号.1
      echo "$((LATEST + 1)).1"
    fi
    ;;
  next-major)
    # 次のメジャーバージョン番号を提案
    LATEST=$(echo "${ALL}" | tail -1 | tr -d '[:space:]')
    if echo "$LATEST" | grep -q '\.'; then
      MAJOR=$(echo "$LATEST" | cut -d. -f1)
      echo "$((MAJOR + 1)).0"
    else
      echo "$((LATEST + 1)).0"
    fi
    ;;
  *)
    echo "Usage: $0 [latest|major|next-minor|next-major]" >&2
    exit 1
    ;;
esac
```

**ポイント**:
- 旧形式 (`ver12`) と新形式 (`ver13.0`) の両方をソート・取得可能
- `MODE` 引数で用途に応じた情報を返す
- 各SKILLは引数を変えて呼び出せる

## 2. CLAUDE.md の更新

**ファイル**: `CLAUDE.md`（プロジェクトルート）

### 変更箇所: バージョン管理規則セクション

#### Before
```markdown
## バージョン管理規則

各バージョンフォルダ `docs/{category}/ver{N}/` の構成:
- `ROUGH_PLAN.md` — タスク概要
- `REFACTOR.md` — リファクタリング計画
- `IMPLEMENT.md` — 実装計画
- `MEMO.md` — 実装メモ・残課題
- `CURRENT.md` — そのバージョン完了時のコード現況（CLAUDE.md と重複しない内容のみ）
```

#### After
```markdown
## バージョン管理規則

バージョン形式: `ver{Major}.{Minor}`（例: `ver13.0`, `ver13.1`）
- **メジャーバージョン (X.0)**: 新機能追加・アーキテクチャ変更・MASTER_PLAN の新項目着手時
- **マイナーバージョン (X.Y, Y>0)**: バグ修正・既存機能改善・ISSUES対応

各バージョンフォルダ `docs/{category}/ver{X.Y}/` の構成:
- `ROUGH_PLAN.md` — タスク概要
- `PLAN_HANDOFF.md` — 選定理由・除外理由・関連 ISSUE パス・後続 step への注意点（handoff 情報ゼロなら省略可）
- `REFACTOR.md` — リファクタリング計画
- `IMPLEMENT.md` — 実装計画
- `MEMO.md` — 実装メモ・残課題
- `CURRENT.md` — **メジャーバージョンのみ**: コード現況の完全版（CLAUDE.md と重複しない内容のみ）
- `CHANGES.md` — **マイナーバージョンのみ**: 前バージョンからの変更差分

※ 旧形式 (ver9〜ver12) は整数名のまま保持
```

## 3. `split_plan` SKILL の修正

**ファイル**: `.claude/skills/split_plan/SKILL.md`

### 変更内容

#### 3.1 コンテキストセクションに追加
```markdown
- 次のマイナーバージョン番号: !`bash .claude/scripts/get_latest_version.sh next-minor`
- 次のメジャーバージョン番号: !`bash .claude/scripts/get_latest_version.sh next-major`
```

#### 3.2 「分割」セクションの冒頭を変更

Before:
```markdown
次のバージョン番号（最新バージョン番号 + 1）で新しい空の `docs/{カテゴリ}/ver{N}` フォルダを作成してください。
```

After:
```markdown
### バージョン種別の判定

今回のタスクがメジャー・マイナーのどちらに該当するか判定する:

**メジャーバージョンアップ (X.0)** の条件（いずれか）:
- MASTER_PLAN の新項目に着手する
- アーキテクチャの変更を伴う
- 新規の外部ライブラリ・サービスを導入する
- 破壊的変更を伴うリファクタリング

**マイナーバージョンアップ (X.Y)** の条件（上記に該当しない場合）:
- ISSUES の解消（バグ修正・改善）
- 既存機能の微調整・UX改善
- ドキュメント整理・テスト追加

判定結果に基づいて、新しい空の `docs/{カテゴリ}/ver{次のバージョン番号}` フォルダを作成してください。
```

## 4. `write_current` SKILL の修正（最大の変更）

**ファイル**: `.claude/skills/write_current/SKILL.md`

### 変更内容: CURRENT.md セクションを分岐構造に

Before:
```markdown
## CURRENT.md の作成
1. 最新の手前のバージョンの `CURRENT.md` を参照して...
2. 最新バージョンの `REFACTOR.md` と `IMPLEMENT.md` と `MEMO.md` を参照して...
3. 最新バージョンの `CURRENT.md` を作成または修正する
```

After:
```markdown
## バージョン種別に応じたドキュメント作成

最新バージョンのフォルダ名から、メジャー (X.0) かマイナー (X.Y, Y>0) かを判定する。

### メジャーバージョン (X.0) の場合: CURRENT.md を作成

1. 直前のメジャーバージョンの `CURRENT.md` を参照して、前回のコード状況を把握する
   - 間にマイナーバージョンがある場合は、それらの `CHANGES.md` も参照して差分を把握する
2. 最新バージョンの `REFACTOR.md` と `IMPLEMENT.md` と `MEMO.md` を参照して、今回行われた変更を把握する
3. 最新バージョンの `CURRENT.md` を **完全版（ASIS）** で作成する

（記載ルールは従来通り）

### マイナーバージョン (X.Y, Y>0) の場合: CHANGES.md を作成

1. 最新バージョンの `REFACTOR.md` と `IMPLEMENT.md` と `MEMO.md` を参照して、今回行われた変更を把握する
2. 最新バージョンの `CHANGES.md` を作成する

#### CHANGES.md の記載ルール

- **差分のみ記載する**（完全なASISスナップショットは不要）
- 以下のセクションで構成する:
  - `## 変更ファイル一覧` — 変更・追加・削除されたファイルとその概要
  - `## 変更内容の詳細` — 各変更の技術的な説明（なぜ・何を・どう変えたか）
  - `## API変更` — APIの追加・変更がある場合のみ
  - `## 技術的判断` — 新たな技術的判断があった場合のみ
```

## 5. `imple_plan` SKILL の修正

**ファイル**: `.claude/skills/imple_plan/SKILL.md`

### 変更箇所: 準備セクション

Before:
```markdown
最新の手前のバージョンの `CURRENT.md` を参照して、現在のコード状況を把握してください。
（例: 最新バージョンが 4 なら `docs/{カテゴリ}/ver3/CURRENT.md` を参照）
```

After:
```markdown
現在のコード状況を把握するために、以下を参照してください:

1. 直前のメジャーバージョンの `CURRENT.md` を参照する
   - メジャーバージョンの特定: `bash .claude/scripts/get_latest_version.sh major`
2. そのメジャーバージョン以降のマイナーバージョンに `CHANGES.md` があれば、それらも参照する
3. 上記がいずれも存在しない場合は、サブエージェントによるコードベース調査で現状を把握する

（例: 最新バージョンが 13.2 なら `ver13.0/CURRENT.md` → `ver13.1/CHANGES.md` → `ver13.2` が今回の作業フォルダ）
```

## 6. `retrospective` SKILL の修正

**ファイル**: `.claude/skills/retrospective/SKILL.md`

### 追加セクション（「2. バージョン作成の流れの検討」の後に追加）

```markdown
## 3. 次バージョンの種別推奨

次に予定されるタスク（MASTER_PLAN の次項目、未解決 ISSUES）を踏まえて、次バージョンがメジャー・マイナーのどちらが適切かを推奨する。

- 次のマイナーバージョン候補: !`bash .claude/scripts/get_latest_version.sh next-minor`
- 次のメジャーバージョン候補: !`bash .claude/scripts/get_latest_version.sh next-major`
```

（既存の「3. Git にコミットする」は「4. Git にコミットする」に繰り下げ）

## 7. `wrap_up` SKILL の修正

**ファイル**: `.claude/skills/wrap_up/SKILL.md`

変更なし（バージョン番号の形式変更に影響されるパス参照はなく、`get_latest_version.sh` の出力を通じて自動対応）

## 8. settings.local.json の更新

**ファイル**: `.claude/settings.local.json`

スクリプトの引数追加に伴い、許可パターンの追加が必要な場合のみ対応。

## 実行順序

| Step | 対象 | 内容 |
|---|---|---|
| 1 | ユーザー確認 | 旧バージョンの扱い（A/B/C）を決定 |
| 2 | `get_latest_version.sh` | Major.Minor 対応 + MODE引数追加 |
| 3 | `CLAUDE.md` | バージョン管理規則の更新 |
| 4 | `split_plan` SKILL | メジャー/マイナー判定基準・バージョン番号分岐 |
| 5 | `write_current` SKILL | CURRENT.md / CHANGES.md の分岐ロジック |
| 6 | `imple_plan` SKILL | コード状況把握のメジャー基準参照 |
| 7 | `retrospective` SKILL | 次バージョン種別推奨セクション追加 |
| 8 | 動作確認 | スクリプトの各MODE出力を検証 |
| 9 | git commit |  |

## 検証

```bash
# 旧形式との互換性（現在の ver12 を正しく取得）
bash .claude/scripts/get_latest_version.sh latest   # → 12
bash .claude/scripts/get_latest_version.sh major     # → 12
bash .claude/scripts/get_latest_version.sh next-major # → 13.0
bash .claude/scripts/get_latest_version.sh next-minor # → 13.1

# 新形式のフォルダ作成後
mkdir -p docs/app/ver13.0
bash .claude/scripts/get_latest_version.sh latest     # → 13.0
bash .claude/scripts/get_latest_version.sh major       # → 13.0
bash .claude/scripts/get_latest_version.sh next-minor  # → 13.1
bash .claude/scripts/get_latest_version.sh next-major  # → 14.0

# マイナー追加後
mkdir -p docs/app/ver13.1
bash .claude/scripts/get_latest_version.sh latest     # → 13.1
bash .claude/scripts/get_latest_version.sh major       # → 13.0
bash .claude/scripts/get_latest_version.sh next-minor  # → 13.2
```

## スコープ外

- 旧バージョン (ver9〜ver12) の CURRENT.md を CHANGES.md 形式に変換する作業
- Hooks による自動バリデーション（将来的に有効だが今回は対象外）
- `meta_judge` SKILL の修正（パス参照なし、変更不要）

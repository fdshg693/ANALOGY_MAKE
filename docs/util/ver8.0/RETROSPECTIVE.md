# ver8.0 RETROSPECTIVE — `/issue_plan` SKILL 新設 + プラン前半/後半の責務分離（PHASE6.0 §2）

## 1. ドキュメント構成整理

### 1-1. `docs/util/MASTER_PLAN.md` の状態

- `MASTER_PLAN.md` 本体は 1 行サマリ構成、詳細は `docs/util/MASTER_PLAN/PHASE{X}.md` に分割済み。肥大化の兆候なし
- PHASE6.0 は §1 / §2 / §4 が実装済み。未着手は §3（`--workflow auto` 自動選択）・§5（`--workflow auto` のユニットテスト追加）
- 当面 PHASE6.0 の枠内で ver9 系を消化できる見込みのため、新フェーズの策定は不要
- **再構成提案: なし**

### 1-2. `CLAUDE.md` の肥大化チェック

- プロジェクトルート `CLAUDE.md` は 60 行弱で健全
- `.claude/CLAUDE.md` は `@./claude_docs/ROLE.md` の読み込みのみ、ROLE.md も 15 行程度で健全
- サブフォルダ固有 `CLAUDE.md` は ver7.0 同様、現時点では不要
- **分割提案: なし**

### 1-3. `.claude/rules/` の新設について

ver8.0 で `.claude/rules/claude_edit.md` を新規追加した（`.claude/**/*` 編集時の `claude_sync.py` 手順を rules 化）。これまで暗黙のルールだったものが明文化され、次セッション以降の作業ブレを抑えられる。この形式（特定パターンのファイルに対する運用ルールを `rules/` 配下に置く）は将来的に横展開する価値があり、直近は `REQUESTS/AI/` の消費ルールや `FEEDBACKS/` の処理ルールを同様に rules 化できる余地あり（本バージョンの即時適用対象ではない）。

**結論**: ver8.0 時点でドキュメント構成は健全。構造的な再構成提案はなし。

## 2. バージョン作成の流れの検討

### 2-1. 各ステップの効果

| ステップ | 評価 | コメント |
|---|---|---|
| `/split_plan` | ◎ | ver8.0 時点では旧 `/split_plan` がプラン前半＋後半の混在形だった。ROUGH_PLAN.md でスコープ切り出し（PHASE6.0 §2 のみ、§3 / §5 は後送り）が明確に行えた |
| `/imple_plan` | ◎ | R1〜R6 の事前リスク列挙が IMPLEMENT.md に完備されており、R1（`claude_sync.py` 全置換動作）が想定通り発現した際も即時対応できた。YAML 変更・SKILL 新設・削除・縮小の論理的密結合を 1 コミットにまとめる判断も奏功 |
| `/wrap_up` | ○ | PHASE6.0 §2 の実装ステータスを「実装済み」に更新するのみで軽量に完了。大きな再調整は発生せず、IMPLEMENT の質の高さを示唆 |
| `/write_current` | ◎ | ver7.0 で導入した 4 ファイル分割（`CURRENT.md` + `CURRENT_scripts/skills/tests.md`）を ver8.0 でも踏襲し、差分追記ではなく新版として再生成する方針が機能 |
| `/retrospective` | — | 本ステップ。`issue_worklist.py` の json 展開（ver7.0 で追加）が util 4 件分正常に提示され、次バージョンのスコープ判断に直接貢献 |

### 2-2. 流れに対する改善提案

#### 改善 1: `retrospective/SKILL.md` の「5ステップ」記述が古い

`/retrospective` SKILL の §2「バージョン作成の流れ」では 5 ステップ構成（`/split_plan` が先頭）のまま放置されていた。ver8.0 で `/issue_plan` を新設し 6 ステップ化したにも関わらず更新漏れ。

→ **即時適用**: `/retrospective` SKILL §2 のステップ列挙を 6 ステップに更新し、`/issue_plan` を先頭に追加。軽量ワークフロー quick（3 ステップ）との対応関係も明記。

#### 改善 2: `/issue_plan` → `/split_plan` 間の情報引き継ぎ（R2 持ち越し）

ver8.0 は `/issue_plan` → `/split_plan` を新規セッションで運用する方針を採用したが、実ワークフローでの動作検証はまだ。ROUGH_PLAN.md の情報量が `/split_plan` で IMPLEMENT.md を起こすのに十分かは、次バージョンの実走で判定する必要がある。

→ 既に `ISSUES/util/medium/issue-plan-split-plan-handoff-verification.md` として ISSUE 化済み。次の util ワークフロー実行時に検証対象とする。**本 RETROSPECTIVE では追加アクションなし**。

#### 改善 3: `/issue_plan` 単独実行 YAML の未整備（R6 持ち越し）

`scripts/claude_loop_issue_plan.yaml` の新設は PHASE6.0 §3（ver8.1 以降）として計画されている。現状は `--max-step-runs 1` で手動代替する運用のため、「ISSUE レビュー＋plan 作成だけ回したい」ユースケースが重い。

→ 既に `ISSUES/util/low/issue-plan-standalone-yaml.md` として ISSUE 化済み。ver9.0 で PHASE6.0 §3 と合わせて実装する想定。**本 RETROSPECTIVE では追加アクションなし**。

#### 改善 4: `rules/` ディレクトリ活用の拡張余地

ver8.0 で `claude_edit.md` のみ新設されたが、`REQUESTS/AI/` 消費ルール・`FEEDBACKS/done/` への移動タイミング等、暗黙運用がまだ残っている。ただし現時点ではワークフローが回っており、過剰設計のリスクがあるため即時適用はしない。

→ **即時適用せず**。肥大化の兆候が出た段階で再検討する。

### 2-3. 即時適用したスキル変更

- `.claude/skills/retrospective/SKILL.md` §2 のステップ列挙を 5 → 6 に更新（`/issue_plan` を先頭に追加、quick ワークフロー 3 ステップ構成を追記）

（`claude_sync.py export` → `.claude_sync/SKILLS/retrospective/SKILL.md` を編集 → `import` の手順で適用）

### 2-4. `REQUESTS/AI/` の整理

- `REQUESTS/AI/` 配下は `README.md` のみ。ver8.0 固有の用済みファイルは存在しない。**変更なし**

## 3. 次バージョンの種別推奨

### 3-1. 現カテゴリの着手候補（util、`issue_worklist.py` 結果）

| path | priority | status | assigned | 備考 |
|---|---|---|---|---|
| `ISSUES/util/medium/issue-plan-split-plan-handoff-verification.md` | medium | ready | ai | ver8.0 新規。`/issue_plan` → `/split_plan` の情報引き継ぎ検証（R2 持ち越し） |
| `ISSUES/util/medium/issue-review-rewrite-verification.md` | medium | ready | ai | ver6.0 からの持ち越し。app/infra ワークフロー起動時に消化可能な性質で、util 単体では処理不能 |
| `ISSUES/util/low/issue-plan-standalone-yaml.md` | low | ready | ai | ver8.0 新規。`/issue_plan` 単独実行 YAML（R6 持ち越し）。PHASE6.0 §3 と合わせて消化したい |
| `ISSUES/util/low/issue-worklist-json-context-bloat.md` | low | ready | ai | ver8.0 新規。ISSUE 件数増加時の `--limit` 対応（R5 持ち越し）。現状 4 件で余裕あり |

### 3-2. MASTER_PLAN の次項目

**PHASE6.0 §3** — `scripts/claude_loop.py` に `--workflow auto` を導入し、`/issue_plan` が出力した ROUGH_PLAN.md frontmatter の `workflow:` 値に応じて後続 YAML を分岐させる。ver8.0 で `/issue_plan` が frontmatter を書き込む実装は完了しているため、受け皿側（loop 本体）を整える段階。

§3 は以下を含む:
- `claude_loop.py` の `--workflow` 引数に `auto` 値を追加し、ROUGH_PLAN.md の frontmatter を読んで `full`/`quick` の YAML を選択
- `claude_loop_issue_plan.yaml`（`/issue_plan` 単独実行 YAML）の新設 → `issue-plan-standalone-yaml.md` の消化にもつながる
- `tests/test_claude_loop.py` に `--workflow auto` 分岐テスト追加（PHASE6.0 §5）
- `.claude/skills/meta_judge/WORKFLOW.md` の自動選択フロー図更新

### 3-3. 次バージョン種別の推奨

**メジャー = ver9.0 を推奨**。

判定根拠:

- PHASE6.0 §3 は **`claude_loop.py` 本体の新引数追加**（`--workflow auto`）という挙動変更を伴う
- **新規 YAML ファイル**（`claude_loop_issue_plan.yaml`）の追加と、**ユニットテストの追加**（§5 と一体で実施）を含む
- 影響範囲が `scripts/claude_loop.py` 本体 + 設定 YAML + テストと広く、CLAUDE.md 版管理規則「メジャー = MASTER_PLAN 新項目着手・アーキテクチャ変更」に合致
- マイナー ver8.1 として扱うには、`--workflow auto` は引数の新規追加かつ分岐ロジックの導入であり、範囲が大きすぎる

**代替案**: ver8.1（マイナー）として `ISSUES/util/medium/issue-plan-split-plan-handoff-verification.md` の実動作検証 1 件だけを回す案もありうる。ただしこれは「次に util ワークフローを回したタイミングで自然に検証される」性質のため、ver8.1 として単独で切る積極的理由は弱い。ver9.0 スコープ内で同時に観察する方が合理的。

→ **最終推奨: ver9.0（メジャー）として PHASE6.0 §3 + §5 に着手。ver8.0 で持ち越した `/issue_plan` 単独 YAML（`issue-plan-standalone-yaml.md`）も同スコープで消化する**。

## 4. 振り返り結果の記録

### 4-1. ISSUES ファイルの整理

- **持ち越し**（削除しない）:
  - `ISSUES/util/medium/issue-plan-split-plan-handoff-verification.md` — R2 検証先送り（ver8.0 MEMO §R2 参照）。次 util ワークフロー実行で検証
  - `ISSUES/util/medium/issue-review-rewrite-verification.md` — ver6.0 からの持ち越し。util 単体では消化不能で、app/infra ワークフロー起動を待つ
  - `ISSUES/util/low/issue-plan-standalone-yaml.md` — R6 検証先送り。ver9.0 で PHASE6.0 §3 と合わせて消化予定
  - `ISSUES/util/low/issue-worklist-json-context-bloat.md` — R5 検証先送り。件数が閾値を超えるまで対処保留
- **削除**: なし（ver8.0 で新設した 3 件は全て先送り宣言付き）
- **frontmatter 無しファイル**: なし

### 4-2. `REQUESTS/AI/` の整理

- `REQUESTS/AI/` 配下は `README.md` のみ。ver8.0 固有の用済みファイルは存在しない。**変更なし**

### 4-3. 即時適用したスキル変更

- `.claude/skills/retrospective/SKILL.md` §2 のステップ列挙を 5 → 6 に更新（`/issue_plan` を先頭に追加、quick ワークフロー 3 ステップ構成を追記）

### 4-4. 次バージョン ver9.0 への引き継ぎ

PHASE6.0 §3 + §5 着手時の注意点:

1. **`/issue_plan` frontmatter の壊れ対応**: `workflow` フィールド未記載・不正値（`quick | full` 以外）の場合は `full` フォールバック。テストで明示的にカバーする
2. **`claude_loop.py` 既存引数との整合**: 現状 `-w` オプションで YAML ファイルパス直接指定が可能。`--workflow auto` の新設は既存オプションと排他にせず、`--workflow auto` 指定時のみ frontmatter 読み取りに切り替える設計が無難
3. **`/issue_plan` → 後続 YAML 切替の検証**: `auto` モードで `/issue_plan` 実行後、選択された YAML が正しく後続ステップを起動するかを実走で確認。`ISSUES/util/medium/issue-plan-split-plan-handoff-verification.md` の検証とも連動する
4. **`claude_sync.py` 運用継続**: `.claude/skills/meta_judge/WORKFLOW.md` 更新、`/issue_plan` SKILL の微修正が発生する場合に備えて、imple_plan 冒頭で export/import フローを明示
5. **`issue_worklist.py` 件数**: ver9.0 開始時点で util 4 件、app は別途確認要。3 件を消化し新規 0〜1 件発生の想定ならば、context bloat ISSUE（worklist json 肥大化）は依然先送りで可

### 4-5. 今バージョンからの学び（手法面）

- **SKILL 責務分離＋ YAML ワークフロー変更を 1 コミットにまとめた判断が奏功**: SKILL 定義と YAML ステップ列の整合性を履歴に残せた。論理的密結合の変更では「ファイル種別で分ける」より「機能単位で束ねる」方が rollback・bisect 時に扱いやすい
- **`claude_sync.py` の全置換動作（R1）が想定通り機能**: `quick_plan/` ディレクトリの削除も正しく伝搬。事前に `git status .claude/` で前提差分をクリアにする習慣が重要
- **`rules/claude_edit.md` の新設**: これまで暗黙運用だった `.claude/` 編集手順を明文化。類似パターン（REQUESTS/FEEDBACKS の運用）も将来的に rules 化できる余地を確認
- **事前リスク列挙（R1〜R6）が検証先送り判断にも寄与**: 先送りにした R2 / R5 / R6 はすべて ISSUES 化し、後続バージョンへの引き継ぎが確実化。「先送り理由」を事前に言語化できていたため、ISSUE 化コストが低かった

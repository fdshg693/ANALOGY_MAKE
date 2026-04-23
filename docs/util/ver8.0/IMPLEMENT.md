# ver8.0 IMPLEMENT — `/issue_plan` SKILL 新設 + `/split_plan` 責務縮小 + `/quick_plan` 削除

## 0. 事前リファクタリング

**不要**。既存 SKILL から新 SKILL への切り出しはテキスト移動が中心で、共通ロジック関数化などの下準備は必要ない。`issue_review/SKILL.md`（一次資料）からの手順インライン展開の方式は現状を踏襲する。REFACTOR.md は作成しない。

## 1. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---|---|---|
| `.claude/skills/issue_plan/SKILL.md` | 新規作成 | 前半ステップ: 現状把握 + ISSUE レビュー + ISSUE/MASTER_PLAN 選定 + ROUGH_PLAN.md 作成 + workflow 選択。review は行わない |
| `.claude/skills/split_plan/SKILL.md` | 大規模編集 | 後半ステップに縮小。REFACTOR/IMPLEMENT 作成 + plan_review_agent での review のみ。現状把握・ISSUE 選定・ROUGH_PLAN 作成ロジックは削除 |
| `.claude/skills/quick_plan/SKILL.md` | **削除** | 責務を `/issue_plan` に完全吸収。後方互換ラッパーは残さない（CLAUDE.md の「Avoid backwards-compatibility hacks」方針に従う） |
| `scripts/claude_loop.yaml` | 編集 | 先頭ステップを `/split_plan` から `/issue_plan` に差し替え、`/split_plan` を 2 ステップ目に移す |
| `scripts/claude_loop_quick.yaml` | 編集 | 先頭ステップを `/quick_plan` から `/issue_plan` に差し替え（`/quick_impl` / `/quick_doc` は現状維持） |
| `scripts/README.md` | 編集 | 「サンプル YAML」節と「フル/quick の使い分け」セクションの SKILL チェーン列挙を更新、クイックスタートの `--workflow` 記述は据え置き |
| `.claude/skills/meta_judge/WORKFLOW.md` | 編集 | §1・§2 のステップ列と §2 の保守注意点を最新 SKILL チェーンに合わせる |
| `.claude/skills/issue_review/SKILL.md` | 軽微編集 | 「呼び出し元との同期」の対象を `/issue_plan` に変更（`split_plan` / `quick_plan` の参照を外す） |
| `ISSUES/README.md` | 軽微編集 | 「plan ステップ（`/split_plan` / `/quick_plan`）」を「plan ステップ（`/issue_plan`）」に更新 |

変更対象ファイル合計 9 件。`.claude/` 配下 5 件 + `scripts/` 配下 3 件 + `ISSUES/README.md` 1 件。メジャーワークフロー妥当。

## 2. `.claude/` 配下の編集手順

ver7.0 RETROSPECTIVE 2-2 で顕在化した権限制約により、`.claude/` 配下への直接 Edit/Write は `-p` モードで弾かれる。本ステップ・後続 `/imple_plan` では次の順序で操作する:

1. `python scripts/claude_sync.py export` — `.claude/` → `.claude_sync/`
2. Edit/Write ツールで `.claude_sync/skills/...` を編集
3. `python scripts/claude_sync.py import` — `.claude_sync/` → `.claude/` に書き戻し
4. 複数ファイルを編集する場合は、全編集完了後に 1 回だけ `import` する（差分の把握を容易にするため）

検証: 編集後に `git diff .claude/skills/` で想定通りのファイル群が変化していることを確認する。

## 3. `/issue_plan` SKILL の新規作成

### 3-1. ファイル構成

`.claude/skills/issue_plan/SKILL.md` を以下の骨格で作成する。既存 `/split_plan` と `/quick_plan` から移植する部分は **コピーしつつ用途に合わせて整理**（重複のカットや表現の統一）する。

```markdown
---
name: issue_plan
disable-model-invocation: true
user-invocable: true
---

## コンテキスト

- カテゴリ: !`cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app`
- 最新バージョン番号: !`bash .claude/scripts/get_latest_version.sh`
- 次のマイナーバージョン番号: !`bash .claude/scripts/get_latest_version.sh next-minor`
- 次のメジャーバージョン番号: !`bash .claude/scripts/get_latest_version.sh next-major`
- AI 向け ready/review ISSUE: !`python scripts/issue_worklist.py --format json`

## 役割

ワークフロー先頭の共通ステップ。`/split_plan`・`/quick_plan` からプラン前半責務を切り出した位置づけ。

- 現状把握（`CURRENT.md` / 直前 `RETROSPECTIVE.md` / `MASTER_PLAN.md` を参照）
- ISSUE レビューフェーズ（`review / ai` → `ready / ai` or `need_human_action / human`）
- `status: ready` / `assigned: ai` の ISSUE 優先選定（優先度順 high → medium → low）
- MASTER_PLAN 新項目への着手判断（ready/ai が無い場合）
- `docs/{カテゴリ}/ver{次バージョン}/ROUGH_PLAN.md` を作成する
- ROUGH_PLAN.md 冒頭 frontmatter に `workflow: quick | full` と `source: issues | master_plan` を記録する
- **review は行わない**（plan_review_agent は起動しない）

## 準備

（現在の `/split_plan` 冒頭の「準備」節と同等の内容を配置。ISSUE レビューフェーズ手順は `issue_review/SKILL.md` を一次資料として参照する旨を明記）

## バージョン種別の判定

（現在の `/split_plan` の該当節をそのまま移植。メジャー条件 4 つ、マイナー条件 3 つ）

## ワークフロー選択（`workflow: quick | full`）

選定 ISSUE・タスクの性質に応じて以下ルールで決定する:

- 選定 ISSUE に `status: review` が 1 件でも含まれる場合 → **必ず `full`**
- MASTER_PLAN 新項目 / アーキテクチャ変更 / 新規ライブラリ導入を含む場合 → **必ず `full`**
- 全 `ready` で、変更対象が 3 ファイル以下かつ 100 行以下の見込みなら → `quick`
- 判断に迷う場合 → 安全側で `full`

決定結果を ROUGH_PLAN.md 冒頭の frontmatter に記録する:

    ---
    workflow: full
    source: issues
    ---

## ROUGH_PLAN.md の作成

（現在の `/split_plan` 「ステップ1」の ROUGH_PLAN 作成ガイドをそのまま移植。粒度注意書きも維持）

## Git にコミットする

- 作成した ROUGH_PLAN.md をコミットする
- コミットメッセージ例: `docs(ver{バージョン番号}): issue_plan完了`
- **プッシュは不要**
- **plan_review_agent は起動しない**（review は後続 `/split_plan` で実施）
```

### 3-2. `/split_plan` からの移植対象（逐語的に切り出す節）

- 「準備」節全体（「現状を把握して」「目標となるプランを把握して」「ISSUE レビューフェーズ」）
- 「バージョン種別の判定」節
- 「ステップ1: タスク概要の作成と承認」の 1 番目（ROUGH_PLAN.md 作成の記述）

ただし **`plan_review_agent サブエージェントを起動して、タスク概要を説明して、承認を得ること` の一文は `/issue_plan` からは削除する**（方針転換: review は `/split_plan` 側にのみ存在させる）。

### 3-3. `workflow` 判定ロジックの出所

MASTER_PLAN PHASE6.0 §2-1 の「ワークフロー選択ルール」を SKILL の「ワークフロー選択」節として本文に書き起こす。現状 `.claude/skills/` には同等の記述がないため、新規追加となる。

## 4. `/split_plan` SKILL の責務縮小

### 4-1. 削除する節

- 「コンテキスト」節の `次のメジャーバージョン番号` 行（major 判定は `/issue_plan` で済むため不要）
- 「準備」節全体
- 「バージョン種別の判定」節
- 「ステップ1: タスク概要の作成と承認」節

### 4-2. 残す節

- 「小規模タスクの判定」節 → **要改訂**（後述 4-3）
- 「ステップ2: 実装計画の作成と承認」節 → **要改訂**（後述 4-4）
- 「ステップ3: Git にコミットする」節 → 節番号のみ「ステップ2」に繰り上げ

### 4-3. 「小規模タスクの判定」節の改訂

ワークフロー選択は `/issue_plan` が完了済みなので、本節は削除する。代替として「ROUGH_PLAN.md frontmatter の `workflow` 値を確認し、`quick` の場合は本 SKILL は呼ばれない想定である（両 YAML は `/issue_plan → 後続` の設計）」という整合メモを 1〜2 行で残す。

### 4-4. 「ステップ2: 実装計画の作成と承認」の改訂

冒頭文言を次に置換:

> `/issue_plan` が作成した `ROUGH_PLAN.md`（`docs/{カテゴリ}/ver{次バージョン}/ROUGH_PLAN.md`）を読み、対象タスクを固定する。
>
> ROUGH_PLAN.md frontmatter に `workflow: full` が記録されていることを確認する（`quick` になっている場合は本ステップは実行されるべきでないため、`REQUESTS/AI/` に整合性エラーとして記録し終了する）。

その後は現行の REFACTOR.md / IMPLEMENT.md 作成ガイドをそのまま流用。plan_review_agent の起動指示も現行のまま維持（**本 SKILL はワークフロー内で唯一 review を行うステップ**）。

### 4-5. 変更後の節構成プレビュー

```
---
name: split_plan
disable-model-invocation: true
user-invocable: true
---

## コンテキスト
- カテゴリ: ...
- 最新バージョン番号: ...
- 次のマイナーバージョン番号: ...

## ステップ1: 実装計画の作成と承認
（REFACTOR.md / IMPLEMENT.md 作成ガイド + plan_review_agent 起動）

## ステップ2: Git にコミットする
（既存記述）
```

## 5. `/quick_plan` SKILL の削除

`.claude/skills/quick_plan/SKILL.md` を `.claude_sync/skills/quick_plan/` から削除 → `import`。

`scripts/claude_sync.py` の `import_claude()` は `.claude/` 全体を `shutil.rmtree` で削除してから `.claude_sync/` を `copytree` で置き換える設計（`scripts/claude_sync.py` L36-38 で確認済み）。このため `.claude_sync/skills/quick_plan/` を削除してから `import` すれば、削除は完全に伝搬する。フォールバック手順は不要。

手順:

1. `python scripts/claude_sync.py export`
2. `rm -rf .claude_sync/skills/quick_plan/`
3. 他の編集もこの段階で全て済ませる
4. `python scripts/claude_sync.py import`
5. `git status` で `.claude/skills/quick_plan/` が削除済みになっていることを確認

## 6. ワークフロー YAML の更新

### 6-1. `scripts/claude_loop.yaml`

`steps:` セクションを以下に差し替え:

```yaml
steps:
  - name: issue_plan
    prompt: /issue_plan
    model: opus
    effort: high

  - name: split_plan
    prompt: /split_plan
    model: opus
    effort: high

  - name: imple_plan
    prompt: /imple_plan
    model: opus
    effort: high

  - name: wrap_up
    prompt: /wrap_up
    continue: true

  - name: write_current
    prompt: /write_current

  - name: retrospective
    prompt: /retrospective
    model: opus
```

ポイント:

- 新規追加する `issue_plan` は `opus` + `effort: high`（`/split_plan` と同等の判断負荷のため）
- `/split_plan` の `continue` フラグは現状省略 = 新規セッション。`/issue_plan` でも新規セッションとし、`/split_plan` は `continue: true` で `/issue_plan` の選定結果を引き継ぎたいかを検討 → **初版では `continue: false`（明示省略）とし、ROUGH_PLAN.md の frontmatter 経由で必要情報は伝達する**。セッション引き継ぎは後続リリースで検討

### 6-2. `scripts/claude_loop_quick.yaml`

`steps:` セクションを以下に差し替え:

```yaml
steps:
  - name: issue_plan
    prompt: /issue_plan
    model: opus
    effort: high

  - name: quick_impl
    prompt: /quick_impl
    effort: high
    continue: true

  - name: quick_doc
    prompt: /quick_doc
    effort: low
    continue: true
```

ポイント:

- `/quick_plan` ステップを完全に削除
- `/quick_impl` の `continue: true` の起点は `/issue_plan` になる
- `defaults` は現行のまま（`model: sonnet`, `effort: medium`）

### 6-3. 整合確認

- `WORKFLOW.md` §2 の「保守上の注意」で `command` セクションの同期義務が書かれている。`command` / `defaults` / `mode` セクションは 2 YAML で差異が出ないことを `diff` で確認

## 7. ドキュメント最小更新

### 7-1. `scripts/README.md`

- 「サンプル YAML」（163 行付近）のステップ列挙を更新
  - フル: `issue_plan → split_plan → imple_plan → wrap_up → write_current → retrospective`（6 ステップ）
  - 軽量: `issue_plan → quick_impl → quick_doc`（3 ステップ）
- 「テスト」節の件数（103 件）は `/imple_plan` 後に再計測して必要なら更新
- 「クイックスタート」の `-w scripts/claude_loop_quick.yaml` などの既存コマンド例は変更不要

### 7-2. `.claude/skills/meta_judge/WORKFLOW.md`

- §1「実装ワークフロー」のステップ列に `/issue_plan` を先頭に追加（6 ステップに）
- §2「軽量ワークフロー（quick）」のステップ列から `/quick_plan` を外し `/issue_plan` を先頭に追加

### 7-3. `.claude/skills/issue_review/SKILL.md`

「呼び出し元との同期」の対象を更新:

- 削除: `.claude/skills/split_plan/SKILL.md` と `.claude/skills/quick_plan/SKILL.md` への参照
- 追加: `.claude/skills/issue_plan/SKILL.md` への参照（一次資料から手順がインライン展開される旨）

### 7-4. `ISSUES/README.md`

4 行目の「plan ステップ（`/split_plan` / `/quick_plan`）」を「plan ステップ（`/issue_plan`）」に置換。

### 7-5. 触らない想定のファイル

- プロジェクトルート `CLAUDE.md` — `split_plan`/`quick_plan` への直接言及なし（確認済み: Grep で 0 件）
- `.claude/CLAUDE.md` / `.claude/claude_docs/ROLE.md` — ワークフロー SKILL の言及なし
- `docs/util/MASTER_PLAN.md` / `docs/util/MASTER_PLAN/PHASE*.md` — 実装状況更新は `/wrap_up` / `/write_current` で行う範疇。本 IMPLEMENT では触らない
- `tests/test_claude_loop.py` — YAML の `steps:` は構造的バリデーションテストの対象だが、`/issue_plan` 追加で既存アサーションが壊れるか `/imple_plan` で確認する（壊れる場合は最小限の修正）

## 8. 動作検証（`/imple_plan` 以降で実施）

以下は `/imple_plan` ステップで実施する検証項目。本 IMPLEMENT.md には**方針のみ**を記録する:

1. `python -m unittest tests.test_claude_loop` が通ること（YAML 構造テストの破綻がないこと）
2. `.claude/skills/issue_plan/SKILL.md` / `.claude/skills/split_plan/SKILL.md` が `claude_sync.py` 経由で正しく書き戻されていること（`git diff .claude/` で確認）
3. `.claude/skills/quick_plan/` ディレクトリが削除されていること（`import_claude()` は全置換のため自動的に伝搬する）
4. `scripts/claude_loop.yaml` / `scripts/claude_loop_quick.yaml` が有効な YAML であること（`python -c "import yaml; yaml.safe_load(open('scripts/claude_loop.yaml'))"`）
5. **実ワークフロー実行検証は行わない**（`/imple_plan` 中に本 SKILL 群を実行すると再帰的に発動するリスクがあるため、次回ワークフロー起動時に検証する）

## 9. リスク・不確実性

### R1: `claude_sync.py` の全置換動作に起因する作業漏れリスク

- **状況**: `import_claude()` は `.claude/` を `shutil.rmtree` → `copytree` で全置換する（§5 参照）。このため `.claude_sync/` で削除したファイルは確実に伝搬するが、逆に **`export` せずに `.claude/` を直接編集していた差分は `import` で消える**
- **影響**: 本 IMPLEMENT 手順に従っていれば問題は出ないが、`/imple_plan` 中に並行して `.claude/` 側を直接編集すると復旧不能
- **対処**: `/imple_plan` 冒頭で `git status .claude/` を確認し、想定外の差分がないことを確かめてから `export` を開始する。`.claude/` 側の編集は全て `.claude_sync/` 経由で行う

### R2: `/split_plan` の `continue` 取り扱い

- **状況**: ver8.0 では `/issue_plan` → `/split_plan` 間を新規セッションで運用する方針としたが、`/split_plan` が ROUGH_PLAN.md の内容だけから詳細実装計画を起こせるかは運用上の検証事項
- **影響**: `/split_plan` が前段の判断経緯を失い、ROUGH_PLAN.md だけでは IMPLEMENT.md 作成の材料不足となるリスク
- **対処**: 本バージョンでは `/split_plan` の記述で「ROUGH_PLAN.md だけで実装計画を起こせるよう、`/issue_plan` は ROUGH_PLAN.md に必要情報を漏れなく記載すること」を `/issue_plan` 側の注意として明記する。不足が顕在化したら ver8.1 で `continue: true` に切替を検討

### R3: ISSUE レビューフェーズの所属先

- **状況**: 現在 `/split_plan` / `/quick_plan` の「準備」節末尾にインライン展開されている ISSUE レビューフェーズ手順を `/issue_plan` に統一移管する
- **影響**: `issue_review/SKILL.md` の「呼び出し元との同期」セクションの更新漏れ
- **対処**: 7-3 節で明示更新対象とする

### R4: `tests/test_claude_loop.py` の YAML 構造依存

- **状況**: 既存テストが `claude_loop.yaml` / `claude_loop_quick.yaml` の `steps:` 構造に対してハードコードされた期待値を持っていないか未確認
- **影響**: テスト破綻
- **対処**: `/imple_plan` 冒頭で `python -m unittest tests.test_claude_loop` を実行して現状の青色を確認 → YAML 変更 → 再実行。失敗した場合は最小限のテスト期待値修正で対応

### R5: `/issue_plan` 内で `issue_worklist.py --format json` の出力が巨大化するケース

- **状況**: カテゴリによっては `ready / review` の ISSUE が多数あり、SKILL コンテキスト先頭の `!` バックティック展開でトークンを消費する
- **影響**: `/issue_plan` の model/effort に対して想定外のコンテキスト肥大
- **対処**: 本バージョンでは件数制限を設けない（ver7.0 時点で util 1 件、app 6 件程度）。肥大化が顕在化したら ver8.1 以降で `issue_worklist.py --limit` オプション追加を検討（スコープ外）

### R6: `/issue_plan` 単独実行のしづらさ

- **状況**: PHASE6.0 §3 で予定されている `scripts/claude_loop_issue_plan.yaml`（`/issue_plan` 単独実行用）は本バージョンでは作成しない
- **影響**: `/issue_plan` の動作確認は full / quick YAML を 1 ステップ目で中断する形でしか行えない
- **対処**: 本バージョンではあくまで手動確認（ドライラン or `--max-step-runs 1`）で良しとする

## 10. コミット戦略

`/imple_plan` ステップで以下の粒度でコミットする想定（参考情報）:

1. `.claude/skills/issue_plan/SKILL.md` 新規作成
2. `.claude/skills/split_plan/SKILL.md` 責務縮小
3. `.claude/skills/quick_plan/` 削除 + `issue_review/SKILL.md` 同期更新 + `WORKFLOW.md` 更新
4. `scripts/claude_loop.yaml` / `scripts/claude_loop_quick.yaml` / `scripts/README.md` / `ISSUES/README.md` 更新

`/imple_plan` 側で実際の分割は調整してよいが、`.claude/` 配下と `scripts/` 配下を混在させないほうが `claude_sync.py` のフローと整合する。

## 11. スコープ外（ver8.1 以降）

- `scripts/claude_loop.py` の `--workflow auto` 導入（予約値解決・`/issue_plan` 実行後の分岐ロジック）
- `scripts/claude_loop_issue_plan.yaml` の作成（`/issue_plan` 単独実行用 YAML）
- `tests/test_claude_loop.py` への `--workflow auto` 分岐テスト追加
- `issue_worklist.py --limit` オプション追加
- `/issue_plan` → `/split_plan` の `continue: true` 化の是非検討

これらは PHASE6.0 §3 / §5 に含まれ、ver8.0 の範囲外。

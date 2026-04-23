# ver9.0 RETROSPECTIVE — `--workflow auto` 導入（PHASE6.0 §3 + §5）

## 1. ドキュメント構成整理

### 1-1. `docs/util/MASTER_PLAN.md` の状態

- 本体は 1 行サマリ形式、詳細は `MASTER_PLAN/PHASE{X}.md` に分割済。肥大化の兆候なし
- **PHASE6.0 は ver9.0 完了時点で §1〜§5 すべて実装済**。`MASTER_PLAN.md` のサマリと `PHASE6.0.md` の進捗表を「実装済み」に更新済（`2992c49` / `9e428ea` で反映済）
- `docs/util/MASTER_PLAN/` に **次フェーズ `PHASE7.0.md` がまだ存在しない**。ver9.0 で PHASE6.0 を完走したため、次に util カテゴリでまとまった MASTER_PLAN 項目を取り組むには新フェーズの骨子が必要
- **再構成提案**: MASTER_PLAN.md 本体に「PHASE6.0 まで一括 ✅」表記を追加し、次フェーズ枠の不在を明示することで、次バージョン起点の判断がしやすくなる。ただし PHASE7.0 の具体テーマは ver9.0 完了時点では未決（後述 §3 で整理）。本 RETROSPECTIVE での即時適用は見送り、次 util ワークフローの `/issue_plan` 冒頭で判断する

### 1-2. `CLAUDE.md` の肥大化チェック

- プロジェクトルート `CLAUDE.md`: 60 行弱、健全
- `.claude/CLAUDE.md`: `@./claude_docs/ROLE.md` 読み込みのみ。ROLE.md も 15 行程度で健全
- サブフォルダ固有 `CLAUDE.md` は引き続き不要
- **分割提案: なし**

### 1-3. ISSUES ディレクトリ健全性

- util 4 件（medium 2 / low 2）。肥大化の兆候なし
- app / infra 側は ver9.0 中に手を入れていないため不変
- **構成変更提案: なし**

## 2. バージョン作成の流れの検討

### 2-1. 各ステップの効果

| ステップ | 評価 | コメント |
|---|---|---|
| `/issue_plan` | ◎ | ROUGH_PLAN.md の frontmatter `workflow: full` / `source: master_plan` が正しく記録された。ISSUE レビュー対象 0 件のケースでも想定通り動作。後続 `/split_plan` への引き継ぎに必要な「関連ファイル」「判断経緯」「除外理由」がすべて格納されていた |
| `/split_plan` | ◎ | IMPLEMENT.md 564 行に展開。R1〜R8 のリスク事前列挙が ver9.0 中盤以降で R4（dry-run 相性）・R5（frontmatter フォールバック）・R6（load_workflow）などの検証を即断できる素地となった。`plan_review_agent` の起動・結果取り込みも通常通り |
| `/imple_plan` | ◎ | 32 件のユニットテスト追加・`_execute_yaml()` / `_resolve_uncommitted_status()` の追加抽象化（MEMO §L1 / §L2）を含め、実装中の設計判断がすべて MEMO.md に言語化された。`claude_sync.py` export/import も事故なく完了 |
| `/wrap_up` | ○ | MEMO に列挙した L1 / L2 / R1〜R8 / D1〜D4 が wrap_up 時点で全項目「対応不要」または「先送り済み」に整理済。PHASE6.0.md 進捗表の更新（§3・§5 を ver9.0 完了にマーク）も同時実施 |
| `/write_current` | ◎ | ver8.0 踏襲の 4 分割（`CURRENT.md` + `CURRENT_scripts/skills/tests.md`）を維持。`--workflow auto` 仕様・CLI 実行例・`--auto` との違い（3 項目の表）が `CURRENT.md` 本体に格納され、将来セッションが読みに行きやすい |
| `/retrospective` | — | 本ステップ |

### 2-2. `/issue_plan` → `/split_plan` 情報引き継ぎの実地観察（R2 持ち越し ISSUE の観察結果）

ver8.0 RETROSPECTIVE §4-4-5 で持ち越した「新規セッションでの情報引き継ぎ」を ver9.0 実走で観察した結果:

- ver9.0 の `/issue_plan` は **単一 ROUGH_PLAN.md（190 行）に、関連ファイル一覧・判断経緯・除外理由・前提リスク（ver8.0 RETROSPECTIVE §4-4 から 5 項目を引用）・事前リファクタリング判断** までを格納している
- 後続 `/split_plan` はその ROUGH_PLAN.md のみから IMPLEMENT.md / REFACTOR.md を生成可能で、過去 RETROSPECTIVE.md 等の他ファイル参照は最小限で済んだ
- よって「ROUGH_PLAN.md 単体で後続セッションに十分な情報量が渡る」ことが実地確認された
- ただし **`claude_loop.yaml` を 1 本のプロセスで通した場合**であり、`continue: true` の効果とも重畳している。完全に独立した新規セッションでの引き継ぎは未検証

→ **ISSUE `issue-plan-split-plan-handoff-verification.md` は「半検証」状態**。完全独立セッションでの検証は今後 `--max-step-runs 1` 停止 → 別プロセス再起動パターンで再確認する必要がある。本 RETROSPECTIVE ではファイルは削除せず、「半検証済。完全独立セッションでは未検証」のメモを ISSUE 本体に追記する

### 2-3. 流れに対する改善提案

#### 改善 1: `/retrospective` SKILL の §1 に「フェーズ完走時の次フェーズ計画」言及を追加

現状の `retrospective/SKILL.md` §1 は「MASTER_PLAN への追加・ファイル分割・再構成」の検討を書いているが、**現行 PHASE が完走した直後**の特殊ケース（= 次に取り組むべき PHASE の骨子が `docs/{category}/MASTER_PLAN/` に存在しない状態）への対応指針がない。ver9.0 でまさにこの状態に到達したため、次 util ワークフローの `/issue_plan` が判断に迷うリスクがある。

→ **即時適用**: `retrospective/SKILL.md` §1 に「現行 PHASE が完走した場合、次 PHASE の骨子作成の要否を検討する」旨の一文を追加する。具体的には「新フェーズの具体化は `/retrospective` の責務外（次 `/issue_plan` で MASTER_PLAN を参照した上で判断）」と「骨子が明らかに既存枠で吸収不能な場合は本 RETROSPECTIVE で PHASE 新設提案を書き残す」の 2 点を追記。

#### 改善 2: `/issue_plan` SKILL に「次 PHASE 不在時の振る舞い」記述を追加

`/issue_plan` が MASTER_PLAN 新項目を探すときに、**現行 PHASE がすべて実装済かつ次 PHASE 未着手**のケースに対する挙動が未定義。次 util ワークフローでこのケースに該当する可能性が高いため、事前にガイドラインを入れておく。

→ **即時適用**: `.claude/skills/issue_plan/SKILL.md` に「MASTER_PLAN の全 PHASE が実装済の場合」の節を追加し、「新 PHASE の骨子作成を ROUGH_PLAN.md のスコープに入れるか、既存 ISSUES の中から優先度上位を拾って小粒対応で区切るかを明示的に判断する」旨を記載。

#### 改善 3: `retrospective/SKILL.md` §3 の「次バージョン推奨」に「現行 PHASE 完走状態」を判断材料に追加

現状は ISSUE 状況と MASTER_PLAN 次項目のみが判断材料。PHASE の完走状態という情報が推奨プロセスに入っていない。

→ **即時適用**: §3 冒頭に「次バージョン判定の材料」として 3 点（ISSUE 状況 / MASTER_PLAN 次項目 / **現行 PHASE 完走状態**）を明示。

### 2-4. `--workflow auto` 実走検証（未実施分）

ver9.0 では `--workflow auto` の**実ワークフロー走行**（Claude CLI を実際に起動）は未実施（MEMO §D3）。ユニットテスト・ドライランまでが検証スコープ。次 util ワークフローは `python scripts/claude_loop.py`（= `--workflow auto` 新デフォルト）で起動し、以下を観察する:

1. フェーズ 1（`/issue_plan` 単独）が `claude_loop_issue_plan.yaml` から正常起動する
2. 生成 ROUGH_PLAN.md の frontmatter が `_read_workflow_kind()` で正しく読まれる
3. フェーズ 2（`claude_loop.yaml` または `claude_loop_quick.yaml` の `steps[1:]`）が `_compute_remaining_budget()` の残り予算で走る
4. `PYTHONIOENCODING=utf-8` 未設定でも em-dash を含む `auto: phase2` 表示で UnicodeEncodeError が出ない（MEMO §D4 観察対象）
5. `_find_latest_rough_plan` の mtime 同定が実環境で誤動作しない（`auto-mtime-robustness.md` の観察対象）

### 2-5. 即時適用したスキル変更（詳細は §4-3 に集約）

本 RETROSPECTIVE で §2-3 の改善 1〜3 を `.claude/skills/` に即時適用する。

## 3. 次バージョンの種別推奨

### 3-1. 現カテゴリの着手候補（util、`issue_worklist.py` 結果）

| path | priority | status | assigned | 性質 |
|---|---|---|---|---|
| `ISSUES/util/medium/issue-plan-split-plan-handoff-verification.md` | medium | ready | ai | ver9.0 で半検証（§2-2 参照）。**完全独立セッションでの引き継ぎ検証**が残課題 |
| `ISSUES/util/medium/issue-review-rewrite-verification.md` | medium | ready | ai | ver6.0 からの持ち越し。util 単体で消化不能、app/infra ワークフロー起動待ち |
| `ISSUES/util/low/auto-mtime-robustness.md` | low | ready | ai | ver9.0 新規。`_find_latest_rough_plan` の mtime 依存を閾値記録方式に強化。実走時の事故発生率は現状未知 |
| `ISSUES/util/low/issue-worklist-json-context-bloat.md` | low | ready | ai | 件数閾値未到達（util 4 件）。当面 YAGNI |

### 3-2. MASTER_PLAN の状況

- **PHASE6.0 まで全 PHASE 実装済**（MASTER_PLAN.md サマリ・PHASE6.0.md 進捗表ともに ver9.0 完了時点で反映済）
- **PHASE7.0 の骨子は未作成**。次 util ワークフローで新規作成するか、既存 ISSUES を軽量で消化するかの選択を `/issue_plan` が行う必要がある

### 3-3. 次バージョン種別の推奨

**推奨: ver9.1（マイナー）で既存 ISSUE の軽量消化 → その後 ver10.0 で PHASE7.0 骨子作成に着手**

推奨根拠:

- ver9.0 で PHASE6.0 の最後のブロックを完了した直後であり、**新しい PHASE7.0 を即座に立ち上げるのは拙速**。実際に `--workflow auto` を何度か実走してからでないと、新フェーズの課題がクリアに見えてこない
- 残 4 件の ISSUE のうち **`auto-mtime-robustness.md`** は ver9.0 で導入された新機能 `--workflow auto` の堅牢性に直結しており、実走で事故が起これば即座にブロッカーとなる。ver9.1 で先に閉じる価値が高い
- ver9.1（マイナー = quick ワークフロー）の適合条件:
  - `auto-mtime-robustness.md` 単体消化は `scripts/claude_loop.py::_find_latest_rough_plan` + 該当テストの修正のみ（変更ファイル 2〜3 本）
  - アーキテクチャ変更なし、新規ライブラリなし、新 MASTER_PLAN 項目なし
  - CLAUDE.md 版管理規則「マイナー = バグ修正・既存機能改善・ISSUES 対応」に合致
- `issue-plan-split-plan-handoff-verification.md` の完全独立セッション検証は ver9.1 実走中に自然発生する機会に委ねる（`--max-step-runs 1` で分割実行した場合）
- `issue-review-rewrite-verification.md` は util 単体では消化不能、持ち越し継続
- `issue-worklist-json-context-bloat.md` は閾値未到達、持ち越し継続

**代替案（採用しない）**: いきなり ver10.0 で PHASE7.0 骨子作成に着手する案。ver9.0 で導入した `--workflow auto` の実走検証が不十分なまま次フェーズに飛ぶことになり、`auto-mtime-robustness.md` が将来ブロッカー化するリスクがある。

→ **最終推奨: ver9.1（マイナー、quick ワークフロー）で `auto-mtime-robustness.md` を閉じる。PHASE7.0 骨子作成は ver10.0 以降に先送り**。

## 4. 振り返り結果の記録

### 4-1. ISSUES ファイルの整理

- **持ち越し**（削除しない、理由記載済）:
  - `ISSUES/util/medium/issue-plan-split-plan-handoff-verification.md` — ver9.0 で半検証（§2-2）。完全独立セッション検証は未実施。**本 RETROSPECTIVE 時点で ISSUE 本体に「半検証済」メモを追記**
  - `ISSUES/util/medium/issue-review-rewrite-verification.md` — app/infra ワークフロー起動待ち。util 単体では消化不能
  - `ISSUES/util/low/auto-mtime-robustness.md` — ver9.1 で消化予定（§3-3）
  - `ISSUES/util/low/issue-worklist-json-context-bloat.md` — 件数閾値未到達で YAGNI 継続
- **削除**: なし（ver9.0 で解決した `issue-plan-standalone-yaml.md` は `/wrap_up` 時点で削除済）
- **frontmatter 無しファイル**: なし

### 4-2. `REQUESTS/AI/` の整理

- `REQUESTS/AI/` 配下は `README.md` のみ。ver9.0 固有の用済みファイルなし。**変更なし**

### 4-3. 即時適用したスキル変更

§2-3 の改善 1〜3 に対応して以下を `claude_sync.py export → 編集 → import` 経由で即時適用:

- `.claude/skills/retrospective/SKILL.md` §1 に「現行 PHASE 完走時の次フェーズ計画方針」を追記
- `.claude/skills/retrospective/SKILL.md` §3 の冒頭に「次バージョン判定の材料（ISSUE 状況 / MASTER_PLAN 次項目 / 現行 PHASE 完走状態）」を明示
- `.claude/skills/issue_plan/SKILL.md` に「MASTER_PLAN の全 PHASE が実装済の場合の判断ガイドライン」を追記
- `ISSUES/util/medium/issue-plan-split-plan-handoff-verification.md` 本体に「ver9.0 で半検証済（完全独立セッション未検証）」の観察結果メモを追記（`.claude` 配下ではないため直接編集）

### 4-4. 次バージョン ver9.1 への引き継ぎ

`auto-mtime-robustness.md` 消化時の注意点:

1. **対応方針の選択**: ISSUE 本文は 2 案併記（方針 1: 閾値記録方式、方針 2: サイドチャネル経由）。方針 1 を推奨（SKILL 改修が不要で、`claude_loop.py` 内で完結）
2. **既存テストへの影響**: `TestFindLatestRoughPlan` / `TestAutoWorkflowIntegration` の既存ケースは閾値方式でも通るように設計。新規ケースとして「閾値超過なし → `SystemExit`」「閾値超過が複数 → `ver` 番号最大」を追加
3. **quick ワークフロー適合性**: 変更ファイルは `scripts/claude_loop.py` + `tests/test_claude_loop.py` の 2 本のみの想定。ROUGH_PLAN.md の `workflow:` は `quick` で適切
4. **`--workflow auto` 実走機会**: ver9.1 自体を `python scripts/claude_loop.py`（auto 新デフォルト）で起動することで、§2-4 の検証項目 1〜5 が自然に観察される
5. **PHASE7.0 骨子作成の先送り理由**: ver10.0 以降に回す方針を本 RETROSPECTIVE §3-3 で明文化済。ver9.1 の `/issue_plan` でも MASTER_PLAN 新項目ではなく既存 ISSUE 起点を明示的に選ぶこと

### 4-5. 今バージョンからの学び（手法面）

- **`workflow.py` への定数切り出し**（`FULL_YAML_FILENAME` / `QUICK_YAML_FILENAME` / `ISSUE_PLAN_YAML_FILENAME`）が、予約値解決ロジックのテスト可能性を向上させた。CLI 引数に「予約値 or パス」の両立を入れるパターンは、今後同様のユースケース（例: `--category auto`）でも流用可能
- **`_execute_yaml()` / `_resolve_uncommitted_status()` という局所リファクタ**を IMPLEMENT.md にないが実装中に追加した判断（MEMO §L1・§L2）が、`main()` の肥大化抑制とテスト簡素化の両方に効いた。「計画に書かれていないが合理的な抽象化」を後から MEMO で言語化する運用が、ver9.0 のコード品質に貢献
- **ドライラン・ユニットテストのみで実走検証を見送った判断**（MEMO §D3）はトレードオフ。実走まで行えば R5 / R7 の観察が加わり、`auto-mtime-robustness.md` の発生率も予測できた。一方で ver9.0 のスコープ膨張を防げたため、「次バージョン（ver9.1）で実走しつつ閉じる」運用に寄せた
- **`retrospective/SKILL.md` の更新を本ステップ内で行う運用**（前回 ver8.0 RETROSPECTIVE §2-3 と今回 §2-3 で 2 回連続）が機能。「持ち越さない即時適用」の原則が SKILL ドキュメントのドリフト防止に効いている

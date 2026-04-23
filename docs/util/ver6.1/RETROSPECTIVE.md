# ver6.1 RETROSPECTIVE

util ver6.1（`parse_frontmatter` 共通化、PHASE6.0 着手前の露払い）の振り返り。

## 1. ドキュメント構成整理

| 対象 | 状態 | 判断 |
|---|---|---|
| `docs/util/MASTER_PLAN.md` | PHASE5.0 まで実装済み、PHASE6.0 のみ未実装 | **再構成不要** |
| `docs/util/MASTER_PLAN/PHASE{1..6}.0.md` | フェーズ別ファイル分割が機能中 | **維持** |
| `docs/util/ver6.1/` | マイナー版構成（`ROUGH_PLAN` / `IMPLEMENT` / `MEMO` / `CHANGES`）が小さく整った | **維持** |
| `CLAUDE.md`（プロジェクトルート） | ver6.1 のリファクタリングは内部 API 変更のみで記載追加不要 | **修正不要** |
| `.claude/CLAUDE.md` | ROLE.md 参照のみで肥大化なし | **維持** |
| `ISSUES/util/` | `medium/issue-review-rewrite-verification.md` 1 件のみ残存（`ready / ai` の持ち越し） | **削除対象なし** |
| `ISSUES/util/done/` | ver6.1 で新規作成、`parse-frontmatter-shared-util.md` を収録 | **維持** |

ドキュメント構成の再編は不要。マイナーバージョンとして `CHANGES.md` のみで差分を十分に記録できており、詳細ファイル分割も生じていない。

## 2. バージョン作成の流れの振り返り

### 5 ステップ実行状況

| ステップ | コミット | 所感 |
|---|---|---|
| `/split_plan` | `11474cd docs(ver6.1): split_plan完了` | 対象 ISSUE が 1 件（`parse-frontmatter-shared-util.md`）と明確。ROUGH_PLAN / IMPLEMENT が計画どおり作成された。小規模判定により `REFACTOR.md` は省略 |
| `/imple_plan` | `c478fed refactor(util): extract shared parse_frontmatter utility (ver6.1)` | IMPLEMENT §1〜§5 にそのまま沿って実装完了。R1（import パス）を `sys.path.insert` 方式で解消、R2（挙動同一性）を既存テストで担保、R3（警告消失）は意図的に受容 |
| `/wrap_up` | `45f8e40 docs(ver6.1): wrap_up完了` | 対応済み ISSUE を `ISSUES/util/done/` に移動（新規ディレクトリ作成） |
| `/write_current` | `4c26e86 docs(ver6.1): write_current完了` | マイナー版のため `CHANGES.md` のみ作成。内部 API のみの変更で `CURRENT.md` / プロジェクト `CLAUDE.md` の更新不要と判定 |
| `/retrospective` | 本コミット | — |

### 良かった点

#### 小規模タスクの簡潔化ルールが機能した

ROUGH_PLAN §「小規模タスク判定」で `REFACTOR.md` の省略、IMPLEMENT.md の簡潔化を明文化し、ドキュメント側も計画コストを圧縮できた。実装も一発で完走し、正味コード変更約 50 行・追加テスト 5 ケースで完結。`/split_plan` SKILL の小規模判定ロジックが意図通りに働いた好例。

#### IMPLEMENT の「挙動同一性マトリクス」が効いた

`parse_feedback_frontmatter` の 4 パターン（no fm / unclosed / invalid yaml / non-dict）を表形式で新旧比較する項を IMPLEMENT.md §2 に置いたことで、リファクタリング時の戻り値分岐漏れをゼロにできた。次回同種のリファクタでも同じフォーマットを推奨したい。

#### ver6.0 retrospective で先送り宣言していた ISSUE を素直に消化できた

ver6.0 RETROSPECTIVE §3 は PHASE6.0（ver7.0 メジャー）推奨だったが、ver6.1 を低コスト（＝ half-day 相当）で挟むことで PHASE6.0 時に `issue_worklist.py` が 3 個目の frontmatter 重複実装を持つのを予防できた。意図的な「先行共通化」として投資効果が高い。

### 改善が必要な点

#### 2-1. AUTO モードで quick ワークフローが選べない（PHASE6.0 で解消予定）

ver6.1 は小規模タスク判定上 quick ワークフローが妥当だったが、AUTO モード運用中は `/split_plan` 冒頭で判断を差し挟めないため、full ワークフローで完走した。`/split_plan` は判定結果を `REQUESTS/AI/quick-workflow-suggestion-ver6.1.md` として記録し、中断せずに続行した（想定どおりの挙動）。

→ PHASE6.0（`--workflow auto` + `/issue_plan`）で `ROUGH_PLAN.md` frontmatter の `workflow: quick | full` を読んで自動分岐する設計が入るため、本問題は **PHASE6.0 の副次効果として自然に解消される**。ver6.1 で個別対応は不要。

#### 2-2. `REQUESTS/AI/` の使用後クリーンアップが retrospective SKILL に未記載

`REQUESTS/AI/quick-workflow-suggestion-ver6.1.md` には「ver6.1 完了後に本ファイルを削除してください」と明記してあるが、`retrospective/SKILL.md` にこの手のリクエストファイルを回収するステップがなく、`wrap_up` でも触れていないため、放置されやすい構造。

→ **`retrospective/SKILL.md` §4 に「当バージョン完結により用済みとなった `REQUESTS/AI/*.md` を削除・または `REQUESTS/AI/done/` などへ移動する」手順を即時追記**。本ステップで実ファイル（`quick-workflow-suggestion-ver6.1.md`）も削除する。

#### 2-3. plan_review_agent が quick 候補タスクに対し過剰にフルレビューを掛ける

小規模リファクタに対しても plan_review_agent の詳細レビューは回ったが、今回の規模では指摘がほぼ発生しない（計画が単純すぎる）一方で実行コストは発生している。PHASE6.0 で「`/issue_plan` が `quick` を選んだ場合は plan_review_agent を起動しない」設計が PHASE6.0 ドキュメントに明記済みのため、こちらも PHASE6.0 で自然に解消される。

→ ver6.1 単独での SKILL 変更は不要。PHASE6.0 時に一体で整える。

### ver6.0 retrospective 持ち越し事項の状況

| 持ち越し事項 | ver6.1 での扱い |
|---|---|
| PHASE6.0 着手 | 未着手（ver6.1 は PHASE6.0 の露払い） |
| `.claude/settings.local.json` の Edit/Write 権限問題 | 本 ver6.1 では `.claude/` 配下書き込みが発生しなかったため検証機会なし。PHASE6.0 で `/issue_plan` 新規作成時に再検証 |
| `WORKFLOW.md` のモデル/effort 使い分け方針明文化 | 未着手。PHASE6.0 で `/issue_plan` 新設時に統合予定 |
| `write_current/SKILL.md` の CLAUDE.md 既存リスト外フォルダ検出強化 | 今回 `ISSUES/util/done/` を新設したが、`ISSUES/` 配下は CLAUDE.md の既存記述でカバーされる運用のため触れていない |
| `ISSUES/util/medium/issue-review-rewrite-verification.md` の実動作確認 | 継続持ち越し（`app` / `infra` カテゴリでのワークフロー起動時に消化） |

## 3. 次バージョンの種別推奨

### 候補の棚卸し

| 候補 | 内容 | 種別 |
|---|---|---|
| A. PHASE6.0（`/issue_plan` 分離 + `--workflow auto`） | ver6.0 RETROSPECTIVE §3 の本命。ver6.1 で共通 `parse_frontmatter` が用意できたため、前提条件が完全に揃った | **メジャー (7.0)** |
| B. `ISSUES/util/medium/issue-review-rewrite-verification.md` の対処 | `app` / `infra` カテゴリでの `/split_plan` 起動時に消化される性質なので util カテゴリからは能動的に着手できない | — |
| C. `WORKFLOW.md` のモデル/effort 使い分け方針明文化 | PHASE6.0 と統合する方が自然 | — |

### 推奨

**PHASE6.0（ver7.0 メジャー）** を推奨。

理由:
- ver6.1 で `parse_frontmatter` 共通化が完了し、PHASE6.0 の `scripts/issue_worklist.py` が再利用する土台が整った。意図した「露払い」が目的どおりに効く
- ver6.0 / ver6.1 の両 retrospective が PHASE6.0 を次の自然な一歩と位置付けており、もうマイナーを挟む積極的理由がない（util カテゴリに残る AI 向け `ready` は medium 1 件のみで、これは util 外カテゴリのワークフローで消化される性質）
- PHASE6.0 自体で `/retrospective` に `issue_worklist.py` 利用手順を追加する設計が含まれるため、ver7.0 の retrospective は本バージョンより次バージョンの取捨選択が楽になる（効果の自己強化）

## 4. 対応済み ISSUES の整理

`ISSUES/util/` 配下に削除対象なし:

- `ISSUES/util/medium/issue-review-rewrite-verification.md` — `ready / ai` で持ち越し中（`app` / `infra` ワークフロー実行時に自然消化）

`ISSUES/util/done/parse-frontmatter-shared-util.md` は ver6.1 で対応完了し `done/` に移動済み。本ステップでの追加移動・削除なし。

## 5. 即時適用したスキル変更

- `.claude/skills/retrospective/SKILL.md` §4: 「当バージョン用の `REQUESTS/AI/*.md` を確認し、用済みなら削除する」手順を追記
- `REQUESTS/AI/quick-workflow-suggestion-ver6.1.md` を削除（PHASE6.0 解消前提、情報提供目的は達成）

## 6. 今後の持ち越し事項

- PHASE6.0 着手（ver7.0 メジャー想定）
- `.claude/settings.local.json` の Edit/Write 権限問題 → PHASE6.0 で `/issue_plan` 新規作成時に再検証
- `WORKFLOW.md` のモデル/effort 使い分け方針明文化 → PHASE6.0 の `/issue_plan` 新設と統合
- `ISSUES/util/medium/issue-review-rewrite-verification.md` の実動作確認 → `app` / `infra` カテゴリワークフロー起動時に自然消化

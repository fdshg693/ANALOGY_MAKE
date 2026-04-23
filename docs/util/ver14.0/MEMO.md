# ver14.0 MEMO

## 実装サマリ

PHASE7.0 §6（retrospective からの FEEDBACK handoff）+ §7（`.claude/rules/scripts.md` 新設と規約集約）+ §8（workflow prompt / model 評価）を一括着手。計画どおり §7（rules）→ §6（handoff）→ §8（prompt 評価）の順で実装し、docs 側の整合も同バージョンで完了。

### 変更ファイル

| ファイル | 操作 | 実際の変更規模 |
|---|---|---|
| `.claude/rules/scripts.md` | 新規作成 | 約 40 行 |
| `.claude/SKILLS/retrospective/SKILL.md` | §3.5 / §4.5 追記 | +98 行 |
| `.claude/SKILLS/issue_plan/SKILL.md` | FEEDBACK 受信指示 1 行追加 | +1 行 |
| `.claude/SKILLS/meta_judge/WORKFLOW.md` | `mode` 誤記訂正 + handoff 言及 | ±4 行 |
| `scripts/README.md` | rules 存在の前書き 1 段落追記 | +2 行 |
| `scripts/USAGE.md` | 拡張ガイド冒頭に rules へのポインタ追記、rules §番号を括弧付与 | ±3 行 |
| `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md` | 新規作成（リスク §6 の先送り記録） | 約 40 行 |

`.claude/` 配下は `scripts/claude_sync.py export → edit → import` 経由で更新し、`git status` で 3 ファイルの diff + 1 ファイルの新規追加を確認済。

## IMPLEMENT.md §6 リスク・不確実性の検証結果

| # | リスク | 結果 |
|---|---|---|
| 1 | rules と docs の責務分離が曖昧化 | **検証済** — 軽減策どおり `.claude/rules/scripts.md` 末尾に「詳細仕様は `scripts/README.md` / `scripts/USAGE.md` を一次資料とする」を明記。`scripts/README.md` 前提条件節にも rules との責務分担を 1 段落で示した |
| 2 | FEEDBACK handoff が感想メモ化 | **検証済** — `/retrospective` §4.5 に「書き出し対象 / 書き出さないケース」を明記し、ファイル名プレフィックスを `handoff_ver*_to_next.md` に固定 |
| 3 | prompt / model 評価の過剰化 | **検証済** — §3.5 に「省略条件」と「差分評価を基本姿勢とする」を明記 |
| 4 | `.claude/` 編集手順のミスで反映漏れ | **検証済** — import 直後に `git status --short .claude/` で `rules/scripts.md`（新規）+ 3 SKILL の diff が入っていることを確認 |
| 5 | `mode` 誤記の連鎖参照 | **検証済** — `grep "^\s*mode:\s"` で `docs/util/MASTER_PLAN/PHASE2.0.md` / `PHASE3.0.md` に残存を確認したが、これらは当時の状態を記録する歴史的 PHASE 文書のため意図的に現状維持（本バージョンは「現行の SKILL / WORKFLOW 誤記訂正」がスコープ）。現行運用に影響する誤記は `meta_judge/WORKFLOW.md` L45 のみで修正済 |
| 6 | `paths:` frontmatter の自動読込挙動が未検証 | **検証先送り** — 本バージョン中にセッションを跨いだ検証ができないため、`ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md` に独立 ISSUE を作成済。次ループ以降の `/retrospective` §3.5 評価で観察対象にする |

## 動作確認

- **既存テスト**: `python -m unittest discover -s scripts/tests -t .` → 233 件全通過（Ran 233 tests, OK）
- **validation**: `python scripts/claude_loop.py --dry-run` → `--workflow auto` phase1 validation pass、phase2 は dry-run のためスキップ（想定どおり）
- **`npx nuxi typecheck`**: vue-router volar 関連の既知エラーで失敗（`sfc-route-blocks.cjs` から `vue-tsc` 解決失敗）。CLAUDE.md「開発上の注意」にて「ビルド・実行に影響なし」と既知明記済。本バージョンは Markdown のみの編集で TypeScript / Vue コードは一切触っていないため、本エラーは本バージョン起因ではない
- **手動確認**:
  - `.claude/rules/scripts.md` の frontmatter + 本文が期待どおり import されていることを確認
  - `retrospective/SKILL.md` に §3.5 / §4.5 が想定位置（§3 の直後 / §4 の直後）に挿入されていることを確認
  - `issue_plan/SKILL.md` の「retrospective からの FEEDBACK handoff」節が ISSUE レビューフェーズの直前に入っていることを確認
  - `meta_judge/WORKFLOW.md` L45 が `command / defaults` に修正されたことを確認

## 関連 ISSUE の次バージョン扱い方針（IMPLEMENT.md §8 より）

| ISSUE | 次バージョンでの判断 |
|---|---|
| `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md`（`raw/ai`） | 本バージョン §7 で scripts 系 CLI 規約を rules §3 に集約済。ver14.1 or 15.0 の retrospective で「rules §3 に吸収できたか」を確認し、吸収済なら `done` 化、残論点があれば `ready` 昇格 |
| `ISSUES/util/low/system-prompt-replacement-behavior-risk.md`（`raw/ai`） | 本バージョン §8 で prompt 評価観点を明文化済。retrospective §3.5 の評価項目として織り込めたかを確認し、織り込み済なら `done` 化 |
| `ISSUES/util/medium/issue-review-rewrite-verification.md`（`ready/ai`） | util 単体消化不能のため本バージョンでは触らず。持ち越し継続 |
| `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md`（新規 `raw/ai`） | 本バージョンで先送り決定したリスク §6 の独立記録。次ループ以降の `/retrospective` §3.5 で観察対象にする |

## 計画との乖離

- `scripts/USAGE.md` の「拡張ガイド」見出し統一について、IMPLEMENT.md §3-4 では「rules の項目番号と整合するよう見出しを統一するのみ」と記載されていた。既存の bullet 見出しは CLI 系（rules §3）/ フィードバック系（rules §4）とそのまま対応が取れるため、見出しを書き換える代わりに **該当 bullet の末尾に `（rules §3）` のような参照を添え**、冒頭に「rules を一次資料とする」1 文を追加する方針に変更した。これは IMPLEMENT.md の意図（「内容は残す」「rules との参照関係を示す」）を保ちつつ、見出し書式の大幅変更を避けるための判断
- `CLAUDE.md` L31 は IMPLEMENT.md §3-4 の予告どおり変更不要

## 将来のリファクタ・ドキュメント候補（`/wrap_up` 以降で判断）

- `.claude/rules/` に今後 `frontend.md` / `infra.md` など category 単位で rule を増やしていく前提で、`.claude/rules/README.md` に責務分担原則（stable / volatile の境界、`paths:` 設計方針）を 1 ファイル集約すると、ver15.0 以降の rule 新設時に判断負荷が下がる。ただし現状 2 ファイルでは過剰設計なので、3 ファイル目を作る時点で要検討
- `scripts/README.md` と `scripts/USAGE.md` の境界が曖昧（拡張ガイドが両方にある）。今回は rules 側への集約を優先したため手を入れていないが、別バージョンで「README = 全体構成・spec、USAGE = 操作手順」に整理する余地あり

## 既存回帰維持確認

- 233 件の既存 unittest 全通過（`Ran 233 tests in 0.462s / OK`）
- `claude_loop.py --dry-run` による validation 全通過
- §4 FEEDBACKS 異常終了 invariant（`TestFeedbackInvariant`）は handoff ファイルも通常 FEEDBACK と同一パス規約で扱われるため暗黙的にカバー。新規テストは追加しない（IMPLEMENT.md §7-2 判断どおり）

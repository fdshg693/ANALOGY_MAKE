---
workflow: research
source: master_plan
---

# ROUGH_PLAN: util ver16.1 — PHASE8.0 §2 deferred execution 着手

## バージョン種別の判定

**マイナーバージョン (ver16.1)**。

判定根拠:
- 本版は PHASE8.0 §2（deferred execution）に着手するもので、新 PHASE 開始ではない。ver16.0 で着手済みの PHASE8.0 の 2 節目にあたる
- 本プロジェクトは「PHASE 単位で major を切る」運用のため、PHASE 内部の節進行はマイナー扱いとする（ver16.0 RETROSPECTIVE §3 で確定済）
- ただし差分規模（新モジュール `deferred_commands.py` 新規・`claude_loop.py` 実行ライフサイクル変更・テスト新規追加）は `quick` 条件（3 ファイル / 100 行）を大幅に超えるため、スケール自体は「メジャー扱い」で進める

## 着手対象 / スコープ

### 実施する（PHASE8.0 §2 内の最小完走セット）

1. **deferred command の登録・外部実行・結果保存・request 削除・session 再開までの 1 経路を無人で完走可能にする**
   - Claude が workflow 実行中に「長時間タスクとして外出しするコマンド群」を構造化ファイルとして登録
   - Python 側ランナーが検知 → 実行 → 結果ファイル保存 → request 削除 → `claude -r <session-id>` で session 再開
   - 登録情報に元 step 名、session ID、作業ディレクトリ、実行コマンド群、期待する成果物、結果出力先、再開時補足メモを含める
   - 非ゼロ終了・タイムアウト時の resume 経路も共通化する

2. **結果ファイル仕様の確立**
   - 結果ファイル単体から「何のコマンドが走ったか」「成功したか」「出力サイズ」が判定可能
   - 巨大ログを prompt へ直接流し込まず、文字数 / サイズ / 先頭サマリを渡す設計

3. **失敗時の orphan request ゼロ保証**
   - 成功・失敗どちらでも registered command request が queue に残らない
   - resume 経路の失敗切り分け（「結果を読んで次の判断をする失敗」 vs 「workflow 自体を止めるべき失敗」）

4. **実現方式の比較整理（`experiments/` に試行記録を残す）**
   - 専用 fixture / worktree / 模擬 queue / wrapper script / file watcher 等の方式比較
   - 本番 `ISSUES/` / `QUESTIONS/` / `FEEDBACKS/` / `logs/workflow/` と queue を共有しない原則の確認

5. **パラレル小改修: `/write_current` effort を medium → high に引き上げ**
   - 根拠: ver16.0 RETROSPECTIVE §3.5 で提起された調整候補。ver16.1 以降で `CURRENT.md` の複雑度が上がる見込みへの先行対応。model は sonnet 維持
   - 対象 YAML: `claude_loop_research.yaml`（本版で使用）。`claude_loop.yaml` / `claude_loop_quick.yaml` は scope 外（必要なら ver16.2 以降）

### 実施しない（明示的に次バージョン以降へ繰り延べ）

- **PHASE8.0 §3（token/cost 計測）は着手しない**。MASTER_PLAN では ver16.2 に割当済。§2 / §3 を 1 バージョンで同時進行するとリスクが相互干渉するため分離
- **workflow 自己テストの本番組込み / CI ジョブ化は行わない**。PHASE8.0 §2-2 で「可能性の探索と小さな試行まで」と明記（`experiments/` 配下での方式比較メモのみ）
- **YAML sync 契約の自動化（生成元 1 箇所化 or 起動時 validation 強化）**。ver16.0 で課題提起済だが本版スコープ外。§2 で YAML が増えた場合の影響評価までにとどめ、自動化は ver16.2 以降で判断
- **持ち越し 4 件の ISSUE 消化**（`issue-review-rewrite-verification` / `toast-persistence-verification` / `rules-paths-frontmatter-autoload-verification` / `scripts-readme-usage-boundary-clarification`）は本版では据え置き
- **新 PHASE 骨子作成**。PHASE8.0 は §2 / §3 が残存するため PHASE9.0 等の新設は不要

## 想定成果物（現時点）

| 成果物 | 種別 | 備考 |
|---|---|---|
| `scripts/claude_loop_lib/deferred_commands.py` | 新規 | request 登録 / 外部実行 / 結果保存 / 削除 / resume 入力生成 |
| `scripts/claude_loop.py` | 変更 | deferred execution の実行ライフサイクル分岐追加 |
| `scripts/claude_loop_lib/logging_utils.py` | 変更 | deferred result のログ整形追加 |
| `scripts/claude_loop_lib/validation.py` | 変更 | registered command schema の検証追加 |
| `scripts/claude_loop_research.yaml` | 変更 | `/write_current` effort を medium → high に更新 |
| `scripts/tests/test_deferred_commands.py` | 新規 | request cleanup / 結果ファイル / resume 情報生成の単体テスト |
| `scripts/tests/test_claude_loop_integration.py` | 変更 | deferred execution → resume の統合経路検証 |
| `scripts/README.md` / `scripts/USAGE.md` | 変更 | deferred execution と結果ファイル仕様の説明追記 |
| `experiments/deferred-execution/` | 新規 | 方式比較の試行記録（`experiments/README.md` の規約に準拠） |
| `docs/util/ver16.1/RESEARCH.md` | 新規 | research workflow 成果物。外部仕様 / 既存 session 再開機構の調査 |
| `docs/util/ver16.1/EXPERIMENT.md` | 新規 | research workflow 成果物。方式比較の実証ログ |
| `docs/util/ver16.1/IMPLEMENT.md` / `REFACTOR.md` / `MEMO.md` / `CHANGES.md` | 新規 | マイナー版標準セット |

※ 詳細 API / schema / file layout は IMPLEMENT.md で確定させる（ROUGH_PLAN では仕様に踏み込まない）。

## ワークフロー選択根拠

**`workflow: research`** を選定。

PHASE8.0 §2 は「MASTER_PLAN の新項目着手（※PHASE 内部の節進行ではあるが実質アーキテクチャ変更を伴う）」に該当し、かつ `research` 選定 4 条件のうち **2 条件を明確に満たす**:

- ✅ **実装方式を実験で絞り込む必要がある**（「専用 fixture / worktree / 模擬 queue / wrapper script / file watcher 等」の方式比較が PHASE8.0 §2-2 で明記されている）
- ✅ **軽い隔離環境（`experiments/` 配下）での試行が前提**（PHASE8.0 §2-2 で `experiments/` での方式整理が明記）
- （参考）「1 step で 5 分以上の実測系検証」「外部仕様・公式 docs の確認」は主要条件ではないが、`claude -r <session-id>` の動作確認で一部該当する可能性あり

追加理由: ver16.0 で新設した `research` workflow の **初の本格 self-apply ケース**として最適（`research` workflow の実走評価が次ループ retrospective で可能）。

## 事前リファクタリング要否

**要否: 要（軽度）**。

結論のみ: `scripts/claude_loop.py` の実行ライフサイクルへ deferred execution の分岐を差し込む前に、既存の session 継続・step 切替ロジックの責務境界を `workflow.py` との間で軽く整理しておく価値がある。根拠は `PLAN_HANDOFF.md` を参照。

## ISSUE レビュー結果

- ready/ai に遷移: **1**（`ISSUES/util/low/toast-persistence-verification.md`）
- need_human_action/human に遷移: 0
- 追記した `## AI からの依頼`: 0

判定根拠（`toast-persistence-verification.md`）:
- 再現手順（人間追記の「薄いテストスクリプト切り出し」）、期待動作（Action Center 永続表示の目視確認）、影響範囲（`notify.py::_notify_toast` と PHASE7.1 §4 完了条件）の 3 点が揃っており、`ready / ai` 判定基準の「2 点以上読み取れる」を満たす
- 人間追記で「AI に薄いスクリプトを切り出してもらい、人間が手元で実行して結果を貼る」運用が明示されており、AI 側で実施可能な作業（スクリプト切り出し）が定義できる
- ver16.1 スコープには含めない（持ち越し判断）が、queue 状態は `ready / ai` に正常化

## ISSUE 状態サマリ

| status / assigned | 件数 |
|---|---|
| ready / ai | 2 |
| review / ai | 0 |
| need_human_action / human | 0 |
| raw / human | 0 |
| raw / ai | 2 |

# ver7.0 RETROSPECTIVE — issue_worklist.py 導入（PHASE6.0 §1 + §4）

## 1. ドキュメント構成整理

### 1-1. `docs/util/MASTER_PLAN.md` の状態

- PHASE1.0〜PHASE5.0 実装済、PHASE6.0 が「一部実装済み」に更新済み（§1 / §4 完了、§2 / §3 未着手）
- 行数は現状 11 行で肥大化の兆候なし。分割・再構成の必要なし
- `MASTER_PLAN/PHASE6.0.md` 側に実装進捗テーブルを持っており、MASTER_PLAN.md 本体は 1 行サマリで追えるため、この構造を維持する

### 1-2. `CLAUDE.md` の肥大化チェック

- プロジェクトルート `CLAUDE.md` は 60 行弱で問題なし
- `.claude/CLAUDE.md` は `@./claude_docs/ROLE.md` を読み込むだけの薄いエントリ。ROLE.md も 15 行程度。分割不要
- `scripts/` / `app/` / `server/` 等のサブフォルダ固有 CLAUDE.md は現状存在しないが、ver7.0 時点では scripts 側の情報は `scripts/README.md` に集約されており、サブフォルダ CLAUDE.md を切り出す必要性は薄い。将来 `scripts/claude_loop_lib/` 内部のルールが増えたタイミングで改めて検討

**結論**: ver7.0 時点でドキュメント構成は健全。再構成提案なし。

## 2. バージョン作成の流れの検討

### 2-1. 各ステップの効果

| ステップ | 評価 | コメント |
|---|---|---|
| `/split_plan` | ◎ | スコープ切り出し（§1 + §4 のみで §2 / §3 / §5 部分を後送り）が的確。ROUGH_PLAN で「事前リファクタリング未確定 → IMPLEMENT で確定」と明記する運用が機能した |
| `/imple_plan` | ◎ | 事前リスク（R1〜R5）を全て IMPLEMENT に書いており、特に R5（`.claude/` 編集権限）がそのまま顕在化 → `claude_sync.py` 経由で即対処できた |
| `/wrap_up` | ○ | MEMO 追記と MASTER_PLAN 進捗表の追加のみで完了。新規スクリプト＋テストは最初から完成度が高く wrap_up のフィードバック量が少なかった（＝事前計画の質が高かった証拠） |
| `/write_current` | ◎ | `CURRENT.md` を 4 ファイル（本体 + scripts/skills/tests）に分割した構成が初採用で、ver8.0 向けテンプレとして有効 |
| `/retrospective` | ◎ | §3 に `issue_worklist.py` の `!` バックティック展開が入ったことで、本ステップ冒頭で util の着手候補が自動展開される UX が実動作した（ドッグフーディング成功） |

### 2-2. 流れに対する改善提案（即時適用対象）

#### 改善 1: `split_plan` SKILL に「スコープ切り出し」のガイドラインを追加すべきか

ver7.0 は PHASE6.0（5 節構成の大フェーズ）を §1+§4 に絞る判断を ROUGH_PLAN で下した。この「大フェーズを複数バージョンに分割する判断」は現在 SKILL に明文化されていない。PHASE6.0 §2（`/issue_plan`）が実装されれば、`/issue_plan` 側で ROUGH_PLAN を生成する時点で扱う件数を制限するロジックが入るため、`/split_plan` への追記は ver8.0（§2 実装時）で一体化して行うのが合理的。

→ **本バージョンでは追加しない**（§2 実装時に `/issue_plan` + `/split_plan` の責務整理と合わせて記述する）。

#### 改善 2: `.claude/` 配下編集の権限問題の恒久対応

IMPLEMENT R5 として想定されていた通り、本ステップを含めて `.claude/skills/retrospective/SKILL.md` への直接 Edit がツール権限で弾かれるため、`scripts/claude_sync.py` 経由が必要だった。この制約は ver6.0 retrospective から繰り返し顕在化している。

→ 恒久対応候補:
  - (A) `claude_sync.py` の使用手順を `scripts/README.md` に明記（現状も簡易記載あり）
  - (B) ワークフロー側で `.claude/` 編集ステップを検出したら `claude_sync export` を自動実行するフックを追加
  - (C) settings.json の permission を緩和

いずれも ver7.0 スコープ外（スキル設計の大きな変更を伴う）。本 RETROSPECTIVE の「引き継ぎ」に記録するに留める。

#### 改善 3: `retrospective/SKILL.md` §3 の json 展開

現状 `- 機械可読形式: !`python scripts/issue_worklist.py --format json`` として整形 JSON がそのまま埋め込まれる。ISSUE 件数が増えると SKILL コンテキストが肥大化するリスクあり。今回は util カテゴリで 1 件のため問題なかったが、app カテゴリで実行すると 6 件ほど展開される。

→ **即時適用**: 現段階では件数が少ないため問題なし。将来 ISSUE が膨張した際に「件数しきい値で自動省略」などの対応を検討する。本 RETROSPECTIVE では変更しない。

### 2-3. 即時適用したスキル変更

**なし**（ver7.0 で `/retrospective` SKILL §3 に `issue_worklist.py` 呼び出しを追加する改善は本バージョンの実装範囲内で §4 として既に適用済み。本ステップで追加の変更は発生せず）。

## 3. 次バージョンの種別推奨

### 3-1. 現カテゴリの着手候補（util）

`python scripts/issue_worklist.py` の結果:

- `medium | ready | ai | ISSUES/util/medium/issue-review-rewrite-verification.md`（ver6.0 からの持ち越し、`reviewed_at: 2026-04-23`）

件数 1 件。これは `issue_review` SKILL の書き換えロジック実動作確認であり、app/infra ワークフロー起動時にのみ消化可能な性質のため、util ワークフローでは直接取り組めない（ver7.0 ROUGH_PLAN でも同判断）。

### 3-2. MASTER_PLAN の次項目

PHASE6.0 §2（`/issue_plan` SKILL 新設 + `/split_plan` 責務縮小）が最有力。§3（`--workflow auto`）は §2 の成果物（ROUGH_PLAN frontmatter の `workflow` フィールド）を前提とするため §2 完了後が適切。

### 3-3. 次バージョン種別の推奨

**メジャー = ver8.0 を推奨**。

判定根拠:

- PHASE6.0 §2 は **新 SKILL（`/issue_plan`）の追加 + 既存 SKILL（`/split_plan` / `/quick_plan`）の責務変更 + YAML ワークフロー構造変更** を含む。CLAUDE.md の版管理規則「メジャー = 新機能追加・アーキテクチャ変更・MASTER_PLAN の新項目着手時」に合致する
- ver7.0 ROUGH_PLAN / IMPLEMENT では §2 を「ver7.1 想定」と記載しているが、これは PHASE6.0 全体を「6.x 系で完遂する」発想での便宜表記。実体はアーキテクチャ変更のためメジャー相当
- 持ち越し ISSUE（`issue-review-rewrite-verification.md`）は util ワークフロー外での消化のため、メジャー版立ち上げの判断には影響しない
- マイナー版（ver7.1）として扱うとしたら、PHASE5.0 時代のようにフェーズ中の小粒な追加（`raw / review / ready` ラベル運用の微調整等）に留まる案件が前提。今回の §2 はスコープがそれを大きく超える

**代替案**: もし §2 を ver7.1（マイナー）で通すなら、ROUGH_PLAN 冒頭に「本バージョンは PHASE6.0 の分割作業中のため便宜的にマイナー扱いとする」と明記し、CURRENT.md は ver7.0 のものを差分更新するに留める運用が必要。推奨しない。

→ **最終推奨: 次バージョンは ver8.0（メジャー）として PHASE6.0 §2 に着手する**。

## 4. 振り返り結果の記録

### 4-1. ISSUES ファイルの整理

- `ISSUES/util/medium/issue-review-rewrite-verification.md` → **削除しない**。`status: ready / ai` で次バージョン以降の消化待ち。app/infra ワークフローに組み込まれた `issue_review` SKILL の書き換えロジックを実動作で検証するもので、util カテゴリ単体では消化不能。ver6.0 → ver6.1 → ver7.0 と持ち越し中。次の app/infra 着手時に再評価する
- `ISSUES/util/high/` / `ISSUES/util/low/` → 空。変更なし
- 他カテゴリ（app / infra / cicd）の ISSUE は本バージョンのスコープ外のため触らない

### 4-2. `REQUESTS/AI/` の整理

- `REQUESTS/AI/` 配下は `README.md` のみ。ver7.0 固有の用済みファイルは存在しない。変更なし

### 4-3. 即時適用したスキル変更

本ステップで追加の `.claude/` 配下変更は実施していない。ver7.0 本体実装で `/retrospective` SKILL §3 に `issue_worklist.py` 呼び出しを追加する改善は完了済み（PHASE6.0 §4 として実装範囲に含まれていたため、本ステップでの追加適用は不要）。

### 4-4. 次バージョン ver8.0 への引き継ぎ

PHASE6.0 §2 着手時の注意点:

1. **`claude_sync.py` 運用**: `.claude/SKILLS/` 配下の新規作成・編集が多発する。ver7.0 でも R5 として顕在化しており、imple_plan 冒頭で必ず権限チェックしてから `claude_sync.py export` → 編集 → `import` のフローに切り替える
2. **`claude_loop_lib/issues.py` 再利用**: ver7.0 で作った `extract_status_assigned` は 4-tuple（`status, assigned, fm, body`）で、`fm["priority"]` や本文参照が可能。`/issue_plan` SKILL の自動 frontmatter 生成（`ROUGH_PLAN.md` の `workflow: quick | full` 決定）で再利用する
3. **`/quick_plan` の扱い**: PHASE6.0 §2-3 では「`/issue_plan` のラッパーにするか削除するか」を選択肢としている。quick ワークフローの既存利用者（現状は util カテゴリのみ）への影響を確認してから判断する
4. **ROUGH_PLAN frontmatter の壊れ対応**: PHASE6.0 リスク §3 に記載の通り、`workflow` 未記載時は `full` フォールバックを実装する
5. **テスト**: `tests/test_claude_loop.py` に `--workflow auto` 分岐の解決ロジックテストを追加（PHASE6.0 §5 準拠）

### 4-5. 今バージョンからの学び（手法面）

- **スコープ切り出しの判断をコミット 1 つ目（split_plan）に入れたことが奏功**: PHASE6.0 全 5 節を一気にやろうとせず §1+§4 に絞った結果、1491 行の増加（うち 520 行は IMPLEMENT.md）で収まり、レビュー可能な粒度で着地した
- **IMPLEMENT.md §7 のリスク列挙が事前対処として機能**: R5（`.claude/` 編集権限）が想定通り発現し、即座に `claude_sync.py` 経由へ切替。事前列挙がなければ imple_plan 中に混乱していた可能性大
- **新規スクリプト + ユニットテストの組み合わせは事前計画どおりに進みやすい**: 既存コードへの影響が極小で、手戻りが発生しなかった。大きな SKILL 責務変更を伴う §2（ver8.0 想定）では同じレベルの進捗は期待できないため、ROUGH_PLAN で追加の安全策（フィーチャーフラグ、旧パス併存など）を盛り込む必要あり

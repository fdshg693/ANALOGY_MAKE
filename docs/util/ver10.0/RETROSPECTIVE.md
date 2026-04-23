# ver10.0 RETROSPECTIVE — workflow YAML step 単位 system prompt / model override（PHASE7.0 §1）

## 1. ドキュメント構成整理

### 1-1. `docs/util/MASTER_PLAN.md` の状態

- 1 行サマリ形式を維持。`PHASE7.0.md` の項目を「**一部実装済み**」に更新済（`dbac9c9`）。肥大化の兆候なし
- `MASTER_PLAN/PHASE7.0.md` の進捗表に §1 = 「**部分完了**（条件①②充足、条件③は ver10.1 待ち）」を反映済
- **再構成提案: なし**（PHASE7.0 は §2〜§8 が控えており、現バージョン番号枠 ver10.x で十分吸収可能）

### 1-2. `CLAUDE.md` の肥大化チェック

- ルート `CLAUDE.md` 60 行台、`.claude/CLAUDE.md` は ROLE.md 参照のみで健全
- ver10.0 で追加した override キーの説明は `scripts/README.md` に集約済で、CLAUDE.md への波及はなし
- **分割提案: なし**

### 1-3. ISSUES ディレクトリ健全性

- util カテゴリ 4 件（medium 3 / low 1）。ver10.0 開始時 1 件 → wrap_up で 3 件追加（後述 §4-1）
- 件数閾値（おおむね 10 件超で構成検討）には未到達
- **構成変更提案: なし**

### 1-4. 現行 PHASE 完走状態

- PHASE7.0 §1 が部分完了、§2〜§8 が未着手のため、**現行 PHASE は完走していない**
- 次バージョンは PHASE7.0 内で進める（新 PHASE 骨子作成は不要）

## 2. バージョン作成の流れの検討

### 2-1. 各ステップの効果

| ステップ | 評価 | コメント |
|---|---|---|
| `/issue_plan` | ◎ | `workflow: full` / `source: master_plan` を frontmatter に正しく記録。`ready / ai` 1 件は util 単体消化不能と判定し、PHASE7.0 §1 起点を採用。判断経緯（§「なぜ MASTER_PLAN 起点」「なぜ §1 のみスコープ」「なぜ full」）が ROUGH_PLAN に明文化された |
| `/split_plan` | ◎ | IMPLEMENT.md 463 行に展開。override 対象キー（4 種に限定）の決定根拠、`temperature`/`max_tokens` 不採用理由（CLI フラグ非対応）、`--append-system-prompt` 二重渡し問題の温存方針、descriptor 行への存在ビット追加など、§1 完了条件①②③とリスク 5-1〜5-6 を事前に列挙。`plan_review_agent` 経由で実装計画 review を実施 |
| `/imple_plan` | ◎ | IMPLEMENT.md §6 の実装順序に沿い、TDD 寄りで `OVERRIDE_STRING_KEYS` / `ALLOWED_STEP_KEYS` 定数化 → テスト 32 件追加 → `commands.py` 拡張 → descriptor → README の順で進行。MEMO「計画との乖離: なし」 |
| `/wrap_up` | ◎ | MEMO に列挙した 6 リスク中、検証可能な 4 件は検証済、検証先送り 2 件は ISSUES 化（cli-flag-compatibility / system-prompt-replacement-risk）。pre-existing な test 失敗も ISSUES 化。PHASE7.0.md 進捗表更新も同時実施 |
| `/write_current` | ◎ | ver8.0〜ver9.0 と同形式の 4 分割（`CURRENT.md` + `_scripts/_skills/_tests`）を維持。util ISSUES 状況の最新表（4 件）も格納 |
| `/retrospective` | — | 本ステップ |

### 2-2. 流れに対する改善提案

ver10.0 は MEMO に「計画との乖離: なし」と明記されているとおり、6 ステップが事前計画どおり進行した。SKILL 改修につながる構造的問題は観察されなかった。

検討した観点（いずれも改修不要と判断）:

- **a. `--workflow auto` 実走**: `--workflow auto` で本バージョンを最初から最後まで通したことで、ver9.0 RETROSPECTIVE §2-4 で残された 5 観察項目（フェーズ遷移・ROUGH_PLAN 同定・残予算計算・Unicode 出力・mtime 同定）が**事故なく動作**することが実地確認できた。`auto-mtime-robustness.md` 由来の閾値方式（ver9.1）も問題発生せず → 関連 ISSUE は ver9.0 完了時点で削除済（`ver9.1/CHANGES.md` 参照）。SKILL 改修不要
- **b. `/imple_plan` の baseline test 確認**: `tests.test_claude_loop.TestIssueWorklist.test_limit_omitted_returns_all` の **pre-existing 失敗** が wrap_up 段階で発覚した（実装変更前から fail していたが ver10.0 開始時点で気づかれていなかった）。`/imple_plan` か `/split_plan` の冒頭で baseline テスト全件 run を義務化すれば早期検知できるが、**現状の SKILL も「テスト pass を必須」と書かれており、運用上はカバーされている**（ver10.0 でも実装後の最終 pass 確認の段階で検知された）。新たな手順追加よりも、検出時に ISSUES 化して持ち越す現運用で十分と判断。SKILL 改修不要
- **c. リスク事前列挙の効果**: IMPLEMENT.md §5（5-1〜5-6）で計 6 リスクを事前列挙し、wrap_up でその 6 件に逐一対応する形が機能した（4 件検証済 / 2 件 ISSUES 化）。ver8.0 から続く「リスク列挙 → wrap_up で対応マトリクス」の運用が安定している。SKILL 改修不要

### 2-3. 即時適用したスキル変更

**なし**。ver10.0 は事前計画どおり進行したため、`.claude/skills/` 配下への即時適用は行わない。

## 3. 次バージョンの種別推奨

### 3-1. 判定材料 3 点の突合

1. **ISSUE 状況**: `ready / ai` は util 4 件（medium 3 / low 1）。
   - `cli-flag-compatibility-system-prompt.md`（medium、ver10.0 由来、新 override キーの実値投入時の CLI flag 互換性）
   - `test-issue-worklist-limit-omitted-returns-all.md`（medium、pre-existing test 失敗の原因調査）
   - `issue-review-rewrite-verification.md`（medium、ver6.0 持ち越し、util 単体消化不能）
   - `system-prompt-replacement-behavior-risk.md`（low、`--system-prompt` 利用時の置換リスク注記）
2. **MASTER_PLAN の次項目**: PHASE7.0 §2「起動前 validation」が **ver10.0 想定だった枠で未着手**。§1 完了条件③（model 名・型不正の実行前 validation）の充足は §2 に委ねる設計のため、**次バージョンの最有力候補は §2**
3. **現行 PHASE 完走状態**: 未完走（§1 部分完了 / §2〜§8 未着手）。新 PHASE 骨子作成は不要

### 3-2. 推奨

**推奨: ver10.1（マイナー）で `test-issue-worklist-limit-omitted-returns-all.md` を quick で消化 → ver11.0（メジャー）で PHASE7.0 §2 起動前 validation に着手**

推奨根拠:

- PHASE7.0 §2「起動前 validation」は MASTER_PLAN の新項目着手 + アーキテクチャ寄り変更（全 step 走査 + schema 検証 + エラー集約報告）であり、CLAUDE.md 版管理規則「メジャー = MASTER_PLAN 新項目着手・アーキテクチャ変更」に合致 → `ver11.0` メジャー + `workflow: full` が妥当
- PHASE7.0 §2 と §1 完了条件③は密結合だが、ver10.0 直後に §2 へ飛ぶより、**先に pre-existing な test 失敗（`test_limit_omitted_returns_all`）を片付けて baseline 健全性を確保**してから §2 に着手するほうが、ver11.0 で「validation 追加によるテスト全件 pass」を確実に保証しやすい
- `test_limit_omitted_returns_all` 単体消化は `tests/test_claude_loop.py` の修正 ± `scripts/issue_worklist.py` の挙動確認の 1〜2 ファイル想定で quick 適合（小規模・単一 ISSUE・新規ライブラリなし）
- `cli-flag-compatibility-system-prompt.md` / `system-prompt-replacement-behavior-risk.md` は **§2 起動前 validation の中で吸収できる可能性が高い**（model 名検証・system_prompt 利用時の警告など）。ver11.0（PHASE7.0 §2）と束ねて消化するほうが効率的なため、ver10.1 では拾わない
- `issue-review-rewrite-verification.md` は引き続き util 単体消化不能。持ち越し継続

**代替案 A（採用しない）**: ver10.1 で PHASE7.0 §2 へ直接着手。利点は完了条件③を最短で満たせること。欠点は `test_limit_omitted_returns_all` の pre-existing 失敗が放置されたまま新規 validation テストが大量追加され、テスト全件 pass の判定が「pre-existing 1 件除き pass」のままドリフトすること

**代替案 B（採用しない）**: ver10.1 で `cli-flag-compatibility` と `system-prompt-replacement-risk` を含めて quick 消化。欠点は §2 起動前 validation との内容重複が大きく、ver11.0 で再触する手戻りが発生すること

→ **最終推奨: ver10.1（マイナー、quick）で `test-issue-worklist-limit-omitted-returns-all.md` を消化。PHASE7.0 §2 着手は ver11.0 以降**

## 4. 振り返り結果の記録

### 4-1. ISSUES ファイルの整理

- **持ち越し**（削除しない、理由記載済）:
  - `ISSUES/util/medium/issue-review-rewrite-verification.md` — ver6.0 からの持ち越し継続。util 単体消化不能（app/infra ワークフロー起動待ち）
  - `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md` — ver10.0 由来。新 override キー（`system_prompt` / `append_system_prompt`）の CLI flag 互換性確認は実値投入時に顕在化するため検証先送り。ver11.0（PHASE7.0 §2 起動前 validation）で吸収予定
  - `ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md` — ver10.0 由来。pre-existing test 失敗の原因調査と修正。ver10.1 で消化予定（§3-2）
  - `ISSUES/util/low/system-prompt-replacement-behavior-risk.md` — ver10.0 由来。`--system-prompt` 利用時の置換リスク注記。ver11.0 で §2 と束ねて消化予定
- **削除**: なし
- **frontmatter 無しファイル**: なし

### 4-2. `REQUESTS/AI/` の整理

- `REQUESTS/AI/` 配下に実ファイルなし（`README.md` のみ）。**変更なし**

### 4-3. 即時適用したスキル変更

**なし**（§2-3 のとおり）。

### 4-4. 次バージョン ver10.1 への引き継ぎ

`test-issue-worklist-limit-omitted-returns-all.md` 消化時の注意点:

1. **対応方針**: ISSUE 本文の調査要点に従い、まず `python -m unittest tests.test_claude_loop.TestIssueWorklist.test_limit_omitted_returns_all -v` を再現実行 → `--limit` 省略時の `issue_worklist.py` 出力件数を確認 → 期待値と実装のどちらが正しいかを判定
2. **想定される原因**: ver9.2 で `--limit` 追加（`2a36378`）時にデフォルト挙動（省略 = 全件）が壊れた可能性。ただし当時 retrospective ではテスト pass 確認済（`ver9.2/quick_doc` 完了）であり、その後の `2992c49`〜`a512fb7` のいずれかで混入した可能性も
3. **quick ワークフロー適合性**: 変更ファイルは `scripts/issue_worklist.py` + `tests/test_claude_loop.py` の 2 本程度の見込み。ROUGH_PLAN.md `workflow: quick` で適切
4. **PHASE7.0 §2 着手の前提条件**: 本 ISSUE 消化により、ver11.0 開始時点で `python -m unittest tests.test_claude_loop` が**全件 pass する状態**を確保できる。これが §2 起動前 validation で大量のテスト追加を行う際の baseline となる
5. **PHASE7.0 §2 のスコープ予告（ver11.0 で扱う）**: §2-1 検証対象 5 項目（category 妥当性 / YAML 存在・schema / 全 step 解決可能性 / override 設定の許容範囲 / 入出力条件）と §2-2 期待挙動 3 項目（実行前一括停止 / エラー集約報告 / 「最後まで到達可能」最低保証）。`cli-flag-compatibility` / `system-prompt-replacement-risk` も同バージョンで吸収を検討

### 4-5. 今バージョンからの学び（手法面）

- **「override 対象キーの限定列挙」設計判断**が拡張容易性とのバランスを取れた。`temperature` / `max_tokens` を「CLI flag 非対応のため YAML に書かれてもエラー」と明示的に reject する方針（silent ignore せず）により、将来 §2 起動前 validation での schema 検証拡張が直接的に積み上がる
- **`--append-system-prompt` の二重引数化問題を ver10.0 では温存し PHASE7.0 §3 に委ねた判断**は、「§1 と §3 を別バージョンに分ける」スコープ分離（ROUGH_PLAN §「なぜ §1 のみ」）と整合。混ぜると CLI 互換性破壊と新機能導入が同コミット化してレビュー困難になる
- **descriptor 行への存在ビット追加**（`SystemPrompt: set` / `AppendSystemPrompt: set`）は、値そのものを表示せず存在のみ示す設計により、ログ肥大化を防ぎつつ「step ごとに override が効いているか」をオペレータが目視確認できるようにした。値表示が必要になったら ver11.0 §2 validation で「resolved 設定のダンプ」機能として追加可能
- **pre-existing test 失敗の wrap_up 段階での発覚**は、`/imple_plan` 完了時点でテスト pass 確認はしているものの、開始時点での baseline 確認が無いことに起因する観察。SKILL 強制までは不要だが、`/issue_plan` 段階で「現状テスト全件 pass か」を `MEMO.md` または `ROUGH_PLAN.md` の脚注に書き残す運用を ver10.1 で試行する価値あり（強制せず観察に留める）
